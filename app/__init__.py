
"""Attendance Management System application factory."""

import os
import secrets
from datetime import timedelta

from flask import Flask, jsonify

from .db import init_db
from .routes import api


def create_app(test_config=None):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # FR-01: Authentication and session configuration
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
        DATABASE="attendance.db",
        TESTING=False,

        # Automatically expire an inactive login session
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),

        # Prevent JavaScript from reading the session cookie
        SESSION_COOKIE_HTTPONLY=True,

        # Restrict cross-site cookie transmission
        SESSION_COOKIE_SAMESITE="Lax",

        # Set FLASK_COOKIE_SECURE=1 when using HTTPS in deployment
        SESSION_COOKIE_SECURE=(
            os.environ.get("FLASK_COOKIE_SECURE") == "1"
        ),
    )

    # Allow tests to override configuration
    if test_config:
        app.config.update(test_config)

    # Initialize database
    init_db(app)

    # Register REST API
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def home():
        return jsonify(
            application="Attendance Management System",
            status="starter",
            note="Sprint 1 features under development",
        )

    return app
