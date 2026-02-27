from flask import Flask, request, jsonify, send_from_directory
import json
import os
import random
import re
import ast
import operator
from difflib import SequenceMatcher
from werkzeug.utils import secure_filename
import database

app = Flask(__name__, static_folder='.')
application = app # Pentru compatibilitate Vercel
database.init_db()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Încarcă datele curiculei
def load_data():
    try:
        with open('data/chapters.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading chapters: {e}")
        return []

CHAPTERS = load_data()

# --- CONFIGURARE INTENȚII (extins cu multe sinonime) ---
INTENTS = {
    "elaborate": [
        "detaliaz", "mai mult", "povesteste", "explica-mi mai mult", "pe larg",
        "detalii", "aprofund", "informat", "continua", "mai departe",
        "lectiile", "lectie", "teoria", "teorie", "spune tot", "detalii complete",
        "toata materia", "ce trebuie sa stiu", "invata-ma", "preda-mi",
        "tot ce stii", "rezumat complet", "materia", "cursul", "lectia completa",
        "aprofundeaza", "dezvolta", "elaboreaza"
    ],
    "example": [
        "exemplu", "da-mi un exemplu", "poti sa-mi dai un exemplu",
        "pune un exemplu", "poti sa exemplifici", "arata-mi",
        "un caz", "sa vad", "demonstreaza", "cum se face", "cum se rezolva",
        "model", "rezolvare", "cum se calculeaza", "arata un model",
        "da-mi un model", "cum fac", "cum rezolv", "pas cu pas"
    ],
    "exercise": [
        "exercitiu", "da-mi ceva de rezolvat", "vreau sa exersez", "provocare",
        "vreau sa lucrez", "da-mi o problema", "test rapid", "antrenament",
        "problema", "da-mi de lucru", "pune-mi ceva", "vreau exercitii",
        "da-mi de rezolvat", "lucru", "practica"
    ],
    "define": [
        "ce inseamna", "ce este", "ce sunt", "defineste", "spune-mi despre",
        "ce reprezinta", "explicatia pentru", "care e definitia", "cine e",
        "cine sunt", "cum se defineste", "definitia", "ce se intelege prin",
        "explica", "explicati", "explica-mi", "care este", "care e", "cum e",
        "la ce se refera", "ce-i ala", "ce-i aia", "ce inseamna asta",
        "ce e ala", "ce e aia", "ce-i", "ce e", "despre ce e vorba",
        "ce presupune", "la ce ajuta"
    ],
    "fact": [
        "curiozitati", "stiai ca", "ceva interesant", "spune-mi ceva nou",
        "fun fact", "curiozitate", "spune ceva misto", "interesant",
        "wow", "amuzant", "ceva cool", "fun", "fascinant", "hai o curiozitate",
        "stii ceva interesant"
    ],
    "identity": [
        "cine esti", "ce faci", "ce esti tu", "cum te cheama", "numele tau",
        "tu cine esti", "cu cine vorbesc", "esti robot", "esti om", "tu ce esti"
    ],
    "greeting": [
        "salut", "buna", "hei", "hi", "hello", "servus", "neata", "buna ziua",
        "ce mai faci", "yo", "hola", "hey", "buna dimineata", "buna seara",
        "salutare", "ziua buna"
    ],
    "compare": [
        "compara", "compararea", "mai mic", "mai mare", "semnele",
        "cum compar", "ordonare", "crescator", "descrescator"
    ],
    "quiz": [
        "quiz", "intreaba-ma", "chestioneaza-ma", "pune-mi o intrebare",
        "testeaza-ma", "intreaba", "provocare", "verifica-ma", "stiu eu",
        "pune-mi intrebari", "vreau quiz", "hai un quiz"
    ],
    "recap": [
        "recapitulare", "ce am invatat", "sumar", "rezuma", "ce stiu",
        "ce am vazut", "rezumat", "ce am parcurs", "ce am facut"
    ],
    "test": [
        "mod test", "vreau sa fiu testat", "test final", "nota mea",
        "da-mi un test", "test complet", "evaluare", "vreau test",
        "examen", "nota"
    ],
    "help": [
        "ajutor", "help", "ce poti face", "comenzi", "cum functionezi",
        "ce stii sa faci", "optiuni", "instructiuni", "ghid", "meniu",
        "ce poti", "cum te folosesc", "ce pot intreba", "cum te pot folosi"
    ],
    "next": [
        "urmatorul", "urmatorul capitol", "alt capitol", "mergi mai departe",
        "urmatoarea lectie", "treci mai departe", "capitol urmator",
        "next", "mai departe lectia"
    ],
    "plan": [
        "plan", "plan de invatare", "cum invat", "program de invatare",
        "plan saptamanal", "cum sa invat", "strategie invatare"
    ],
    "step_by_step": [
        "pas cu pas", "explica pas cu pas", "metoda", "cum ajung",
        "arata pasii", "rezolvare pas cu pas"
    ],
    "summary": [
        "pe scurt", "scurt", "rezumat rapid", "in 3 idei",
        "esential", "concluzie"
    ]
}

# F7 — Pool de prefix-uri pentru variante de răspuns
RESPONSE_PREFIXES = [
    "Bună întrebare! ",
    "Cu plăcere! ",
    "Să vedem împreună! 🤔 ",
    "Excelent subiect! ",
    "Sigur! ",
    "Desigur! ✨ ",
    "Super! ",
    "Hai să descoperim! ",
    "Ce temă interesantă! ",
    "",
    "",
]

VAGUE_TERMS = ["asta", "aia", "acesta", "aceasta", "termenul", "cuvantul", "conceptul", "lucrul asta"]
GENERIC_VARIABLES = {"x", "y", "z", "n", "m"}

def normalize(text):
    if not text: return ""
    text = text.lower()
    replacements = {'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't', 'ş': 's', 'ţ': 't'}
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return re.sub(r'[?.,!;:\-]', '', text).strip()

def tokenize(text):
    norm = normalize(text)
    if not norm:
        return []
    return [tok for tok in norm.split() if tok]

def concept_variants(word):
    """Normalizează forme flexionate simple (ex: fractiile -> fractii/fractie)."""
    if not word:
        return []

    variants = {word}
    # Sufixe nominale uzuale; evităm sufixele de 1 literă care creează false positive.
    suffixes = ["ilor", "elor", "ului", "iilor", "ile", "lor", "ul", "le", "ii"]
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            root = word[:-len(suf)]
            variants.add(root)
            variants.add(root + "i")
            variants.add(root + "ie")
            variants.add(root + "ii")
    return [v for v in variants if len(v) >= 3]

def expand_query_words(query):
    words = tokenize(query)
    expanded = []
    for word in words:
        expanded.extend(concept_variants(word))
    # deduplicate păstrând ordinea
    result = []
    for word in expanded:
        if word not in result:
            result.append(word)
    return result

def _fuzzy_similar(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def score_intent(input_text, intent_type):
    norm_input = normalize(input_text)
    if not norm_input:
        return 0.0

    tokens = tokenize(norm_input)
    score = 0.0
    for syn in INTENTS.get(intent_type, []):
        syn_norm = normalize(syn)
        if not syn_norm:
            continue

        if syn_norm in norm_input:
            score += 2.5 if ' ' in syn_norm else 1.5
            continue

        syn_tokens = syn_norm.split()
        if len(syn_tokens) == 1:
            if any(_fuzzy_similar(syn_tokens[0], tok) >= 0.84 for tok in tokens):
                score += 1.0
        else:
            overlap = sum(1 for tok in syn_tokens if tok in tokens)
            # Evităm false positive de tip "ce ..." pe intenții nepotrivite.
            # Pentru expresii de 2+ cuvinte cerem potrivire aproape completă.
            if overlap == len(syn_tokens):
                score += 1.6
            elif len(syn_tokens) >= 3 and overlap >= len(syn_tokens) - 1:
                score += 1.1
    return score

def check_intent(input_text, intent_type, threshold=1.5):
    return score_intent(input_text, intent_type) >= threshold

def detect_best_intent(input_text):
    ranked = [(intent, score_intent(input_text, intent)) for intent in INTENTS.keys()]
    ranked.sort(key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] < 1.5:
        return None
    return ranked[0][0]

def is_identity_query(input_text):
    """Filtrează întrebările reale despre asistent, evitând conflictele cu definiții matematice."""
    norm = normalize(input_text)
    if not norm:
        return False

    identity_markers = [
        "mateai", "tu ", " tu", "cum te cheama", "numele tau", "cine esti",
        "tu cine esti", "esti robot", "esti om", "asistentul tau", "cu cine vorbesc"
    ]

    if any(marker in norm for marker in identity_markers):
        return True

    # întrebări foarte scurte de tip "ce esti?" fără concept matematic
    short_tokens = tokenize(norm)
    if len(short_tokens) <= 3 and ("ce" in short_tokens and "esti" in short_tokens):
        return True

    return False

def random_prefix():
    """F7 — Returnează un prefix aleatoriu pentru variante de răspuns."""
    return random.choice(RESPONSE_PREFIXES)

# --- POTRIVIRE FUZZY ---
def partial_match(word, target):
    """Verifică dacă un cuvânt este prefix al targetului sau invers, sau au overlap suficient."""
    if len(word) < 3:
        return False
    # Exact match
    if word == target:
        return True
    # Prefix: „adun" → „adunare"
    if target.startswith(word) and len(word) >= 3:
        return True
    # Reverse prefix: „adunarea" → „adunare"
    if word.startswith(target) and len(target) >= 3:
        return True
    # Substring match for longer words
    if len(word) >= 4 and word in target:
        return True
    if len(target) >= 4 and target in word:
        return True
    return False

def get_suggestion(current_id):
    """F4 — Returnează capitolul următor logic după cel curent."""
    ids = [ch['id'] for ch in CHAPTERS]
    try:
        idx = ids.index(current_id)
        if idx + 1 < len(CHAPTERS):
            next_ch = CHAPTERS[idx + 1]
            return {"id": next_ch['id'], "title": next_ch['title'], "icon": next_ch.get('icon', '📖')}
    except ValueError:
        pass
    return None

# --- REZOLVITOR MATEMATIC ÎMBUNĂTĂȚIT ---
ALLOWED_AST_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

ALLOWED_AST_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

def _safe_eval_ast(node):
    if isinstance(node, ast.Expression):
        return _safe_eval_ast(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Constanta invalida")
    if isinstance(node, ast.Num):
        return float(node.n)
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_AST_BINOPS:
            raise ValueError("Operator nepermis")
        left = _safe_eval_ast(node.left)
        right = _safe_eval_ast(node.right)
        if abs(left) > 1e10 or abs(right) > 1e10:
            raise ValueError("Numere prea mari")
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ValueError("Impartire la zero")
        return ALLOWED_AST_BINOPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_AST_UNARY:
            raise ValueError("Operator unar nepermis")
        return ALLOWED_AST_UNARY[op_type](_safe_eval_ast(node.operand))
    raise ValueError("Expresie nepermisa")

def extract_math_expression(input_text):
    norm = normalize(input_text)
    math_triggers = ["cat face", "cat e", "calculeaza", "rezolva", "cat este", "cat da", "rezultatul"]
    processed = input_text
    for trigger in math_triggers:
        if trigger in norm:
            idx = norm.find(trigger)
            processed = input_text[idx + len(trigger):]
            break

    processed = processed.lower()
    replacements = {
        " la puterea ": " ^ ",
        " puterea ": " ^ ",
        " ori ": " * ",
        " x ": " * ",
        " inmultit cu ": " * ",
        " impartit la ": " / ",
    }
    for old, new in replacements.items():
        processed = processed.replace(old, new)

    processed = processed.replace(',', '.').replace('^', '**')
    sanitized = re.sub(r'[^-+*/().0-9\s*]', '', processed)
    sanitized = re.sub(r'\s+', '', sanitized).strip()
    return sanitized

def solve_math(input_text):
    # Detectăm întrebări directe de tip "cât face X"
    sanitized = extract_math_expression(input_text)
    if not sanitized or len(sanitized) < 3:
        return None
    if not any(c in sanitized for c in "+*/-") and "**" not in sanitized:
        return None

    try:
        if len(sanitized) > 120:
            return None
        if any(c.isalpha() for c in sanitized):
            return None
        parsed = ast.parse(sanitized, mode='eval')
        result = round(_safe_eval_ast(parsed), 4)
        if result.is_integer():
            result = int(result)
        display_expr = sanitized.replace('**', '^')
        return {
            "steps": [f"Calculăm expresia: {display_expr}", f"Rezultatul final este: {result}"],
            "total": str(result).replace('.', ',')
        }
    except Exception:
        return None

# --- DEEP SEARCH ÎMBUNĂTĂȚIT (cu fuzzy matching) ---
def deep_search(query):
    norm_q = normalize(query)
    words = [w for w in expand_query_words(norm_q) if len(w) >= 3]
    if not words: return None

    # Filtrare stopwords românești
    stopwords = {"ce", "care", "este", "sunt", "pentru", "din", "lui", "unde", "cum", "cand", "mai", "imi",
                 "poti", "vreau", "spune", "despre", "arata", "zici", "asta", "aia", "cele"}
    content_words = [w for w in words if w not in stopwords]
    if not content_words:
        content_words = words  # Fallback dacă toate sunt stopwords

    matches = []
    for ch in CHAPTERS:
        score = 0

        # 1. Titlu - cel mai important
        title_norm = normalize(ch.get('title', ''))
        title_words = title_norm.split()
        for w in content_words:
            if w in title_norm:
                score += 15
            elif any(partial_match(w, tw) for tw in title_words):
                score += 10

        # 2. Keywords - foarte important
        for kw in ch.get('keywords', []):
            kw_norm = normalize(kw)
            for w in content_words:
                if w == kw_norm:
                    score += 12
                elif partial_match(w, kw_norm):
                    score += 8

        # 3. Lecții
        for lesson in ch.get('lessons', []):
            lesson_norm = normalize(lesson)
            for w in content_words:
                if w in lesson_norm:
                    score += 2
                    break  # O singură potrivire per lecție

        # 4. Exemple
        for ex in ch.get('examples', []):
            if any(w in normalize(ex) for w in content_words):
                score += 1

        # 5. Exerciții
        for ex in ch.get('exercises', []):
            q_text = ex.get('question', '') if isinstance(ex, dict) else str(ex)
            if any(w in normalize(q_text) for w in content_words):
                score += 2

        # 6. Dicționar
        dictionary = ch.get('dictionary', {})
        for term in dictionary:
            term_norm = normalize(term)
            for w in content_words:
                if w == term_norm or partial_match(w, term_norm):
                    score += 8

        if score > 0:
            matches.append((ch, score))

    if not matches: return None
    matches.sort(key=lambda x: x[1], reverse=True)

    # Returnăm doar dacă scorul e suficient de mare
    best = matches[0]
    if best[1] >= 3:
        return best[0]
    return None

def get_top_matches(query, count=3):
    """Returnează cele mai relevante capitole (pentru fallback)."""
    norm_q = normalize(query)
    words = [w for w in expand_query_words(norm_q) if len(w) >= 3]
    if not words: return []

    stopwords = {"ce", "care", "este", "sunt", "inseamna", "defineste", "spune", "despre", "explica", "poti", "vreau", "cum"}
    content_words = [w for w in words if w not in stopwords]
    if not content_words:
        content_words = words

    matches = []
    for ch in CHAPTERS:
        score = 0
        title_norm = normalize(ch.get('title', ''))
        for w in content_words:
            if w in title_norm: score += 10
            for kw in ch.get('keywords', []):
                if partial_match(w, normalize(kw)): score += 3
        if score > 0:
            matches.append((ch, score))

    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches[:count]]

def get_definition_from_chapter(ch, query):
    """Extrage definiția cea mai relevantă dintr-un capitol."""
    norm_q = normalize(query)
    dictionary = ch.get('dictionary', {})
    lessons = ch.get('lessons', [])

    # 1. Caută în dicționar termenul exact
    for term, def_text in dictionary.items():
        if normalize(term) in norm_q:
            return f"<strong>{term.upper()}</strong>: {def_text}"

    # 2. Caută în dicționar termenul care conține cuvinte din query
    words = [w for w in norm_q.split() if len(w) > 3]
    for term, def_text in dictionary.items():
        if any(w in normalize(term) for w in words):
            return f"<strong>{term.upper()}</strong>: {def_text}"

    # 3. Caută lecții care conțin "Definiție:"
    for lesson in lessons:
        lesson_norm = normalize(lesson)
        if lesson_norm.startswith("definitie") or " definitie:" in lesson_norm or " definitie " in lesson_norm:
            return lesson

    # 4. Returnează prima lecție relevantă sau prima lecție
    for lesson in lessons:
        if any(w in normalize(lesson) for w in words):
            return lesson

    return lessons[0] if lessons else ""

def get_global_definition(query):
    """Caută definiție în toate capitolele, chiar fără capitol curent."""
    norm_q = normalize(query)
    if not norm_q:
        return None

    # 1) Potrivire exactă pe termen din dicționare
    for ch in CHAPTERS:
        dictionary = ch.get('dictionary', {})
        for term, def_text in dictionary.items():
            term_norm = normalize(term)
            if term_norm and term_norm in norm_q:
                return f"<strong>{term.upper()}</strong>: {def_text}<br><br><em>(din capitolul: {ch['title']})</em>"

    # 2) Potrivire fuzzy simplă pe cuvinte-cheie din întrebare
    words = [w for w in tokenize(norm_q) if len(w) >= 3]
    for ch in CHAPTERS:
        dictionary = ch.get('dictionary', {})
        for term, def_text in dictionary.items():
            term_norm = normalize(term)
            for w in words:
                if w in term_norm or _fuzzy_similar(w, term_norm) >= 0.86:
                    return f"<strong>{term.upper()}</strong>: {def_text}<br><br><em>(din capitolul: {ch['title']})</em>"
    return None

def get_symbol_definition(query):
    """Răspuns pentru întrebări de tip 'ce este x' sau 'ce sunt x și y'."""
    tokens = tokenize(query)
    symbols = [t for t in tokens if t in GENERIC_VARIABLES]
    if not symbols:
        return None

    unique_symbols = []
    for sym in symbols:
        if sym not in unique_symbols:
            unique_symbols.append(sym)

    pieces = []
    for sym in unique_symbols:
        if sym == 'n':
            pieces.append("<li><strong>n</strong>: de obicei reprezintă un număr natural.</li>")
        elif sym == 'm':
            pieces.append("<li><strong>m</strong>: o altă variabilă (număr necunoscut), folosită când avem mai multe necunoscute.</li>")
        else:
            pieces.append(f"<li><strong>{sym}</strong>: variabilă (număr necunoscut) pe care trebuie să o aflăm.</li>")

    return (
        "<strong>🧠 Despre simboluri în matematică:</strong><br>"
        "Literele (x, y, z, n...) sunt <strong>variabile</strong>, adică numere necunoscute sau generale.<br><br>"
        "<ul style='text-align:left'>"
        f"{''.join(pieces)}"
        "</ul>"
        "Exemplu: în ecuația <strong>x + 5 = 12</strong>, valoarea lui <strong>x</strong> este 7."
    )

def find_best_chapter_for_definition(query):
    """Găsește capitolul cel mai probabil pentru întrebări de tip 'ce sunt ...'."""
    words = [w for w in expand_query_words(query) if len(w) >= 3]
    if not words:
        return None

    stopwords = {"ce", "care", "este", "sunt", "inseamna", "defineste", "spune", "despre", "explica", "mi"}
    content_words = [w for w in words if w not in stopwords]
    if not content_words:
        content_words = words

    best_ch = None
    best_score = 0
    for ch in CHAPTERS:
        score = 0
        title_norm = normalize(ch.get('title', ''))
        for word in content_words:
            if word == title_norm or f" {word} " in f" {title_norm} ":
                score += 10
            elif word in title_norm:
                score += 8

        for kw in ch.get('keywords', []):
            kw_norm = normalize(kw)
            for word in content_words:
                if word == kw_norm:
                    score += 10
                elif partial_match(word, kw_norm):
                    score += 6
                elif _fuzzy_similar(word, kw_norm) >= 0.86:
                    score += 4

        dictionary = ch.get('dictionary', {})
        for term in dictionary:
            term_norm = normalize(term)
            for word in content_words:
                if word == term_norm or partial_match(word, term_norm):
                    score += 7
                elif _fuzzy_similar(word, term_norm) >= 0.86:
                    score += 4

        if score > best_score:
            best_score = score
            best_ch = ch

    if best_score >= 7:
        return best_ch
    return None

def get_structured_intro(ch, query):
    lessons = ch.get('lessons', [])
    definition = get_definition_from_chapter(ch, query)
    intro = lessons[0] if lessons else ""
    explanation = lessons[1] if len(lessons) > 1 else ""

    msg = f"Sigur! Te pot ajuta cu o explicație despre <strong>{ch['title']}</strong>.<br><br>"
    if definition and definition != intro:
        msg += f"{definition}<br><br>"
    msg += f"{intro}<br>{explanation}"
    return msg

def get_structured_intro_by_level(ch, query, level):
    lessons = ch.get('lessons', [])
    examples = ch.get('examples', [])
    definition = get_definition_from_chapter(ch, query)
    summary_limit = 2 if level == 'simple' else 5

    msg = f"Sigur! Te ajut cu <strong>{ch['title']}</strong>.<br><br>"
    if definition:
        msg += f"<strong>Ideea-cheie:</strong> {definition}<br><br>"

    if lessons:
        msg += "<strong>Puncte importante:</strong><ul style='text-align:left'>"
        for lesson in lessons[:summary_limit]:
            msg += f"<li>{lesson}</li>"
        msg += "</ul>"

    if level == 'detailed' and examples:
        msg += "<br><strong>Exemple utile:</strong><ul style='text-align:left'>"
        for example in examples[:2]:
            msg += f"<li><em>{example}</em></li>"
        msg += "</ul>"
    return msg

def normalize_answer_parts(value):
    text = normalize(str(value))
    text = text.replace(';', ',')
    parts = [p.strip() for p in text.split(',') if p.strip()]
    return parts if parts else [text]

def numeric_value(value):
    try:
        return float(str(value).replace(',', '.').strip())
    except Exception:
        return None

def answers_match(user_answer, correct_answer):
    user_norm = normalize(str(user_answer))
    correct_norm = normalize(str(correct_answer))

    if not user_norm or not correct_norm:
        return False
    if user_norm == correct_norm:
        return True
    if correct_norm in user_norm or user_norm in correct_norm:
        return True

    user_num = numeric_value(user_answer)
    correct_num = numeric_value(correct_answer)
    if user_num is not None and correct_num is not None:
        return abs(user_num - correct_num) < 1e-9

    user_parts = sorted(normalize_answer_parts(user_answer))
    correct_parts = sorted(normalize_answer_parts(correct_answer))
    if user_parts == correct_parts:
        return True

    if len(user_parts) == len(correct_parts):
        fuzzy_ok = all(_fuzzy_similar(u, c) >= 0.86 for u, c in zip(user_parts, correct_parts))
        if fuzzy_ok:
            return True

    return False

def build_wrong_answer_hint(chapter_id):
    ch = next((c for c in CHAPTERS if c['id'] == chapter_id), None)
    if not ch:
        return ""

    lessons = ch.get('lessons', [])
    dictionary = ch.get('dictionary', {})
    if dictionary:
        term, definition = random.choice(list(dictionary.items()))
        return f"<br><br>💡 Hint: Reamintește-ți termenul <strong>{term}</strong> — {definition}"
    if lessons:
        return f"<br><br>💡 Hint: {lessons[0]}"
    return ""

def get_learning_plan_message():
    topics = [ch['title'] for ch in CHAPTERS[:6]]
    if not topics:
        return "Încă nu am capitole disponibile pentru plan."

    days = [
        ("Ziua 1", topics[0]),
        ("Ziua 2", topics[1] if len(topics) > 1 else topics[0]),
        ("Ziua 3", topics[2] if len(topics) > 2 else topics[0]),
        ("Ziua 4", topics[3] if len(topics) > 3 else topics[0]),
        ("Ziua 5", topics[4] if len(topics) > 4 else topics[0]),
        ("Ziua 6", topics[5] if len(topics) > 5 else topics[0]),
        ("Ziua 7", "Recapitulare + mini-test"),
    ]

    html = "<strong>🗓️ Plan de învățare (7 zile):</strong><ul style='text-align:left'>"
    for day, topic in days:
        html += f"<li><strong>{day}:</strong> {topic}</li>"
    html += "</ul>"
    html += "<br>Tip: În fiecare zi: 15 min teorie + 10 min exemple + 10 min exerciții."
    return html

# --- MESAJ HELP ---
def get_help_message():
    chapter_list = "<br>".join([f"  {ch.get('icon', '📖')} {ch['title']}" for ch in CHAPTERS])
    return (
        "<strong>🤖 Ce pot face pentru tine:</strong><br><br>"
        "<strong>📖 Înveți un capitol:</strong> Scrie numele subiectului (ex: 'adunare', 'puteri', 'numere prime')<br>"
        "<strong>📝 Definiții:</strong> 'Ce este X?' sau 'Explică-mi X'<br>"
        "<strong>💡 Exemple:</strong> 'Dă-mi un exemplu' sau 'Cum se rezolvă?'<br>"
        "<strong>📚 Lecție completă:</strong> 'Detalii' sau 'Toată materia'<br>"
        "<strong>💪 Exerciții:</strong> 'Dă-mi un exercițiu' sau 'Vreau să exersez'<br>"
        "<strong>🧠 Quiz:</strong> 'Quiz' sau 'Testează-mă'<br>"
        "<strong>🎯 Test complet:</strong> 'Dă-mi un test' (5 întrebări, notă finală)<br>"
        "<strong>🗓️ Plan învățare:</strong> 'Dă-mi un plan de învățare'<br>"
        "<strong>🧩 Pas cu pas:</strong> 'Explică pas cu pas'<br>"
        "<strong>🔢 Calculator:</strong> 'Cât face 25+37?' sau '2^3 + 5'<br>"
        "<strong>🌟 Curiozități:</strong> 'Știai că?' sau 'Curiozitate'<br>"
        "<strong>📋 Recapitulare:</strong> 'Ce am învățat?'<br>"
        "<strong>➡️ Capitol următor:</strong> 'Următorul' sau 'Mai departe'<br><br>"
        "<strong>📘 Capitole disponibile:</strong><br>"
        f"{chapter_list}"
    )

# --- RUTE ---
@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path): 
    # If path points directly to uploads folder, serve it securely
    if path.startswith('uploads/'):
        return send_from_directory(app.config['UPLOAD_FOLDER'], path.replace('uploads/', ''))
    return send_from_directory('.', path)

@app.route('/api/chapters', methods=['GET'])
def get_chapters(): return jsonify(CHAPTERS)

# --- AUTH ROUTES ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Numele și parola sunt obligatorii.'}), 400
        
    res = database.create_user(username, password, role)
    return jsonify(res)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user_data = database.login_user(username, password)
    if not user_data:
        return jsonify({'success': False, 'error': 'Nume sau parolă incorectă.'}), 401
        
    return jsonify({'success': True, 'user': user_data})

@app.route('/api/user', methods=['GET'])
def get_current_user():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False}), 401
    return jsonify({'success': True, 'user': user})

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    database.logout_user(token)
    return jsonify({'success': True})

