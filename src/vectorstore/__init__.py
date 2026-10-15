"""Vector store package — public API."""
from src.vectorstore.chunker import chunk_text, rechunk_documents
from src.vectorstore.embedder import get_embeddings
from src.vectorstore.store import (
    upsert_chunks,
    query_collection,
    collection_stats,
    clear_collection,
    get_collection,
)


def index_documents(docs: list[dict], chunk_size: int = 500, overlap: int = 50) -> dict:
    """
    Full pipeline: rechunk → embed → upsert into ChromaDB.
    Returns {"indexed": int, "failed": int, "error": str|None}
    """
    from src.vectorstore.chunker import rechunk_documents
    chunks = rechunk_documents(docs, chunk_size=chunk_size, overlap=overlap)

    try:
        embeddings = get_embeddings([c["text"] for c in chunks])
        n = upsert_chunks(chunks, embeddings)
        return {"indexed": n, "failed": 0, "error": None}
    except Exception as e:
        return {"indexed": 0, "failed": len(chunks), "error": str(e)}
