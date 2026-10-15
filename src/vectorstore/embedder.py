"""
Embedding generation using OpenAI text-embedding-3-small.
Falls back to a simple TF-IDF-style hash embedding for offline testing.
"""
from typing import Optional
import os


def get_embeddings(texts: list[str], api_key: Optional[str] = None) -> list[list[float]]:
    """
    Generate embeddings for a list of texts using OpenAI API.
    Falls back to dummy embeddings if no API key is set.

    Returns list of float vectors (one per text).
    """
    key = api_key or os.getenv("OPENAI_API_KEY", "")

    if not key or key.startswith("sk-your"):
        # Offline fallback — deterministic hash-based mock (768-dim zeros with hash seed)
        return _dummy_embeddings(texts)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        raise RuntimeError(f"OpenAI embedding failed: {e}")


def _dummy_embeddings(texts: list[str], dim: int = 384) -> list[list[float]]:
    """Simple deterministic mock embedding for offline testing."""
    import hashlib

    result = []
    for text in texts:
        h = hashlib.sha256(text.encode()).digest()
        # Map bytes to a bounded range so every vector is finite for ChromaDB.
        floats = [((h[index % len(h)] / 255.0) * 2.0) - 1.0 for index in range(dim)]
        # Normalize to unit vector
        norm = sum(x**2 for x in floats) ** 0.5 or 1.0
        result.append([x / norm for x in floats])
    return result
