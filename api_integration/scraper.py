import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask, jsonify

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

    value = int(parts[0])
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
    print("Scraping Hacker News...")
    response = requests.get(URL)

    if response.status_code != 200:
        print(f"Error: Failed to fetch the page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    stories = []
    story_elements = soup.find_all('tr', class_='athing')

    for story_element in story_elements:
        title_element = story_element.find('span', class_='titleline')
        if not title_element:
            continue

        title_anchor = title_element.find('a')
        if not title_anchor:
            continue

        title = title_anchor.text
        url = title_anchor['href']
        story_id = story_element['id']

        # Get the metadata from the next row
        metadata_element = story_element.find_next_sibling('tr')
        if not metadata_element:
            continue

        subtext = metadata_element.find('td', class_='subtext')
        if not subtext:
            continue

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

    print(f"Found {len(stories)} stories from the last 24 hours.")
    return stories

@app.route('/api/top-stories')
def get_top_stories():
    stories = scrape_hacker_news()
    return jsonify(stories)

if __name__ == "__main__":
    app.run(debug=True)