@app.route('/api/stats/daily', methods=['GET'])
def get_daily_stats():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False}), 401
    
    activity = database.get_daily_activity(user['id'])
    return jsonify({'success': True, 'activity': activity})

# --- CLASSROOM ROUTES ---
@app.route('/api/class/create', methods=['POST'])
def create_class():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
        
    data = request.json
    res = database.create_class(user['id'], data.get('name'))
    return jsonify(res)

@app.route('/api/class/join', methods=['POST'])
def join_class():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 401
        
    data = request.json
    res = database.join_class(user['id'], data.get('code'))
    return jsonify(res)

@app.route('/api/class/rankings/<code>', methods=['GET'])
def get_rankings(code):
    res = database.get_class_rankings(code)
    if not res:
        return jsonify({'success': False, 'error': 'Clasa nu există.'}), 404
    return jsonify({'success': True, 'data': res})

@app.route('/api/progress/update', methods=['POST'])
def update_user_progress():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False}), 401
        
    data = request.json
    database.update_progress(user['id'], data.get('chapterId'), data.get('isCorrect'))
    return jsonify({'success': True})


@app.route('/api/student/details/<int:user_id>', methods=['GET'])
def get_student_detail(user_id):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
    
    details = database.get_student_details(user_id)
    return jsonify({'success': True, 'details': details})


