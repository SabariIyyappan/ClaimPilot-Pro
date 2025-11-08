"""Build embeddings and FAISS index from CSV datasets.

Run: python backend/app/build_index.py --icd data/icd10.csv --cpt data/mock_cpt.csv --out data/
"""
import argparse
import numpy as np
import faiss
from code_index import load_codes_from_csv
from embeddings import embed_texts
import os


def normalize_embeddings(emb):
    # normalize vectors for cosine similarity via inner product
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return emb / norms


def main(icd, cpt, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    icd_codes = load_codes_from_csv(icd, system="ICD-10")
    cpt_codes = load_codes_from_csv(cpt, system="CPT")
    all_codes = icd_codes + cpt_codes
    texts = [f"{c['code']} {c['description']}" for c in all_codes]
    print(f"Embedding {len(texts)} codes...")
    emb = embed_texts(texts)
    emb = normalize_embeddings(emb.astype('float32'))

    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    index_path = os.path.join(out_dir, "faiss.index")
    desc_path = os.path.join(out_dir, "descriptions.npy")
    meta_path = os.path.join(out_dir, "meta.npy")
    faiss.write_index(index, index_path)
    np.save(desc_path, np.array(texts, dtype=object))
    np.save(meta_path, np.array([c["code"] for c in all_codes], dtype=object))
    print("Index written to", index_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--icd', required=True)
    parser.add_argument('--cpt', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    main(args.icd, args.cpt, args.out)
