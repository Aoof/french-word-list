from flask import Flask, render_template_string, session, request
import csv

app = Flask(__name__)
app.secret_key = 'french_words_secret_key'

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

@app.route('/')
def index():
    good = load_csv(GOOD_CSV, ['word', 'pos', 'gender_or_group'])
    missing = load_csv(MISSING_CSV, ['word', 'pos'])
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>French Words Viewer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .table th { background-color: #007bff; color: white; }
            .card-custom { max-width: 600px; margin: 20px auto; }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-center mb-4">French Words Scraper Results</h1>
            <div class="row text-center mb-4">
                <div class="col-md-6">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <h5 class="card-title">✅ Good Entries</h5>
                            <p class="card-text">{{ good|length }}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <h5 class="card-title">⚠️ Missing Entries</h5>
                            <p class="card-text">{{ missing|length }}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="text-center mb-4">
                <a href="/cards" class="btn btn-primary btn-lg">Start Flashcards</a>
            </div>
            <h2>Good Entries</h2>
            <div class="table-responsive">
                <table class="table table-striped table-bordered">
                    <thead>
                        <tr>
                            <th>Word</th>
                            <th>Part of Speech</th>
                            <th>Gender/Group</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in good %}
                        <tr>
                            <td>{{ row.word }}</td>
                            <td>{{ row.pos }}</td>
                            <td>{{ row.gender_or_group }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <h2>Missing Entries</h2>
            <div class="table-responsive">
                <table class="table table-striped table-bordered">
                    <thead>
                        <tr>
                            <th>Word</th>
                            <th>Part of Speech</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in missing %}
                        <tr>
                            <td>{{ row.word }}</td>
                            <td>{{ row.pos }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, good=good, missing=missing)

@app.route('/cards')
def cards():
    good = load_csv(GOOD_CSV, ['word', 'pos', 'gender_or_group'])
    if not good:
        return "No good words to review."
    index = session.get('card_index', 0)
    if index >= len(good):
        index = 0
    session['card_index'] = index
    card = good[index]
    total = len(good)
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>French Flashcards</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .card-custom {
                max-width: 500px;
                margin: 50px auto;
                height: 300px;
                perspective: 1000px;
            }
            .card-flip {
                position: relative;
                width: 100%;
                height: 100%;
                transition: transform 0.6s;
                transform-style: preserve-3d;
            }
            .card-flip.flipped {
                transform: rotateY(180deg);
            }
            .card-front, .card-back {
                position: absolute;
                width: 100%;
                height: 100%;
                backface-visibility: hidden;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                font-weight: bold;
            }
            .card-front {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .card-back {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                transform: rotateY(180deg);
            }
            .progress-text {
                text-align: center;
                margin-bottom: 20px;
                font-size: 1.2rem;
                color: #495057;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mt-4">French Flashcards</h1>
            <div class="progress-text">
                Card {{ index + 1 }} of {{ total }}
            </div>
            <div class="card-custom">
                <div class="card-flip" id="card">
                    <div class="card-front" onclick="flipCard()">
                        {{ card.word }}
                    </div>
                    <div class="card-back" onclick="flipCard()">
                        <div class="text-center">
                            <h4>{{ card.pos.title() }}</h4>
                            <p class="mb-0">{{ card.gender_or_group.title() }}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="text-center">
                <a href="/next" class="btn btn-success btn-lg">Next Card</a>
                <a href="/" class="btn btn-secondary btn-lg ms-2">Back to Home</a>
            </div>
        </div>
        <script>
            function flipCard() {
                document.getElementById('card').classList.toggle('flipped');
            }
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, card=card, index=index, total=total)

@app.route('/next')
def next_card():
    good = load_csv(GOOD_CSV, ['word', 'pos', 'gender_or_group'])
    if not good:
        return "No good words to review."
    index = session.get('card_index', 0) + 1
    if index >= len(good):
        index = 0
    session['card_index'] = index
    return cards()

if __name__ == '__main__':
    app.run(debug=True)
