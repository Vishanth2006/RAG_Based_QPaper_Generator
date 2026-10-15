"""Text chunking with overlap for RAG."""
from typing import Optional


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    source: str = "",
    page: int = 1,
    metadata: Optional[dict] = None,
) -> list[dict]:
    """
    Split text into overlapping chunks by word count.
    Returns list of chunk dicts compatible with ingestion format.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    chunk_num = 1

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)

        chunks.append({
            "text": chunk_text_str,
            "source": source,
            "page": page,
            "chunk_num": chunk_num,
            "metadata": {
                **(metadata or {}),
                "char_count": len(chunk_text_str),
                "word_count": len(chunk_words),
                "chunk_num": chunk_num,
            },
        })

        chunk_num += 1
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def rechunk_documents(docs: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Re-chunk already-extracted document pages/sections into smaller pieces.
    Useful when ingestion produces very large page-level chunks.
    """
    result = []
    for doc in docs:
        sub = chunk_text(
            text=doc["text"],
            chunk_size=chunk_size,
            overlap=overlap,
            source=doc.get("source", ""),
            page=doc.get("page", 1),
            metadata=doc.get("metadata", {}),
        )
        # If the chunk is already small enough, keep as-is
        if not sub or (len(sub) == 1 and sub[0]["text"] == doc["text"]):
            result.append(doc)
        else:
            result.extend(sub)
    return result
