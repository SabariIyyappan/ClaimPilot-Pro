# app/embeddings.py
import numpy as np
from typing import List, Iterable, Optional
from sentence_transformers import SentenceTransformer

# Lazy, shared model
_model: Optional[SentenceTransformer] = None

def get_encoder(model_name: str = "all-mpnet-base-v2") -> SentenceTransformer:
    """Returns a cached sentence-transformers encoder."""
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model

def embed_texts(texts: Iterable[str], batch_size: int = 256, normalize: bool = True) -> np.ndarray:
    """
    Encode an iterable of texts to a float32 numpy array (N, D).
    Normalized so cosine similarity == inner product if normalize=True.
    """
    print('loading the model')
    model = get_encoder()
    print('\nEncoding..')
    vecs = model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=normalize
    )
    return np.asarray(vecs, dtype=np.float32)
