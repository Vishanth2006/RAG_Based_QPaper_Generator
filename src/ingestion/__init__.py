"""
Document Ingestion Package
Unified interface for processing PDF, DOCX, PPTX, and TXT files.
"""

from pathlib import Path
from typing import Union
from src.ingestion.pdf_processor import process_pdf
from src.ingestion.docx_processor import process_docx
from src.ingestion.pptx_processor import process_pptx
from src.ingestion.txt_processor import process_txt

# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}


def process_file(file_path: Union[str, Path]) -> list[dict]:
    """
    Dispatch a file to the correct processor based on its extension.

    Returns a list of document chunks:
        [{"text": str, "source": str, "page": int, "metadata": dict}, ...]

    Raises:
        ValueError  – unsupported file type
        RuntimeError – extraction failure (corrupt / empty / unreadable)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.stat().st_size == 0:
        raise RuntimeError(f"File is empty: {path.name}")

    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if ext == ".pdf":
        return process_pdf(path)
    elif ext == ".docx":
        return process_docx(path)
    elif ext == ".pptx":
        return process_pptx(path)
    elif ext == ".txt":
        return process_txt(path)


def process_batch(file_paths: list[Union[str, Path]]) -> dict:
    """
    Process multiple files. Failures are isolated — one bad file
    does not stop others from being processed.

    Returns:
        {
            "successful": [{"file": str, "chunks": [...]}],
            "failed":     [{"file": str, "error": str}],
            "total_chunks": int
        }
    """
    results = {"successful": [], "failed": [], "total_chunks": 0}

    for fp in file_paths:
        path = Path(fp)
        try:
            chunks = process_file(path)
            results["successful"].append({"file": path.name, "chunks": chunks})
            results["total_chunks"] += len(chunks)
        except Exception as e:
            results["failed"].append({"file": path.name, "error": str(e)})

    return results
