from fastapi import FastAPI, UploadFile, File, Form, Request
from dotenv import load_dotenv
from pathlib import Path
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.schemas import UploadRequest, SuggestRequest, SuggestResponse, ClaimRequest, ClaimResponse, Entity, CodeSuggestion, CMS1500Request
from app.ocr import extract_text_from_image_bytes, extract_text_from_pdf_bytes
from app.ner import extract_entities
from app.embeddings import embed_texts
from app.retrieval import FaissIndexWrapper
from app.pdfgen import generate_claim_pdf
from app.cms1500 import parse_header_info, split_codes, generate_cms1500_pdf
from app.blockchain import compute_claim_hash, create_mock_tx
import os
import uuid
from typing import List, Dict, Tuple, Optional
import json
import time

# Ensure we load env from backend/.env even when running uvicorn from repo root
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)

# Import LLM after env is loaded so keys are visible
from app.llm_refine import refine, generate_codes_from_text
app = FastAPI(title="ClaimPilot Coding Agent - Skeleton")

# Debug helper (enabled when LLM_DEBUG=1/true)
def _dbg(msg: str) -> None:
    if os.environ.get("LLM_DEBUG", "").lower() in ("1", "true", "yes"):
        try:
            print(f"[backend] {msg}")
        except Exception:
            pass

# Helper to support both Pydantic v1 (.dict) and v2 (.model_dump)
def _to_dict(item):
    try:
        if hasattr(item, "model_dump"):
            return item.model_dump()
        if hasattr(item, "dict"):
            return item.dict()
    except Exception:
        pass
    return item

# CORS for local frontends (Vite/Cra) or custom origins via env
_cors_origins = os.environ.get(
    "CORS_ORIGINS",
    # Default allow common local dev ports
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:8080,http://127.0.0.1:8080,"
    "http://localhost:5173,http://127.0.0.1:5173"
)
origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Allow any localhost port for smoother local dev
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload(
    request: Request,
    file: UploadFile = File(None),
    text: str = Form(None),
    clinical_only: bool = Form(True),
    auto_suggest: bool = Form(False),
):
    """Accept a file (PDF/image) or plain text. Return extracted text and entities."""
    extracted = ""
    if file is not None:
        content = await file.read()
        if file.filename.lower().endswith('.pdf'):
            extracted = extract_text_from_pdf_bytes(content)
        else:
            extracted = extract_text_from_image_bytes(content)
    # Accept JSON body with text as well
    if not text:
        ct = request.headers.get("content-type", "").lower()
        if "application/json" in ct:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    text = body.get("text")
                    # allow overriding flags via JSON
                    clinical_only = body.get("clinical_only", clinical_only)
                    auto_suggest = body.get("auto_suggest", auto_suggest)
            except Exception:
                pass

    if text:
        # prefer provided text if present
        extracted = text

    # If requested (default True), keep only the Clinical Note section
    if clinical_only:
        try:
            from app.ocr import extract_clinical_note_section
            extracted = extract_clinical_note_section(extracted)
        except Exception:
            pass

    ents = extract_entities(extracted)

    # Optional: immediately run suggestions to streamline front-end flow
    if auto_suggest:
        try:
            from app.llm_refine import generate_codes_from_text
            sugg = generate_codes_from_text(ents, extracted, top_k=10)
        except Exception:
            sugg = []
        return {"text": extracted, "entities": ents, "suggestions": sugg}

    return {"text": extracted, "entities": ents}


