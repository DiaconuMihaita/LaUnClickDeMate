import json
import re

input_path = 'data/chapters.json'
with open(input_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Replace Romanian quotes
text = text.replace('„', "'").replace('”', "'")

# 2. Heuristic: Replace any double quote that isn't part of JSON structure.
# JSON structure quotes are typically:
# "key":
# "value",
# "value"]
# "value"}
# [ "value"
# { "key"

# We'll use a regex to find " that are between words/chars
# A " preceded by a word char or punctuation and followed by a word char or punctuation
fixed = re.sub(r'(\w)"(\s|\w)', r"\1'\2", text)
fixed = re.sub(r'(\w|\s)"(\w)', r"\1'\2", fixed)

# Try to parse
try:
    data = json.loads(fixed)
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("SUCCESS: JSON cleaned and validated.")
except json.JSONDecodeError as e:
    print(f"FAILED: JSON still has errors: {e}")
    with open(input_path, 'w', encoding='utf-8') as f:
        f.write(fixed)
