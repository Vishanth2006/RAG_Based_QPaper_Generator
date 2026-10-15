"""Stage 5 — generate, edit, validate, and export the question paper."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import GROQ_MODEL, is_api_configured
from src.export.pdf_exporter import build_paper_pdf
from src.generation.generator import build_generation_request, flatten_sections, generate_from_retrieval
from src.validation.paper_validator import validate_blueprint, validate_paper

BL_OPTIONS = [("L1", "Understand"), ("L2", "Analyze"), ("L3", "Apply"), ("L4", "Evaluate"), ("L5", "Create")]

st.set_page_config(page_title="Generation | RAG QPG", page_icon="✨", layout="wide")
st.title("Stage 5 — Generation & Review")
st.caption("Feed retrieved evidence to Groq, edit the questions, validate the paper, and download a PDF.")

sections_state = st.session_state.get("sections", {"A": [], "B": []})
sections = sections_state if isinstance(sections_state, list) else [
    section for part_sections in sections_state.values() for section in part_sections
]
question_slots = flatten_sections({"sections": sections})
paper_config = st.session_state.get("paper_config", {})
blueprint = {**paper_config, "sections": sections}
retrieval_results = st.session_state.get("retrieval_results", [])

blueprint_errors = validate_blueprint(blueprint)
if blueprint_errors:
    st.warning("Complete the paper structure before generation.")
    for error in blueprint_errors:
        st.error(error)
    st.stop()

if not retrieval_results:
    st.warning("Run retrieval for the configured sections before generation.")
    st.stop()

request = build_generation_request(blueprint, retrieval_results)
with st.expander("Prompt and retrieved context sent to Groq", expanded=False):
    st.json(request["messages"])
    for index, context in enumerate(request["contexts"], start=1):
        st.markdown(f"**Retrieved context {index}**")
        st.code(context)

if not is_api_configured():
    st.error("Groq is not configured. Add GROQ_API_KEY to .env, restart Streamlit, and try again.")
else:
    st.caption(f"Provider: Groq | Model: {GROQ_MODEL}")
    if st.button("Generate question paper", type="primary", use_container_width=True):
        with st.spinner("Generating questions from retrieved content..."):
            try:
                generated = generate_from_retrieval(blueprint, retrieval_results, model=GROQ_MODEL)
                paper = generated["paper"]
                questions = paper.get("questions", [])
                expected = question_slots
                for index, question in enumerate(questions):
                    if index < len(expected):
                        section = expected[index]
                        question.setdefault("part", section.get("part", "A"))
                        question.setdefault("unit", section.get("name", ""))
                        question.setdefault("marks", section.get("marks", 0))
                        question.setdefault("co", section.get("co", ""))
                        question.setdefault("bloom_code", section.get("bloom_code", "L1"))
                        question.setdefault("bloom_level", section.get("bloom_level", "Understand"))
                        question.setdefault("difficulty", section.get("difficulty", "Medium"))
                st.session_state.generated_paper = paper
                st.session_state.edited_questions = questions
                st.session_state.generation_request = generated["request"]
                st.rerun()
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

paper = st.session_state.get("generated_paper")
if not paper:
    st.info("The generated paper will appear here after a successful Groq response.")
    st.stop()

st.subheader("Generated questions")
questions = st.session_state.get("edited_questions", paper.get("questions", []))
for index, question in enumerate(questions):
    st.markdown(f"#### Question {index + 1}")
    question["question"] = st.text_area(
        "Question text",
        value=question.get("question", ""),
        key=f"question_text_{index}",
        height=90,
    )
    col_marks, col_co, col_bl, col_difficulty = st.columns(4)
    question["marks"] = col_marks.number_input("Marks", min_value=1, value=int(question.get("marks", 1)), key=f"question_marks_{index}")
    col_co.text_input("CO", value=question.get("co", ""), disabled=True, key=f"question_co_{index}")
    current_bl = question.get("bloom_code", "L1")
    bl_index = next((position for position, option in enumerate(BL_OPTIONS) if option[0] == current_bl), 0)
    question["bloom_code"], question["bloom_level"] = col_bl.selectbox("BL", BL_OPTIONS, index=bl_index, format_func=lambda option: f"{option[0]} - {option[1]}", key=f"question_bl_{index}")
    question["difficulty"] = col_difficulty.text_input("Difficulty", value=question.get("difficulty", ""), key=f"question_difficulty_{index}")

st.session_state.edited_questions = questions
paper["questions"] = questions
validation_errors = validate_paper(paper, blueprint)
if validation_errors:
    st.warning("The current paper needs correction before export.")
    for error in validation_errors:
        st.error(error)
else:
    st.success("Paper is valid and ready for export.")
    pdf_bytes = build_paper_pdf(paper_config, paper)
    st.download_button(
        "Download question paper PDF",
        data=pdf_bytes,
        file_name="question_paper.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
