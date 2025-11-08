import pandas as pd
import os
import numpy as np
from .embeddings import embed_texts
from typing import List, Dict


def load_codes_from_csv(path: str, system: str = "ICD-10") -> List[Dict]:
    df = pd.read_csv(path)
    codes = []
    for _, row in df.iterrows():
        codes.append({"code": str(row["code"]), "description": str(row.get("description", "")), "system": system})
    return codes


def build_and_save_embeddings(codes: List[Dict], out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    texts = [f"{c['code']} {c['description']}" for c in codes]
    embs = embed_texts(texts)
    codes_path = os.path.join(out_dir, "codes.npy")
    desc_path = os.path.join(out_dir, "descriptions.npy")
    meta_path = os.path.join(out_dir, "meta.npy")
    np.save(codes_path, embs)
    np.save(desc_path, np.array(texts, dtype=object))
    np.save(meta_path, np.array([c["code"] for c in codes], dtype=object))
    return codes_path
