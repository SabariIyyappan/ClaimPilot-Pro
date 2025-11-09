import os
import json
from typing import List, Dict, Any, Optional

try:
    import google.generativeai as genai
except Exception:
    genai = None

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


PROMPT_TEMPLATE = """
You are a clinical coding assistant. You are given:
- Clinical Text (discharge summary)
- Extracted Entities
- A list of Candidate codes produced by a vector search (ICD-10 and CPT)

Goal:
- Select the most relevant codes ONLY from the Candidate list.
- Prefer 1 primary diagnosis (ICD-10) and up to 2 procedures/visits (CPT) when applicable.
- If a category is not applicable, return the top overall items (max 3 total).

Output strictly as JSON array (no extra text), each item with fields like:
  {{"code": "...", "system": "ICD-10" or "CPT", "description": "...", "score": 0.0, "reason": "..."}}

Guidance:
- Do not invent codes. Choose only from Candidates.
- Use Entities and the Clinical Text to justify each selection in one concise sentence.
- If multiple candidates are similar, choose the most specific.

ClinicalText:\n{clinical_text}\n
Entities:\n{entities}\n
Candidates:\n{candidates}\n
Return up to {limit} items. JSON only.
"""


def _fallback_refine(entities: List[Dict[str, Any]],
                     candidates: List[Dict[str, Any]],
                     clinical_text: str,
                     top_k: int = 5) -> List[Dict[str, Any]]:
    # Simple deterministic fallback: take top_k by score, craft a reason
    out: List[Dict[str, Any]] = []
    text_lower = (clinical_text or "").lower()
    for c in candidates[:top_k]:
        desc = c.get("description", "")
        # Find a short overlapping cue for the reason
        cue = ""
        for e in entities or []:
            et = str(e.get("text", ""))
            if et and et.lower() in text_lower:
                cue = et
                break
        reason = f"Semantically similar; matches context '{cue or desc[:48]}'."
        out.append({
            "code": c.get("code", ""),
            "system": c.get("system", "ICD-10"),
            "description": desc,
            "score": float(c.get("score", 0.0)),
            "reason": reason,
        })
    return out


def _extract_json(text: str) -> Optional[List[Dict[str, Any]]]:
    try:
        loaded = json.loads(text)
        if isinstance(loaded, list):
            return loaded
        if isinstance(loaded, dict):
            # Common patterns: {"items": [...]}, {"codes": [...]}, or a single item
            for key in ("items", "codes", "suggestions", "results"):
                if key in loaded and isinstance(loaded[key], list):
                    return loaded[key]
            return [loaded]
    except Exception:
        pass
    # Strip code fences
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        # after stripping, try to find JSON array boundaries
    # Find first '[' and last ']'
    try:
        i = t.find("[")
        j = t.rfind("]")
        if i != -1 and j != -1 and j > i:
            arr = json.loads(t[i:j+1])
            if isinstance(arr, list):
                return arr
    except Exception:
        pass
    # As a last resort, try single-object extraction
    try:
        i = t.find("{")
        j = t.rfind("}")
        if i != -1 and j != -1 and j > i:
            obj = json.loads(t[i:j+1])
            if isinstance(obj, dict):
                return [obj]
    except Exception:
        pass
    return None


def _call_gemini(prompt: str) -> Optional[str]:
    if not (GEMINI_API_KEY and genai):
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "max_output_tokens": 1024,
            },
        )
        resp = model.generate_content(prompt)
        # google-generativeai returns candidates; get text
        if hasattr(resp, 'text') and resp.text:
            return resp.text
        # fallback: join parts from candidates if available
        try:
            return "".join([str(p.text) for p in getattr(resp, 'candidates', []) if getattr(p, 'text', None)])
        except Exception:
            return None
    except Exception:
        return None


