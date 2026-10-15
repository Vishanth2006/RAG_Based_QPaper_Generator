"""
PDF Processor — Stage 2
Extracts text from PDFs using PyMuPDF.
Falls back to Tesseract OCR for scanned (image-only) pages.
"""

from pathlib import Path
try:
    import pymupdf as fitz  # PyMuPDF >= 1.24 preferred import
except ImportError:
    import fitz  # fallback for older installs


# Minimum characters on a page to consider it text-based (not scanned)
_TEXT_PAGE_THRESHOLD = 30


def _extract_page_text(page: fitz.Page) -> str:
    """Extract text from a single PyMuPDF page object."""
    return page.get_text("text").strip()


def _ocr_page(page: fitz.Page, dpi: int = 200) -> str:
    """
    Render a page to image and run Tesseract OCR.
    Returns empty string if pytesseract / Tesseract is not installed.
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img).strip()
    except ImportError:
        return ""
    except Exception:
        return ""


def process_pdf(file_path: Path) -> list[dict]:
    """
    Process a PDF file and return a list of page-level document chunks.

    Each chunk:
        {
            "text":     str,
            "source":   str,   # filename
            "page":     int,   # 1-indexed page number
            "metadata": {
                "source_type": "pdf",
                "file_path":   str,
                "ocr_used":    bool,
                "char_count":  int,
            }
        }

    Raises:
        RuntimeError – if the file cannot be opened or yields no text at all.
    """
    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        raise RuntimeError(f"Cannot open PDF '{file_path.name}': {e}")

    if doc.page_count == 0:
        raise RuntimeError(f"PDF has no pages: '{file_path.name}'")

    chunks: list[dict] = []
    total_chars = 0

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = _extract_page_text(page)
        ocr_used = False

        # If the page has very little text, try OCR
        if len(text) < _TEXT_PAGE_THRESHOLD:
            ocr_text = _ocr_page(page)
            if len(ocr_text) > len(text):
                text = ocr_text
                ocr_used = True

        if not text:
            continue  # Skip truly blank pages

        chunks.append({
            "text": text,
            "source": file_path.name,
            "page": page_num + 1,
            "metadata": {
                "source_type": "pdf",
                "file_path": str(file_path),
                "ocr_used": ocr_used,
                "char_count": len(text),
            },
        })
        total_chars += len(text)

    doc.close()

    if not chunks:
        raise RuntimeError(
            f"No text could be extracted from '{file_path.name}'. "
            "The PDF may be fully scanned and Tesseract OCR is not installed, "
            "or the file is corrupted."
        )

    return chunks
