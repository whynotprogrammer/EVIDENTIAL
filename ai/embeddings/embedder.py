import hashlib
import math
import os
from typing import List, Optional, Union
import numpy as np


class DocumentEmbedder:
    """
    Embedding Architecture for EVIDENTIAL Semantic Investigation Search.
    Compatible with PostgreSQL pgvector and local cosine-similarity vector retrieval.
    """

    DIMENSION = 384

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generates a normalized dense vector embedding for text.
        Uses deterministic semantic hashing / n-gram projections for lightweight testability
        and provides drop-in compatibility for SentenceTransformers or pgvector.
        """
        if not text or not text.strip():
            return [0.0] * cls.DIMENSION

        clean_text = text.strip().lower()
        
        # Deterministic semantic vector projection based on token hashes
        vector = np.zeros(cls.DIMENSION, dtype=np.float32)
        tokens = clean_text.split()
        
        for i, token in enumerate(tokens):
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % cls.DIMENSION
            weight = 1.0 / (math.log(i + 2))
            vector[idx] += weight

        # Normalize to unit length (L2 norm)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    @classmethod
    def cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two embedding vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