def refine(entities: List[Dict[str, Any]],
           candidates: List[Dict[str, Any]],
           clinical_text: str = "",
           top_k: int = 5) -> List[Dict[str, Any]]:
    """Refine candidates using OpenAI if available; otherwise a deterministic fallback.

    Returns a list of dicts with keys: code, system, description, score, reason.
    """
    try:
        prompt = PROMPT_TEMPLATE.format(
            clinical_text=str(clinical_text or "")[:4000],
            entities=json.dumps(entities, ensure_ascii=False)[:4000],
            candidates=json.dumps(candidates[:50], ensure_ascii=False)[:6000],
            limit=int(max(1, top_k)),
        )
    except Exception:
        # As a safeguard, avoid str.format and build by concatenation
        prompt = (
            "You are a clinical coding assistant.\n\n"
            "ClinicalText:\n" + str(clinical_text or "")[:4000] + "\n\n"
            "Entities:\n" + json.dumps(entities, ensure_ascii=False)[:4000] + "\n\n"
            "Candidates:\n" + json.dumps(candidates[:50], ensure_ascii=False)[:6000] + "\n\n"
            "Output strictly JSON array of objects with keys code, system, description, score, reason."
        )

    # Gemini-only provider; fallback to deterministic if missing
    text: Optional[str] = _call_gemini(prompt)
    if text:
        parsed = _extract_json(text) or []
        out: List[Dict[str, Any]] = []
        for it in parsed:
            out.append({
                "code": str(it.get("code", "")),
                "system": "CPT" if str(it.get("system", "")).upper().startswith("CPT") else "ICD-10",
                "description": str(it.get("description", "")),
                "score": float(it.get("score", 0.0)),
                "reason": str(it.get("reason", "")),
            })
        if out:
            return out[:max(1, top_k)]

    # If Gemini unavailable or failed, deterministic fallback
    return _fallback_refine(entities, candidates, clinical_text, top_k=top_k)


# Direct LLM coding without retrieval candidates
DIRECT_PROMPT_TEMPLATE = """
You are a senior clinical coding specialist. Read the clinical text and propose the most relevant billing/diagnosis codes.

Requirements:
- Include both ICD-10 (diagnoses) and CPT (procedures/visits/imaging/therapy) as applicable.
- Prefer specific and commonly used codes based on the context.
- Limit to at most {limit} total items.
- Output strictly a JSON array (no extra text). Each item must be:
  {{"code": "...", "system": "ICD-10" or "CPT", "description": "...", "reason": "..."}}

ClinicalText:\n{clinical_text}\n
Entities (optional):\n{entities}\n
Return JSON only.
"""


