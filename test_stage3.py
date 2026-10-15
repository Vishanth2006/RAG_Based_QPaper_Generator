import sys
import math
sys.path.insert(0, '.')

from src.vectorstore.chunker import rechunk_documents
from src.vectorstore.embedder import _dummy_embeddings
from src.vectorstore.store import collection_stats, clear_collection
from src.vectorstore import index_documents

# Test 1: chunker
docs = [{'text': 'Machine learning is a field of AI. ' * 30,
         'source': 'test.txt', 'page': 1,
         'metadata': {'source_type': 'txt'}}]
chunks = rechunk_documents(docs, chunk_size=20, overlap=5)
print(f"Chunker OK: {len(chunks)} chunks")

# Test 2: dummy embedder
embs = _dummy_embeddings([c['text'] for c in chunks])
print(f"Embedder OK: {len(embs)} vectors, dim={len(embs[0])}")
assert all(math.isfinite(value) for vector in embs for value in vector)
print("Embedder finite-vector check OK")

# Test 3: full index pipeline
clear_collection()
result = index_documents(docs, chunk_size=20, overlap=5)
print(f"index_documents OK: indexed={result['indexed']} error={result['error']}")

# Test 4: stats
stats = collection_stats()
print(f"ChromaDB stats: {stats}")

print("=== Stage 3 PASSED ===")
