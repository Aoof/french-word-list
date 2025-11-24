from flask import Flask, render_template, jsonify
import csv
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'french_words_secret_key')
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

GOOD_CSV = 'words_good.csv'
MISSING_CSV = 'words_missing.csv'

def load_csv(path, fields):
    data = []
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == len(fields):
                    data.append(dict(zip(fields, row)))
    except FileNotFoundError:
        pass
    return data

def get_word_type_info(pos):
    """Return color and description for each part of speech"""
    pos_info = {
        'verb': {
            'color': '#667eea',
            'label': 'Verb',
            'description': 'Action or state word'
        },
        'noun': {
            'color': '#f093fb',
            'label': 'Noun',
            'description': 'Person, place, or thing'
        },
        'adjective': {
            'color': '#4fd1c5',
            'label': 'Adjective',
            'description': 'Describes a noun'
        },
        'adverb': {
            'color': '#fbd38d',
            'label': 'Adverb',
            'description': 'Modifies a verb or adjective'
        },
        'pronoun': {
            'color': '#fc8181',
            'label': 'Pronoun',
            'description': 'Replaces a noun'
        },
        'preposition': {
            'color': '#9f7aea',
            'label': 'Preposition',
            'description': 'Shows relationship between words'
        },
        'conjunction': {
            'color': '#ed8936',
            'label': 'Conjunction',
            'description': 'Connects words or phrases'
        },
        'interjection': {
            'color': '#f56565',
            'label': 'Interjection',
            'description': 'Expresses emotion'
        },
        'article': {
            'color': '#48bb78',
            'label': 'Article',
            'description': 'Defines a noun (the, a, an)'
        }
    }
    return pos_info.get(pos.lower(), {
        'color': '#718096',
        'label': pos.title(),
        'description': 'Word type'
    })

def get_gender_info(gender):
    """Return color and description for gender/group"""
    gender_info = {
        'masculine': {
            'color': '#4299e1',
            'label': 'Masculine',
            'icon': '♂'
        },
        'feminine': {
            'color': '#ed64a6',
            'label': 'Feminine',
            'icon': '♀'
        },
        '1st group': {
            'color': '#38b2ac',
            'label': '1st Group',
            'icon': '①'
        },
        '2nd group': {
            'color': '#9f7aea',
            'label': '2nd Group',
            'icon': '②'
        },
        '3rd group': {
            'color': '#ed8936',
            'label': '3rd Group',
            'icon': '③'
        }
    }
    return gender_info.get(gender.lower(), {
        'color': '#a0aec0',
        'label': gender.title(),
        'icon': '•'
    })

@app.route('/')
def index():
    good = load_csv(GOOD_CSV, ['word', 'pos', 'gender_or_group'])
    missing = load_csv(MISSING_CSV, ['word', 'pos'])
    return render_template('index.html', good=good, missing=missing)

@app.route('/api/random-card')
def random_card():
    """API endpoint that returns a random flashcard"""
    good = load_csv(GOOD_CSV, ['word', 'pos', 'gender_or_group'])
    if not good:
        return jsonify({'error': 'No cards available'}), 404
    
    card = random.choice(good)
    pos_info = get_word_type_info(card['pos'])
    gender_info = get_gender_info(card['gender_or_group'])
    
    return jsonify({
        'word': card['word'],
        'pos': {
            'text': card['pos'],
            'color': pos_info['color'],
            'label': pos_info['label'],
            'description': pos_info['description']
        },
        'gender_or_group': {
            'text': card['gender_or_group'],
            'color': gender_info['color'],
            'label': gender_info['label'],
            'icon': gender_info['icon']
        },
        'total_cards': len(good)
    })

@app.route('/cards')
def cards():
    """New flashcard interface with random card loading"""
    return render_template('cards.html')

if __name__ == '__main__':
    app.run(debug=True)
