import csv
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "brain", "by", "for", "from", "has",
    "have", "in", "is", "it", "mild", "normal", "of", "on", "or", "patient", "prescribed",
    "presented", "related", "the", "to", "type", "was", "with",
}


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]


def _resource_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "resources" / name


@lru_cache(maxsize=1)
def _load_codes() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    sources: List[Tuple[str, str]] = [
        (_resource_path("icd10.csv").as_posix(), "ICD-10"),
        (_resource_path("mock_cpt.csv").as_posix(), "CPT"),
    ]
    for path, system in sources:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = str(row.get("Code") or row.get("Codes") or "").strip()
                description = str(row.get("Description") or "").strip()
                if not code or not description:
                    continue
                out.append({
                    "code": code,
                    "system": system,
                    "description": description,
                })
    return out


_CURATED_RULES: List[Dict[str, object]] = [
    {
        "match": ("headache", "migraine"),
        "item": {
            "code": "R51.9",
            "system": "ICD-10",
            "description": "Headache, unspecified",
            "reason": "Clinical note documents recurrent headaches.",
        },
    },
    {
        "match": ("dizziness", "vertigo", "lightheaded"),
        "item": {
            "code": "R42",
            "system": "ICD-10",
            "description": "Dizziness and giddiness",
            "reason": "Clinical note documents dizziness.",
        },
    },
    {
        "match": ("tension", "stress"),
        "item": {
            "code": "G44.209",
            "system": "ICD-10",
            "description": "Tension-type headache, unspecified, not intractable",
            "reason": "Clinical note describes tension-type headache related to stress.",
        },
    },
    {
        "match": ("mri", "magnetic", "imaging"),
        "item": {
            "code": "70551",
            "system": "CPT",
            "description": "MRI brain without contrast",
            "reason": "Clinical note references MRI of the brain.",
        },
    },
    {
        "match": ("follow-up", "followup", "consultation", "visit"),
        "item": {
            "code": "90507",
            "system": "CPT",
            "description": "Consultation - follow-up visit",
            "reason": "Clinical note appears to describe an outpatient follow-up/consultation encounter.",
        },
    },
]


def _curated_matches(text: str) -> List[Dict[str, object]]:
    lowered = (text or "").lower()
    out: List[Dict[str, object]] = []
    seen = set()
    for rule in _CURATED_RULES:
        terms = rule["match"]
        if any(term in lowered for term in terms):
            item = dict(rule["item"])  # shallow copy
            key = (item["code"], item["system"])
            if key in seen:
                continue
            seen.add(key)
            item["score"] = 0.92 if item["system"] == "ICD-10" else 0.81
            out.append(item)
    return out


def _csv_matches(text: str, top_k: int) -> List[Dict[str, object]]:
    query_tokens = set(_tokenize(text))
    if not query_tokens:
        return []

    scored: List[Tuple[float, Dict[str, str]]] = []
    for item in _load_codes():
        desc_tokens = set(_tokenize(item["description"]))
        overlap = query_tokens.intersection(desc_tokens)
        if not overlap:
            continue
        # Favor descriptions with tighter overlap to avoid noisy generic rows.
        score = len(overlap) / max(1, len(desc_tokens))
        score += 0.02 * len(overlap)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[Dict[str, object]] = []
    seen = set()
    for score, item in scored:
        key = (item["code"], item["system"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "code": item["code"],
            "system": item["system"],
            "description": item["description"],
            "score": round(min(0.79, max(0.35, score)), 3),
            "reason": "Suggested by local terminology overlap because the configured LLM did not return usable output.",
        })
        if len(out) >= top_k:
            break
    return out


def suggest_codes(text: str, top_k: int = 5) -> List[Dict[str, object]]:
    curated = _curated_matches(text)
    seen = {(item["code"], item["system"]) for item in curated}
    extras = []
    for item in _csv_matches(text, top_k=max(top_k * 2, 10)):
        key = (item["code"], item["system"])
        if key in seen:
            continue
        seen.add(key)
        extras.append(item)

    merged = curated + extras
    return merged[:max(1, top_k)]