def generate_codes_from_text(entities: List[Dict[str, Any]],
                             clinical_text: str,
                             top_k: int = 5) -> List[Dict[str, Any]]:
    try:
        prompt = DIRECT_PROMPT_TEMPLATE.format(
            clinical_text=str(clinical_text or "")[:6000],
            entities=json.dumps(entities or [], ensure_ascii=False)[:4000],
            limit=int(max(1, top_k)),
        )
    except Exception:
        prompt = (
            "You are a senior clinical coding specialist. Return JSON array of ICD-10 and CPT codes.\n\n"
            "ClinicalText:\n" + str(clinical_text or "")[:6000] + "\n\n"
            "Entities:\n" + json.dumps(entities or [], ensure_ascii=False)[:4000]
        )

    def _rule_based_codes(text: str, ents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        t = (text or "").lower()
        out: List[Dict[str, Any]] = []
        # Side detection
        side = "unspecified"
        if "right" in t:
            side = "right"
        elif "left" in t:
            side = "left"

        # Diagnosis: meniscal tear / knee pain
        if ("meniscal" in t and "tear" in t) or any('meniscal' in str(e.get('text','')).lower() for e in ents):
            if side == "right":
                out.append({
                    "code": "M23.21",
                    "system": "ICD-10",
                    "description": "Derangement of medial meniscus due to old tear or injury, right knee",
                    "score": 0.9,
                    "reason": "Meniscal tear mentioned with right knee context."
                })
            elif side == "left":
                out.append({
                    "code": "M23.22",
                    "system": "ICD-10",
                    "description": "Derangement of medial meniscus due to old tear or injury, left knee",
                    "score": 0.9,
                    "reason": "Meniscal tear mentioned with left knee context."
                })
            else:
                out.append({
                    "code": "M23.20",
                    "system": "ICD-10",
                    "description": "Derangement of medial meniscus due to old tear or injury, unspecified knee",
                    "score": 0.85,
                    "reason": "Meniscal tear mentioned without side specified."
                })
        elif "knee" in t and "pain" in t:
            if side == "right":
                out.append({
                    "code": "M25.561",
                    "system": "ICD-10",
                    "description": "Pain in right knee",
                    "score": 0.7,
                    "reason": "Knee pain present with right side."
                })
            elif side == "left":
                out.append({
                    "code": "M25.562",
                    "system": "ICD-10",
                    "description": "Pain in left knee",
                    "score": 0.7,
                    "reason": "Knee pain present with left side."
                })
            else:
                out.append({
                    "code": "M25.569",
                    "system": "ICD-10",
                    "description": "Pain in unspecified knee",
                    "score": 0.65,
                    "reason": "Knee pain present; side not specified."
                })

        # CPT: arthroscopy / meniscal repair
        if "arthroscop" in t or any(e.get('label') == 'PROCEDURE' for e in ents):
            if "repair" in t:
                out.append({
                    "code": "29882",
                    "system": "CPT",
                    "description": "Arthroscopy, knee, surgical; repair of meniscus",
                    "score": 0.85,
                    "reason": "Arthroscopic surgery with repair noted."
                })
            else:
                out.append({
                    "code": "29881",
                    "system": "CPT",
                    "description": "Arthroscopy, knee, surgical; with meniscectomy (medial OR lateral)",
                    "score": 0.8,
                    "reason": "Arthroscopic knee procedure implied."
                })

        # CPT: MRI knee / lower extremity joint
        if "mri" in t or "magnetic resonance" in t:
            out.append({
                "code": "73721",
                "system": "CPT",
                "description": "MRI, any joint of lower extremity; without contrast material",
                "score": 0.8,
                "reason": "MRI confirmed meniscal tear."
            })

        # CPT: physical therapy
        if "physical therapy" in t or "therapy" in t:
            out.append({
                "code": "97110",
                "system": "CPT",
                "description": "Therapeutic exercises to develop strength and endurance, range of motion and flexibility",
                "score": 0.7,
                "reason": "Physical therapy mentioned."
            })

        # CPT: follow-up / outpatient visit (use common E/M code)
        if "follow-up" in t or "follow up" in t or "outpatient" in t or "consult" in t:
            out.append({
                "code": "99213",
                "system": "CPT",
                "description": "Office or other outpatient visit, established patient, low medical decision making",
                "score": 0.6,
                "reason": "Follow-up visit / outpatient context."
            })

        # De-duplicate by (code, system)
        seen = set()
        unique = []
        for item in out:
            key = (item["code"], item["system"]) 
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique[:max(1, top_k)]

    text = _call_gemini(prompt) or "[]"
    parsed = _extract_json(text) or []
    # Retry once with a stricter instruction if parsing failed
    if not parsed:
        strict_prompt = (
            prompt
            + "\n\nIMPORTANT: Output must be a pure JSON array only, no code fences, no commentary."
        )
        text2 = _call_gemini(strict_prompt) or "[]"
        parsed = _extract_json(text2) or []

    # Final fallback: rule-based suggestions
    if not parsed:
        parsed = _rule_based_codes(clinical_text, entities)

    out: List[Dict[str, Any]] = []
    for it in parsed:
        out.append({
            "code": str(it.get("code", "")),
            "system": "CPT" if str(it.get("system", "")).upper().startswith("CPT") else "ICD-10",
            "description": str(it.get("description", "")),
            "score": float(it.get("score", 0.0)) if isinstance(it.get("score", None), (int, float)) else 0.0,
            "reason": str(it.get("reason", "")),
        })
    return out[:max(1, top_k)]
