import os
import openai
from typing import List, Dict

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
openai.api_key = os.environ.get("OPENAI_API_KEY")


PROMPT_TEMPLATE = """
You are a clinical coding assistant. Given the extracted entities and a list of candidate codes with similarity scores, produce a ranked list of suggestions. For each candidate, provide a one-line reason linking the entity to the code. Return JSON array of objects with fields: code, system, description, score, reason.

Entities:\n{entities}\n
Candidates:\n{candidates}\n
Rules: be concise. If a candidate is clearly irrelevant, it may be omitted. Respect the scores but use domain knowledge to adjust.
"""


def refine(entities: List[Dict], candidates: List[Dict], top_k: int = 5) -> List[Dict]:
    prompt = PROMPT_TEMPLATE.format(entities=entities, candidates=candidates)
    if not openai.api_key:
        # No key configured: return candidates with a simple deterministic "reason"
        out = []
        for c in candidates[:top_k]:
            out.append({
                "code": c.get("meta", ""),
                "system": "ICD-10",
                "description": c.get("description", ""),
                "score": c.get("score", 0.0),
                "reason": f"Matched semantically to: {c.get('description','')[:80]}"
            })
        return out

    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=512,
    )
    text = resp["choices"][0]["message"]["content"]
    # Expect JSON array; attempt to parse, otherwise return fallback
    import json
    try:
        parsed = json.loads(text)
        return parsed
    except Exception:
        # Fallback naive parse: return top-k with generic reasons
        out = []
        for c in candidates[:top_k]:
            out.append({
                "code": c.get("meta", ""),
                "system": "ICD-10",
                "description": c.get("description", ""),
                "score": c.get("score", 0.0),
                "reason": text[:200]
            })
        return out
