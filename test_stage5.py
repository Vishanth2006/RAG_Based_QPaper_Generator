"""Focused tests for retrieval, generation contracts, validation, and PDF export."""

from unittest.mock import patch

from src.export.pdf_exporter import build_paper_pdf
from src.generation.generator import build_generation_request
from src.retrieval.retriever import build_section_query
from src.validation.paper_validator import validate_blueprint, validate_paper


def test_section_query_and_generation_context():
    section = {
        "name": "Unit 1: Machine Learning",
        "topic_hint": "classification",
        "bloom_level": "Understand",
        "difficulty": "Medium",
    }
    assert "classification" in build_section_query(section)

    blueprint = {"paper_type": "MODEL QUESTION PAPER", "sections": [{**section, "count": 1, "marks": 2}]}
    request = build_generation_request(
        blueprint,
        [{"section": section["name"], "chunks": [{"text": "Classification uses labelled data.", "source": "notes.txt", "page": 1}]}],
    )
    assert request["messages"][1]["role"] == "user"
    assert "notes.txt" in request["contexts"][0]


def test_multiple_parts_and_topic_groups_reach_one_prompt():
    blueprint = {
        "paper_type": "MODEL QUESTION PAPER",
        "sections": [
            {"part": "A", "name": "Unit 1", "topic_hint": "classification", "question_type": "Short answer", "bloom_level": "Understand", "difficulty": "Easy", "co": "CO1", "count": 1, "marks": 2},
            {"part": "A", "name": "Unit 2", "topic_hint": "regression", "question_type": "Descriptive", "bloom_level": "Analyze", "difficulty": "Hard", "co": "CO2", "count": 2, "marks": 5},
            {"part": "C", "name": "Unit 3", "topic_hint": "neural networks", "question_type": "Essay", "bloom_level": "Evaluate", "difficulty": "Hard", "co": "CO3", "count": 1, "marks": 10},
        ],
    }
    request = build_generation_request(blueprint, [{"section": "Unit 1", "chunks": [{"text": "classification evidence", "source": "notes.txt", "page": 1}]}])
    prompt = request["messages"][1]["content"]
    assert "Part A" in prompt
    assert "difficulty: Hard" in prompt
    assert "Unit 3" in prompt
    assert "Part C" in prompt


def test_validation_and_pdf_export():
    blueprint = {"max_marks": 2, "sections": [{"name": "Unit 1", "part": "A", "count": 1, "marks": 2}]}
    assert validate_blueprint(blueprint) == []
    paper = {"questions": [{"question": "Explain classification.", "marks": 2}]}
    assert validate_paper(paper, blueprint) == []
    pdf = build_paper_pdf({"institution": "Test University", "max_marks": 2}, paper)
    assert pdf.startswith(b"%PDF")


def test_validation_rejects_source_references():
    blueprint = {"sections": [{"name": "Unit 1", "count": 1, "marks": 2}]}
    paper = {"questions": [{"question": "As mentioned in the study material, explain classification.", "marks": 2}]}
    assert any("source-referencing" in error for error in validate_paper(paper, blueprint))


def test_retrieval_empty_query_is_reported():
    from src.retrieval.retriever import retrieve_for_sections

    with patch("src.retrieval.retriever.get_embeddings") as embed:
        result = retrieve_for_sections([{"name": ""}])
    embed.assert_not_called()
    assert result[0]["error"] == "Empty section query"