@app.route('/api/homework/create', methods=['POST'])
def add_homework():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
    
    # Handle possible multipart/form-data or JSON
    req_json = request.get_json(silent=True) or {}
    chapter_id = request.form.get('chapterId') or req_json.get('chapterId')
    description = request.form.get('description') or req_json.get('description')
    due_date = request.form.get('dueDate') or req_json.get('dueDate')

    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = f'/uploads/{filename}'
            
    database.create_homework(
        user['class_code'],
        chapter_id,
        description,
        file_path,
        due_date
    )
    return jsonify({'success': True})


@app.route('/api/homework/class/<code>', methods=['GET'])
def get_homework_list(code):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    
    # Students get completion status
    user_id = user['id'] if user and user['role'] == 'student' else None
    homework = database.get_class_homework(code, user_id)
    return jsonify({'success': True, 'homework': homework})


@app.route('/api/homework/complete', methods=['POST'])
def mark_homework_done():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False}), 401
    
    req_json = request.get_json(silent=True) or {}
    homework_id = request.form.get('homeworkId') or req_json.get('homeworkId')
    
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = f'/uploads/{filename}'

    database.complete_homework(user['id'], homework_id, file_path)
    return jsonify({'success': True})


@app.route('/api/homework/<int:hw_id>/completions', methods=['GET'])
def get_hw_completions(hw_id):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
    if not user.get('class_code'):
        return jsonify({'success': False, 'error': 'Nu ai o clasă activă.'}), 400
    completions = database.get_homework_completions(hw_id, user['class_code'])
    return jsonify({'success': True, 'completions': completions})


