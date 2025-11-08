# app/code_index.py
import os
import re
import json
import numpy as np
import pandas as pd
from typing import Tuple
from .embeddings import embed_texts

REQ_COLS = ("Codes", "Description")

def _normalize_colnames(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    code_col = cols.get("codes") or cols.get("code")
    desc_col = cols.get("description") or cols.get("desc")
    if code_col is None or desc_col is None:
        raise ValueError(f"CSV must contain columns named {REQ_COLS} (case-insensitive). Got: {list(df.columns)}")
    return df.rename(columns={code_col: "code", desc_col: "description"})

def _clean_text(s: str) -> str:
    s = str(s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def load_codes_from_csv(path: str, system_name: str) -> pd.DataFrame:
    """
    Load a code file with columns Codes,Description (any case), and return:
      columns -> [code, description, system, text]
    """
    df = pd.read_csv(path)
    df = _normalize_colnames(df)
    # Clean
    df["code"] = df["code"].astype(str).map(_clean_text)
    df["description"] = df["description"].astype(str).map(_clean_text)
    # Drop empties & dups
    df = df.replace({"": np.nan}).dropna(subset=["code", "description"])
    df = df.drop_duplicates(subset=["code"], keep="first")
    df["system"] = system_name
    # Combined field for embedding
    df["text"] = df["code"] + " " + df["description"]
    return df[["code", "description", "system", "text"]]

def build_embeddings_only(
    icd_csv: str,
    cpt_csv: str,
    out_dir: str = "data",
    embeddings_path: str = "data/descriptions.npy",
    meta_path: str = "data/meta.npy",
) -> Tuple[int, int]:
    """
    Create and save embeddings + meta for both ICD & CPT (no FAISS yet).
    Saves:
      - descriptions.npy  (float32 embeddings, shape (N, D))
      - meta.npy          (object array of (code, system, description))
    Returns: (num_icd, num_cpt)
    """
    os.makedirs(out_dir, exist_ok=True)

    icd_df = load_codes_from_csv(icd_csv, "ICD-10")
    cpt_df = load_codes_from_csv(cpt_csv, "CPT")
    all_df = pd.concat([icd_df, cpt_df], ignore_index=True)

    # Embed
    embs = embed_texts(all_df["text"].tolist())  # (N,D) float32, normalized
    np.save(embeddings_path, embs)

    # Meta aligned to embeddings row order
    meta = np.array(
        list(zip(all_df["code"].tolist(), all_df["system"].tolist(), all_df["description"].tolist())),
        dtype=object
    )
    np.save(meta_path, meta)

    # Drop a tiny manifest for sanity
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump({"count": int(len(all_df)), "dim": int(embs.shape[1])}, f)

    return len(icd_df), len(cpt_df)
