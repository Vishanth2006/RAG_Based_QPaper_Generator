import sys, tempfile
from pathlib import Path
sys.path.insert(0, '.')

# ── Test 1: TXT processing ────────────────────────────────────────────────────
from src.ingestion.txt_processor import process_txt

txt_content = """Unit 1: Introduction to Machine Learning

Machine learning is a subset of artificial intelligence.
It allows systems to learn from data and improve over time.

Unit 2: Supervised Learning

In supervised learning, models are trained on labelled data.
Classification and regression are common tasks.

Unit 3: Neural Networks

Deep learning uses multi-layer neural networks.
Backpropagation is the core training algorithm.
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write(txt_content)
    tmp_path = Path(f.name)

chunks = process_txt(tmp_path)
tmp_path.unlink()

print(f"TXT Test PASSED: {len(chunks)} chunks extracted")
for i, c in enumerate(chunks):
    chars = c["metadata"]["char_count"]
    print(f"  Chunk {i+1}: {chars} chars | source={c['source']} | page={c['page']}")

# ── Test 2: process_file dispatch ─────────────────────────────────────────────
from src.ingestion import process_file

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write(txt_content)
    tmp_path2 = Path(f.name)

result = process_file(tmp_path2)
tmp_path2.unlink()
print(f"Dispatch Test PASSED: {len(result)} chunks via process_file()")

# ── Test 3: Unsupported format ────────────────────────────────────────────────
try:
    process_file(Path('fake_file.xyz'))
except ValueError as e:
    print(f"Unsupported-format Test PASSED: {e}")
except FileNotFoundError as e:
    print(f"Unsupported-format Test PASSED (FileNotFound first): {e}")

# ── Test 4: Batch isolation ───────────────────────────────────────────────────
from src.ingestion import process_batch

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write("Good file content here. This is a test document with enough text.")
    good_path = Path(f.name)

results = process_batch([good_path, Path('nonexistent_file.txt')])
good_path.unlink()
print(f"Batch Test PASSED: {len(results['successful'])} success, {len(results['failed'])} failed")
print(f"  Total chunks: {results['total_chunks']}")
print(f"  Failed reason: {results['failed'][0]['error'][:70]}")

# ── Test 5: PDF test (with real project PDF) ─────────────────────────────────
import os
pdf_candidates = [
    r"E:\visha\Documents\Sem-6\AI\AI_Mini_Project_Initial_Report (1).pdf",
    r"E:\visha\Documents\Sem-6\AI\RAG_BasePaper.pdf",
]
for pdf_path in pdf_candidates:
    if os.path.exists(pdf_path):
        from src.ingestion.pdf_processor import process_pdf
        pdf_chunks = process_pdf(Path(pdf_path))
        print(f"PDF Test PASSED: '{Path(pdf_path).name}' -> {len(pdf_chunks)} pages extracted")
        print(f"  First page preview ({pdf_chunks[0]['metadata']['char_count']} chars):")
        print("  " + pdf_chunks[0]['text'][:200].replace('\n', ' '))
        break

print()
print("=== ALL STAGE 2 TESTS PASSED ===")
