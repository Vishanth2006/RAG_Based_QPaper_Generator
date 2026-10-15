"""
TXT Processor — Stage 2
Extracts text from plain text files with automatic encoding detection.
"""

from pathlib import Path


# Encodings to try in order if chardet is unavailable
_FALLBACK_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

# Max lines per chunk (to avoid one massive chunk for very large text files)
_LINES_PER_CHUNK = 100


def _detect_encoding(file_path: Path) -> str:
    """Detect file encoding using chardet, fallback to utf-8."""
    try:
        import chardet
        raw = file_path.read_bytes()
        result = chardet.detect(raw)
        encoding = result.get("encoding") or "utf-8"
        return encoding
    except ImportError:
        return "utf-8"


def _read_with_fallback(file_path: Path) -> str:
    """Try multiple encodings until one succeeds."""
    encoding = _detect_encoding(file_path)
    try:
        return file_path.read_text(encoding=encoding)
    except (UnicodeDecodeError, LookupError):
        for enc in _FALLBACK_ENCODINGS:
            try:
                return file_path.read_text(encoding=enc)
            except (UnicodeDecodeError, LookupError):
                continue
    raise RuntimeError(
        f"Cannot decode '{file_path.name}'. "
        "Try saving the file as UTF-8."
    )


def process_txt(file_path: Path) -> list[dict]:
    """
    Process a plain text file and return chunked document sections.

    Chunking strategy:
    - Split on blank lines (paragraph-style chunking)
    - Merge very short paragraphs into the previous chunk
    - Large files are split into chunks of ~_LINES_PER_CHUNK lines

    Each chunk:
        {
            "text":     str,
            "source":   str,
            "page":     int,   # chunk number (1-indexed)
            "metadata": {
                "source_type": "txt",
                "file_path":   str,
                "encoding":    str,
                "char_count":  int,
            }
        }

    Raises:
        RuntimeError – if the file cannot be read or is empty after stripping.
    """
    encoding = _detect_encoding(file_path)
    full_text = _read_with_fallback(file_path)

    if not full_text.strip():
        raise RuntimeError(f"Text file is empty after stripping: '{file_path.name}'")

    # Split into paragraphs on blank lines
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

    # Re-group into chunks of reasonable size
    chunks: list[dict] = []
    current_parts: list[str] = []
    current_lines = 0
    chunk_num = 1

    def _flush():
        nonlocal chunk_num, current_lines
        text = "\n\n".join(current_parts).strip()
        if text:
            chunks.append({
                "text": text,
                "source": file_path.name,
                "page": chunk_num,
                "metadata": {
                    "source_type": "txt",
                    "file_path": str(file_path),
                    "encoding": encoding,
                    "char_count": len(text),
                },
            })
            chunk_num += 1
        current_parts.clear()
        current_lines = 0

    for para in paragraphs:
        lines_in_para = para.count("\n") + 1
        if current_lines + lines_in_para > _LINES_PER_CHUNK and current_parts:
            _flush()
        current_parts.append(para)
        current_lines += lines_in_para

    _flush()  # Flush last chunk

    if not chunks:
        raise RuntimeError(
            f"No usable text chunks found in '{file_path.name}'."
        )

    return chunks
