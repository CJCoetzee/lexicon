"""Flask application factory for Lexicon.

The factory pattern lets us build separate app instances for development,
production, and tests without polluting global state.
"""
from __future__ import annotations

import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config import config
from routes.documents import documents_bp
from routes.health import health_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.max_upload_bytes

    logging.basicConfig(
        level=logging.DEBUG if config.flask_debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    CORS(app, resources={r"/api/*": {"origins": config.cors_origins}})

    app.register_blueprint(health_bp)
    app.register_blueprint(documents_bp, url_prefix="/api")

    @app.errorhandler(413)
    def too_large(_err):
        return (
            jsonify(
                {
                    "error": "file_too_large",
                    "message": (
                        f"Uploaded file exceeds the maximum size of "
                        f"{config.max_upload_bytes} bytes."
                    ),
                }
            ),
            413,
        )

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"error": "not_found"}), 404

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=config.flask_debug)
