import csv
import requests
from bs4 import BeautifulSoup
import time
import os
import logging
from datetime import datetime

INPUT_CSV = 'input_words.csv'
TRACKER_CSV = 'scrape_tracker.csv'
GOOD_CSV = 'words_good.csv'
MISSING_CSV = 'words_missing.csv'
BASE_URL_DICT = 'https://fr.wiktionary.org/wiki/'

# configurable settings
SLEEP_TIME = 1.5          # polite delay between requests (seconds)
AUTO_PAUSE_LIMIT = 10     # pause after this many consecutive missing results

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_tracker():
    """Load existing tracker if present."""
    if not os.path.exists(TRACKER_CSV):
        return {}
    with open(TRACKER_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row['word']: row for row in reader}

def save_tracker(tracker):
    """Write tracker dict back to CSV."""
    with open(TRACKER_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['word','pos','status','gender_or_group','timestamp']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for word, row in tracker.items():
            writer.writerow(row)

def scrape_word(word, session):
    """Scrape Reverso for the given word and detect part of speech."""
    # Normalize word for URL
    word_url = word.lower().replace(' ', '-')
    url = BASE_URL_DICT + word_url
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
    }
    logging.info(f"Requesting {url}")
    try:
        r = session.get(url, timeout=10, headers=headers)
        logging.info(f"Status: {r.status_code}")
        if r.status_code != 200:
            return None
    except Exception as e:
        logging.warning(f"Request failed for {word}: {e}")
        return None

    soup = BeautifulSoup(r.text, 'html.parser')
    logging.info(f"Title: {soup.title.string if soup.title else 'No title'}")
    result = {'word': word, 'pos': 'other', 'gender_or_group': None}

    # Check for verb group
    text = soup.get_text().lower()
    group_text = soup.find(string=lambda t: t and 'groupe' in t.lower())
    if 'verbe' in text and group_text:
        gt = group_text.lower()
        result['pos'] = 'verb'
        if 'troisième' in gt or '3e' in gt:
            result['gender_or_group'] = '3rd group'
        elif 'deuxième' in gt or '2e' in gt:
            result['gender_or_group'] = '2nd group'
        elif 'premier' in gt or '1er' in gt:
            result['gender_or_group'] = '1st group'
        else:
            result['gender_or_group'] = 'unknown group'
        logging.info(f"Found verb for {word}: {result['gender_or_group']}")
        return result

    # Check for gender (noun)
    gender_text = soup.find(string=lambda t: t and ('masculin' in t.lower() or 'féminin' in t.lower()))
    if gender_text:
        gt = gender_text.lower()
        result['pos'] = 'noun'
        if 'masc' in gt:
            result['gender_or_group'] = 'masculine'
        elif 'fem' in gt or 'féminin' in gt:
            result['gender_or_group'] = 'feminine'
        logging.info(f"Found noun for {word}: {result['gender_or_group']}")
        return result

    # If neither, leave as other
    logging.info(f"No verb or noun found for {word}")
    return result

def append_csv(path, fieldnames, row):
    new_file = not os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new_file:
            writer.writeheader()
        writer.writerow(row)

def main():
    if not os.path.exists(INPUT_CSV):
        logging.error(f"Input file {INPUT_CSV} not found.")
        return

    tracker = load_tracker()
    session = requests.Session()

    # Load existing missing words to avoid duplicates
    missing_set = set()
    if os.path.exists(MISSING_CSV):
        with open(MISSING_CSV, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    missing_set.add(row[0])  # word is first column

    # Load input words, handling CSV with comment line
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        lines = f.readlines()
    # Find the header line containing 'lemme'
    header_idx = None
    for i, line in enumerate(lines):
        if 'lemme' in line:
            header_idx = i
            break
    if header_idx is None:
        # Fallback to second line
        if len(lines) > 1:
            header_idx = 1
        else:
            logging.error("Input CSV does not have enough lines.")
            return
    header = lines[header_idx].strip().split(',')
    data_lines = lines[header_idx + 1:]
    from io import StringIO
    reader = csv.DictReader(StringIO(''.join(data_lines)), fieldnames=header)
    words = [row for row in reader if row.get('lemme', '').strip()]
    logging.info(f"Loaded {len(words)} words from input CSV.")

    missing_streak = 0

    for row in words:
        word = row.get('word', row.get('lemme', '')).strip()

        if not word:
            continue

        # skip if already scraped
        if word in tracker and tracker[word]['status'] == 'done':
            continue

        scraped = scrape_word(word, session)
        timestamp = datetime.now().isoformat(timespec='seconds')

        if scraped and scraped['gender_or_group'] and scraped['pos'] != 'other':
            # Success
            pos = scraped['pos']
            tracker[word] = {
                'word': word,
                'pos': pos,
                'status': 'done',
                'gender_or_group': scraped['gender_or_group'],
                'timestamp': timestamp
            }
            append_csv(GOOD_CSV, ['word','pos','gender_or_group'], scraped)
            missing_streak = 0
            logging.info(f"[OK] {word} ({pos}) → {scraped['gender_or_group']}")
        else:
            # Missing or insufficient
            pos = scraped['pos'] if scraped else 'unknown'
            tracker[word] = {
                'word': word,
                'pos': pos,
                'status': 'missing',
                'gender_or_group': '',
                'timestamp': timestamp
            }
            if word not in missing_set:
                append_csv(MISSING_CSV, ['word','pos'], {'word': word, 'pos': pos})
                missing_set.add(word)
            missing_streak += 1
            logging.warning(f"[MISSING] {word} ({pos}) ({missing_streak} in a row)")

            # Auto-pause safeguard
            if missing_streak >= AUTO_PAUSE_LIMIT:
                logging.warning(f"\n⚠️ Auto-pause triggered after {missing_streak} missing results.")
                logging.warning("Check network or site structure before resuming.")
                break

        # save progress every iteration
        save_tracker(tracker)

        # courteous delay
        time.sleep(SLEEP_TIME)

    logging.info("\n✅ Scraping finished or paused.")
    logging.info(f"Tracker saved to {TRACKER_CSV}")

if __name__ == '__main__':
    main()
