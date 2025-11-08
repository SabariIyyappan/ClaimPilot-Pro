import numpy as np
import faiss
import os
from typing import List, Dict


class FaissIndexWrapper:
    def __init__(self, index_path: str, desc_path: str, meta_path: str):
        self.index_path = index_path
        self.desc_path = desc_path
        self.meta_path = meta_path
        self.index = None
        self.descriptions = None
        self.meta = None

    def load(self):
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(self.index_path)
        self.index = faiss.read_index(self.index_path)
        self.descriptions = np.load(self.desc_path, allow_pickle=True)
        self.meta = np.load(self.meta_path, allow_pickle=True)

    def search(self, q_emb: np.ndarray, top_k: int = 5):
        if self.index is None:
            self.load()
        D, I = self.index.search(q_emb.astype('float32'), top_k)
        results = []
        for row_idx, row in enumerate(I):
            for idx_pos, idx in enumerate(row):
                if idx < 0:
                    continue
                results.append({
                    "meta": str(self.meta[idx]),
                    "description": str(self.descriptions[idx]),
                    "score": float(D[row_idx][idx_pos])
                })
        return results
