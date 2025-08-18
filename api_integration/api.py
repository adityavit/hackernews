import os
from flask import Flask, jsonify, request
try:
    from flask_cors import CORS
except Exception:  # pragma: no cover
    CORS = None
from api_integration.scraper import scrape_hacker_news
from api_integration.comment_scraper import fetch_story_comments
from llm_integration.analysis import analyze_comments
from llm_integration.config import env_config, override_config


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


@app.route("/api/stories/<story_id>/comments/summary")
def get_story_comments_summary(story_id: str):
    # Optional fetch parameters for scraping
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

    # Optional analysis overrides
    original_post = request.args.get("original_post")
    ollama_host = request.args.get("ollama_host")
    chat_model = request.args.get("chat_model")
    embed_model = request.args.get("embed_model")
    topk = request.args.get("topk")
    max_summary_comments = request.args.get("max_summary_comments")
    weights_str = request.args.get("weights")  # e.g. "0.45,0.45,0.10"

    # Fetch comments first
    comments = fetch_story_comments(story_id, max_depth=depth_val, limit=limit_val)

    # Build config
    base_cfg = env_config()
    try:
        topk_val = int(topk) if topk else None
    except ValueError:
        topk_val = None
    try:
        msc_val = int(max_summary_comments) if max_summary_comments else None
    except ValueError:
        msc_val = None

    weight_tuple = None
    if weights_str:
        try:
            parts = [float(x.strip()) for x in weights_str.split(",")]
            weight_tuple = (parts + [0.0, 0.0, 0.0])[:3]
        except Exception:
            weight_tuple = None

    cfg = override_config(
        base_cfg,
        ollama_host=ollama_host,
        chat_model=chat_model,
        embed_model=embed_model,
        topk=topk_val,
        max_summary_comments=msc_val,
        weights=weight_tuple,
    )

    result = analyze_comments(comments, original_post, cfg)
    return jsonify(result)


if __name__ == "__main__":
    main()


