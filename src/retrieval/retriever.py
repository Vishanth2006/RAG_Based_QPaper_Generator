"""Reusable query construction and semantic retrieval helpers."""

from collections.abc import Iterable

from src.vectorstore.embedder import get_embeddings
from src.vectorstore.store import query_collection


def build_section_query(section: dict) -> str:
    """Build the text embedded for one paper-structure section."""
    values = [
        section.get("name", ""),
        section.get("topic", section.get("topic_hint", "")),
        section.get("bloom_level", ""),
        section.get("difficulty", ""),
    ]
    return " ".join(str(value).strip() for value in values if str(value).strip())


def retrieve_for_sections(
    sections: Iterable[dict], top_k: int = 4, min_similarity: float = 0.0
) -> list[dict]:
    """Embed each section query and return provenance-preserving search results."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    section_list = list(sections)
    results = []
    for section in section_list:
        query = build_section_query(section)
        if not query:
            results.append({"section": section.get("name", ""), "query": "", "chunks": [], "error": "Empty section query"})
            continue

        try:
            embedding = get_embeddings([query])[0]
            hits = query_collection(embedding, n_results=top_k)
            chunks = []
            seen = set()
            for hit in hits:
                text = hit.get("text", "")
                if not text or text in seen:
                    continue
                seen.add(text)
                similarity = round(1 - float(hit.get("distance", 1)), 4)
                metadata = hit.get("metadata") or {}
                chunks.append({
                    "text": text,
                    "source": metadata.get("source", ""),
                    "page": metadata.get("page", ""),
                    "source_type": metadata.get("source_type", ""),
                    "similarity": similarity,
                    "below_threshold": similarity < min_similarity,
                })
            results.append({
                "section": section.get("name", ""),
                "part": section.get("part", ""),
                "query": query,
                "query_embedding": embedding,
                "chunks": chunks,
                "low_similarity": bool(chunks) and all(c["below_threshold"] for c in chunks),
            })
        except Exception as exc:
            results.append({
                "section": section.get("name", ""),
                "part": section.get("part", ""),
                "query": query,
                "query_embedding": [],
                "chunks": [],
                "error": str(exc),
            })
    return results
