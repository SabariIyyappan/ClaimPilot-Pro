from fastapi import FastAPI, UploadFile, File, Form, Request
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from app.schemas import UploadRequest, SuggestRequest, SuggestResponse, ClaimRequest, ClaimResponse, Entity, CodeSuggestion
from app.ocr import extract_text_from_image_bytes, extract_text_from_pdf_bytes
from app.ner import extract_entities
from app.embeddings import embed_texts
from app.retrieval import FaissIndexWrapper
from app.llm_refine import refine, generate_codes_from_text
import os
import uuid
from typing import List, Dict, Tuple, Optional

load_dotenv()
app = FastAPI(title="ClaimPilot Coding Agent - Skeleton")


@app.post("/upload")
async def upload(file: UploadFile = File(None), text: str = Form(None)):
    """Accept a file (PDF/image) or plain text. Return extracted text and entities."""
    extracted = ""
    if file is not None:
        content = await file.read()
        if file.filename.lower().endswith('.pdf'):
            extracted = extract_text_from_pdf_bytes(content)
        else:
            extracted = extract_text_from_image_bytes(content)
    if text:
        # prefer provided text if present
        extracted = text

    ents = extract_entities(extracted)
    return {"text": extracted, "entities": ents}


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(
    request: Request,
    text: Optional[str] = Form(None),
    top_k: Optional[int] = Form(None),
):
    # Accept both JSON and form-data; JSON wins when present
    ct = request.headers.get("content-type", "").lower()
    if "application/json" in ct:
        try:
            data = await request.json()
            if isinstance(data, dict):
                text = data.get("text", text)
                top_k = data.get("top_k", top_k)
        except Exception:
            pass
    text = text or ""
    top_k = top_k if top_k is not None else 5
    # 1) Extract entities
    ents: List[Dict] = extract_entities(text)

    # Prefer direct LLM coding when enabled (default)
    suggest_mode = os.environ.get("SUGGEST_MODE", "llm").lower()
    if suggest_mode == "llm":
        direct = generate_codes_from_text(ents, text, top_k=top_k)
        ents_models = [Entity(text=e.get('text',''), label=e.get('label',''), start=e.get('start',0), end=e.get('end',0)) for e in ents]
        suggestions: List[CodeSuggestion] = []
        for r in direct:
            suggestions.append(CodeSuggestion(
                code=str(r.get('code','')),
                system=str(r.get('system','ICD-10')),
                description=str(r.get('description','')),
                score=float(r.get('score',0.0)),
                reason=str(r.get('reason',''))
            ))
        return SuggestResponse(entities=ents_models, suggestions=suggestions)

    # 2) Load FAISS index (hybrid mode)
    idx = FaissIndexWrapper(
        index_path="data/faiss.index",
        desc_path="data/descriptions.npy",
        meta_path="data/meta.npy",
    )

    # 3) Hybrid retrieval: full text + key entity phrases
    def _pick_entity_phrases(items: List[Dict], max_n: int = 3) -> List[str]:
        seen = set()
        # prefer longer, meaningful snippets
        texts = sorted([str(e.get("text", "")) for e in items if e.get("text")], key=len, reverse=True)
        out = []
        for t in texts:
            t2 = t.strip()
            if len(t2) < 3:
                continue
            key = t2.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(t2)
            if len(out) >= max_n:
                break
        return out

    all_candidates: List[Dict] = []
    try:
        # Full text query
        q_full = embed_texts([text])
        all_candidates.extend(idx.search(q_full, top_k=max(top_k, 10)))

        # Entity phrase queries
        phrases = _pick_entity_phrases(ents, max_n=3)
        if phrases:
            q_ents = embed_texts(phrases)
            all_candidates.extend(idx.search(q_ents, top_k=max(top_k, 10)))

        # Targeted keyword expansion to improve CPT coverage (MRI, consult, therapy, arthroscopy, etc.)
        kw_phrases: List[str] = []
        tl = text.lower()
        if "mri" in tl or "magnetic resonance" in tl:
            # Include knee/LE joint variants
            kw_phrases += [
                "MRI knee",
                "magnetic resonance imaging knee",
                "MRI lower extremity joint",
                "knee MRI without contrast",
                "MRI joint knee",
            ]
        if "arthroscop" in tl or "surgery" in tl or "repair" in tl:
            kw_phrases += [
                "arthroscopic knee repair",
                "knee arthroscopy",
                "arthroscopic meniscal repair",
            ]
        if "consult" in tl or "outpatient" in tl or "follow-up" in tl:
            kw_phrases += [
                "outpatient consult",
                "evaluation and management new patient",
                "follow-up visit outpatient",
            ]
        if "therapy" in tl or "physical therapy" in tl:
            kw_phrases += [
                "physical therapy session",
                "therapeutic exercise",
            ]
        if kw_phrases:
            q_kw = embed_texts(kw_phrases)
            all_candidates.extend(idx.search(q_kw, top_k=max(top_k, 10)))
    except Exception:
        all_candidates = []

    # 4) Aggregate and apply lightweight heuristics
    def _aggregate(cands: List[Dict]) -> List[Dict]:
        agg: Dict[Tuple[str, str], Dict] = {}
        for c in cands:
            code = str(c.get("code", ""))
            system = str(c.get("system", ""))
            desc = str(c.get("description", ""))
            score = float(c.get("score", 0.0))
            key = (code, system)
            if key not in agg or score > agg[key]["score"]:
                agg[key] = {"code": code, "system": system, "description": desc, "score": score}

        # Heuristic boosts based on clinical text
        text_lower = text.lower()
        icd_cues = ["diagnos", "tear", "fracture", "pain", "disease", "injury", "infarct", "diabetes", "hypertension", "infection"]
        cpt_cues = ["arthroscop", "surgery", "repair", "procedure", "consult", "outpatient", "therapy", "mri", "ct", "x-ray", "injection", "stent", "placement"]
        icd_boost = 0.08 if any(k in text_lower for k in icd_cues) else 0.0
        cpt_boost = 0.08 if any(k in text_lower for k in cpt_cues) else 0.0

        out = []
        for v in agg.values():
            boost = icd_boost if v["system"].upper().startswith("ICD") else (cpt_boost if v["system"].upper().startswith("CPT") else 0.0)
            v2 = dict(v)
            v2["score"] = float(v["score"]) + boost
            out.append(v2)
        out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return out

    aggregated = _aggregate(all_candidates)

    # 5) Use LLM refine when available; fallback otherwise
    # Send a broader pool to the LLM for better choice; keep up to 20
    pool_for_llm = aggregated[:20] if aggregated else []
    refined = refine(ents, pool_for_llm, clinical_text=text, top_k=top_k)

    # 6) Enforce desired mix: 1 ICD-10 + 2 CPT when possible
    def _enforce_mix(ref: List[Dict], pool: List[Dict], k: int) -> List[Dict]:
        # Try to include both ICD and CPT when available, up to k
        icd = [r for r in ref if str(r.get("system", "")).upper().startswith("ICD")]
        cpt = [r for r in ref if str(r.get("system", "")).upper().startswith("CPT")]
        out: List[Dict] = []
        # Always include at least one ICD if available
        if icd:
            out.append(icd[0])
        # Include up to k-1 CPT if available
        for r in cpt:
            if len(out) >= k:
                break
            out.append(r)
        # Backfill with additional ICD then CPT from pool if still short
        if len(out) < k:
            for p in pool:
                if str(p.get("system", "")).upper().startswith("ICD") and p not in out:
                    out.append({**p, "reason": p.get("reason", "Primary diagnosis inferred from text.")})
                if len(out) >= k:
                    break
        if len(out) < k:
            for p in pool:
                if str(p.get("system", "")).upper().startswith("CPT") and p not in out:
                    out.append({**p, "reason": p.get("reason", "Procedure/visit inferred from text.")})
                if len(out) >= k:
                    break
        # Final cap
        return out[:max(1, k)]

    final_suggestions = _enforce_mix(refined, aggregated, top_k)

    # map to response models
    ents_models = [Entity(text=e.get('text',''), label=e.get('label',''), start=e.get('start',0), end=e.get('end',0)) for e in ents]
    suggestions: List[CodeSuggestion] = []
    for r in final_suggestions:
        suggestions.append(CodeSuggestion(
            code=str(r.get('code','')),
            system=str(r.get('system','ICD-10')),
            description=str(r.get('description','')),
            score=float(r.get('score',0.0)),
            reason=str(r.get('reason',''))
        ))

    return SuggestResponse(entities=ents_models, suggestions=suggestions)


@app.post("/generate_claim", response_model=ClaimResponse)
def generate_claim(req: ClaimRequest):
    # In production we would persist claim metadata to Supabase/Postgres and return an id
    claim_id = str(uuid.uuid4())
    metadata = {"source": "local-skeleton"}
    return ClaimResponse(claim_id=claim_id, approved=req.approved, metadata=metadata)


@app.get("/health")
def health():
    return {"status": "ok"}
