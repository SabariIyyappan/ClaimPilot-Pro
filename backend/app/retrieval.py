# app/retrieval.py
import os
import numpy as np
import faiss
from typing import List, Dict, Any
from .embeddings import embed_texts

class FaissIndexWrapper:
    def __init__(self, index_path: str, desc_path: str, meta_path: str):
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Meta file not found: {meta_path}")

        self.index = faiss.read_index(index_path)
        # desc_path (embeddings) is optional at runtime; we don't need to load it to query
        self.meta = np.load(meta_path, allow_pickle=True)  # array of tuples (code, system, description)

    def search(self, query_embeddings: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        query_embeddings: np.ndarray of shape (B, D), normalized float32
        returns flattened list of candidates across batch:
        [{code, system, description, score}, ...]
        """
        if not isinstance(query_embeddings, np.ndarray):
            query_embeddings = np.asarray(query_embeddings, dtype="float32")
        if query_embeddings.ndim == 1:
            query_embeddings = query_embeddings.reshape(1, -1)

        D, I = self.index.search(query_embeddings, top_k)
        out: List[Dict[str, Any]] = []
        for row_scores, row_ids in zip(D, I):
            for score, idx in zip(row_scores, row_ids):
                code, system, desc = self.meta[idx]
                out.append({
                    "code": str(code),
                    "system": str(system),
                    "description": str(desc),
                    "score": float(score)
                })
        return out

def search_text(index_path: str, meta_path: str, text: str, top_k: int = 5):
    """Utility: embed a raw text and search."""
    q = embed_texts([text])  # normalized (1,D)
    wrapper = FaissIndexWrapper(index_path=index_path, desc_path="", meta_path=meta_path)
    return wrapper.search(q, top_k=top_k)
