import os
import json
from typing import List, Dict, Any, Optional

try:
    # Use the official google-genai import style
    from google import genai  # type: ignore
except Exception:
    genai = None  # type: ignore

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def _dbg(msg: str) -> None:
    if os.environ.get("LLM_DEBUG", "").lower() in ("1", "true", "yes"):
        try:
            print(f"[llm_refine] {msg}")
        except Exception:
            pass

def _dbg(msg: str) -> None:
    if os.environ.get("LLM_DEBUG", "").lower() in ("1", "true", "yes"):
        try:
            print(f"[llm_refine] {msg}")
        except Exception:
            pass


PROMPT_TEMPLATE = """
You are a highly accurate clinical coding assistant specializing in ICD-10 and CPT classification.
You are given:
- A clinical note or EHR-style report written by a physician.
- Extracted medical entities (diagnoses, symptoms, procedures, medications, etc.).
- A list of candidate medical codes retrieved from a knowledge base (ICD-10 and CPT).

GOAL:
- Select only the most relevant codes from the provided Candidate list.
- Prioritize primary diagnosis codes (ICD-10) and procedural/service codes (CPT).
- Include multiple relevant codes if the report clearly contains multiple billable conditions or services.
- If a category (ICD or CPT) is not clearly applicable, return the top few clinically relevant matches (maximum {limit} items).

OUTPUT FORMAT (VERY IMPORTANT):
- Return ONLY a valid JSON array.
- Do NOT include any extra text, comments, explanation, or code fences.
- Each element in the array must be an object with the following keys:
  {{
    "code": "...",
    "system": "ICD-10" or "CPT",
    "description": "...",
    "score": 0.0,
    "reason": "One-sentence justification linking this code to the clinical text."
  }}

GUIDANCE:
- Do NOT invent or hallucinate codes; choose only from the provided Candidates.
- Use both ClinicalText and Entities to decide which codes are relevant.
- If multiple candidate codes are similar, choose the most specific and clinically appropriate.
- Use concise, factual reasoning for each selected code.
- Ensure the returned JSON is syntactically valid and directly parsable.

ClinicalText:
{clinical_text}

Entities:
{entities}

Candidates:
{candidates}

Return up to {limit} items.
JSON array ONLY, no surrounding text.
"""


DIRECT_PROMPT_TEMPLATE = """
You are a senior clinical coding specialist. Read the clinical text and propose all clinically relevant billing and diagnosis codes.

REQUIREMENTS:
- Include both ICD-10 (diagnoses) and CPT (procedures, visits/E&M, imaging, therapy) as applicable.
- Prefer specific, standard, and commonly used codes based on the clinical context.
- Do NOT invent codes; only return codes you are confident are justified by the text.
- Deduplicate entries and avoid redundant near-duplicate codes.

OUTPUT FORMAT (VERY IMPORTANT):
- Return ONLY a valid JSON array.
- Do NOT include any extra text, comments, explanation, or code fences.
- Each element in the array must be an object with the following keys:
  {{
    "code": "...",
    "system": "ICD-10" or "CPT",
    "description": "...",
    "score": number between 0 and 1,
    "reason": "Short justification based on the clinical text."
  }}

ClinicalText:
{clinical_text}

Entities (optional):
{entities}

Return JSON array ONLY.
"""