# --- TEST ROUTES ---
@app.route('/api/test/create', methods=['POST'])
def create_test_route():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
        
    req_json = request.get_json(silent=True) or {}
    title = request.form.get('title', 'Test') or req_json.get('title', 'Test')
    chapter_id = request.form.get('chapterId') or req_json.get('chapterId')
    num_questions = int(request.form.get('numQuestions', 5) or req_json.get('numQuestions', 5))
    custom_questions = request.form.get('customQuestions') or req_json.get('customQuestions')

    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = f'/uploads/{filename}'

    res = database.create_test(
        user['class_code'],
        title,
        chapter_id,
        num_questions,
        file_path,
        custom_questions
    )
    return jsonify(res)


@app.route('/api/test/class/<code>', methods=['GET'])
def get_tests_for_class(code):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False}), 401
    user_id = user['id'] if user['role'] == 'student' else None
    tests = database.get_class_tests(code, user_id)
    return jsonify({'success': True, 'tests': tests})


@app.route('/api/test/submit', methods=['POST'])
def submit_test():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False}), 401
    data = request.json
    ok = database.submit_test_result(
        data.get('testId'),
        user['id'],
        data.get('score', 0),
        data.get('total', 0)
    )
    return jsonify({'success': ok})


@app.route('/api/test/<int:test_id>/results', methods=['GET'])
def get_test_results_route(test_id):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
    if not user.get('class_code'):
        return jsonify({'success': False}), 400
    results = database.get_test_results(test_id, user['class_code'])
    return jsonify({'success': True, 'results': results})

