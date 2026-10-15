"""Print-ready PDF export for generated question papers."""

from io import BytesIO
import unicodedata

from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


def build_paper_pdf(paper_config: dict, paper: dict) -> bytes:
    """Render a question paper to PDF and return its bytes."""
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("PaperTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=13, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#0B2D4D"), spaceAfter=3 * mm)
    department = ParagraphStyle("Department", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#24486A"))
    heading = ParagraphStyle("PartHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10, leading=13, alignment=TA_LEFT, textColor=colors.HexColor("#102A43"), spaceBefore=4 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("Question", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, alignment=TA_LEFT, textColor=colors.HexColor("#102A43"), spaceAfter=1 * mm)
    instruction = ParagraphStyle("Instruction", parent=body, fontSize=9, textColor=colors.HexColor("#24486A"), spaceAfter=3 * mm)
    metadata = ParagraphStyle("QuestionMetadata", parent=body, fontSize=7.5, leading=10, leftIndent=6 * mm, textColor=colors.HexColor("#59738B"), spaceAfter=2 * mm)

    def _safe(value: object) -> str:
        text = unicodedata.normalize("NFKC", str(value))
        replacements = {
            "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
            "\u00b7": "-", "\u2022": "-", "\ufffd": "-",
            "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u00a0": " ",
        }
        text = "".join(replacements.get(char, char) for char in text)
        text = "".join(char if ord(char) < 128 else " " for char in text)
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

    story = [
        Paragraph(_safe(paper_config.get("institution", "INSTITUTION / UNIVERSITY NAME")), title),
        Paragraph(_safe(paper_config.get("department", "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING")), department),
        Spacer(1, 3 * mm),
        Table([[Paragraph(_safe(paper_config.get("paper_type", "MODEL QUESTION PAPER")), ParagraphStyle("PaperType", parent=title, fontSize=12, spaceAfter=0))]], colWidths=[174 * mm], style=TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AAFC2")), ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AAFC2")), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)])),
        Paragraph(f"Course Code: {_safe(paper_config.get('course_code', ''))} | Course Title: {_safe(paper_config.get('course_title', ''))}", ParagraphStyle("Course", parent=department, alignment=TA_CENTER, fontSize=9.5, textColor=colors.HexColor("#102A43"))),
    ]
    details = [[Paragraph(f"Duration: {_safe(paper_config.get('duration', ''))}", body), Paragraph(f"Maximum Marks: {_safe(paper_config.get('max_marks', ''))}", ParagraphStyle("Marks", parent=body, alignment=TA_RIGHT))]]
    table = Table(details, colWidths=[87 * mm, 87 * mm])
    table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AAFC2")), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.extend([Spacer(1, 3 * mm), table, Spacer(1, 5 * mm)])

    part_instructions = paper_config.get("part_instructions", {})
    questions = paper.get("questions", [])
    parts = []
    for question in questions:
        part = str(question.get("part", "A"))
        if part not in parts:
            parts.append(part)

    question_number = 1
    for part in parts:
        part_questions = [q for q in questions if str(q.get("part", "A")) == part]
        if not part_questions:
            continue
        story.append(Paragraph(f"PART {_safe(part)}", heading))
        if part_instructions.get(part):
            story.append(Paragraph(_safe(part_instructions[part]), instruction))
        header_style = ParagraphStyle("TableHeader", parent=body, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=colors.HexColor("#102A43"))
        cell_style = ParagraphStyle("TableCell", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#102A43"))
        center_style = ParagraphStyle("TableCenter", parent=cell_style, alignment=TA_CENTER)
        rows = [[Paragraph("No.", header_style), Paragraph("Question", header_style), Paragraph("Marks", header_style), Paragraph("CO", header_style), Paragraph("BL", header_style)]]
        for question in part_questions:
            bloom_code = question.get("bloom_code", question.get("bl", ""))
            rows.append([
                Paragraph(str(question_number), center_style),
                Paragraph(_safe(question.get("question", "")), cell_style),
                Paragraph(_safe(question.get("marks", "")), center_style),
                Paragraph(_safe(question.get("co", "")), center_style),
                Paragraph(_safe(bloom_code), center_style),
            ])
            question_number += 1
        question_table = Table(rows, colWidths=[12 * mm, 117 * mm, 15 * mm, 15 * mm, 15 * mm], repeatRows=1, hAlign="LEFT")
        question_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#8395A7")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(question_table)

    document.build(story)
    return output.getvalue()
