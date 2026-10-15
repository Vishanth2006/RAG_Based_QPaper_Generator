"""LLM package — public API."""
from src.llm.client import chat_completion, count_tokens
from src.llm.prompts import (
    build_question_prompt,
    build_paper_prompt,
    BLOOMS_LEVELS,
    BLOOMS_VERBS,
)
import json
import re


def generate_questions(
    context: str,
    unit: str,
    bloom_level: str,
    marks: int,
    num_questions: int = 1,
    topic_hint: str = "",
    model: str = "gpt-4o-mini",
) -> list[dict]:
    """
    Generate questions for a single unit/bloom combination.
    Returns list of question dicts (parsed from JSON).
    Raises RuntimeError on LLM or parse failure.
    """
    messages = build_question_prompt(
        context=context,
        unit=unit,
        bloom_level=bloom_level,
        marks=marks,
        num_questions=num_questions,
        topic_hint=topic_hint,
    )
    raw = chat_completion(messages, model=model)
    return _parse_json_list(raw)


def generate_paper(
    contexts: list[str],
    blueprint: dict,
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Generate a full question paper from a blueprint.
    Returns paper dict with 'title', 'total_marks', 'questions'.
    """
    messages = build_paper_prompt(contexts=contexts, blueprint=blueprint)
    raw = chat_completion(messages, model=model, max_tokens=3000)
    return _parse_json_object(raw)


def _parse_json_list(raw: str) -> list[dict]:
    """Extract JSON array from LLM response (handles markdown fences)."""
    text = _strip_fences(raw)
    # Find first [ ... ]
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def _parse_json_object(raw: str) -> dict:
    """Extract JSON object from LLM response."""
    text = _strip_fences(raw)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` markdown fences."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()