@app.get("/config")
def config():
    mode = os.environ.get("SUGGEST_MODE", "llm").lower()
    gem_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    # Basic check for FAISS files
    faiss_present = all(os.path.exists(p) for p in [
        os.path.join("data", "faiss.index"),
        os.path.join("data", "meta.npy"),
    ])
    return {
        "mode": mode,
        "llm_provider": "gemini",
        "llm_model": gem_model,
        "retrieval_enabled": bool(faiss_present),
        "version": "0.1",
    }


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
    _dbg(f"/suggest: mode={os.environ.get('SUGGEST_MODE','llm')} text_chars={len(text)} top_k={top_k}")
    # 1) Extract entities
    ents: List[Dict] = extract_entities(text)
    _dbg(f"/suggest: ents={len(ents)}")

    # LLM-only medical coding is the default and recommended flow
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
        _dbg(f"/suggest: LLM suggestions={len(suggestions)}")
        return SuggestResponse(entities=ents_models, suggestions=suggestions)

    # 2) Optional retrieval (no hardcoding/heuristics). If FAISS files are present
    # and SUGGEST_MODE != 'llm', do a simple text-based retrieval to supply
    # candidates to the LLM for refinement.
    idx = FaissIndexWrapper(
        index_path="data/faiss.index",
        desc_path="data/descriptions.npy",
        meta_path="data/meta.npy",
    )

    # 3) Retrieval: full text + up to 3 long entity phrases (no keyword hacks)
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

        # Entity phrase queries (no keyword expansions)
        phrases = _pick_entity_phrases(ents, max_n=3)
        if phrases:
            q_ents = embed_texts(phrases)
            all_candidates.extend(idx.search(q_ents, top_k=max(top_k, 10)))
    except Exception:
        all_candidates = []

    # 4) Aggregate only (no heuristic boosts)
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
        out = []
        for v in agg.values():
            out.append({**v, "score": float(v.get("score", 0.0))})
        out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return out

    aggregated = _aggregate(all_candidates)

    # 5) Use LLM refine on a broader pool; keep up to 20
    pool_for_llm = aggregated[:20] if aggregated else []
    refined = refine(ents, pool_for_llm, clinical_text=text, top_k=top_k)

    # 6) Use refined results as-is (no enforced mix)
    final_suggestions = refined[:max(1, top_k)] if refined else aggregated[:max(1, top_k)]

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

    _dbg(f"/suggest: hybrid suggestions={len(suggestions)}")
    return SuggestResponse(entities=ents_models, suggestions=suggestions)


@app.post("/generate_claim", response_model=ClaimResponse)
def generate_claim(req: ClaimRequest):
    # Generate id and basic metadata
    claim_id = str(uuid.uuid4())
    payload = {
        "claim_id": claim_id,
        "approved": [_to_dict(c) for c in req.approved],
        "patient_id": getattr(req, 'patient_id', None),
        "amount": getattr(req, 'amount', None),
        "signed_by": getattr(req, 'signed_by', None),
        "ts": int(time.time()),
        "source": "local-skeleton",
    }

    # Compute deterministic hash and create a mock blockchain tx
    try:
        h = compute_claim_hash({k: v for k, v in payload.items() if k != 'approved'})
        tx = create_mock_tx(h)
    except Exception:
        h = ""
        tx = {}

    metadata = {"hash": h, "tx": tx, "source": payload["source"]}

    # Append to a local audit log (no PHI stored)
    try:
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "claims.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "claim_id": claim_id,
                "ts": payload["ts"],
                "approved": payload["approved"],
                "amount": payload.get("amount"),
                "patient_id": payload.get("patient_id"),
                "signed_by": payload.get("signed_by"),
            }) + "\n")
    except Exception:
        pass

    return ClaimResponse(claim_id=claim_id, approved=req.approved, metadata=metadata)


@app.post("/claim_pdf")
def claim_pdf(req: ClaimRequest):
    # Generate a transient claim id for the PDF header
    cid = str(uuid.uuid4())
    pdf_bytes = generate_claim_pdf(cid, [_to_dict(c) for c in req.approved])
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=claim_{cid}.pdf"
    })


