import sys
import os
import re

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def normalize(text):
    if not text: return ""
    t = text.lower()
    t = re.sub(r'[ăâ]', 'a', t)
    t = re.sub(r'[î]', 'i', t)
    t = re.sub(r'[ș]', 's', t)
    t = re.sub(r'[ț]', 't', t)
    return t

SECTION_QUERY_MAP = {
    "reguli": {"lesson_markers": ["regula", "calcul", "formula", "proproprietate", "puterii", "puterile", "bazele"]},
    "criterii": {"lesson_markers": ["criteriul", "criteriu", "divizibilitate", "divizibil"]},
    "concepte": {"lesson_markers": ["definitia", "conceptul", "inseamna", "este", "sunt"]},
}

def extract_section_block(ch, section_name, filter_words=None):
    if not ch or section_name not in SECTION_QUERY_MAP:
        return None

    lessons = ch.get('lessons', [])
    if not lessons:
        return None

    markers = [normalize(m) for m in SECTION_QUERY_MAP[section_name]["lesson_markers"]]
    picked = []
    seen = set()

    norm_filters = [normalize(w) for w in filter_words] if filter_words else []

    def _append(line):
        txt = (line or "").strip()
        if txt and txt not in seen:
            seen.add(txt)
            picked.append(txt)

    for idx, lesson in enumerate(lessons):
        lesson_norm = normalize(lesson)
        marker_hit = any(marker in lesson_norm for marker in markers)
        
        if marker_hit:
            if norm_filters:
                hit_filter = any(fw in lesson_norm for fw in norm_filters)
                if not hit_filter:
                    if lesson.strip().endswith(":") and idx + 1 < len(lessons):
                        next_norm = normalize(lessons[idx + 1])
                        if any(fw in next_norm for fw in norm_filters):
                            hit_filter = True
                
                if not hit_filter:
                    continue

            _append(lesson)

            if idx + 1 < len(lessons):
                next_line = (lessons[idx + 1] or "").strip()
                next_norm = normalize(next_line)
                # Simplified check for test
                looks_like_formula_or_detail = (
                    "=" in next_line
                    or "^" in next_line
                )
                if next_line and looks_like_formula_or_detail:
                    _append(next_line)

    if not picked:
        return None

    return picked

# Mock chapter data
ch_div = {
    "lessons": [
        "Criteriul cu 2: Ultima cifră e 0,2,4,6,8.",
        "Criteriul cu 5: Ultima cifră e 0 sau 5.",
        "Criteriul cu 3: Suma cifrelor este divizibilă cu 3.",
        "📌 CRITERIUL DIVIZIBILITĂȚII CU 2:",
        "   Un număr este divizibil cu 2 dacă ultima sa cifră este 0, 2, 4, 6 sau 8",
        "📌 CRITERIUL DIVIZIBILITĂȚII CU 5:",
        "   Un număr este divizibil cu 5 dacă ultima sa cifră este 0 sau 5",
        "📌 CRITERIUL DIVIZIBILITĂȚII CU 3:",
        "   Un număr este divizibil cu 3 dacă SUMA CIFRELOR sale este divizibilă cu 3"
    ]
}

print("Test 1: 'criteriu cu 5'")
query1 = "care este criteriul cu 5"
filters1 = re.findall(r"\d+", normalize(query1))
res1 = extract_section_block(ch_div, "criterii", filter_words=filters1)
print(f"Result for 5: {res1}")
assert len(res1) == 2, f"Should have 2 lines (summary + detailed), got {len(res1)}"
assert all("5" in l for l in res1)

print("\nTest 2: 'criterii' (no filter)")
query2 = "criterii"
filters2 = re.findall(r"\d+", normalize(query2))
res2 = extract_section_block(ch_div, "criterii", filter_words=filters2)
print(f"Linii returnate (no filter): {len(res2)}")
assert len(res2) == 9

print("\nTest 3: 'criteriul cu 3'")
query3 = "da-mi criteriul cu 3"
filters3 = re.findall(r"\d+", normalize(query3))
res3 = extract_section_block(ch_div, "criterii", filter_words=filters3)
print(f"Result for 3: {res3}")
assert len(res3) == 2
assert all("3" in l for l in res3)

print("\nALL SPECIFICITY TESTS PASSED!")
