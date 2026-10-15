"""
PPTX Processor — Stage 2
Extracts text from PowerPoint presentations using python-pptx.
Preserves: slide titles, body text, speaker notes, and slide numbers.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Pt


def _extract_shape_text(shape) -> str:
    """Extract text from a single shape (text frame)."""
    if not shape.has_text_frame:
        return ""
    lines = []
    for para in shape.text_frame.paragraphs:
        line = para.text.strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _extract_notes(slide) -> str:
    """Extract speaker notes from a slide."""
    try:
        notes_slide = slide.notes_slide
        notes_text = notes_slide.notes_text_frame.text.strip()
        return notes_text
    except Exception:
        return ""


def process_pptx(file_path: Path) -> list[dict]:
    """
    Process a PPTX file and return slide-level document chunks.

    Each slide becomes one chunk containing:
    - Slide title
    - All text from all shapes
    - Speaker notes (if any)

    Each chunk:
        {
            "text":     str,
            "source":   str,
            "page":     int,   # slide number (1-indexed)
            "metadata": {
                "source_type":  "pptx",
                "file_path":    str,
                "slide_title":  str,
                "has_notes":    bool,
                "char_count":   int,
            }
        }

    Raises:
        RuntimeError – if the file cannot be opened or yields no text.
    """
    try:
        prs = Presentation(str(file_path))
    except Exception as e:
        raise RuntimeError(f"Cannot open PPTX '{file_path.name}': {e}")

    if not prs.slides:
        raise RuntimeError(f"Presentation has no slides: '{file_path.name}'")

    chunks: list[dict] = []

    for slide_idx, slide in enumerate(prs.slides, start=1):
        slide_title = ""
        body_lines: list[str] = []

        for shape in slide.shapes:
            # Detect title placeholder
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                continue
            text = _extract_shape_text(shape)
            if not text:
                continue

            # Identify title placeholder
            try:
                if shape.is_title:
                    slide_title = text
                    body_lines.insert(0, f"# {text}")
                else:
                    body_lines.append(text)
            except AttributeError:
                body_lines.append(text)

        notes = _extract_notes(slide)
        has_notes = bool(notes)

        all_lines = body_lines[:]
        if notes:
            all_lines.append(f"\n[NOTES]\n{notes}\n[/NOTES]")

        full_text = "\n".join(all_lines).strip()
        if not full_text:
            continue  # Skip blank slides

        chunks.append({
            "text": full_text,
            "source": file_path.name,
            "page": slide_idx,
            "metadata": {
                "source_type": "pptx",
                "file_path": str(file_path),
                "slide_title": slide_title or f"Slide {slide_idx}",
                "has_notes": has_notes,
                "char_count": len(full_text),
            },
        })

    if not chunks:
        raise RuntimeError(
            f"No text could be extracted from '{file_path.name}'. "
            "All slides may be blank or image-only."
        )

    return chunks
