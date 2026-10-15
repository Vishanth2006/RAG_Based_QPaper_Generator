"""
ChromaDB vector store operations.
Handles collection creation, upsert, query, and deletion.
"""
import uuid
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings


_client: Optional[chromadb.PersistentClient] = None
_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "vectorstore"
COLLECTION_NAME = "rag_qpg_docs"


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    """Get or create the main ChromaDB collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> int:
    """
    Upsert chunks + embeddings into ChromaDB.
    Returns number of items upserted.
    """
    if not chunks or not embeddings:
        return 0
    if len(chunks) != len(embeddings):
        raise ValueError(f"chunks({len(chunks)}) and embeddings({len(embeddings)}) length mismatch")

    collection = get_collection()

    ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {k: str(v) for k, v in (c.get("metadata") or {}).items()}
        meta["source"] = c.get("source", "")
        meta["page"] = str(c.get("page", 1))
        metadatas.append(meta)

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(ids)


def query_collection(
    query_embedding: list[float],
    n_results: int = 5,
    where: Optional[dict] = None,
) -> list[dict]:
    """
    Query ChromaDB with an embedding vector.
    Returns list of {text, metadata, distance} dicts.
    """
    collection = get_collection()
    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"text": doc, "metadata": meta, "distance": dist})
    return output


def collection_stats() -> dict:
    """Return basic stats about the collection."""
    try:
        col = get_collection()
        count = col.count()
        return {"total_chunks": count, "collection": COLLECTION_NAME, "status": "ok"}
    except Exception as e:
        return {"total_chunks": 0, "collection": COLLECTION_NAME, "status": str(e)}


def collection_sources() -> list[dict]:
    """Return persisted source names and their stored chunk counts."""
    try:
        collection = get_collection()
        data = collection.get(include=["metadatas"])
        counts = {}
        for metadata in data.get("metadatas", []) or []:
            source = (metadata or {}).get("source", "Unknown source")
            source_type = (metadata or {}).get("source_type", "")
            key = (source, source_type)
            counts[key] = counts.get(key, 0) + 1
        return [
            {"source": source, "source_type": source_type, "chunks": chunks}
            for (source, source_type), chunks in sorted(counts.items())
        ]
    except Exception:
        return []


def clear_collection() -> bool:
    """Delete and recreate the collection (nuclear reset)."""
    try:
        client = _get_client()
        client.delete_collection(COLLECTION_NAME)
        client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        return True
    except Exception:
        return False
