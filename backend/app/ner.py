from typing import List, Dict
import re

_nlp = None


def _init_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    # Try medspaCy first if available
    try:
        import medspacy  # type: ignore
        _nlp = medspacy.load()
        return _nlp
    except Exception:
        pass
    # Optionally try spaCy if present
    try:
        import spacy  # type: ignore
        try:
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = spacy.blank("en")
        return _nlp
    except Exception:
        _nlp = None
        return None


def _heuristic_entities(text: str) -> List[Dict]:
    ents: List[Dict] = []
    tl = text.lower()
    patterns = [
        (r"\b(mri|magnetic resonance imaging)\b[\w\s-]*\b(knee|joint|lower extremity)\b", "IMAGING"),
        (r"\barthroscop(ic|y)[\w\s-]*(repair|procedure)?\b", "PROCEDURE"),
        (r"\bmeniscal? tear\b", "DIAGNOSIS"),
        (r"\bdiagnos(is|es)?\b[\w\s-]*", "DIAGNOSIS"),
        (r"\bconsult(ation)?\b|\boutpatient consult\b|\bfollow-?up\b", "VISIT"),
        (r"\bphysical therapy\b|\btherapy\b", "THERAPY"),
        (r"\bpain\b[\w\s-]*(knee|joint)", "SYMPTOM"),
    ]
    for pat, label in patterns:
        for m in re.finditer(pat, tl, flags=re.IGNORECASE):
            s, e = m.span()
            ents.append({
                "text": text[s:e],
                "label": label,
                "start": s,
                "end": e,
            })
    # Also include lines with key headers
    for line in text.splitlines():
        low = line.lower()
        if any(k in low for k in ["diagnos", "procedure", "impression", "assessment"]):
            start = text.find(line)
            ents.append({
                "text": line.strip(),
                "label": "CLINICAL_TEXT",
                "start": start,
                "end": start + len(line)
            })
    return ents


def extract_entities(text: str) -> List[Dict]:
    """Clinical NER with graceful degradation.

    - Uses medSpaCy if installed
    - Falls back to spaCy if available
    - Otherwise uses robust regex-based heuristics
    Returns [{text,label,start,end}]
    """
    nlp = _init_nlp()
    ents: List[Dict] = []
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in getattr(doc, "ents", []):
                ents.append({
                    "text": ent.text,
                    "label": getattr(ent, "label_", "ENTITY"),
                    "start": getattr(ent, "start_char", 0),
                    "end": getattr(ent, "end_char", 0)
                })
        except Exception:
            pass
    # If none found or no pipeline, use heuristics
    if not ents:
        ents = _heuristic_entities(text)
    return ents