# --- PROVOCAREA ZILEI ---
DAILY_CHALLENGES = [
    {
        "id": 1,
        "question": "Dacă 3 kilograme de mere costă 15 lei, cât costă 5 kilograme?",
        "answer": "25",
        "hint": "Află mai întâi prețul unui singur kilogram (15 : 3)."
    },
    {
        "id": 2,
        "question": "Suma a două numere este 30, iar diferența lor este 10. Care este numărul mai mare?",
        "answer": "20",
        "hint": "Suma numerelor este 30, diferența 10. (S+D):2."
    },
    {
        "id": 3,
        "question": "Câte numere de două cifre se pot forma folosind doar cifrele 5 și 7?",
        "answer": "4",
        "hint": "Gândește-te la toate combinațiile: 55, 57, 75, 77."
    },
    {
        "id": 4,
        "question": "Un tren parcurge 120 km în 2 ore. Câți km parcurge în 3 ore dacă păstrează viteza?",
        "answer": "180",
        "hint": "Află câți km parcurge într-o oră (120 : 2)."
    }
]

@app.route('/api/daily-challenge', methods=['GET'])
def get_daily_challenge():
    import datetime
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    challenge = DAILY_CHALLENGES[day_of_year % len(DAILY_CHALLENGES)]
    return jsonify(challenge)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('input', '')
        norm_input = normalize(user_input)
        level = data.get('level', 'simple')
        if level not in ['simple', 'detailed']:
            level = 'simple'
        last_id = data.get('lastChapterId')
        visited_chapters = data.get('visitedChapters', [])
        current_ch = next((c for c in CHAPTERS if c['id'] == last_id), None)
        primary_intent = detect_best_intent(user_input)

        # 1. Identitate / Salut / Garbage
        if len(norm_input) < 2:
            return jsonify({"message": "Hopa! Mesajul tău e prea scurt. Spune-mi cu ce te pot ajuta la matematică! 💡 Scrie <strong>ajutor</strong> pentru a vedea ce pot face."})
        if (primary_intent == "identity" or check_intent(user_input, "identity")) and is_identity_query(user_input):
            return jsonify({"message": "Sunt <strong>MateAI</strong>, asistentul tău virtual de matematică! 🤖 Te pot ajuta cu oricare din cele 22 de capitole de clasa a 5-a. Scrie <strong>ajutor</strong> pentru lista completă de comenzi!"})
        if (primary_intent == "greeting" or check_intent(user_input, "greeting")) and len(norm_input.split()) < 4:
            return jsonify({"message": "Salut! 😄 Sunt aici să explorăm matematica. Ce capitol vrei să discutăm azi? 🍕🔢<br><br>💡 Scrie <strong>ajutor</strong> dacă vrei să vezi ce pot face!"})

        # HELP — Afișare comenzi
        if primary_intent == "help" or check_intent(user_input, "help"):
            return jsonify({"message": get_help_message()})

        # DEFINIȚII GENERALE (fără capitol detectat): x, y, z, n + termeni globali
        if primary_intent == "define" or check_intent(user_input, "define"):
            symbol_def = get_symbol_definition(user_input)
            if symbol_def:
                return jsonify({"message": symbol_def, "lastChapterId": last_id})

            concept_ch = find_best_chapter_for_definition(user_input)
            if concept_ch:
                definition = get_definition_from_chapter(concept_ch, user_input)
                examples = concept_ch.get('examples', [])
                msg = f"📘 <strong>{concept_ch['title']}</strong><br><br>{definition}"
                if examples:
                    msg += f"<br><br><strong>Exemplu:</strong> <em>{examples[0]}</em>"
                return jsonify({
                    "message": msg,
                    "lastChapterId": concept_ch['id'],
                    "suggestion": get_suggestion(concept_ch['id'])
                })

            global_def = get_global_definition(user_input)
            if global_def:
                return jsonify({"message": global_def, "lastChapterId": last_id})

            # Fallback dedicat pentru întrebări de definiție: sugerăm concepte apropiate
            define_matches = get_top_matches(user_input, count=3)
            if define_matches:
                suggestions_html = "<br>".join([f"• <strong>{ch['title']}</strong>" for ch in define_matches])
                return jsonify({
                    "message": (
                        "Am înțeles că vrei o <strong>definiție</strong>, dar nu am identificat exact termenul.<br><br>"
                        f"Încearcă unul dintre aceste subiecte:<br>{suggestions_html}<br><br>"
                        "Exemple: <em>ce sunt fracțiile</em>, <em>ce este un număr prim</em>, <em>ce înseamnă divizor</em>."
                    ),
                    "lastChapterId": last_id
                })
            return jsonify({
                "message": "Văd că ceri o definiție. Scrie termenul matematic cât mai exact, de exemplu: <em>ce sunt numerele naturale</em>.",
                "lastChapterId": last_id
            })

        # PLAN DE ÎNVĂȚARE
        if primary_intent == "plan" or check_intent(user_input, "plan"):
            return jsonify({"message": get_learning_plan_message(), "lastChapterId": last_id})

        # NEXT — Capitol următor
        if primary_intent == "next" or check_intent(user_input, "next"):
            if current_ch:
                suggestion = get_suggestion(current_ch['id'])
                if suggestion:
                    next_ch = next((c for c in CHAPTERS if c['id'] == suggestion['id']), None)
                    if next_ch:
                        msg = get_structured_intro(next_ch, next_ch['title'])
                        return jsonify({
                            "message": f"➡️ Mergem la capitolul următor!<br><br>{msg}",
                            "lastChapterId": next_ch['id'],
                            "suggestion": get_suggestion(next_ch['id'])
                        })
            return jsonify({"message": "Nu am un capitol activ din care să merg mai departe. Alege mai întâi un subiect! Scrie <strong>ajutor</strong> pentru lista de capitole."})

        # F3 — RECAPITULARE
        if primary_intent == "recap" or check_intent(user_input, "recap"):
            if not visited_chapters:
                return jsonify({"message": "Nu am explorat niciun capitol împreună în această sesiune. Hai să începem! Alege un subiect sau întreabă-mă ceva. 📚"})
            recap_html = "<strong>📋 Recapitulare sesiune:</strong><br><ul style='text-align:left'>"
            for ch_id in visited_chapters:
                ch = next((c for c in CHAPTERS if c['id'] == ch_id), None)
                if ch:
                    first_lesson = ch.get('lessons', [''])[0]
                    short = first_lesson[:90] + ("..." if len(first_lesson) > 90 else "")
                    recap_html += f"<li><strong>{ch['title']}</strong>: {short}</li>"
            recap_html += "</ul><br>Continuă să explorezi! 💪"
            return jsonify({"message": recap_html})

        # F6 — MOD TEST
        if primary_intent == "test" or check_intent(user_input, "test"):
            chapters_with_ex = [c for c in CHAPTERS if c.get('exercises')]
            test_chapters = random.sample(chapters_with_ex, min(5, len(chapters_with_ex)))
            questions = []
            for ch in test_chapters:
                ex = random.choice(ch['exercises'])
                questions.append({"chapterId": ch['id'], "chapterTitle": ch['title'], "question": ex['question'], "answer": ex['answer']})
            return jsonify({
                "message": "🎯 <strong>Mod Test Activat!</strong><br><br>Îți voi pune 5 întrebări din capitole diferite. Răspunde cu tot ce știi! Hai să începem!",
                "testMode": True,
                "testQuestions": questions,
                "currentQuestion": 0
            })

        # 2. Detecție capitol
        found_ch = deep_search(user_input)
        if check_intent(user_input, "compare"):
            found_ch = next((c for c in CHAPTERS if c['id'] == "comparare_ordonare"), found_ch)

        if found_ch:
            if found_ch['id'] != last_id:
                current_ch = found_ch
                last_id = found_ch['id']
                if not any(check_intent(user_input, i) for i in ["elaborate", "example", "exercise", "define", "quiz", "fact", "step_by_step", "summary"]):
                    msg = get_structured_intro_by_level(found_ch, user_input, level)
                    suggestion = get_suggestion(last_id)
                    return jsonify({
                        "message": f"{msg}<br><br>Vrei să aprofundăm subiectul? 💡 Poți cere: detalii, exemple, exerciții, quiz sau curiozități!",
                        "lastChapterId": last_id,
                        "suggestion": suggestion
                    })

        # 3. Interacțiuni specifice
        target = found_ch if found_ch else current_ch
        if target:
            # F1 — QUIZ
            if primary_intent == "quiz" or check_intent(user_input, "quiz"):
                exercises = target.get('exercises', [])
                if exercises:
                    ex = random.choice(exercises)
                    suggestion = get_suggestion(target['id'])
                    return jsonify({
                        "message": f"🧠 <strong>Quiz — {target['title']}</strong><br><br>{ex['question']}",
                        "quizMode": True,
                        "exercise": ex['question'],
                        "correctAnswer": ex['answer'],
                        "chapterId": target['id'],
                        "lastChapterId": target['id'],
                        "suggestion": suggestion
                    })

            # CURIOZITĂȚI / FUN FACTS
            if primary_intent == "fact" or check_intent(user_input, "fact"):
                fun_facts = target.get('fun_facts', [])
                if fun_facts:
                    prefix = random_prefix()
                    fact = random.choice(fun_facts)
                    suggestion = get_suggestion(target['id'])
                    return jsonify({
                        "message": f"{prefix}🌟 <strong>Știai că?</strong> ({target['title']})<br><br>{fact}",
                        "lastChapterId": target['id'],
                        "suggestion": suggestion
                    })
                else:
                    return jsonify({
                        "message": f"Momentan nu am curiozități pentru <strong>{target['title']}</strong>, dar pot să-ți explic capitolul, să-ți dau exemple sau exerciții! Ce preferi?",
                        "lastChapterId": target['id']
                    })

            # DEFINIȚIE + F7 prefix
            if primary_intent == "define" or check_intent(user_input, "define"):
                definition = get_definition_from_chapter(target, user_input)
                lessons = target.get('lessons', [])
                examples = target.get('examples', [])
                prefix = random_prefix()
                msg = f"{prefix}📖 <strong>{target['title']}</strong><br><br>"
                if definition:
                    msg += f"{definition}<br><br>"
                if lessons:
                    msg += "<strong>Ce trebuie să știi:</strong><br><ul style='text-align: left;'>"
                    for l in lessons:
                        if l != definition:
                            msg += f"<li>{l}</li>"
                    msg += "</ul>"
                if examples:
                    msg += f"<br><strong>Exemplu:</strong><br><em>{random.choice(examples)}</em>"
                suggestion = get_suggestion(target['id'])
                return jsonify({"message": msg, "lastChapterId": target['id'], "suggestion": suggestion})

            # ELABORARE + F7 prefix
            if primary_intent == "elaborate" or check_intent(user_input, "elaborate"):
                lessons = target.get('lessons', [])
                lessons_html = "<strong>Lecțiile capitolului:</strong><br><ul style='text-align: left;'>" + "".join([f"<li>{l}</li>" for l in lessons]) + "</ul>"
                examples = target.get('examples', [])
                if examples:
                    lessons_html += "<br><strong>Exemple:</strong><br><ul style='text-align: left;'>" + "".join([f"<li><em>{e}</em></li>" for e in examples]) + "</ul>"

                dictionary = target.get('dictionary', {})
                if dictionary:
                    dict_items = "".join([f"<li><strong>{term}</strong>: {definition}</li>" for term, definition in dictionary.items()])
                    lessons_html += f"<br><strong>Dicționar de termeni:</strong><br><ul style='text-align: left;'>{dict_items}</ul>"

                exercises = target.get('exercises', [])
                if exercises:
                    ex_items = []
                    for ex in exercises:
                        if isinstance(ex, dict):
                            ex_items.append(f"<li>{ex.get('question', '')}</li>")
                        else:
                            ex_items.append(f"<li>{str(ex)}</li>")
                    lessons_html += "<br><strong>Exerciții propuse:</strong><br><ul style='text-align: left;'>" + "".join(ex_items) + "</ul>"

                prefix = random_prefix()
                suggestion = get_suggestion(target['id'])
                return jsonify({"message": f"{prefix}Iată varianta completă pentru <strong>{target['title']}</strong>:<br><br>{lessons_html}", "lastChapterId": target['id'], "suggestion": suggestion})

            if primary_intent == "step_by_step" or check_intent(user_input, "step_by_step"):
                examples = target.get('examples', [])
                exercises = target.get('exercises', [])
                msg = f"🧩 <strong>Explicație pas cu pas — {target['title']}</strong><br><br>"
                if examples:
                    msg += f"<strong>1)</strong> Privește modelul: <em>{examples[0]}</em><br>"
                if exercises:
                    ex = exercises[0]
                    q = ex['question'] if isinstance(ex, dict) else str(ex)
                    msg += f"<strong>2)</strong> Aplică aceeași idee pe: <em>{q}</em><br>"
                msg += "<strong>3)</strong> Verifică rezultatul comparând pașii, nu doar răspunsul final."
                suggestion = get_suggestion(target['id'])
                return jsonify({"message": msg, "lastChapterId": target['id'], "suggestion": suggestion})

            if primary_intent == "summary" or check_intent(user_input, "summary"):
                lessons = target.get('lessons', [])
                short_points = lessons[:3] if lessons else []
                msg = f"⚡ <strong>Pe scurt — {target['title']}</strong><br><ul style='text-align:left'>"
                for point in short_points:
                    msg += f"<li>{point}</li>"
                msg += "</ul>"
                suggestion = get_suggestion(target['id'])
                return jsonify({"message": msg, "lastChapterId": target['id'], "suggestion": suggestion})

            # EXEMPLE + F7 prefix
            if primary_intent == "example" or check_intent(user_input, "example"):
                examples = target.get('examples', [])
                if examples:
                    prefix = random_prefix()
                    suggestion = get_suggestion(target['id'])
                    return jsonify({"message": f"{prefix}Iată un exemplu din <strong>{target['title']}</strong>:<br><em>{random.choice(examples)}</em>", "lastChapterId": target['id'], "suggestion": suggestion})

            # EXERCIȚII (cu quizMode activ)
            if primary_intent == "exercise" or check_intent(user_input, "exercise"):
                exercises = target.get('exercises', [])
                if exercises:
                    ex = random.choice(exercises)
                    suggestion = get_suggestion(target['id'])
                    return jsonify({
                        "message": f"💪 Provocare! <strong>{target['title']}</strong>:<br>{ex['question']}",
                        "quizMode": True,
                        "exercise": ex['question'],
                        "correctAnswer": ex['answer'],
                        "chapterId": target['id'],
                        "lastChapterId": target['id'],
                        "suggestion": suggestion
                    })

        # 4. Math Solver
        solution = solve_math(user_input)
        if solution:
            return jsonify({
                "message": f"🔢 {random_prefix()}Rezultatul calculului este <strong>{solution['total']}</strong>.<br><br><em>{solution['steps'][0]}</em>",
                "lastChapterId": last_id
            })

        # 5. Fallback inteligent
        if found_ch:
            lessons = found_ch.get('lessons', [])
            relevant_parts = [l for l in lessons if any(w in normalize(l) for w in norm_input.split() if len(w) > 3)]
            if relevant_parts:
                suggestion = get_suggestion(found_ch['id'])
                return jsonify({"message": f"Legat de întrebarea ta, iată o informație din <strong>{found_ch['title']}</strong>:<br><br>{relevant_parts[0]}", "lastChapterId": found_ch['id'], "suggestion": suggestion})

        # Fallback cu sugestii de capitole
        top_matches = get_top_matches(user_input)
        if top_matches:
            suggestions_html = "<br>".join([f"  • <strong>{ch['title']}</strong>" for ch in top_matches])
            return jsonify({
                "message": f"Nu am găsit un răspuns exact, dar cred că te-ar putea interesa:<br><br>{suggestions_html}<br><br>Scrie numele capitolului pentru mai multe detalii! 📖"
            })

        # Fallback general
        topics_sample = random.sample(CHAPTERS, min(5, len(CHAPTERS)))
        topics_list = "<br>".join([f"  {ch.get('icon', '📖')} {ch['title']}" for ch in topics_sample])
        return jsonify({
            "message": f"Hmm, nu am înțeles exact ce cauți. 🤔 Ca asistent de matematică clasa a 5-a, iată câteva subiecte pe care le pot explica:<br><br>{topics_list}<br><br>Scrie ce te interesează, sau tastează <strong>ajutor</strong> pentru toate comenzile! 💡"
        })
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"message": "Am întâmpinat o mică problemă tehnică. Poți repeta întrebarea?"}), 500

