import sys
sys.path.insert(0, '.')

from src.llm.client import count_tokens
from src.llm.prompts import build_question_prompt, BLOOMS_LEVELS
from src.llm import _parse_json_list, _parse_json_object, _strip_fences

# Test 1: prompt building
msgs = build_question_prompt('ML is a subset of AI.', 'Unit 1', 'Understand', 5, 2)
user_len = len(msgs[1]["content"])
print(f"Prompt built: {len(msgs)} messages, user msg = {user_len} chars")

# Test 2: Bloom levels
print(f"Bloom levels: {BLOOMS_LEVELS}")

# Test 3: JSON parse with markdown fences
raw = '```json\n[{"question":"Explain ML","bloom_level":"Understand","marks":5,"unit":"U1","expected_answer_points":["p1"],"difficulty":"Medium"}]\n```'
parsed = _parse_json_list(raw)
print(f"JSON parse OK: {parsed[0]['question']}")

# Test 4: token counter
t = count_tokens("Machine learning is amazing.")
print(f"Token count: {t}")

print("=== Stage 4 imports PASSED ===")
