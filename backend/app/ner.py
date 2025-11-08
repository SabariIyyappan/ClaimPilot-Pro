from typing import List, Dict
import spacy

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            # fallback minimal blank model
            _nlp = spacy.blank("en")
    return _nlp


def extract_entities(text: str) -> List[Dict]:
    """Simple clinical NER stub. Returns list of {text,label,start,end}.

    Replace/extend with medSpaCy or a clinical model for production.
    """
    nlp = _get_nlp()
    doc = nlp(text)
    ents = []
    for ent in doc.ents:
        ents.append({"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char})
    # If no ents found, heuristically extract lines containing 'diagnos' or 'procedure'
    if not ents:
        for line in text.splitlines():
            low = line.lower()
            if "diagnos" in low or "procedure" in low or "impression" in low or "assessment" in low:
                ents.append({"text": line.strip(), "label": "CLINICAL_TEXT", "start": text.find(line), "end": text.find(line) + len(line)})
    return ents
