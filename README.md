# Hacker News Letter

A project to create a daily newsletter of the top posts from Hacker News.

## Features

*   Fetch the top posts from Hacker News from the last 24 hours.
*   Filter and rank posts based on popularity (score, comments) and importance.
*   Generate a static HTML webpage for the newsletter.
*   Create a mailing list of the top posts.
*   Email the newsletter daily.

## Project Plan

### Phase 1: Core Functionality

1.  **Hacker News API Integration:**
    *   Fetch top story IDs from the Hacker News API.
    *   For each story, fetch its details (title, URL, score, author, number of comments).
2.  **Post Filtering and Ranking:**
    *   Implement a scoring algorithm to rank stories based on a combination of votes and comments.
    *   Filter stories to include only those from the last 24 hours.
    *   Select the top N stories for the newsletter.
3.  **HTML Newsletter Generation:**
    *   Create a simple, clean HTML template for the newsletter.
    *   Populate the template with the ranked stories.
    *   Save the generated newsletter as an HTML file.

### Phase 2: Automation and Delivery

1.  **Web Page for the Newsletter:**
    *   Serve the generated HTML file using a simple web server.
2.  **Emailing:**
    *   Integrate with an email service provider (e.g., SendGrid, Mailgun).
    *   Create a script to send the HTML newsletter to a predefined list of recipients.
3.  **Automation:**
    *   Set up a daily cron job or a scheduler (like GitHub Actions) to run the entire process automatically.

## Technology Stack (Proposed)

*   **Backend:** Python
    *   `requests` for making API calls.
    *   `Jinja2` for HTML templating.
*   **Frontend:** HTML & CSS for the newsletter template.
*   **Automation:** GitHub Actions or a system cron job.