def _fallback_refine(
    entities: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    clinical_text: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Extremely simple fallback: if Gemini is not available or parsing fails,
    just return the top_k candidates as-is with a generic reason. No clinical logic.
    """
    out: List[Dict[str, Any]] = []
    for c in candidates[:top_k]:
        out.append(
            {
                "code": str(c.get("code", "")),
                "system": "CPT" if str(c.get("system", "")).upper().startswith("CPT") else "ICD-10",
                "description": str(c.get("description", "")),
                "score": float(c.get("score", 0.0)),
                "reason": "Selected from candidate list as a fallback because the model response was unavailable.",
            }
        )
    return out


def _extract_json(text: str) -> Optional[List[Dict[str, Any]]]:
    if not text:
        return None
    try:
        loaded = json.loads(text)
        if isinstance(loaded, list):
            return loaded
        if isinstance(loaded, dict):
            for key in ("items", "codes", "suggestions", "results"):
                if key in loaded and isinstance(loaded[key], list):
                    return loaded[key]
            return [loaded]
    except Exception:
        pass
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").strip()
    try:
        i = t.find("[")
        j = t.rfind("]")
        if i != -1 and j != -1 and j > i:
            arr = json.loads(t[i : j + 1])
            if isinstance(arr, list):
                return arr
    except Exception:
        pass
    try:
        i = t.find("{")
        j = t.rfind("}")
        if i != -1 and j != -1 and j > i:
            obj = json.loads(t[i : j + 1])
            if isinstance(obj, dict):
                return [obj]
    except Exception:
        pass
    return None


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini using google-genai.
    Uses a single env var GEMINI_API_KEY; we pass it explicitly to the client.
    """
    if genai is None:
        _dbg("google.genai not importable; is google-genai installed in this env?")
        return None
    if not GEMINI_API_KEY:
        _dbg("GEMINI_API_KEY missing in environment")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        _dbg(f"call: model={GEMINI_MODEL} prompt_chars={len(prompt)} (models.generate_content)")
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        if getattr(resp, "text", None):
            txt = resp.text
            _dbg(f"call: got text len={len(txt)} head={txt[:120]!r}")
            return txt
        return None
    except Exception as e:
        _dbg(f"call: exception: {e}")
        return None


def refine(
    entities: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    clinical_text: str = "",
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Refine a list of candidate ICD-10/CPT codes using Gemini if available.

    Returns a list of dicts with keys: code, system, description, score, reason.
    """
    limit = int(max(1, top_k))
    try:
        prompt = PROMPT_TEMPLATE.format(
            clinical_text=str(clinical_text or "")[:4000],
            entities=json.dumps(entities or [], ensure_ascii=False)[:4000],
            candidates=json.dumps(candidates[:50], ensure_ascii=False)[:6000],
            limit=limit,
        )
    except Exception:
        prompt = (
            "You are a clinical coding assistant.\n\n"
            "ClinicalText:\n" + str(clinical_text or "")[:4000] + "\n\n"
            "Entities:\n" + json.dumps(entities or [], ensure_ascii=False)[:4000] + "\n\n"
            "Candidates:\n" + json.dumps(candidates[:50], ensure_ascii=False)[:6000] + "\n\n"
            "Return ONLY a JSON array of objects with keys: code, system, description, score, reason."
        )

    _dbg(f"refine: top_k={top_k} ents={len(entities)} cands={len(candidates)}")
    text: Optional[str] = _call_gemini(prompt)
    if text:
        parsed = _extract_json(text) or []
        _dbg(f"refine: parsed={len(parsed)}")
        out: List[Dict[str, Any]] = []
        for it in parsed:
            out.append(
                {
                    "code": str(it.get("code", "")),
                    "system": "CPT" if str(it.get("system", "")).upper().startswith("CPT") else "ICD-10",
                    "description": str(it.get("description", "")),
                    "score": float(it.get("score", 0.0)) if isinstance(it.get("score", None), (int, float)) else 0.0,
                    "reason": str(it.get("reason", "")),
                }
            )
        if out:
            return out[:limit]

    # If Gemini unavailable or parsing failed, trivial non-clinical fallback
    return _fallback_refine(entities, candidates, clinical_text, top_k=limit)


def generate_codes_from_text(
    entities: List[Dict[str, Any]],
    clinical_text: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Directly generate ICD-10 and CPT codes from raw clinical text using Gemini.

    Returns a list of dicts with keys: code, system, description, score, reason.
    If Gemini is not available or parsing fails, returns an empty list (no hard-coded guesses).
    """
    try:
        prompt = DIRECT_PROMPT_TEMPLATE.format(
            clinical_text=str(clinical_text or "")[:6000],
            entities=json.dumps(entities or [], ensure_ascii=False)[:4000],
        )
    except Exception:
        prompt = (
            "You are a senior clinical coding specialist. Return ONLY a JSON array of ICD-10 and CPT codes.\n\n"
            "ClinicalText:\n" + str(clinical_text or "")[:6000] + "\n\n"
            "Entities:\n" + json.dumps(entities or [], ensure_ascii=False)[:4000]
        )

    _dbg(f"direct: top_k={top_k} ents={len(entities)} text_chars={len(clinical_text or '')}")
    text = _call_gemini(prompt) or "[]"
    parsed = _extract_json(text) or []
    if not parsed:
        # Second attempt: stricter instruction and explicit minimum count
        min_items = max(1, min(5, int(top_k or 5)))
        strict_prompt = (
            prompt
            + f"\n\nIMPORTANT: Return a JSON array ONLY with at least {min_items} items when applicable. "
              "No comments, no code fences."
        )
        text2 = _call_gemini(strict_prompt) or "[]"
        parsed = _extract_json(text2) or []
    _dbg(f"direct: parsed={len(parsed)}")

    if not parsed:
        return []

    out: List[Dict[str, Any]] = []
    for idx, it in enumerate(parsed[: max(1, top_k)]):
        raw_score = it.get("score", None)
        if isinstance(raw_score, (int, float)):
            score = max(0.0, min(1.0, float(raw_score)))
        else:
            # Reasonable fallback: descending scores when LLM omits them
            score = max(0.5, 0.9 - 0.1 * idx)
        out.append(
            {
                "code": str(it.get("code", "")),
                "system": "CPT" if str(it.get("system", "")).upper().startswith("CPT") else "ICD-10",
                "description": str(it.get("description", "")),
                "score": score,
                "reason": str(it.get("reason", "")),
            }
        )
    return out
