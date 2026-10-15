"""
Prompt Templates — Stage 4
All prompts for question generation, validation, and refinement.
Bloom's Taxonomy levels: Remember, Understand, Apply, Analyze, Evaluate, Create
"""

BLOOMS_LEVELS = [
    "Remember",
    "Understand",
    "Apply",
    "Analyze",
    "Evaluate",
    "Create",
]

BLOOMS_VERBS = {
    "Remember":   ["Define", "List", "State", "Recall", "Identify", "Name"],
    "Understand": ["Explain", "Describe", "Summarize", "Interpret", "Classify", "Compare"],
    "Apply":      ["Solve", "Demonstrate", "Use", "Implement", "Calculate", "Show"],
    "Analyze":    ["Analyze", "Differentiate", "Examine", "Break down", "Compare", "Contrast"],
    "Evaluate":   ["Evaluate", "Justify", "Critique", "Assess", "Judge", "Defend"],
    "Create":     ["Design", "Develop", "Construct", "Formulate", "Propose", "Create"],
}


SYSTEM_PROMPT = """You are an expert university professor and question paper setter.
Your task is to generate high-quality exam questions grounded in the provided study content.
Follow Bloom's Taxonomy strictly and write standalone questions.
Never mention the study material, retrieved context, documents, notes, syllabus, references,
or phrases such as "mentioned in the study material", "according to the provided context",
or "as discussed above". Do not include answers, citations, source names, page numbers,
internal metadata, or commentary in question text.
Return ONLY valid JSON — no explanations, no markdown fences."""


def build_question_prompt(
    context: str,
    unit: str,
    bloom_level: str,
    marks: int,
    num_questions: int = 1,
    topic_hint: str = "",
) -> list[dict]:
    """
    Build the messages list for a question generation call.
    """
    verbs = BLOOMS_VERBS.get(bloom_level, ["Explain"])
    verb_hint = ", ".join(verbs[:3])
    topic_part = f' focusing on "{topic_hint}"' if topic_hint else ""

    user_content = f"""Generate {num_questions} descriptive exam question(s) for:
- Unit/Topic: {unit}{topic_part}
- Bloom's Taxonomy Level: {bloom_level} (use verbs like: {verb_hint})
- Marks: {marks}
- Context from study material:

\"\"\"
{context}
\"\"\"

Return a JSON array. Each element must have exactly these keys:
{{
  "question": "<full question text>",
  "bloom_level": "{bloom_level}",
  "marks": {marks},
  "unit": "{unit}",
  "expected_answer_points": ["point 1", "point 2", "point 3"],
  "difficulty": "Easy|Medium|Hard"
}}"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]


def build_paper_prompt(
    contexts: list[str],
    blueprint: dict,
) -> list[dict]:
    """
    Build prompt for generating a full question paper from a blueprint.
    blueprint = {
        "title": str,
        "units": [{"name": str, "bloom_level": str, "marks": int, "count": int}]
    }
    """
    combined_context = "\n\n---\n\n".join(contexts[:6])   # cap context length

    blueprint_str = "\n".join(
        f"  - Unit '{u['name']}': {u['count']} question(s), "
        f"{u['marks']} marks each, Topic: {u.get('topic', u.get('topic_hint', '')) or 'any syllabus topic under this unit'}, "
        f"BL: {u.get('bloom_code', 'L1')} - {u['bloom_level']}, difficulty: {u.get('difficulty', 'Medium')}, "
        f"CO: {u.get('co', '')}, Part {u.get('part', 'A')}"
        for u in blueprint.get("units", [])
    )

    user_content = f"""Generate a complete question paper titled "{blueprint.get('title', 'Exam')}".

Blueprint:
{blueprint_str}

Context from study materials:
\"\"\"
{combined_context}
\"\"\"

Question-writing rules:
- Every question must be understandable without seeing the context.
- Use the requested unit and Bloom level directly. If Topic is blank, choose an appropriate topic from the syllabus content under that unit.
- Do not say that information is mentioned, given, or provided in any material.
- Do not put citations, source names, page numbers, or retrieval explanations in question text.
- Use ASCII punctuation only; write compound terms with the normal hyphen, for example table-driven and goal-based.

Return a JSON object:
{{
  "title": "<paper title>",
  "total_marks": <sum of all marks>,
  "questions": [
    {{
      "q_no": 1,
      "question": "<text>",
    "bloom_code": "L1|L2|L3|L4|L5",
    "bloom_level": "<level>",
      "marks": <int>,
      "unit": "<unit name>",
        "part": "<part letter>",
        "co": "<course outcome>",
      "expected_answer_points": ["..."],
      "difficulty": "Easy|Medium|Hard"
    }}
  ]
}}"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]
