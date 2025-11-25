# VectorService - BGE-Large Embedding Model Wrapper
# Handles text embedding using Hugging Face BGE-large model
#
# Model: BAAI/bge-large-en-v1.5
# Embedding Dimension: 1024
#
# Functions:
# - embed_text(text) -> vector (1024-dim)
#   * Takes text string
#   * Returns embedding vector as numpy array or list
#
# - embed_batch(texts) -> vectors
#   * Batch embedding for efficiency
#   * Used when embedding multiple chunks
#
# Model Loading:
# - Load on service startup
# - Keep in memory for fast inference
# - Consider GPU if available
#
# Responsibilities:
# - Model initialization and loading
# - Text preprocessing (if needed)
# - Embedding generation
# - Batch processing for efficiency

# vector_service/app/embedder.py

from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-large-en-v1.5"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Lazily load and cache the embedding model.
    Called once on first use (or at startup from main.py).
    """
    model = SentenceTransformer(MODEL_NAME)
    # Recommended for BGE: normalize embeddings
    return model


def embed_text(text: str) -> List[float]:
    """
    Embed a single text to a list[float].
    """
    model = get_model()
    emb = model.encode(text, normalize_embeddings=True)
    return emb.tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of texts.
    """
    if not texts:
        return []

    model = get_model()
    embs = model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embs]
