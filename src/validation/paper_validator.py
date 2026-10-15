"""Deterministic validation for blueprints and generated papers."""


def validate_blueprint(blueprint: dict) -> list[str]:
    errors = []
    sections = blueprint.get("sections", [])
    if not sections:
        errors.append("Add at least one paper section.")
    for index, section in enumerate(sections, start=1):
        if not str(section.get("name", "")).strip():
            errors.append(f"Section {index} needs a unit or topic name.")
        if int(section.get("count", 0)) < 1:
            errors.append(f"Section {index} must request at least one question.")
        if int(section.get("marks", 0)) < 1:
            errors.append(f"Section {index} must assign positive marks.")
    return errors


def validate_paper(paper: dict, blueprint: dict) -> list[str]:
    errors = []
    questions = paper.get("questions", [])
    forbidden_phrases = (
        "mentioned in the study material",
        "according to the provided context",
        "as discussed above",
        "in the study material",
        "in the provided material",
    )
    expected_count = sum(int(section.get("count", 0)) for section in blueprint.get("sections", []))
    expected_marks = sum(int(section.get("count", 0)) * int(section.get("marks", 0)) for section in blueprint.get("sections", []))
    if len(questions) != expected_count:
        errors.append(f"Generated {len(questions)} questions; expected {expected_count}.")
    actual_marks = sum(int(question.get("marks", 0)) for question in questions)
    if actual_marks != expected_marks:
        errors.append(f"Generated {actual_marks} marks; expected {expected_marks}.")
    if len({str(question.get("question", "")).strip() for question in questions}) != len(questions):
        errors.append("Generated questions must be unique.")
    for index, question in enumerate(questions, start=1):
        text = str(question.get("question", "")).lower()
        if any(phrase in text for phrase in forbidden_phrases):
            errors.append(f"Question {index} contains source-referencing language and must be rewritten.")
    return errors
