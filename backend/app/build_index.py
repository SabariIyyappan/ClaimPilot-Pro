import argparse
from app.code_index import build_embeddings_only
import numpy as np
import faiss
import os
import json

def build_faiss_index(embeddings_path: str, out_path: str):
    embs = np.load(embeddings_path)
    d = embs.shape[1]
    index = faiss.IndexFlatIP(d)      # cosine (embeddings already normalized)
    index.add(embs)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    faiss.write_index(index, out_path)
    return int(index.ntotal), d

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--icd_csv", required=True, help="CSV with columns Codes,Description")
    ap.add_argument("--cpt_csv", required=True, help="CSV with columns Codes,Description")
    ap.add_argument("--out_dir", default="data")
    ap.add_argument("--embeddings_path", default="data/descriptions.npy")
    ap.add_argument("--meta_path", default="data/meta.npy")
    ap.add_argument("--faiss_path", default="data/faiss.index")
    args = ap.parse_args()
    print('starting building embeddings...')
    # 1) build embeddings + meta first (safe to re-run)
    n_icd, n_cpt = build_embeddings_only(
        icd_csv=args.icd_csv,
        cpt_csv=args.cpt_csv,
        out_dir=args.out_dir,
        embeddings_path=args.embeddings_path,
        meta_path=args.meta_path
    )
    print('Building FAISS Index....')
    # 2) build FAISS
    count, dim = build_faiss_index(args.embeddings_path, args.faiss_path)
    print('FAISS indexing completed.')fa
    # 3) manifest for sanity
    with open(os.path.join(args.out_dir, "manifest.json"), "w") as f:
        json.dump({"count": count, "dim": dim, "icd": n_icd, "cpt": n_cpt}, f)

    print(f"✅ FAISS index built at {args.faiss_path} | vectors: {count} dim: {dim} | ICD:{n_icd} CPT:{n_cpt}")
