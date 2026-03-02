from flask import Flask, request, jsonify, send_from_directory
import json
import os
import random
import re
import ast
import operator
import uuid
import time
from difflib import SequenceMatcher
from werkzeug.utils import secure_filename
import database

app = Flask(__name__, static_folder='.')
database.init_db()

if os.environ.get('VERCEL'):
    UPLOAD_DIR = os.path.join('/tmp', 'uploads')
else:
    UPLOAD_DIR = os.path.join('data', 'uploads')
ALLOWED_UPLOAD_EXTENSIONS = {'.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.webp', '.gif'}
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        "aprofundeaza", "dezvolta", "elaboreaza", "dezvolta ideea",
        "explica mai amplu", "explica mai pe larg", "mai multe detalii"
    ],
    "example": [
        "exemplu", "da-mi un exemplu", "poti sa-mi dai un exemplu",
        "pune un exemplu", "poti sa exemplifici", "arata-mi",
        "un caz", "sa vad", "demonstreaza", "cum se face", "cum se rezolva",
        "model", "rezolvare", "cum se calculeaza", "arata un model",
        "da-mi un model", "cum fac", "cum rezolv", "pas cu pas",
        "exemplificare", "un exemplu concret", "da un exemplu"
    ],
    "exercise": [
        "exercitiu", "da-mi ceva de rezolvat", "vreau sa exersez", "provocare",
        "vreau sa lucrez", "da-mi o problema", "test rapid", "antrenament",
        "problema", "da-mi de lucru", "pune-mi ceva", "vreau exercitii",
        "da-mi de rezolvat", "lucru", "practica", "exersam",
        "vreau practica", "probleme de antrenament"
    ],
    "define": [
        "ce inseamna", "ce este", "ce sunt", "defineste", "spune-mi despre",
        "ce reprezinta", "explicatia pentru", "care e definitia", "cine e",
        "cine sunt", "cum se defineste", "definitia", "ce se intelege prin",
        "explica", "explicati", "explica-mi", "care este", "care e", "cum e",
        "la ce se refera", "ce-i ala", "ce-i aia", "ce inseamna asta",
        "ce e ala", "ce e aia", "ce-i", "ce e", "despre ce e vorba",
        "ce presupune", "la ce ajuta", "ce reprezinta concret",
        "definitie simpla", "definitie pe inteles", "adica",
        "care-i", "care i", "cum adica", "ce vrea sa zica"
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
        "ce poti", "cum te folosesc", "ce pot intreba", "cum te pot folosi",
        "cum te folosim", "ce stii", "ce intrebari pot pune"
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
        "esential", "concluzie", "rezumat pe scurt", "explica pe scurt",
        "scurt si clar", "foarte pe scurt"
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
FILLER_TERMS = {
    "te", "rog", "pls", "please", "gen", "adica", "deci", "na", "chestia", "chestie",
    "asta", "aia", "acela", "aceea", "acel", "aceasta", "alea", "de", "din", "despre",
    "la", "cu", "si", "sau", "in", "pe", "ce", "cum", "care", "cat", "este", "sunt"
}

PHRASE_NORMALIZATION = {
    "poti sa imi explici": "explica",
    "poti sa mi explici": "explica",
    "poti sa-mi explici": "explica",
    "imi poti explica": "explica",
    "mi poti explica": "explica",
    "poti explica": "explica",
    "descrie mi": "descrie",
    "descrie-mi": "descrie",
    "explica mi": "explica",
    "explica-mi": "explica",
    "detaliaza mi": "detaliaza",
    "detaliaza-mi": "detaliaza",
    "da mi": "da",
    "da-mi": "da",
    "arata mi": "arata",
    "arata-mi": "arata",
    "pas cu pas": "pas_cu_pas"
}

TYPO_CORRECTIONS = {
    "meda": "media",
    "aritmetie": "aritmetica",
    "regurile": "regulile",
    "regulaile": "regulile",
    "divizibilitste": "divizibilitate",
    "divizibiltate": "divizibilitate"
}

SEMANTIC_SYNONYMS = {
    "explica": ["descrie", "detaliaza", "clarifica", "lamureste", "explicati", "explicatie", "explicatii", "descriemi", "explicami", "amanunteste"],
    "detaliaza": ["aprofundeaza", "dezvolta", "elaboreaza", "amanunte", "detalii", "pe_larg"],
    "exemplu": ["model", "caz", "instanta", "exemplificare", "demonstratie"],
    "exercitiu": ["problema", "antrenament", "practica", "tema", "aplicatie"],
    "definitie": ["sens", "inteles", "semnificatie", "ce_inseamna", "explicatie"],
    "rezumat": ["sumar", "pe_scurt", "esential", "concluzie", "sinteza"],
    "quiz": ["intrebare", "testare", "verificare", "chestionare"],
    "urmator": ["next", "mai_departe", "urmatoare"],
    "ajutor": ["help", "ghid", "instructiuni", "cum_folosesc"],
    "compara": ["comparatie", "ordonare", "mai_mic", "mai_mare"]
}

CANONICAL_BY_VARIANT = {}
CANONICAL_VARIANTS = {}
for canonical, variants in SEMANTIC_SYNONYMS.items():
    norm_c = canonical
    pool = {norm_c}
    for variant in variants:
        norm_v = variant
        pool.add(norm_v)
        CANONICAL_BY_VARIANT[norm_v] = norm_c
    CANONICAL_BY_VARIANT[norm_c] = norm_c
    CANONICAL_VARIANTS[norm_c] = pool

CHAPTER_GENERAL_DEFINITIONS = {
    "intro_scriere_citire": "Numerele naturale sunt numerele folosite pentru a exprima cantități și pentru a număra obiecte: 0, 1, 2, 3, 4, … Ele se scriu folosind cifrele de la 0 la 9 și se organizează pe ordine și clase (unități, zeci, sute, mii, milioane etc.). Citirea numerelor naturale presupune identificarea valorii fiecărei cifre în funcție de poziția sa în număr.",
    "sir_axa_naturale": "Șirul numerelor naturale reprezintă succesiunea lor în ordine crescătoare, fiecare număr având un succesor (numărul următor). Axa numerelor este o reprezentare grafică a acestui șir pe o dreaptă, unde numerele sunt plasate la distanțe egale, crescând de la stânga la dreapta.",
    "comparare_ordonare": "Compararea numerelor naturale înseamnă stabilirea relației dintre două numere folosind semnele < (mai mic), > (mai mare) sau = (egal). Ordonarea numerelor presupune așezarea lor în ordine crescătoare sau descrescătoare, analizând mai întâi numărul de cifre și apoi valorile pe ordine.",
    "aproximari_rotunjiri": "Aproximarea unui număr înseamnă înlocuirea lui cu un număr apropiat pentru a simplifica calculele. Rotunjirea se face la un anumit ordin (zeci, sute, mii etc.), după regula: dacă cifra următoare este 5 sau mai mare, rotunjim în sus; dacă este mai mică de 5, rotunjim în jos.",
    "adunarea_naturale": "Adunarea este operația matematică prin care reunim două sau mai multe cantități pentru a afla totalul. Numerele care se adună se numesc termeni, iar rezultatul se numește sumă. Adunarea respectă proprietăți precum comutativitatea și asociativitatea.",
    "scaderea_naturale": "Scăderea este operația prin care determinăm diferența dintre două numere. Primul număr se numește descăzut, al doilea scăzător, iar rezultatul diferență. Scăderea este operația inversă adunării.",
    "inmultirea_naturale": "Înmulțirea reprezintă adunarea repetată a aceluiași număr. Numerele care se înmulțesc se numesc factori, iar rezultatul produs. Înmulțirea respectă proprietăți precum comutativitatea, asociativitatea și distributivitatea față de adunare.",
    "impartirea_naturale": "Împărțirea este operația prin care un număr (deîmpărțitul) se împarte în părți egale după un alt număr (împărțitorul). Rezultatul se numește cât, iar uneori poate exista și un rest. Împărțirea este operația inversă înmulțirii.",
    "factorul_comun": "Factorul comun este un număr sau o expresie care apare în mai mulți termeni ai unui calcul și poate fi scos în fața parantezei pentru a simplifica expresia. Această metodă se numește scoaterea factorului comun.",
    "puteri_naturale": "Ridicarea la putere înseamnă înmulțirea repetată a unui număr cu el însuși. Numărul care se înmulțește se numește bază, iar de câte ori se înmulțește se numește exponent.",
    "reguli_calcul_puteri": "Regulile de calcul cu puteri permit simplificarea operațiilor. De exemplu, la înmulțirea puterilor cu aceeași bază se adună exponenții, iar la împărțire se scad exponenții.",
    "compararea_puterilor": "Compararea puterilor presupune stabilirea relației dintre două expresii de forma a^n. Se pot compara bazele sau exponenții, folosind proprietățile puterilor.",
    "ordine_operatii": "Într-un calcul cu mai multe operații, se respectă o ordine: paranteze, puteri, înmulțiri și împărțiri, adunări și scăderi. Respectarea acestei ordini asigură obținerea rezultatului corect.",
    "baze_aritmetica": "O bază de numerație este un sistem de scriere a numerelor folosind un anumit set de cifre. De exemplu, baza 10 folosește cifrele 0–9, iar baza 2 folosește doar 0 și 1. Fiecare cifră are o valoare în funcție de poziția sa.",
    "media_aritmetica": "Media aritmetică este o măsură a tendinței centrale. Se calculează adunând toate valorile și împărțind suma la numărul total de valori. Ea indică valoarea medie a unui set de date.",
    "metode_aritmetice_1": "Metoda reducerii la unitate constă în aflarea valorii unei singure unități pornind de la o valoare totală, apoi determinarea valorii cerute prin înmulțire.",
    "metode_aritmetice_2": "Metoda comparației se folosește pentru rezolvarea problemelor prin stabilirea relațiilor dintre mărimi, comparând datele oferite pentru a determina necunoscuta.",
    "metode_aritmetice_3": "Metoda mersului invers presupune rezolvarea problemei pornind de la rezultat și efectuând operațiile în ordine inversă pentru a ajunge la datele inițiale.",
    "metode_aritmetice_4": "Metoda falsei ipoteze constă în presupunerea unei valori pentru necunoscută, verificarea rezultatului și corectarea presupunerii în funcție de diferența obținută.",
    "divizibilitate": "Un număr este divizibil cu altul dacă împărțirea se face fără rest. Divizibilitatea ajută la simplificarea fracțiilor și la descompunerea numerelor.",
    "criterii_divizibilitate": "Criteriile de divizibilitate sunt reguli care permit verificarea rapidă a divizibilității fără a efectua împărțirea. De exemplu, un număr este divizibil cu 2 dacă ultima cifră este pară.",
    "numere_prime_compuse": "Un număr prim este un număr natural mai mare decât 1 care are exact doi divizori: 1 și el însuși. Un număr compus are mai mult de doi divizori și poate fi descompus în factori primi.",
    "fractii_ordinare": "Fracțiile ordinare reprezintă părți egale dintr-un întreg. Ele sunt formate din numărător (partea de sus) și numitor (partea de jos), care arată în câte părți egale este împărțit întregul.",
    "fractii_zecimale": "Fracțiile zecimale sunt numere scrise cu virgulă și reprezintă împărțiri la puteri ale lui 10 (10, 100, 1000 etc.). Ele pot fi finite sau periodice."
}

def normalize(text):
    if not text: return ""
    text = text.lower()
    replacements = {'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't', 'ş': 's', 'ţ': 't'}
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = re.sub(r"[?.,!;:\-_/()\[\]{}\"'`]", ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    for src, dst in PHRASE_NORMALIZATION.items():
        text = text.replace(src, dst)
    return re.sub(r'\s+', ' ', text).strip()

def tokenize(text):
    norm = normalize(text)
    if not norm:
        return []
    tokens = [TYPO_CORRECTIONS.get(tok, tok) for tok in norm.split() if tok]
    return [CANONICAL_BY_VARIANT.get(tok, tok) for tok in tokens]

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
        variants = set(concept_variants(word))
        canonical = CANONICAL_BY_VARIANT.get(word)
        if canonical:
            variants.update(concept_variants(canonical))
            variants.update(CANONICAL_VARIANTS.get(canonical, set()))

        for variant in list(variants):
            canonical_of_variant = CANONICAL_BY_VARIANT.get(variant)
            if canonical_of_variant:
                variants.add(canonical_of_variant)
                variants.update(CANONICAL_VARIANTS.get(canonical_of_variant, set()))

        expanded.extend(v for v in variants if v)
    # deduplicate păstrând ordinea
    result = []
    for word in expanded:
        if word not in result:
            result.append(word)
    return result

def significant_terms(query, min_len=3):
    words = [w for w in expand_query_words(query) if len(w) >= min_len]
    return [w for w in words if w not in FILLER_TERMS]

def _fuzzy_similar(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def score_intent(input_text, intent_type):
    norm_input = normalize(input_text)
    if not norm_input:
        return 0.0

    tokens = expand_query_words(norm_input)
    if not tokens:
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
            syn_variants = concept_variants(syn_tokens[0])
            if any(
                (_fuzzy_similar(variant, tok) >= 0.84) or partial_match(variant, tok)
                for variant in syn_variants for tok in tokens
            ):
                score += 1.0
        else:
            overlap = 0
            for syn_tok in syn_tokens:
                syn_tok_variants = concept_variants(syn_tok)
                if any(
                    (variant in tokens) or any(_fuzzy_similar(variant, tok) >= 0.9 for tok in tokens)
                    for variant in syn_tok_variants
                ):
                    overlap += 1

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
    if not ranked or ranked[0][1] < 1.6:
        return None

    if len(ranked) > 1:
        top_score = ranked[0][1]
        second_score = ranked[1][1]
        # Dacă două intenții sunt foarte apropiate, evităm să alegem greșit.
        if (top_score - second_score) < 0.22 and top_score < 2.6:
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

def _allowed_file(filename):
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_UPLOAD_EXTENSIONS

def _save_uploaded_file(file_storage):
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or not _allowed_file(filename):
        return None

    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(UPLOAD_DIR, unique_name)
    file_storage.save(full_path)
    return f"/api/uploads/{unique_name}"

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
    if best[1] >= 7:
        return best[0]
    return None

def rank_chapters(query):
    """Returnează capitole candidate cu scor pentru dezambiguizare."""
    norm_q = normalize(query)
    words = [w for w in expand_query_words(norm_q) if len(w) >= 3]
    if not words:
        return []

    stopwords = {"ce", "care", "este", "sunt", "pentru", "din", "lui", "unde", "cum", "cand", "mai", "imi",
                 "poti", "vreau", "spune", "despre", "arata", "zici", "asta", "aia", "cele", "te", "rog"}
    content_words = [w for w in words if w not in stopwords]
    if not content_words:
        content_words = words

    ranked = []
    for ch in CHAPTERS:
        score = 0
        title_norm = normalize(ch.get('title', ''))
        title_words = title_norm.split()

        for w in content_words:
            if w in title_norm:
                score += 15
            elif any(partial_match(w, tw) for tw in title_words):
                score += 10

        for kw in ch.get('keywords', []):
            kw_norm = normalize(kw)
            for w in content_words:
                if w == kw_norm:
                    score += 12
                elif partial_match(w, kw_norm):
                    score += 8

        dictionary = ch.get('dictionary', {})
        for term in dictionary:
            term_norm = normalize(term)
            for w in content_words:
                if w == term_norm or partial_match(w, term_norm):
                    score += 7

        if score > 0:
            ranked.append((ch, score))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked

def is_explicit_chapter_reference(ch, query):
    if not ch:
        return False
    norm_q = normalize(query)
    if not norm_q:
        return False

    title_norm = normalize(ch.get('title', ''))
    if title_norm and title_norm in norm_q:
        return True

    for kw in ch.get('keywords', []):
        kw_norm = normalize(kw)
        if kw_norm and kw_norm in norm_q:
            return True
    return False

def is_next_request(query):
    norm_q = normalize(query)
    markers = [
        "urmatorul", "capitolul urmator", "urmatorul capitol", "treci la urmatorul",
        "next", "mergem la urmatorul", "du ma la urmatorul"
    ]
    return any(marker in norm_q for marker in markers)

def is_continue_current_request(query):
    norm_q = normalize(query)
    markers = [
        "continua", "continua te rog", "continua aici", "continua la asta",
        "mergi mai departe aici", "mai multe aici"
    ]
    return any(marker in norm_q for marker in markers)

def is_short_affirmative(query):
    norm_q = normalize(query)
    if not norm_q:
        return False
    affirmatives = {
        "da", "da te rog", "da please", "ok", "oke", "bine", "sigur", "desigur", "mhm", "yes"
    }
    if norm_q in affirmatives:
        return True
    tokens = norm_q.split()
    return len(tokens) <= 2 and any(tok in {"da", "ok", "bine", "sigur", "yes"} for tok in tokens)

def extract_rules_section(ch):
    if not ch:
        return None

    lessons = ch.get('lessons', [])
    if not lessons:
        return None

    picked = []
    seen = set()

    def _append_line(line):
        key = (line or "").strip()
        if key and key not in seen:
            seen.add(key)
            picked.append(key)

    for idx, lesson in enumerate(lessons):
        lesson_norm = normalize(lesson)
        is_rule_header = (
            "regula" in lesson_norm
            or lesson.strip().startswith("📌 REGULA")
        )
        is_strategy = "strategii" in lesson_norm

        if is_rule_header:
            _append_line(lesson)

            # Dacă formula este pe linia următoare, o includem automat.
            if idx + 1 < len(lessons):
                next_line = (lessons[idx + 1] or "").strip()
                next_norm = normalize(next_line)
                looks_like_formula = (
                    "=" in next_line
                    or "^" in next_line
                    or "ᵐ" in next_line
                    or "ⁿ" in next_line
                    or "exponent" in next_norm
                )
                if next_line and looks_like_formula and "regula" not in next_norm:
                    _append_line(next_line)

        elif is_strategy:
            _append_line(lesson)

    if not picked:
        return None

    return "📚 <strong>Din secvența lecției:</strong><br>" + "<br>".join(picked)

SECTION_QUERY_MAP = {
    "reguli": {
        "query_terms": ["regula", "reguli", "regulile"],
        "lesson_markers": ["regula", "📌 regula", "strategii"]
    },
    "criterii": {
        "query_terms": ["criteriu", "criterii", "criteriile"],
        "lesson_markers": ["criteriu", "criterii", "test de divizibilitate"]
    },
    "formule": {
        "query_terms": ["formula", "formule", "formula de calcul"],
        "lesson_markers": ["formula", "formule", "="]
    },
    "proprietati": {
        "query_terms": ["proprietate", "proprietati", "proprietatile"],
        "lesson_markers": ["proprietate", "proprietati"]
    },
    "pasi": {
        "query_terms": ["pas", "pasi", "pasii", "metoda", "procedura"],
        "lesson_markers": ["pas", "metoda", "procedura", "algoritm"]
    },
    "definitii": {
        "query_terms": ["definitie", "definitii", "ce inseamna", "ce este"],
        "lesson_markers": ["definitie", "se numeste", "inseamna"]
    }
}

def _matches_query_term(term, query_terms):
    for q in query_terms:
        if term == q:
            return True
        if partial_match(term, q) or partial_match(q, term):
            return True
        if _fuzzy_similar(term, q) >= 0.84:
            return True
    return False

def detect_requested_section(query):
    terms = significant_terms(query)
    if not terms:
        return None

    scores = []
    for section_name, config in SECTION_QUERY_MAP.items():
        query_terms = [normalize(t) for t in config["query_terms"]]
        score = 0
        for term in terms:
            if _matches_query_term(term, query_terms):
                score += 1
        if score > 0:
            scores.append((section_name, score))

    if not scores:
        return None
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[0][0]

def is_general_definition_query(query):
    norm_q = normalize(query)
    if not norm_q:
        return False

    generic_markers = [
        "ce este", "ce sunt", "care e definitia", "care este definitia",
        "definitia generala", "definitia capitolului"
    ]
    if not any(marker in norm_q for marker in generic_markers):
        return False

    # Dacă utilizatorul cere o secțiune specifică, NU e definiție generală.
    if detect_requested_section(query) is not None:
        return False

    if is_rules_query(query):
        return False

    # Întrebări de tip „cu 5 / cu 3 / regula X” sunt specifice.
    if re.search(r"\bcu\s+\d+\b", norm_q) or re.search(r"\b\d+\b", norm_q):
        return False

    # Când se cere "pentru n numere" / "pentru 2 numere" este cerință specifică, nu definiție generală.
    if "pentru" in norm_q and ("numere" in norm_q or re.search(r"\bn\b", norm_q) is not None):
        return False

    terms = set(significant_terms(query))
    specific_terms = {
        "criteriu", "criterii", "regula", "reguli", "formula", "formule",
        "proprietate", "proprietati", "pas", "pasi"
    }
    if any(term in specific_terms for term in terms):
        return False

    return True

def extract_section_block(ch, section_name, filter_words=None):
    if not ch or section_name not in SECTION_QUERY_MAP:
        return None

    lessons = ch.get('lessons', [])
    if not lessons:
        return None

    markers = [normalize(m) for m in SECTION_QUERY_MAP[section_name]["lesson_markers"]]
    picked = []
    seen = set()

    # Pre-climatizare filter_words
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
            # Dacă avem filter_words, verificăm dacă linia sau contextul imediat conține unul din ele.
            # Exemplu: dacă userul cere "criteriu cu 5", linia trebuie să conțină "5".
            if norm_filters:
                # Verificăm hit direct pe line
                hit_filter = any(fw in lesson_norm for fw in norm_filters)
                if not hit_filter:
                    # Verificăm și linia următoare doar dacă linia curentă pare a fi un titlu/header (ex: se termină în ":")
                    if lesson.strip().endswith(":") and idx + 1 < len(lessons):
                        next_norm = normalize(lessons[idx + 1])
                        if any(fw in next_norm for fw in norm_filters):
                            hit_filter = True
                
                if not hit_filter:
                    continue

            _append(lesson)

            # Include formula/continuation line right after section line when relevant.
            if idx + 1 < len(lessons):
                next_line = (lessons[idx + 1] or "").strip()
                next_norm = normalize(next_line)
                looks_like_formula_or_detail = (
                    "=" in next_line
                    or "^" in next_line
                    or "ᵐ" in next_line
                    or "ⁿ" in next_line
                    or "exponent" in next_norm
                    or any(marker in next_norm for marker in markers)
                )
                if next_line and looks_like_formula_or_detail:
                    _append(next_line)

            # Evită linii-header goale de tip "📌 CRITERIUL ...:" fără detaliul imediat.
            if section_name in {"criterii", "reguli"}:
                if lesson.strip().startswith("📌") and lesson.strip().endswith(":"):
                    if idx + 1 < len(lessons):
                        next_norm = normalize(lessons[idx + 1])
                        if next_norm.strip().startswith("📌"):
                            if lesson in picked:
                                picked.remove(lesson)
                                seen.discard(lesson)

    if not picked:
        return None

    title = section_name.capitalize()
    return f"📚 <strong>Din secvența lecției ({title}):</strong><br>" + "<br>".join(picked)

def extract_number_targeted_section(ch, section_name, number_value):
    if not ch or section_name not in SECTION_QUERY_MAP:
        return None

    lessons = ch.get('lessons', [])
    if not lessons:
        return None

    markers = [normalize(m) for m in SECTION_QUERY_MAP[section_name]["lesson_markers"]]
    number_str = str(number_value)

    # Pattern-uri stricte, ca să evităm includerea tuturor criteriilor/regulilor.
    if section_name == "criterii":
        patterns = [f"criteriul cu {number_str}", f"divizibilitatii cu {number_str}", f"cu {number_str}:"]
    elif section_name == "reguli":
        patterns = [f"regula {number_str}", f"regula {number_str}:"]
    else:
        patterns = [f" {number_str}"]

    picked = []
    seen = set()

    def _append(txt):
        line = (txt or "").strip()
        if line and line not in seen:
            seen.add(line)
            picked.append(line)

    for idx, lesson in enumerate(lessons):
        lesson_norm = normalize(lesson)
        marker_hit = any(marker in lesson_norm for marker in markers)
        pattern_hit = any(pattern in lesson_norm for pattern in patterns)

        if marker_hit and pattern_hit:
            lesson_txt = (lesson or "").strip()
            is_header_line = lesson_txt.startswith("📌") and lesson_txt.endswith(":")

            if not is_header_line:
                _append(lesson)

            if idx + 1 < len(lessons):
                next_line = (lessons[idx + 1] or "").strip()
                next_norm = normalize(next_line)
                next_is_header = next_line.startswith("📌")
                next_matches_same_number = any(pattern in next_norm for pattern in patterns)
                next_is_other_short_criterion = False
                next_number_match = re.match(r"^criteriul\s+cu\s+(\d+)\b", next_norm, flags=re.IGNORECASE)
                if next_number_match and next_number_match.group(1) != number_str:
                    next_is_other_short_criterion = True

                next_is_other_header_criterion = False
                next_header_match = re.search(r"divizibilitatii\s+cu\s+(\d+)", next_norm)
                if next_header_match and next_header_match.group(1) != number_str:
                    next_is_other_header_criterion = True

                looks_like_detail = (
                    "=" in next_line
                    or "^" in next_line
                    or "ᵐ" in next_line
                    or "ⁿ" in next_line
                    or "ultima" in next_norm
                    or "suma" in next_norm
                    or "divizibil" in next_norm
                )

                # Păstrăm doar detalii pentru același criteriu, fără a prelua header-ul altui criteriu.
                if (
                    next_line
                    and not next_is_header
                    and not next_is_other_short_criterion
                    and not next_is_other_header_criterion
                    and (next_matches_same_number or looks_like_detail)
                ):
                    _append(next_line)

                # Dacă linia curentă este header pentru numărul cerut, următoarea linie utilă e detaliul.
                if is_header_line and idx + 1 < len(lessons):
                    detail_line = (lessons[idx + 1] or "").strip()
                    detail_norm = normalize(detail_line)
                    detail_is_header = detail_line.startswith("📌")
                    detail_looks_like_rule = (
                        "ultima" in detail_norm
                        or "suma" in detail_norm
                        or "divizibil" in detail_norm
                        or "cifre" in detail_norm
                        or "=" in detail_line
                    )
                    if detail_line and not detail_is_header and detail_looks_like_rule:
                        _append(detail_line)
            break

    if not picked:
        return None

    title = section_name.capitalize()
    return f"📚 <strong>Din secvența lecției ({title}):</strong><br>" + "<br>".join(picked)

def build_divisibility_criteria_guide(ch):
    """Răspuns structurat pentru capitolul de criterii de divizibilitate."""
    if not ch:
        return None

    chapter_id = ch.get('id')
    title = ch.get('title', '')
    title_norm = normalize(title)
    if chapter_id != "criterii_divizibilitate" and "criterii" not in title_norm:
        return None

    lessons = ch.get('lessons', [])
    if not lessons:
        return None

    criteria_details = {}

    # Linii scurte de tip: "Criteriul cu 2: ..."
    for line in lessons:
        line_txt = (line or "").strip()
        m = re.match(r"^Criteriul\s+cu\s+(\d+)\s*:\s*(.+)$", line_txt, flags=re.IGNORECASE)
        if m:
            number = m.group(1)
            rule = m.group(2).strip().rstrip('.')
            criteria_details.setdefault(number, {})
            criteria_details[number]["short_rule"] = rule

    # Blocuri detaliate de tip: "📌 CRITERIUL DIVIZIBILITĂȚII CU 5:" + linia următoare
    for idx, line in enumerate(lessons):
        line_norm = normalize(line)
        m = re.search(r"divizibilitatii\s+cu\s+(\d+)", line_norm)
        if not m:
            continue

        number = m.group(1)
        detail = ""
        if idx + 1 < len(lessons):
            detail = (lessons[idx + 1] or "").strip().rstrip('.')

        if detail:
            criteria_details.setdefault(number, {})
            criteria_details[number]["detail_rule"] = detail

    if not criteria_details:
        return None

    def how_to_apply(number):
        if number in {"2", "5", "10"}:
            return "Te uiți la ultima cifră și verifici regula."
        if number in {"4", "25"}:
            return "Te uiți la ultimele două cifre și verifici regula."
        if number in {"3", "9"}:
            return f"Aduni cifrele numărului, apoi verifici dacă suma este divizibilă cu {number}."
        return "Aplici regula criteriului direct pe cifrele relevante."

    sorted_numbers = sorted(criteria_details.keys(), key=lambda x: int(x))
    lines = []
    for number in sorted_numbers:
        info = criteria_details[number]
        rule = info.get("detail_rule") or info.get("short_rule")
        if not rule:
            continue

        lines.append(
            f"• <strong>Cu {number}</strong><br>"
            f"&nbsp;&nbsp;Definiție / regulă: {rule}.<br>"
            f"&nbsp;&nbsp;Cum se face: {how_to_apply(number)}"
        )

    if not lines:
        return None

    return (
        f"📏 <strong>{title}</strong><br><br>"
        "<strong>Definiție:</strong> Criteriile de divizibilitate sunt reguli rapide prin care verifici dacă un număr se împarte exact la altul, fără împărțire scrisă.<br><br>"
        "<strong>Formule / reguli la fiecare criteriu:</strong><br>"
        + "<br>".join(lines)
    )

def extract_chapter_focus_options(ch, limit=4):
    """Construiește sugestii scurte de subiecte din capitol pentru clarificare."""
    if not ch:
        return []

    options = []
    seen = set()

    for term in ch.get('dictionary', {}).keys():
        t = (term or '').strip()
        if t and t not in seen:
            seen.add(t)
            options.append(t)
        if len(options) >= limit:
            return options

    for lesson in ch.get('lessons', []):
        text = (lesson or '').strip()
        if not text:
            continue

        if text.startswith('📌'):
            candidate = text.replace('📌', '').strip()
        elif ':' in text:
            candidate = text.split(':', 1)[0].strip()
        else:
            continue

        candidate = re.sub(r'\s+', ' ', candidate)
        if 3 <= len(candidate) <= 70 and candidate not in seen:
            seen.add(candidate)
            options.append(candidate)
        if len(options) >= limit:
            break

    return options[:limit]

def is_rules_query(query):
    terms = significant_terms(query)
    for term in terms:
        if term in {"regula", "reguli", "regulile"}:
            return True
        if partial_match(term, "reguli") or partial_match(term, "regula"):
            return True
        if _fuzzy_similar(term, "reguli") >= 0.82 or _fuzzy_similar(term, "regula") >= 0.82:
            return True
    return False

def find_explicit_chapter_in_query(query):
    """Detectează dacă userul a menționat explicit un capitol/subiect în întrebare."""
    norm_q = normalize(query)
    if not norm_q:
        return None

    terms = set(significant_terms(query))
    generic_chapter_keywords = {
        "numere", "numar", "numarul", "metoda", "operatii", "calcul", "problema", "termen"
    }
    best = None
    best_score = 0

    for ch in CHAPTERS:
        score = 0
        title_norm = normalize(ch.get('title', ''))
        if title_norm and title_norm in norm_q:
            score += 8

        for kw in ch.get('keywords', []):
            kw_norm = normalize(kw)
            if not kw_norm:
                continue

            if kw_norm in generic_chapter_keywords or len(kw_norm) < 4:
                continue

            if kw_norm in norm_q:
                score += 5
            elif any(partial_match(term, kw_norm) for term in terms):
                score += 2

        if score > best_score:
            best_score = score
            best = ch

    if best_score >= 8:
        return best
    return None

def get_targeted_snippet(ch, query):
    """Răspuns scurt pe subiectul întrebat, fără recapitulare completă."""
    if not ch:
        return None

    content_words = significant_terms(query)
    if not content_words:
        return None

    norm_q = normalize(query)

    # Tratament specific pentru capitolul de media aritmetică.
    if ch.get('id') == 'media_aritmetica':
        if "n numere" in norm_q or "pentru n" in norm_q:
            return "📌 <strong>15. Media Aritmetică</strong><br><br>Pentru n numere: ma = (Suma elementelor) : n."
        if re.search(r"\b2\s+numere\b", norm_q):
            return "📌 <strong>15. Media Aritmetică</strong><br><br>Pentru 2 numere: ma = (a + b) : 2."

    section_requested = detect_requested_section(query)
    if section_requested:
        # Extragem numerele din query (ex: "criteriu cu 5").
        filters = re.findall(r"\d+", normalize(query))
        if filters:
            for number_value in filters:
                exact_block = extract_number_targeted_section(ch, section_requested, number_value)
                if exact_block:
                    return exact_block

            if section_requested == "criterii":
                return (
                    f"În capitolul <strong>{ch['title']}</strong> nu am criteriu standard pentru <strong>{filters[0]}</strong>."
                )

        if section_requested == "criterii" and not filters:
            criteria_guide = build_divisibility_criteria_guide(ch)
            if criteria_guide:
                return criteria_guide

        section_block = extract_section_block(ch, section_requested, filter_words=filters)
        if section_block:
            return section_block
        # Fallback dacă filtrarea e prea strictă, dăm tot blocul
        section_block_fallback = extract_section_block(ch, section_requested)
        if section_block_fallback:
            return section_block_fallback

    if any(partial_match(w, "criterii") or partial_match(w, "criteriu") for w in content_words):
        title_norm = normalize(ch.get('title', ''))
        if "puteri" in title_norm:
            candidates = get_top_matches("criterii de divizibilitate", count=2)
            if candidates:
                suggestions_html = "<br>".join([f"• <strong>{c['title']}</strong>" for c in candidates])
                return (
                    "În capitolul de <strong>puteri</strong> avem <strong>reguli de calcul</strong>, nu criterii.<br><br>"
                    "Pentru criterii, mergi la:<br>"
                    f"{suggestions_html}"
                )
            return "În capitolul de <strong>puteri</strong> avem reguli de calcul, nu criterii. Criteriile sunt la divizibilitate."

    if is_rules_query(query):
        rules_block = extract_rules_section(ch)
        if rules_block:
            return rules_block

    dictionary = ch.get('dictionary', {})
    for term, definition in dictionary.items():
        term_norm = normalize(term)
        if any(w == term_norm or partial_match(w, term_norm) for w in content_words):
            return f"📌 <strong>{ch['title']}</strong><br><br><strong>{term}</strong>: {definition}<br><br>Scrie <em>detaliază</em> dacă vrei mai mult."

    lessons = ch.get('lessons', [])
    best_lesson = None
    best_hits = 0
    lessons_with_hit = 0
    for lesson in lessons:
        lesson_norm = normalize(lesson)
        hits = sum(1 for w in content_words if w in lesson_norm)
        if hits > 0:
            lessons_with_hit += 1
        if hits > best_hits:
            best_hits = hits
            best_lesson = lesson

    # Dacă întrebarea e prea vagă și atinge multe lecții la fel de slab, cerem clarificare.
    if best_hits == 1 and lessons_with_hit >= 4 and len(content_words) <= 2:
        options = extract_chapter_focus_options(ch, limit=4)
        if options:
            options_html = "<br>".join([f"• <strong>{opt}</strong>" for opt in options])
            return (
                f"Sunt în <strong>{ch['title']}</strong>, dar întrebarea e prea generală.<br><br>"
                f"Alege exact subiectul:<br>{options_html}"
            )
        return f"Sunt în <strong>{ch['title']}</strong>, dar întrebarea e prea generală. Spune exact noțiunea din capitol."

    if best_lesson and best_hits >= 1:
        return f"📌 <strong>{ch['title']}</strong><br><br>{best_lesson}<br><br>Vrei și un exemplu rapid?"
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

    # 4. Returnează prima lecție relevantă
    for lesson in lessons:
        if any(w in normalize(lesson) for w in words):
            return lesson

    return ""

def get_chapter_general_definition(ch):
    """Returnează definiția generală a capitolului (fără detalii suplimentare)."""
    if not ch:
        return ""

    chapter_id = ch.get('id')
    if chapter_id in CHAPTER_GENERAL_DEFINITIONS:
        return CHAPTER_GENERAL_DEFINITIONS[chapter_id]

    lessons = ch.get('lessons', [])
    if not lessons:
        return ""

    # Prioritate: o linie explicită de tip definiție.
    for lesson in lessons:
        lesson_norm = normalize(lesson)
        if lesson_norm.startswith("definitie") or " definitie:" in lesson_norm or " se numeste " in f" {lesson_norm} ":
            return lesson.strip()

    # Fallback: prima idee din capitol (de obicei introducerea/definiția generală).
    return lessons[0].strip()

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

    if best_score >= 10:
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
    if level == 'simple':
        if definition:
            msg += f"<strong>Ideea-cheie:</strong> {definition}<br><br>"
        elif lessons:
            msg += f"<strong>Ideea-cheie:</strong> {lessons[0]}<br><br>"

        if examples:
            msg += f"<strong>Exemplu scurt:</strong> <em>{examples[0]}</em><br><br>"

        msg += "Dacă vrei, continui cu detalii, pași sau exerciții."
        return msg

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
        ("Ziua 7", "Recapitulare + consolidare"),
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
    if path.startswith('uploads/'):
        filename = path[len('uploads/'):]
        return send_from_directory(UPLOAD_DIR, filename)
    return send_from_directory('.', path)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/api/uploads/<path:filename>')
def serve_upload_api(filename):
    return send_from_directory(UPLOAD_DIR, filename)

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
    try:
        token = request.headers.get('Authorization')
        user = database.get_user_by_token(token)
        if not user or user['role'] != 'teacher':
            return jsonify({'success': False, 'error': 'Neautorizat.'}), 403

        chapter_id = request.form.get('chapterId') or None
        description = request.form.get('description') or None
        due_date = request.form.get('dueDate') or None
        uploaded = request.files.get('file')
        file_path = _save_uploaded_file(uploaded)

        if uploaded and not file_path:
            return jsonify({'success': False, 'error': 'Tipul fișierului nu este permis.'}), 400

        if not user.get('class_code'):
            return jsonify({'success': False, 'error': 'Nu ai clasă activă. Creează mai întâi o clasă.'}), 400

        created = database.create_homework(user['class_code'], chapter_id, description, file_path, due_date)
        if not created:
            return jsonify({'success': False, 'error': 'Nu am putut salva tema.'}), 500

        return jsonify({'success': True})
    except Exception as e:
        print(f"add_homework error: {e}")
        return jsonify({'success': False, 'error': 'Eroare la încărcarea temei. Încearcă din nou.'}), 500


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
    
    homework_id = request.form.get('homeworkId')
    uploaded = request.files.get('file')
    file_path = _save_uploaded_file(uploaded)

    if not homework_id:
        return jsonify({'success': False, 'error': 'Lipsește homeworkId.'}), 400

    if uploaded and not file_path:
        return jsonify({'success': False, 'error': 'Tipul fișierului nu este permis.'}), 400

    database.complete_homework(user['id'], homework_id, file_path)
    return jsonify({'success': True})

@app.route('/api/homework/<int:homework_id>/completions', methods=['GET'])
def get_homework_completions(homework_id):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user or user['role'] != 'teacher':
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 403
    if not user.get('class_code'):
        return jsonify({'success': False, 'error': 'Profesorul nu are clasă activă.'}), 400

    completions = database.get_homework_completions(homework_id, user['class_code'])
    return jsonify({'success': True, 'completions': completions})

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
        explicit_ch = find_explicit_chapter_in_query(user_input)

        # 1. Identitate / Salut / Garbage
        if len(norm_input) < 2:
            return jsonify({"message": "Hopa! Mesajul tău e prea scurt. Spune-mi cu ce te pot ajuta la matematică! 💡 Scrie <strong>ajutor</strong> pentru a vedea ce pot face."})
        if (primary_intent == "identity" or check_intent(user_input, "identity")) and is_identity_query(user_input):
            return jsonify({"message": "Sunt <strong>Mate dintr-un Click</strong>, asistentul tău virtual de matematică! 🤖 Te pot ajuta cu oricare din cele 22 de capitole de clasa a 5-a. Scrie <strong>ajutor</strong> pentru lista completă de comenzi!"})
        if (primary_intent == "greeting" or check_intent(user_input, "greeting")) and len(norm_input.split()) < 4:
            return jsonify({"message": "Salut! 😄 Sunt aici să explorăm matematica. Ce capitol vrei să discutăm azi? 🍕🔢<br><br>💡 Scrie <strong>ajutor</strong> dacă vrei să vezi ce pot face!"})

        # HELP — Afișare comenzi
        if primary_intent == "help" or check_intent(user_input, "help"):
            return jsonify({"message": get_help_message()})

        # DEFINIȚII GENERALE (fără capitol detectat): x, y, z, n + termeni globali
        if primary_intent == "define" or check_intent(user_input, "define"):
            best_define_ch = find_best_chapter_for_definition(user_input)
            concept_ch = explicit_ch or best_define_ch or current_ch
            if concept_ch:
                if is_general_definition_query(user_input):
                    general_definition = get_chapter_general_definition(concept_ch)
                    if general_definition:
                        return jsonify({
                            "message": f"📘 <strong>{concept_ch['title']}</strong><br><br><strong>Definiție generală:</strong> {general_definition}",
                            "lastChapterId": concept_ch['id'],
                            "suggestion": get_suggestion(concept_ch['id'])
                        })

                focused = get_targeted_snippet(concept_ch, user_input)
                if focused:
                    return jsonify({
                        "message": focused,
                        "lastChapterId": concept_ch['id'],
                        "suggestion": get_suggestion(concept_ch['id'])
                    })

                definition = get_definition_from_chapter(concept_ch, user_input)
                if definition:
                    return jsonify({
                        "message": f"📘 <strong>{concept_ch['title']}</strong><br><br>{definition}",
                        "lastChapterId": concept_ch['id'],
                        "suggestion": get_suggestion(concept_ch['id'])
                    })

            # Dacă nu avem capitol clar, păstrăm fallback-urile existente.
            symbol_def = get_symbol_definition(user_input)
            if symbol_def:
                return jsonify({"message": symbol_def, "lastChapterId": last_id})

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

        if current_ch and is_continue_current_request(user_input):
            focused = get_targeted_snippet(current_ch, user_input)
            if focused:
                return jsonify({
                    "message": focused,
                    "lastChapterId": current_ch['id'],
                    "suggestion": get_suggestion(current_ch['id'])
                })

            msg = (
                f"Continuăm în <strong>{current_ch['title']}</strong>. "
                "Spune exact ce vrei să continui: <em>reguli</em>, <em>exemplu</em> sau <em>exerciții</em>."
            )
            return jsonify({
                "message": msg,
                "lastChapterId": current_ch['id'],
                "suggestion": get_suggestion(current_ch['id'])
            })

        if current_ch and is_short_affirmative(user_input):
            examples = current_ch.get('examples', [])
            if examples:
                return jsonify({
                    "message": f"Perfect! Iată un exemplu rapid din <strong>{current_ch['title']}</strong>:<br><em>{random.choice(examples)}</em>",
                    "lastChapterId": current_ch['id'],
                    "suggestion": get_suggestion(current_ch['id'])
                })

        # NEXT — Capitol următor
        if primary_intent == "next" and is_next_request(user_input):
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

        if primary_intent == "test" or check_intent(user_input, "test"):
            return jsonify({
                "message": "Am eliminat modul de test. Îți pot oferi în schimb quiz-uri rapide și exerciții pe capitol. Scrie <strong>quiz</strong> sau <strong>vreau exerciții</strong>."
            })

        # 2. Detecție capitol + dezambiguizare
        ranked_chapters = rank_chapters(user_input)
        found_ch = explicit_ch or (ranked_chapters[0][0] if ranked_chapters else deep_search(user_input))
        if check_intent(user_input, "compare"):
            found_ch = next((c for c in CHAPTERS if c['id'] == "comparare_ordonare"), found_ch)

        if ranked_chapters and len(ranked_chapters) >= 2 and not current_ch:
            top_score = ranked_chapters[0][1]
            second_score = ranked_chapters[1][1]
            if top_score < 8 or (second_score >= top_score * 0.82 and (top_score - second_score) <= 4):
                a = ranked_chapters[0][0]
                b = ranked_chapters[1][0]
                return jsonify({
                    "message": (
                        "Întrebarea poate fi din mai multe capitole. Alege exact:<br><br>"
                        f"• <strong>{a['title']}</strong><br>"
                        f"• <strong>{b['title']}</strong>"
                    ),
                    "lastChapterId": last_id
                })

        if current_ch and found_ch and current_ch['id'] != found_ch['id']:
            if explicit_ch is None and not is_explicit_chapter_reference(found_ch, user_input):
                found_ch = current_ch

        if found_ch:
            if found_ch['id'] != last_id:
                current_ch = found_ch
                last_id = found_ch['id']
                if not any(check_intent(user_input, i) for i in ["elaborate", "example", "exercise", "define", "quiz", "fact", "step_by_step", "summary"]):
                    msg = get_targeted_snippet(found_ch, user_input) or get_structured_intro_by_level(found_ch, user_input, level)
                    suggestion = get_suggestion(last_id)
                    return jsonify({
                        "message": msg,
                        "lastChapterId": last_id,
                        "suggestion": suggestion
                    })

        # 3. Interacțiuni specifice
        target = found_ch if found_ch else current_ch
        if target:
            # Calibrare strictă: întrebări normale primesc doar secvența relevantă.
            if primary_intent is None:
                focused = get_targeted_snippet(target, user_input)
                if focused:
                    return jsonify({
                        "message": focused,
                        "lastChapterId": target['id'],
                        "suggestion": get_suggestion(target['id'])
                    })
                return jsonify({
                    "message": (
                        f"Sunt pe capitolul <strong>{target['title']}</strong>, dar nu am identificat termenul exact din întrebare.<br><br>"
                        "Scrie exact noțiunea (ex: <em>criteriul de divizibilitate cu 3</em>, <em>fracție ireductibilă</em>)."
                    ),
                    "lastChapterId": target['id'],
                    "suggestion": get_suggestion(target['id'])
                })

            neutral_intents = {"elaborate", "example", "exercise", "define", "quiz", "fact", "step_by_step", "summary", "plan", "next", "recap", "help", "greeting", "identity", "test"}
            if primary_intent not in neutral_intents:
                focused = get_targeted_snippet(target, user_input)
                if focused:
                    return jsonify({
                        "message": focused,
                        "lastChapterId": target['id'],
                        "suggestion": get_suggestion(target['id'])
                    })

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
                prefix = random_prefix()
                focused = get_targeted_snippet(target, user_input)
                if focused:
                    msg = f"{prefix}{focused}"
                else:
                    definition = get_definition_from_chapter(target, user_input)
                    msg = f"{prefix}📖 <strong>{target['title']}</strong><br><br>{definition}<br><br>Spune-mi exact termenul dacă vrei răspuns punctual."
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

        if not target and primary_intent in {"elaborate", "example", "exercise", "quiz", "step_by_step", "summary", "define"}:
            candidates = get_top_matches(user_input, count=3)
            if candidates:
                suggestions_html = "<br>".join([f"• <strong>{ch['title']}</strong>" for ch in candidates])
                return jsonify({
                    "message": (
                        "Ca să răspund corect, am nevoie de capitolul exact.<br><br>"
                        f"Poți alege unul dintre acestea:<br>{suggestions_html}"
                    ),
                    "lastChapterId": last_id
                })
            return jsonify({
                "message": "Spune-mi capitolul exact (ex: fracții, puteri, divizibilitate) și îți dau direct răspunsul potrivit.",
                "lastChapterId": last_id
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


def _build_multiplayer_questions(count=10):
    pool = []
    for ch in CHAPTERS:
        for ex in ch.get('exercises', []):
            if isinstance(ex, dict) and ex.get('question') and ex.get('answer') is not None:
                pool.append({
                    "chapterId": ch.get('id'),
                    "chapterTitle": ch.get('title'),
                    "question": ex.get('question'),
                    "answer": str(ex.get('answer')).strip()
                })

    if not pool:
        return [
            {"chapterId": "fallback", "chapterTitle": "General", "question": c["question"], "answer": c["answer"]}
            for c in DAILY_CHALLENGES[:count]
        ]

    if len(pool) <= count:
        random.shuffle(pool)
        return pool

    return random.sample(pool, count)


def _advance_multiplayer_on_timeout(session_row, state):
    now = int(time.time())
    if not state:
        return state, False

    if state.get('status') == 'finished':
        return state, False

    if state.get('currentQ', 0) >= len(state.get('questions', [])):
        state['status'] = 'finished'
        state['lastFeedback'] = '🏁 Joc terminat.'
        return state, True

    round_start = int(state.get('roundStartTime') or now)
    duration = int(state.get('roundDuration') or 20)
    if now - round_start < duration:
        return state, False

    state['lastFeedback'] = '⌛ Timp expirat pentru rundă.'
    state['currentQ'] = state.get('currentQ', 0) + 1
    state['roundStartTime'] = now

    if state['currentQ'] >= len(state.get('questions', [])):
        state['status'] = 'finished'
        return state, True

    return state, True


@app.route('/api/multiplayer/create', methods=['POST'])
def multiplayer_create():
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 401

    state = {
        'questions': _build_multiplayer_questions(10),
        'scores': [0, 0],
        'currentQ': 0,
        'roundDuration': 20,
        'roundStartTime': int(time.time()),
        'lastFeedback': '',
        'status': 'waiting'
    }

    code = database.create_multiplayer_session(user['id'], json.dumps(state))
    return jsonify({'success': True, 'code': code})


@app.route('/api/multiplayer/join/<code>', methods=['POST'])
def multiplayer_join(code):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 401

    ok = database.join_multiplayer_session(user['id'], code)
    if not ok:
        return jsonify({'success': False, 'error': 'Camera nu există, nu e disponibilă sau ești deja host.'}), 400

    session_row = database.get_multiplayer_session(code)
    if not session_row:
        return jsonify({'success': False, 'error': 'Camera nu a fost găsită după join.'}), 404

    try:
        state = json.loads(session_row.get('state_json') or '{}')
    except Exception:
        state = {}

    state['status'] = 'playing'
    state['roundStartTime'] = int(time.time())
    state['lastFeedback'] = '🎮 Joc început!'
    database.update_multiplayer_state(code, json.dumps(state), status='playing')

    return jsonify({'success': True})


@app.route('/api/multiplayer/status/<code>', methods=['GET'])
def multiplayer_status(code):
    session_row = database.get_multiplayer_session(code)
    if not session_row:
        return jsonify({'success': False, 'error': 'Camera nu există.'}), 404

    try:
        state = json.loads(session_row.get('state_json') or '{}')
    except Exception:
        state = {}

    status = session_row.get('status', 'waiting')
    state['status'] = status

    updated = False
    if status == 'playing':
        state, updated = _advance_multiplayer_on_timeout(session_row, state)
        status = state.get('status', status)
        if updated:
            database.update_multiplayer_state(code, json.dumps(state), status='finished' if status == 'finished' else 'playing')

    return jsonify({
        'success': True,
        'code': session_row.get('code'),
        'status': status,
        'state': state,
        'host_name': session_row.get('host_name'),
        'guest_name': session_row.get('guest_name'),
        'server_time': int(time.time())
    })


@app.route('/api/multiplayer/action/<code>', methods=['POST'])
def multiplayer_action(code):
    token = request.headers.get('Authorization')
    user = database.get_user_by_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Neautorizat.'}), 401

    session_row = database.get_multiplayer_session(code)
    if not session_row:
        return jsonify({'success': False, 'error': 'Camera nu există.'}), 404

    host_id = session_row.get('host_id')
    guest_id = session_row.get('guest_id')
    if user['id'] not in {host_id, guest_id}:
        return jsonify({'success': False, 'error': 'Nu faci parte din această cameră.'}), 403

    try:
        state = json.loads(session_row.get('state_json') or '{}')
    except Exception:
        state = {}

    if session_row.get('status') != 'playing':
        return jsonify({'success': False, 'error': 'Jocul nu este în desfășurare.'}), 400

    state['status'] = 'playing'
    state, updated = _advance_multiplayer_on_timeout(session_row, state)
    if state.get('status') == 'finished':
        if updated:
            database.update_multiplayer_state(code, json.dumps(state), status='finished')
        return jsonify({'success': True, 'timeout': True, 'isCorrect': False})

    current_q = state.get('currentQ', 0)
    questions = state.get('questions', [])
    if current_q >= len(questions):
        state['status'] = 'finished'
        database.update_multiplayer_state(code, json.dumps(state), status='finished')
        return jsonify({'success': True, 'timeout': True, 'isCorrect': False})

    answer_payload = request.json or {}
    user_answer = str(answer_payload.get('answer', '')).strip()
    correct_answer = str(questions[current_q].get('answer', '')).strip()
    is_correct = answers_match(user_answer, correct_answer)

    if is_correct:
        player_idx = 0 if user['id'] == host_id else 1
        scores = state.get('scores', [0, 0])
        if len(scores) < 2:
            scores = [0, 0]
        scores[player_idx] = scores[player_idx] + 1
        state['scores'] = scores
        state['lastFeedback'] = f"✅ {user.get('username', 'Jucător')} a răspuns corect!"
        state['currentQ'] = current_q + 1
        state['roundStartTime'] = int(time.time())

        if state['currentQ'] >= len(questions):
            state['status'] = 'finished'
            database.update_multiplayer_state(code, json.dumps(state), status='finished')
        else:
            database.update_multiplayer_state(code, json.dumps(state), status='playing')

        return jsonify({'success': True, 'isCorrect': True})

    database.update_multiplayer_state(code, json.dumps(state), status='playing')
    return jsonify({'success': True, 'isCorrect': False})


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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
