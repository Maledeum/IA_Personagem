import functools
from typing import List

from sentence_transformers import SentenceTransformer

from core.config import EMBED_MODEL

_model = None


def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_embedding(text: str) -> List[float]:
    model = load_model()
    emb = model.encode([text])[0]
    return emb.tolist()