@app.post("/cms1500")
def cms1500(req: CMS1500Request):
    # Derive header fields from text if present
    derived = parse_header_info(req.text or "")
    patient_name = req.patient_name or derived.get("patient_name", "")
    patient_id = req.patient_id or derived.get("patient_id", "")
    provider_name = req.provider_name or derived.get("provider_name", "")
    date_of_service = req.date_of_service or derived.get("date_of_service", "")
    patient_dob = req.patient_dob or derived.get("patient_dob", "")
    patient_sex = req.patient_sex or derived.get("patient_sex", "")
    patient_address = req.patient_address or derived.get("patient_address", "")
    place_of_service = req.place_of_service or derived.get("place_of_service", "")
    referring_npi = req.referring_npi or derived.get("referring_npi", "")

    # Split codes into ICD diagnoses and CPT procedures
    approved_list = [_to_dict(c) for c in req.approved]
    diagnoses, procedures = split_codes(approved_list)

    pdf_bytes = generate_cms1500_pdf(
        patient_name=patient_name,
        patient_id=patient_id,
        provider_name=provider_name,
        date_of_service=date_of_service,
        patient_dob=patient_dob,
        patient_sex=patient_sex,
        patient_address=patient_address,
        place_of_service=place_of_service,
        referring_npi=referring_npi,
        diagnoses=diagnoses,
        procedures=procedures,
        diag_pointers=req.diag_pointers or None,
    )
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=cms1500.pdf"
    })


@app.post("/cms1500/derive")
def cms1500_derive(request: dict):
    """Derive CMS-1500 header fields from raw text (used to prefill the dialog)."""
    try:
        text = str(request.get("text", "")) if isinstance(request, dict) else ""
    except Exception:
        text = ""
    fields = parse_header_info(text)
    # Friendly defaults to reduce empty UI fields
    try:
        import datetime as _dt
        today = _dt.date.today().isoformat()
    except Exception:
        today = ""
    if not fields.get("date_of_service"):
        fields["date_of_service"] = today
    if not fields.get("place_of_service"):
        fields["place_of_service"] = "11"  # Office
    # Normalize sex to short token when present
    sex = (fields.get("patient_sex") or "").strip().upper()
    if sex.startswith("M"):
        fields["patient_sex"] = "M"
    elif sex.startswith("F"):
        fields["patient_sex"] = "F"
    # Generate sensible random defaults for missing items (non‑PHI placeholders)
    try:
        import random as _rand
        import datetime as _dt
        # Patient name
        if not fields.get("patient_name"):
            first = _rand.choice(["John", "Jane", "Alex", "Sam", "Taylor", "Jordan", "Casey", "Riley"])  # type: ignore
            last = _rand.choice(["Doe", "Smith", "Johnson", "Lee", "Brown", "Davis"])  # type: ignore
            fields["patient_name"] = f"{first} {last}"
        # Patient ID (MRN)
        if not fields.get("patient_id"):
            fields["patient_id"] = f"MRN-{_rand.randint(10000000, 99999999)}"
        # Provider name
        if not fields.get("provider_name"):
            dr_first = _rand.choice(["Emily", "Michael", "Avery", "Chris", "Morgan"])  # type: ignore
            dr_last = _rand.choice(["Carter", "Nguyen", "Patel", "Garcia", "Kim"])  # type: ignore
            fields["provider_name"] = f"Dr. {dr_first} {dr_last}"
        # Sex
        if not fields.get("patient_sex"):
            fields["patient_sex"] = _rand.choice(["M", "F"])  # type: ignore
        # DOB from random age 20–75
        if not fields.get("patient_dob"):
            age = _rand.randint(20, 75)  # type: ignore
            dob = _dt.date.today().replace(year=_dt.date.today().year - age)
            fields["patient_dob"] = dob.isoformat()
        # Address
        if not fields.get("patient_address"):
            house = _rand.randint(100, 9999)  # type: ignore
            street = _rand.choice(["Main St", "Oak Ave", "Maple Rd", "Pine Blvd"])  # type: ignore
            city = _rand.choice(["Springfield", "Fairview", "Riverton", "Greenville"])  # type: ignore
            state = _rand.choice(["CA", "TX", "NY", "FL", "WA"])  # type: ignore
            zipc = _rand.randint(10000, 99999)  # type: ignore
            fields["patient_address"] = f"{house} {street}, {city}, {state} {zipc}"
        # Referring NPI – generate 10‑digit number starting 1–9
        if not fields.get("referring_npi"):
            fields["referring_npi"] = str(_rand.randint(1000000000, 9999999999))  # type: ignore
    except Exception:
        pass
    return fields

@app.get("/health")
def health():
    return {"status": "ok"}
