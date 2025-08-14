import os
from flask import Flask, jsonify, request
try:
    from flask_cors import CORS
except Exception:  # pragma: no cover
    CORS = None
from api_integration.scraper import scrape_hacker_news
from api_integration.comment_scraper import fetch_story_comments


app = Flask(__name__)

# Configure CORS to allow the UI origin (UI_PORT) to access the API (API_PORT)
if CORS is not None:
    ui_port = os.getenv("UI_PORT", "8081")
    # Allow both localhost and 127.0.0.1 for convenience
    allowed_origins = [
        f"http://127.0.0.1:{ui_port}",
        f"http://localhost:{ui_port}",
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Accept"],
        methods=["GET", "OPTIONS"],
        supports_credentials=False,
    )
else:
    # Fallback: manually set CORS headers if flask-cors is unavailable
    ui_port = os.getenv("UI_PORT", "8081")
    allowed_origins = {f"http://127.0.0.1:{ui_port}", f"http://localhost:{ui_port}"}

    @app.after_request
    def add_cors_headers(response):  # type: ignore[no-redef]
        origin = request.headers.get("Origin", "")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response


@app.route("/api/top-stories")
def get_top_stories():
    stories = scrape_hacker_news()
    return jsonify(stories)


def main():
    app.run(debug=True)


@app.route("/api/stories/<story_id>/comments")
def get_story_comments(story_id: str):
    limit_param = request.args.get("limit")
    depth_param = request.args.get("max_depth")
    try:
        limit_val = int(limit_param) if limit_param else None
    except ValueError:
        limit_val = None
    try:
        depth_val = int(depth_param) if depth_param else 2
    except ValueError:
        depth_val = 2

    comments = fetch_story_comments(story_id, max_depth=depth_val, limit=limit_val)
    return jsonify(comments)


if __name__ == "__main__":
    main()


