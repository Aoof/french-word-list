from flask import Flask, render_template, jsonify
import csv
import random
import os
import re
import sqlite3
import requests as http_requests
from dotenv import load_dotenv
from larousse_api import larousse

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'french_words_secret_key')
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

GOOD_CSV   = 'words_good.csv'
MISSING_CSV = 'words_missing.csv'
DB_PATH    = 'words.db'


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    """Return a thread-local DB connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and import CSVs (idempotent)."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS words_good (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                word              TEXT    NOT NULL UNIQUE,
                pos               TEXT    NOT NULL,
                gender_or_group   TEXT    NOT NULL,
                definition        TEXT,
                definition_source TEXT
            );

            CREATE TABLE IF NOT EXISTS words_missing (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT    NOT NULL UNIQUE,
                pos  TEXT    NOT NULL
            );
        """)

        # Import words_good.csv
        try:
            with open(GOOD_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [(r['word'], r['pos'], r['gender_or_group']) for r in reader
                        if r.get('word') and r.get('pos') and r.get('gender_or_group')]
            conn.executemany(
                "INSERT OR IGNORE INTO words_good (word, pos, gender_or_group) VALUES (?,?,?)",
                rows
            )
        except FileNotFoundError:
            pass

        # Import words_missing.csv
        try:
            with open(MISSING_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [(r['word'], r['pos']) for r in reader
                        if r.get('word') and r.get('pos')]
            conn.executemany(
                "INSERT OR IGNORE INTO words_missing (word, pos) VALUES (?,?)",
                rows
            )
        except FileNotFoundError:
            pass

        conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────
# Allowed word pattern: Unicode letters, hyphens, apostrophes, spaces; 1–80 chars
_WORD_RE = re.compile(r"^[\w\s'\-]{1,80}$", re.UNICODE)


def is_valid_word_param(word: str) -> bool:
    """Return True only if the word looks like a plausible French word."""
    return bool(word and _WORD_RE.match(word))


def word_exists_in_db(word: str) -> bool:
    """Return True only if the word is already in our words_good table."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM words_good WHERE word = ? LIMIT 1", (word,)
        ).fetchone()
    return row is not None

def fetch_definition_from_api(word):
    """Fetch definition from Larousse (primary) or freedictionaryapi.com (fallback)."""
    # 1. Larousse API – first choice
    try:
        definitions = larousse.get_definitions(word)
        if definitions and len(definitions) > 0:
            return definitions[0], 'larousse'
    except Exception:
        pass

    # 2. freedictionaryapi.com – fallback
    try:
        resp = http_requests.get(
            f'https://freedictionaryapi.com/api/v1/entries/fr/{word}',
            params={'translations': 'true'},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            for entry in data.get('entries', []):
                for sense in entry.get('senses', []):
                    defn = sense.get('definition', '').strip()
                    if defn:
                        return defn, 'freedictionaryapi'
    except Exception:
        pass

    return None, None


def get_word_type_info(pos):
    """Return label and description for a part of speech."""
    pos_info = {
        'verb':         {'label': 'Verb',         'description': 'Action or state word'},
        'noun':         {'label': 'Noun',         'description': 'Person, place, or thing'},
        'adjective':    {'label': 'Adjective',    'description': 'Describes a noun'},
        'adverb':       {'label': 'Adverb',       'description': 'Modifies a verb or adjective'},
        'pronoun':      {'label': 'Pronoun',      'description': 'Replaces a noun'},
        'preposition':  {'label': 'Preposition',  'description': 'Shows relationship between words'},
        'conjunction':  {'label': 'Conjunction',  'description': 'Connects words or phrases'},
        'interjection': {'label': 'Interjection', 'description': 'Expresses emotion'},
        'article':      {'label': 'Article',      'description': 'Defines a noun (the, a, an)'},
    }
    return pos_info.get(pos.lower(), {'label': pos.title(), 'description': 'Word type'})


def get_gender_info(gender):
    """Return label and icon for a gender/group value."""
    gender_info = {
        'masculine': {'label': 'Masculine', 'icon': '♂'},
        'feminine':  {'label': 'Feminine',  'icon': '♀'},
        '1st group': {'label': '1st Group', 'icon': '①'},
        '2nd group': {'label': '2nd Group', 'icon': '②'},
        '3rd group': {'label': '3rd Group', 'icon': '③'},
    }
    return gender_info.get(gender.lower(), {'label': gender.title(), 'icon': '•'})


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    with get_db() as conn:
        good    = [dict(r) for r in conn.execute(
            "SELECT word, pos, gender_or_group FROM words_good ORDER BY word"
        ).fetchall()]
        missing = [dict(r) for r in conn.execute(
            "SELECT word, pos FROM words_missing ORDER BY word"
        ).fetchall()]
    return render_template('index.html', good=good, missing=missing)


@app.route('/api/random-card')
def random_card():
    """Return a random flashcard from the database."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM words_good").fetchone()[0]
        if not total:
            return jsonify({'error': 'No cards available'}), 404
        row = conn.execute(
            "SELECT word, pos, gender_or_group FROM words_good ORDER BY RANDOM() LIMIT 1"
        ).fetchone()

    card        = dict(row)
    pos_info    = get_word_type_info(card['pos'])
    gender_info = get_gender_info(card['gender_or_group'])

    return jsonify({
        'word': card['word'],
        'pos': {
            'text':        card['pos'],
            'label':       pos_info['label'],
            'description': pos_info['description'],
        },
        'gender_or_group': {
            'text':  card['gender_or_group'],
            'label': gender_info['label'],
            'icon':  gender_info['icon'],
        },
        'total_cards': total,
    })


@app.route('/api/definition/<word>')
def get_definition(word):
    """Return a cached definition or fetch, store, and return a new one.

    Security:
    - The word is validated against a strict regex before any processing.
    - We only fetch/write definitions for words that already exist in our
      words_good table; arbitrary client-supplied strings are rejected with 404.
    - All DB interactions use parameterized queries.
    """
    # 1. Reject malformed input immediately
    if not is_valid_word_param(word):
        return jsonify({'error': 'Invalid word'}), 400

    # 2. Only serve/store definitions for words we actually imported
    if not word_exists_in_db(word):
        return jsonify({'error': 'Word not found'}), 404

    # 3. Return cached definition if we already have one
    with get_db() as conn:
        row = conn.execute(
            "SELECT definition, definition_source FROM words_good WHERE word = ?",
            (word,)
        ).fetchone()

    if row and row['definition']:
        return jsonify({
            'word':       word,
            'definition': row['definition'],
            'source':     row['definition_source'],
            'cached':     True,
        })

    # 4. Fetch from external API
    definition, source = fetch_definition_from_api(word)
    
    print(f"Fetched definition for the word {word} from {source}")

    # 5. Persist result (including None, to avoid hammering the API again)
    #    Only updates the row that already exists; INSERT is never triggered here.
    with get_db() as conn:
        conn.execute(
            """UPDATE words_good
               SET definition = ?, definition_source = ?
               WHERE word = ?""",
            (definition, source, word)
        )
        conn.commit()

    if definition:
        return jsonify({'word': word, 'definition': definition, 'source': source, 'cached': False})

    return jsonify({'word': word, 'definition': None, 'source': None}), 404


@app.route('/cards')
def cards():
    return render_template('cards.html')


# ── Entry point ───────────────────────────────────────────────────────────────

init_db()

if __name__ == '__main__':
    app.run(debug=True)