# --- NIVEL ADAPTIV: Sugestie capitol slab ---
@app.route('/api/suggest-weak', methods=['POST'])
def suggest_weak():
    data = request.json
    chapter_scores = data.get('chapterScores', {})
    if not chapter_scores:
        return jsonify({"suggestion": None})

    worst_id = None
    worst_ratio = 1.0
    for ch_id, scores in chapter_scores.items():
        total = scores.get('total', 0)
        correct = scores.get('correct', 0)
        if total >= 2:  # Minim 2 răspunsuri pentru a fi relevant
            ratio = correct / total
            if ratio < worst_ratio:
                worst_ratio = ratio
                worst_id = ch_id

    if worst_id and worst_ratio < 0.7:
        ch = next((c for c in CHAPTERS if c['id'] == worst_id), None)
        if ch:
            pct = int(worst_ratio * 100)
            return jsonify({
                "suggestion": {
                    "id": ch['id'],
                    "title": ch['title'],
                    "icon": ch.get('icon', '📖'),
                    "score": pct
                }
            })
    return jsonify({"suggestion": None})


# --- MOD COMPETIȚIE: 5 întrebări pentru 2 jucători ---
@app.route('/api/competition', methods=['GET'])
def get_competition():
    chapters_with_ex = [c for c in CHAPTERS if c.get('exercises')]
    if len(chapters_with_ex) < 5:
        selected = chapters_with_ex
    else:
        selected = random.sample(chapters_with_ex, 5)

    questions = []
    for ch in selected:
        ex = random.choice(ch['exercises'])
        questions.append({
            "chapterId": ch['id'],
            "chapterTitle": ch['title'],
            "question": ex['question'],
            "answer": ex['answer']
        })
    return jsonify({"questions": questions})


