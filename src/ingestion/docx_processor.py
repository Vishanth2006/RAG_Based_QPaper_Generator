"""
DOCX Processor — Stage 2
Extracts text from Word documents using python-docx.
Preserves: headings, paragraphs, table content, and paragraph style metadata.
"""

from pathlib import Path
from docx import Document
from docx.oxml.ns import qn


def _get_paragraph_style(para) -> str:
    """Return a normalized style label for a paragraph."""
    style_name = para.style.name if para.style else "Normal"
    return style_name


def _extract_table_text(table) -> str:
    """Convert a table to plain text with pipe-separated cells."""
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def process_docx(file_path: Path) -> list[dict]:
    """
    Process a DOCX file and return section-level document chunks.

    Chunking strategy:
    - Each Heading 1 / Heading 2 starts a new chunk.
    - Paragraphs and tables are grouped into the current chunk.
    - If no headings exist, the whole document is one chunk.

    Each chunk:
        {
            "text":     str,
            "source":   str,
            "page":     int,   # section number (DOCX has no true page numbers)
            "metadata": {
                "source_type": "docx",
                "file_path":   str,
                "section_heading": str,
                "char_count":  int,
            }
        }

    Raises:
        RuntimeError – if the file cannot be opened or yields no text.
    """
    try:
        doc = Document(str(file_path))
    except Exception as e:
        raise RuntimeError(f"Cannot open DOCX '{file_path.name}': {e}")

    chunks: list[dict] = []
    current_heading = "Introduction"
    current_lines: list[str] = []
    section_num = 1

    def _flush_chunk():
        nonlocal section_num
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({
                "text": text,
                "source": file_path.name,
                "page": section_num,
                "metadata": {
                    "source_type": "docx",
                    "file_path": str(file_path),
                    "section_heading": current_heading,
                    "char_count": len(text),
                },
            })
            section_num += 1

    for block in doc.element.body:
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

        if tag == "p":
            # Paragraph
            para_text = block.text_content().strip() if hasattr(block, "text_content") else ""
            # Use python-docx paragraph API for style info
            from docx.text.paragraph import Paragraph as DocxParagraph
            para = DocxParagraph(block, doc)
            style = _get_paragraph_style(para)
            text = para.text.strip()

            if not text:
                continue

            if style.startswith("Heading 1") or style.startswith("Heading 2"):
                _flush_chunk()
                current_heading = text
                current_lines = [f"## {text}"]
            elif style.startswith("Heading"):
                current_lines.append(f"### {text}")
            else:
                current_lines.append(text)

        elif tag == "tbl":
            # Table — convert to plain text
            from docx.table import Table as DocxTable
            tbl = DocxTable(block, doc)
            table_text = _extract_table_text(tbl)
            if table_text.strip():
                current_lines.append("\n[TABLE]\n" + table_text + "\n[/TABLE]")

    # Flush the last chunk
    _flush_chunk()

    if not chunks:
        raise RuntimeError(
            f"No text could be extracted from '{file_path.name}'. "
            "The file may be empty or corrupted."
        )

    return chunks
