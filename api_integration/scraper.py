import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL to scrape
URL = "https://news.ycombinator.com/"

app = Flask(__name__)

def parse_age_to_timestamp(age_string):
    """
    Parses the age string (e.g., '2 hours ago') and returns a timestamp.
    """
    if not age_string:
        return None

    parts = age_string.split()
    if len(parts) < 3:
        return None

    try:
        value = int(parts[0])
    except ValueError:
        return None
    unit = parts[1]

    now = datetime.now()

    if "minute" in unit:
        return now - timedelta(minutes=value)
    elif "hour" in unit:
        return now - timedelta(hours=value)
    elif "day" in unit:
        return now - timedelta(days=value)
    else:
        return None

def scrape_hacker_news():
    """
    Scrapes the Hacker News website to get the top stories from the last 24 hours.
    """
    logging.info("Scraping Hacker News...")
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the page: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    stories = []
    story_elements = soup.find_all('tr', class_='athing')

    for story_element in story_elements:
        try:
            title_element = story_element.find('span', class_='titleline')
            title_anchor = title_element.find('a')

            title = title_anchor.text
            url = title_anchor['href']
            story_id = story_element['id']

            # Get the metadata from the next row
            metadata_element = story_element.find_next_sibling('tr')
            subtext = metadata_element.find('td', class_='subtext')

            score_element = subtext.find('span', class_='score')
            score = int(score_element.text.split()[0]) if score_element else 0

            user_element = subtext.find('a', class_='hnuser')
            user = user_element.text if user_element else None

            age_element = subtext.find('span', class_='age')
            age_string = age_element.text if age_element else None
            timestamp = parse_age_to_timestamp(age_string)

            # Filter stories older than 24 hours
            if timestamp and (datetime.now() - timestamp) > timedelta(days=1):
                continue

            comments_element = subtext.find_all('a')[-1]
            comments_text = comments_element.text
            if 'comment' in comments_text:
                comments = int(comments_text.split()[0])
            else:
                comments = 0
            
            stories.append({
                'id': story_id,
                'title': title,
                'url': url,
                'score': score,
                'user': user,
                'age': age_string,
                'timestamp': timestamp.isoformat() if timestamp else None,
                'comments': comments
            })
        except (AttributeError, TypeError, ValueError) as e:
            logging.warning(f"Could not parse a story: {e}. Skipping...")
            continue

    logging.info(f"Found {len(stories)} stories from the last 24 hours.")
    return stories

@app.route('/api/top-stories')
def get_top_stories():
    stories = scrape_hacker_news()
    return jsonify(stories)

if __name__ == "__main__":
    app.run(debug=True)