@app.route('/api/check', methods=['POST'])
def check_answer():
    data = request.json
    user_answer = data.get('userAnswer')
    correct_answer = data.get('correctAnswer')
    chapter_id = data.get('chapterId')

    is_correct = answers_match(user_answer, correct_answer)
    hint = ""
    if not is_correct:
        hint = build_wrong_answer_hint(chapter_id)

    feedback = "🎉 Excelent! Ai răspuns corect." if is_correct else f"Opa! Nu e chiar așa. {hint}<br>Răspunsul corect era: <strong>{correct_answer}</strong>"
    
    return jsonify({
        "isCorrect": is_correct,
        "feedback": feedback
    })


# --- API MULTIPLAYER (ONLINE) ---

@app.route('/api/multiplayer/create', methods=['POST'])
def mp_create():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 401
    
    # Generăm setul de 10 întrebări (din toate capitolele)
    chapters_with_ex = [c for c in CHAPTERS if c.get('exercises')]
    selected_chapters = random.sample(chapters_with_ex, min(10, len(chapters_with_ex)))
    questions = []
    for ch in selected_chapters:
        ex = random.choice(ch['exercises'])
        questions.append({
            "question": ex['question'],
            "answer": ex['answer'],
            "chapterTitle": ch['title']
        })

    import time
    initial_state = {
        "questions": questions,
        "currentQ": 0,
        "scores": [0, 0], 
        "roundStartTime": time.time(),
        "lastFeedback": "",
        "roundActive": True
    }
    
    import json
    code = database.create_multiplayer_session(user['id'], json.dumps(initial_state))
    return jsonify({'success': True, 'code': code})

