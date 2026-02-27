import sqlite3
import os
import secrets
import hashlib
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'mateai.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            class_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chapter_id TEXT NOT NULL,
            correct INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, chapter_id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            teacher_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS daily_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE DEFAULT (date('now')),
            count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, date)
        );

        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_code TEXT NOT NULL,
            chapter_id TEXT,
            description TEXT,
            file_path TEXT,
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_code) REFERENCES classes(code)
        );

        CREATE TABLE IF NOT EXISTS homework_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homework_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            file_path TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (homework_id) REFERENCES homework(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(homework_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_code TEXT NOT NULL,
            title TEXT NOT NULL,
            chapter_id TEXT,
            num_questions INTEGER DEFAULT 5,
            file_path TEXT,
            custom_questions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_code) REFERENCES classes(code)
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            score INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES tests(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(test_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS multiplayer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            host_id INTEGER NOT NULL,
            guest_id INTEGER,
            status TEXT DEFAULT 'waiting',
            state_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (host_id) REFERENCES users(id),
            FOREIGN KEY (guest_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()


def hash_password(password):
    salt = 'mateai_salt_2026'
    return hashlib.sha256((password + salt).encode()).hexdigest()


def create_user(username, password, role='student'):
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username.strip().lower(), hash_password(password), role)
        )
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        return {'success': True, 'user_id': user_id}
    except sqlite3.IntegrityError:
        conn.close()
        return {'success': False, 'error': 'Numele de utilizator există deja.'}


def login_user(username, password):
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password_hash = ?',
        (username.strip().lower(), hash_password(password))
    ).fetchone()

    if not user:
        conn.close()
        return None

    # Create session token
    token = secrets.token_hex(32)
    expires = datetime.now() + timedelta(days=30)
    conn.execute(
        'INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)',
        (token, user['id'], expires.isoformat())
    )
    conn.commit()
    conn.close()
    return {
        'token': token,
        'user_id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'class_code': user['class_code']
    }


def get_user_by_token(token):
    if not token:
        return None
    conn = get_db()
    row = conn.execute('''
        SELECT u.* FROM users u
        JOIN sessions s ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > ?
    ''', (token, datetime.now().isoformat())).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def logout_user(token):
    conn = get_db()
    conn.execute('DELETE FROM sessions WHERE token = ?', (token,))
    conn.commit()
    conn.close()


def update_progress(user_id, chapter_id, is_correct):
    conn = get_db()
    existing = conn.execute(
        'SELECT * FROM progress WHERE user_id = ? AND chapter_id = ?',
        (user_id, chapter_id)
    ).fetchone()

    if existing:
        conn.execute('''
            UPDATE progress SET total = total + 1, correct = correct + ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND chapter_id = ?
        ''', (1 if is_correct else 0, user_id, chapter_id))
    else:
        conn.execute('''
            INSERT INTO progress (user_id, chapter_id, correct, total)
            VALUES (?, ?, ?, 1)
        ''', (user_id, chapter_id, 1 if is_correct else 0))

    # Update daily activity
    conn.execute('''
        INSERT INTO daily_activity (user_id, date, count)
        VALUES (?, date('now'), 1)
        ON CONFLICT(user_id, date) DO UPDATE SET count = count + 1
    ''', (user_id,))

    conn.commit()
    conn.close()


def get_user_progress(user_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT chapter_id, correct, total FROM progress WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()
    return {row['chapter_id']: {'correct': row['correct'], 'total': row['total']} for row in rows}


def get_user_stats(user_id):
    conn = get_db()
    stats = conn.execute('''
        SELECT COUNT(DISTINCT chapter_id) as chapters,
               COALESCE(SUM(correct), 0) as total_correct,
               COALESCE(SUM(total), 0) as total_answers
        FROM progress WHERE user_id = ?
    ''', (user_id,)).fetchone()
    conn.close()
    return dict(stats)


def get_daily_activity(user_id):
    conn = get_db()
    rows = conn.execute('''
        SELECT date, count FROM daily_activity 
        WHERE user_id = ? AND date >= date('now', '-7 days')
        ORDER BY date ASC
    ''', (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# --- CLASSROOM ---
def create_class(teacher_id, class_name):
    code = secrets.token_hex(3).upper()  # 6 char code
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO classes (name, code, teacher_id) VALUES (?, ?, ?)',
            (class_name, code, teacher_id)
        )
        conn.execute('UPDATE users SET class_code = ? WHERE id = ?', (code, teacher_id))
        conn.commit()
        conn.close()
        return {'success': True, 'code': code, 'name': class_name}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}


def join_class(user_id, code):
    conn = get_db()
    cls = conn.execute('SELECT * FROM classes WHERE code = ?', (code.strip().upper(),)).fetchone()
    if not cls:
        conn.close()
        return {'success': False, 'error': 'Codul clasei nu există.'}

    conn.execute('UPDATE users SET class_code = ? WHERE id = ?', (code.strip().upper(), user_id))
    conn.commit()
    conn.close()
    return {'success': True, 'className': cls['name']}


def get_class_rankings(code):
    conn = get_db()
    cls = conn.execute('SELECT * FROM classes WHERE code = ?', (code.strip().upper(),)).fetchone()
    if not cls:
        conn.close()
        return None

    students = conn.execute('''
        SELECT u.id, u.username,
               COALESCE(SUM(p.correct), 0) as total_correct,
               COALESCE(SUM(p.total), 0) as total_answers,
               COUNT(DISTINCT p.chapter_id) as chapters_explored
        FROM users u
        LEFT JOIN progress p ON p.user_id = u.id
        WHERE u.class_code = ? AND u.role = 'student'
        GROUP BY u.id
        ORDER BY total_correct DESC
    ''', (code.strip().upper(),)).fetchall()
    conn.close()

    return {
        'className': cls['name'],
        'code': cls['code'],
        'students': [dict(s) for s in students]
    }


def get_student_details(user_id):
    conn = get_db()
    progress = conn.execute('''
        SELECT chapter_id, correct, total, updated_at
        FROM progress WHERE user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return [dict(p) for p in progress]


# --- HOMEWORK ---
def create_homework(class_code, chapter_id, description=None, file_path=None, due_date=None):
    conn = get_db()
    conn.execute(
        'INSERT INTO homework (class_code, chapter_id, description, file_path, due_date) VALUES (?, ?, ?, ?, ?)',
        (class_code.strip().upper(), chapter_id, description, file_path, due_date)
    )
    conn.commit()
    conn.close()
    return True


def get_class_homework(class_code, user_id=None):
    conn = get_db()
    # If user_id is provided, also check completion status
    if user_id:
        rows = conn.execute('''
            SELECT h.*, hc.completed_at
            FROM homework h
            LEFT JOIN homework_completions hc ON hc.homework_id = h.id AND hc.user_id = ?
            WHERE h.class_code = ?
            ORDER BY h.created_at DESC
        ''', (user_id, class_code.strip().upper())).fetchall()
    else:
        rows = conn.execute('''
            SELECT * FROM homework WHERE class_code = ? ORDER BY created_at DESC
        ''', (class_code.strip().upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_homework(user_id, homework_id, file_path=None):
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO homework_completions (homework_id, user_id, file_path) VALUES (?, ?, ?)',
            (homework_id, user_id, file_path)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_homework_completions(homework_id, class_code):
    """Returns list of students in class with their completion status for this homework."""
    conn = get_db()
    rows = conn.execute('''
        SELECT u.id, u.username,
               hc.completed_at, hc.file_path
        FROM users u
        LEFT JOIN homework_completions hc ON hc.homework_id = ? AND hc.user_id = u.id
        WHERE u.class_code = ? AND u.role = 'student'
        ORDER BY hc.completed_at DESC
    ''', (homework_id, class_code.strip().upper())).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- TESTS ---
def create_test(class_code, title, chapter_id=None, num_questions=5, file_path=None, custom_questions=None):
    conn = get_db()
    conn.execute(
        'INSERT INTO tests (class_code, title, chapter_id, num_questions, file_path, custom_questions) VALUES (?, ?, ?, ?, ?, ?)',
        (class_code.strip().upper(), title, chapter_id, num_questions, file_path, custom_questions)
    )
    conn.commit()
    test_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return {'success': True, 'test_id': test_id}


def get_class_tests(class_code, user_id=None):
    conn = get_db()
    if user_id:
        rows = conn.execute('''
            SELECT t.*, tr.score, tr.total, tr.completed_at as result_at
            FROM tests t
            LEFT JOIN test_results tr ON tr.test_id = t.id AND tr.user_id = ?
            WHERE t.class_code = ?
            ORDER BY t.created_at DESC
        ''', (user_id, class_code.strip().upper())).fetchall()
    else:
        rows = conn.execute('''
            SELECT t.*,
                   COUNT(tr.id) as completions
            FROM tests t
            LEFT JOIN test_results tr ON tr.test_id = t.id
            WHERE t.class_code = ?
            GROUP BY t.id
            ORDER BY t.created_at DESC
        ''', (class_code.strip().upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def submit_test_result(test_id, user_id, score, total):
    conn = get_db()
    try:
        conn.execute(
            'INSERT OR REPLACE INTO test_results (test_id, user_id, score, total) VALUES (?, ?, ?, ?)',
            (test_id, user_id, score, total)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def get_test_results(test_id, class_code):
    """Returns all student results for a given test."""
    conn = get_db()
    rows = conn.execute('''
        SELECT u.id, u.username,
               tr.score, tr.total, tr.completed_at
        FROM users u
        LEFT JOIN test_results tr ON tr.test_id = ? AND tr.user_id = u.id
        WHERE u.class_code = ? AND u.role = 'student'
        ORDER BY tr.score DESC
    ''', (test_id, class_code.strip().upper())).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- MULTIPLAYER ---
def create_multiplayer_session(host_id, state_json):
    conn = get_db()
    # Generate random 6-char code
    import random
    import string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    conn.execute(
        'INSERT INTO multiplayer_sessions (code, host_id, state_json) VALUES (?, ?, ?)',
        (code, host_id, state_json)
    )
    conn.commit()
    conn.close()
    return code

def join_multiplayer_session(guest_id, code):
    conn = get_db()
    session = conn.execute('SELECT * FROM multiplayer_sessions WHERE code = ? AND status = "waiting"', (code.upper().strip(),)).fetchone()
    if not session:
        conn.close()
        return False
    
    if session['host_id'] == guest_id:
        conn.close()
        return False

    conn.execute(
        'UPDATE multiplayer_sessions SET guest_id = ?, status = "playing" WHERE code = ?',
        (guest_id, code.upper().strip())
    )
    conn.commit()
    conn.close()
    return True

def get_multiplayer_session(code):
    conn = get_db()
    row = conn.execute('''
        SELECT m.*, u1.username as host_name, u2.username as guest_name
        FROM multiplayer_sessions m
        LEFT JOIN users u1 ON m.host_id = u1.id
        LEFT JOIN users u2 ON m.guest_id = u2.id
        WHERE m.code = ?
    ''', (code.upper().strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_multiplayer_state(code, new_state_json, status=None):
    conn = get_db()
    if status:
        conn.execute('UPDATE multiplayer_sessions SET state_json = ?, status = ? WHERE code = ?', (new_state_json, status, code.upper().strip()))
    else:
        conn.execute('UPDATE multiplayer_sessions SET state_json = ? WHERE code = ?', (new_state_json, code.upper().strip()))
    conn.commit()
    conn.close()
