"""Flask application entry point."""

from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS

from api import register_blueprints
from config import Settings


def create_app(overrides: Optional[dict] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(Settings.from_environment().to_flask_config())
    CORS(app)
    if overrides:
        app.config.update(overrides)
    register_blueprints(app)
    app.add_url_rule("/health", "health_check", health_check, methods=["GET"])
    return app


def health_check():
    return jsonify({"status": "ok"})


app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