@app.route('/api/multiplayer/join/<code>', methods=['POST'])
def mp_join(code):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 401
    
    success = database.join_multiplayer_session(user['id'], code)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Cod invalid sau cameră plină.'}), 400

@app.route('/api/multiplayer/status/<code>', methods=['GET'])
def mp_status(code):
    session = database.get_multiplayer_session(code)
    if not session:
        return jsonify({'success': False, 'error': 'Sesiune inexistentă.'}), 404
    
    import json
    import time
    state = json.loads(session['state_json'])
    
    # Check if timer expired (20 seconds)
    if session['status'] == 'playing' and state['roundActive']:
        elapsed = time.time() - state['roundStartTime']
        if elapsed > 20:
            state['lastFeedback'] = "⏰ Timpul a expirat pentru această rundă!"
            state['currentQ'] += 1
            state['roundStartTime'] = time.time() # Reset timer for next Q
            
            if state['currentQ'] >= len(state['questions']):
                database.update_multiplayer_state(code, json.dumps(state), status='finished')
            else:
                database.update_multiplayer_state(code, json.dumps(state))

    return jsonify({
        'success': True,
        'status': session['status'],
        'host_name': session['host_name'],
        'guest_name': session['guest_name'],
        'state': state,
        'server_time': time.time()
    })

@app.route('/api/multiplayer/action/<code>', methods=['POST'])
def mp_action(code):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    session = database.get_multiplayer_session(code)
    if not user or not session:
        return jsonify({'success': False}), 403

    import json
    import time
    data = request.json
    answer = data.get('answer', '').strip()
    
    state = json.loads(session['state_json'])
    
    # Verificăm dacă timpul a expirat deja între timp
    if time.time() - state['roundStartTime'] > 20:
        return jsonify({'success': True, 'timeout': True})

    curr_q = state['questions'][state['currentQ']]
    p_idx = 0 if user['id'] == session['host_id'] else 1
    
    is_correct = answers_match(answer, curr_q['answer'])
    
    if is_correct and state['roundActive']:
        state['scores'][p_idx] += 10
        state['currentQ'] += 1
        state['roundStartTime'] = time.time() # Reset timer for next Q
        state['lastFeedback'] = f"🎉 {user['username']} a răspuns corect!"
        
        if state['currentQ'] >= len(state['questions']):
            database.update_multiplayer_state(code, json.dumps(state), status='finished')
        else:
            database.update_multiplayer_state(code, json.dumps(state))
        
        return jsonify({'success': True, 'isCorrect': True})
    
    return jsonify({'success': True, 'isCorrect': False})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
