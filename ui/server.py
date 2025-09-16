from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory, Response, abort


BASE_DIR = Path(__file__).resolve().parent
API_DIR = BASE_DIR / "api"
STATIC_DIR = BASE_DIR

# Ensure correct mimetype for .json
mimetypes.add_type("application/json", ".json")


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="",
    )

    @app.route("/")
    def index():
        return send_from_directory(str(STATIC_DIR), "index.html")

    @app.route("/api/top-stories")
    def api_top_stories():
        file_path = API_DIR / "top-stories.json"
        if not file_path.exists():
            abort(404)
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            payload = data
        else:
            payload = {"generated_at": None, "data": data}

        return Response(json.dumps(payload), mimetype="application/json")

    @app.route("/api/<path:subpath>")
    def api_proxy_static(subpath: str):
        # Serve any JSON under ui/api/* with proper headers
        file_path = (API_DIR / subpath).resolve()
        # Ensure path traversal is not allowed
        if not str(file_path).startswith(str(API_DIR.resolve())):
            abort(403)
        if not file_path.exists():
            abort(404)
        if file_path.suffix.lower() == ".json":
            with file_path.open("r", encoding="utf-8") as f:
                return Response(f.read(), mimetype="application/json")
        # Fallback to send_from_directory for other types
        return send_from_directory(str(API_DIR), subpath)

    return app


if __name__ == "__main__":
    port = int(os.getenv("UI_PORT", "8081"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)

