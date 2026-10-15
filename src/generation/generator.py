"""Question paper generation and normalization helpers."""

from src.llm import _parse_json_object, generate_paper
from src.llm.prompts import build_paper_prompt


def flatten_sections(blueprint: dict) -> list[dict]:
    """Expand topic groups into ordered per-question generation slots."""
    expanded = []
    for section in blueprint.get("sections", []):
        specs = section.get("question_specs") or []
        if not specs:
            specs = [
                {
                    "marks": section.get("marks", 1),
                    "bloom_code": section.get("bloom_code", "L1"),
                    "bloom_level": section.get("bloom_level", "Understand"),
                    "difficulty": section.get("difficulty", "Medium"),
                    "co": section.get("co", "CO1"),
                }
                for _ in range(int(section.get("count", 1)))
            ]
        for spec in specs[:int(section.get("count", len(specs)))]:
            expanded.append({**section, **spec, "count": 1})
    return expanded


def build_generation_context(retrieval_results: list[dict]) -> list[str]:
    """Create bounded context strings with source provenance for the LLM."""
    contexts = []
    for result in retrieval_results:
        section = result.get("section", "section")
        parts = [f"Section: {section}"]
        for chunk in result.get("chunks", []):
            source = chunk.get("source", "unknown source")
            page = chunk.get("page", "?")
            parts.append(f"[{source}, page {page}]\n{chunk.get('text', '')}")
        if len(parts) > 1:
            contexts.append("\n".join(parts))
    return contexts


def build_generation_request(blueprint: dict, retrieval_results: list[dict]) -> dict:
    """Return prompt messages plus context for transparent UI display."""
    contexts = build_generation_context(retrieval_results)
    prompt_blueprint = {
        "title": blueprint.get("paper_type", "Question Paper"),
        "units": [
            {
                "name": section.get("name", ""),
                "topic_hint": section.get("topic_hint", ""),
                "topic": section.get("topic", section.get("topic_hint", "")),
                "count": int(section.get("count", 0)),
                "marks": int(section.get("marks", 0)),
                "bloom_level": section.get("bloom_level", "Understand"),
                "bloom_code": section.get("bloom_code", "L1"),
                "difficulty": section.get("difficulty", "Medium"),
                "co": section.get("co", ""),
                "part": section.get("part", "A"),
            }
            for section in flatten_sections(blueprint)
        ],
    }
    return {
        "messages": build_paper_prompt(contexts, prompt_blueprint),
        "contexts": contexts,
        "blueprint": prompt_blueprint,
    }


def generate_from_retrieval(blueprint: dict, retrieval_results: list[dict], model: str | None = None) -> dict:
    """Generate one normalized paper using only retrieved context."""
    request = build_generation_request(blueprint, retrieval_results)
    paper = generate_paper(request["contexts"], request["blueprint"], model=model or "openai/gpt-oss-120b")
    paper.setdefault("questions", [])
    return {"paper": paper, "request": request}


def parse_paper_response(raw: str) -> dict:
    """Parse a raw JSON response for unit tests and callers outside the LLM client."""
    return _parse_json_object(raw)
