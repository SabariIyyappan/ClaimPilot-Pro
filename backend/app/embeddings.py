from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

_MODEL = None


def get_model(name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(name)
    return _MODEL


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    model = get_model(model_name)
    emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return np.asarray(emb)
