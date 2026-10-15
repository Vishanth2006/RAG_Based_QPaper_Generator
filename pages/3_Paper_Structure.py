"""
Page 3 — Question Paper Structure
Configure institution details, Part A & Part B sections (unit, topic, bloom's, CO, marks, count).
"""
import re
import streamlit as st, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Paper Structure | RAG QPG", page_icon="📝", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.ph{background:linear-gradient(135deg,#7C3AED,#6C63FF);padding:1.4rem 2rem;border-radius:14px;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(124,58,237,.35);}
.ph h1{color:#fff;font-size:1.7rem;margin:0;font-weight:800;}
.ph p{color:rgba(255,255,255,.78);margin:.3rem 0 0;font-size:.88rem;}
.sec-hdr{font-size:1rem;font-weight:700;color:#E8E8F0;padding:.5rem 0;border-bottom:1px solid rgba(124,58,237,.25);margin-bottom:.8rem;}
.bprow{background:#12121f;border:1px solid rgba(124,58,237,.18);border-radius:8px;padding:.6rem 1rem;margin:.28rem 0;display:flex;align-items:center;gap:.7rem;}
.bprow .unit{font-size:.83rem;font-weight:600;color:#E8E8F0;flex:2;}
.bprow .meta{font-size:.73rem;color:rgba(232,232,240,.5);}
.bloom{display:inline-block;border-radius:20px;padding:.1rem .58rem;font-size:.67rem;font-weight:700;}
.bR{background:rgba(239,68,68,.15);color:#F87171;border:1px solid rgba(239,68,68,.4);}
.bU{background:rgba(245,158,11,.15);color:#FCD34D;border:1px solid rgba(245,158,11,.4);}
.bAp{background:rgba(16,185,129,.15);color:#34D399;border:1px solid rgba(16,185,129,.4);}
.bAn{background:rgba(59,130,246,.15);color:#60A5FA;border:1px solid rgba(59,130,246,.4);}
.bE{background:rgba(139,92,246,.15);color:#A78BFA;border:1px solid rgba(139,92,246,.4);}
.bC{background:rgba(236,72,153,.15);color:#F472B6;border:1px solid rgba(236,72,153,.4);}
.summary-box{background:#12121f;border:1px solid rgba(124,58,237,.25);border-radius:10px;padding:1rem 1.3rem;margin-top:.8rem;}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="ph"><h1>📝 Step 3 — Question Paper Structure</h1>
<p>Define institution details, sections, topics, Bloom's levels, difficulty, and marks</p></div>""",
unsafe_allow_html=True)

if not st.session_state.get("indexed"):
    st.warning("⚠️ Please complete **Step 1 → Upload** first.")
    st.stop()

from src.llm.prompts import BLOOMS_LEVELS

# ── session defaults ──────────────────────────────────────────────────────────
if "part_count" not in st.session_state:
    st.session_state.part_count = 2
if "sections" not in st.session_state:
    st.session_state.sections = {"A": [], "B": []}
if "paper_config" not in st.session_state:
    st.session_state.paper_config = {}

# ── Institution Details ───────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">🏫 Institution & Course Details</div>', unsafe_allow_html=True)

r1 = st.columns(3)
institution  = r1[0].text_input("Institution / University Name", st.session_state.paper_config.get("institution","INSTITUTION / UNIVERSITY NAME"), key="cfg_inst")
department   = r1[1].text_input("Department", st.session_state.paper_config.get("department","DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING"), key="cfg_dept")
paper_type   = r1[2].text_input("Paper Type", st.session_state.paper_config.get("paper_type","MODEL QUESTION PAPER"), key="cfg_ptype")

r2 = st.columns(4)
course_code  = r2[0].text_input("Course Code", st.session_state.paper_config.get("course_code","CE23E02"), key="cfg_code")
course_title = r2[1].text_input("Course Title", st.session_state.paper_config.get("course_title","Artificial Intelligence"), key="cfg_ctitle")
duration     = r2[2].text_input("Duration", st.session_state.paper_config.get("duration","3 Hours"), key="cfg_dur")
max_marks    = r2[3].number_input("Maximum Marks", 10, 300, int(st.session_state.paper_config.get("max_marks",100)), 5, key="cfg_marks")

# Save config on every interaction
st.session_state.paper_config = dict(
    institution=institution, department=department, paper_type=paper_type,
    course_code=course_code, course_title=course_title,
    duration=duration, max_marks=max_marks,
)

st.markdown("---")

BLOOM_CLS = {"Remember":"bR","Understand":"bU","Apply":"bAp","Analyze":"bAn","Evaluate":"bE","Create":"bC"}
DIFF_OPTS = ["Easy", "Medium", "Hard"]
BL_OPTIONS = [
    ("L1", "Understand"),
    ("L2", "Analyze"),
    ("L3", "Apply"),
    ("L4", "Evaluate"),
    ("L5", "Create"),
]


def _unit_co(unit):
    match = re.search(r"unit\s*(\d+)", unit, re.IGNORECASE)
    return f"CO{match.group(1)}" if match else "CO1"


def _available_units():
    texts = [item.get("text", "") for item in st.session_state.get("syl_docs", [])]
    matches = []
    for text in texts:
        matches.extend(re.findall(r"(?im)^\s*(unit\s+\d+(?:\s*[:.-]\s*[^\n]+)?)", text))
    units = list(dict.fromkeys(match.strip() for match in matches))
    return units or [f"Unit {index}" for index in range(1, 7)]

def _invalidate_downstream():
    st.session_state.retrieval_results = []
    st.session_state.pop("generated_paper", None)
    st.session_state.pop("edited_questions", None)


def _sync_parts(part_count):
    letters = [chr(ord("A") + index) for index in range(part_count)]
    old_sections = st.session_state.sections
    st.session_state.sections = {letter: old_sections.get(letter, []) for letter in letters}
    for index, letter in enumerate(letters):
        st.session_state.setdefault(f"inst_{letter}", "Answer all questions." if index == 0 else "Answer as instructed.")


part_count = st.selectbox("Number of parts", options=list(range(1, 7)), index=st.session_state.part_count - 1, key="part_count_selector")
if part_count != st.session_state.part_count:
    st.session_state.part_count = part_count
    _sync_parts(part_count)
    _invalidate_downstream()
    st.rerun()

_sync_parts(part_count)
unit_options = _available_units()

for part in st.session_state.sections:
    st.markdown(f'<div class="sec-hdr">📌 PART {part}</div>', unsafe_allow_html=True)
    default_instruction = "Answer all questions." if part == "A" else "Answer any FOUR" if part == "B" else "Answer as instructed."
    stored_instruction = st.session_state.get(f"inst_{part}", default_instruction)
    part_instruction = st.text_input(
        "Instruction for this part",
        value=stored_instruction,
        placeholder="Example: Answer any FIVE",
        key=f"inst_{part}",
    )
    st.session_state.paper_config.setdefault("part_instructions", {})[part] = part_instruction
    st.session_state.paper_config.pop("part_titles", None)
    st.session_state.paper_config.pop("part_starts", None)

    with st.form(f"form_{part}", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 2])
        units = c1.multiselect("Units (select one or more) *", options=unit_options, key=f"units_{part}")
        topic = c2.text_input("Topic (optional)", placeholder="Leave blank to use topics under the selected unit", key=f"topic_{part}")
        selected_co = _unit_co(units[0]) if units else "CO will be filled from the selected unit"
        c3.text_input("CO (automatic)", value=selected_co, disabled=True, key=f"co_preview_{part}")
        c4, c5, c6 = st.columns([1, 1, 1])
        count = c4.number_input("Number of questions", min_value=1, max_value=50, value=1, key=f"count_{part}")
        marks = c5.number_input("Default marks", min_value=1, max_value=100, value=2, key=f"marks_{part}")
        difficulty = c6.selectbox("Default difficulty", DIFF_OPTS, index=1, key=f"difficulty_{part}")
        bl_code, bl_name = st.selectbox("BL", [f"{code} - {name}" for code, name in BL_OPTIONS], index=0, key=f"bl_{part}").split(" - ", 1)
        if st.form_submit_button(f"➕ Add topic group to Part {part}") and units:
            for unit in units:
                co = _unit_co(unit)
                st.session_state.sections[part].append({
                    "name": unit,
                    "topic": topic.strip(),
                    "topic_hint": topic.strip(),
                    "bloom_code": bl_code,
                    "bloom_level": bl_name,
                    "count": int(count),
                    "marks": int(marks),
                    "difficulty": difficulty,
                    "co": co,
                    "part": part,
                    "question_specs": [
                        {"marks": int(marks), "bloom_code": bl_code, "bloom_level": bl_name, "difficulty": difficulty, "co": co}
                        for _ in range(int(count))
                    ],
                })
            _invalidate_downstream()
            st.rerun()

    for index, section in enumerate(st.session_state.sections[part]):
        bloom_class = BLOOM_CLS.get(section["bloom_level"], "bU")
        summary = (
            f'{section["name"]} → {section.get("topic_hint") or "all suggested topics"} · '
            f'{section["count"]} question(s) · default {section["marks"]} marks · '
            f'{section["difficulty"]}'
        )
        row, remove = st.columns([9, 1])
        row.markdown(
            f'<div class="bprow"><span class="unit">{summary}</span>'
            f'<span class="bloom {bloom_class}">{section["bloom_level"]}</span></div>',
            unsafe_allow_html=True,
        )
        specs = section.setdefault("question_specs", [
            {"marks": section.get("marks", 1), "bloom_code": section.get("bloom_code", "L1"), "bloom_level": section.get("bloom_level", "Understand"), "difficulty": section.get("difficulty", "Medium"), "co": section.get("co", _unit_co(section.get("name", "Unit 1")))}
            for _ in range(section.get("count", 1))
        ])
        for question_index in range(section.get("count", 1)):
            spec = specs[question_index]
            with st.expander(f"Question {question_index + 1} settings", expanded=False):
                q1, q2, q3, q4 = st.columns([1, 1, 1, 2])
                spec["marks"] = q1.number_input("Marks", min_value=1, max_value=100, value=int(spec.get("marks", section.get("marks", 1))), key=f"slot_marks_{part}_{index}_{question_index}")
                q2.text_input("CO", value=spec.get("co", section.get("co", "CO1")), disabled=True, key=f"slot_co_{part}_{index}_{question_index}")
                current_bl = f"{spec.get('bloom_code', 'L1')} - {spec.get('bloom_level', 'Understand')}"
                spec["bl"] = q3.selectbox("BL", [f"{code} - {name}" for code, name in BL_OPTIONS], index=next((i for i, option in enumerate([f"{code} - {name}" for code, name in BL_OPTIONS]) if option == current_bl), 0), key=f"slot_bl_{part}_{index}_{question_index}")
                spec["difficulty"] = q4.selectbox("Difficulty", DIFF_OPTS, index=DIFF_OPTS.index(spec.get("difficulty", "Medium")), key=f"slot_difficulty_{part}_{index}_{question_index}")
                spec["bloom_code"], spec["bloom_level"] = spec["bl"].split(" - ", 1)
        section["marks"] = max((int(spec.get("marks", 1)) for spec in specs), default=1)
        if remove.button("✕", key=f"delete_{part}_{index}"):
            st.session_state.sections[part].pop(index)
            _invalidate_downstream()
            st.rerun()
    st.markdown("---")

# ── Summary ────────────────────────────────────────────────────────────────────
all_secs = [section for part_sections in st.session_state.sections.values() for section in part_sections]
if all_secs:
    tq = sum(s["count"] for s in all_secs)
    tm = sum(s["count"]*s["marks"] for s in all_secs)
    st.markdown(f"""
<div class="summary-box">
  <b>📋 Blueprint Summary</b><br>
  <span style="color:rgba(232,232,240,.6);font-size:.85rem">
    Parts: {len(st.session_state.sections)} &nbsp;·&nbsp;
    Topic groups: {len(all_secs)} &nbsp;·&nbsp;
    <b style="color:#E8E8F0">{tq} questions</b> &nbsp;·&nbsp;
    <b style="color:#6C63FF">{tm} marks total</b>
  </span>
</div>""", unsafe_allow_html=True)
    st.success("✅ Blueprint ready! Proceed to **Step 4 → Retrieval Pipeline**")
else:
    st.info("Add at least one section to Part A or Part B above.")
