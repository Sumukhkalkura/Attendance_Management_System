
"""Attendance Management System application factory."""

import os
import sqlite3
import secrets
from datetime import timedelta

from flask import Flask, jsonify, request

from .db import init_db
from .pages import pages
from .api import api as api_blueprint

STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# NFR-05: Standard types for scripts and styles. Flask otherwise takes them
# from the host's MIME table (/etc/mime.types, the Windows registry), which
# differs between machines; with "nosniff" a browser refuses a script or
# stylesheet served with the wrong type.
STATIC_MIME_TYPES = {".js": "text/javascript", ".css": "text/css"}


def create_app(test_config=None):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # FR-01: Authentication and session configuration
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
        DATABASE="attendance.db",
        TESTING=False,
        DEFAULT_ATTENDANCE_THRESHOLD=75.0,

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

    # FR-11: Load persisted settings if available in the database
    with app.app_context():
        try:
            conn = sqlite3.connect(app.config["DATABASE"])
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'attendance_threshold'"
            ).fetchone()
            if row is not None:
                app.config["DEFAULT_ATTENDANCE_THRESHOLD"] = float(row["value"])
            conn.close()
        except Exception:
            pass

    # Register REST API
    app.register_blueprint(api_blueprint, url_prefix="/api")
    
    # Frontend pages: login and role-based dashboards
    app.register_blueprint(pages)

    # NFR-01: CSRF protection for cookie-authenticated API calls.
    # Browsers attach an Origin (or Referer) header to cross-site requests;
    # reject state-changing requests that come from another site.
    @app.before_request
    def reject_cross_site_requests():
        if request.method not in STATE_CHANGING_METHODS:
            return None

        source = request.headers.get("Origin") or request.headers.get("Referer")

        if source is None:
            return None

        own_origin = request.host_url.rstrip("/")

        if source != own_origin and not source.startswith(own_origin + "/"):
            return jsonify(error="Cross-site request rejected"), 403

        return None

    @app.get("/")
    def home():
        return jsonify(
            application="Attendance Management System",
            status="starter",
            note="Sprint 1 features under development",
        )

    # NFR-01 & NFR-05: Security and browser compatibility response headers
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        # NFR-05: Standards mode directive for Microsoft Edge and Chromium
        response.headers["X-UA-Compatible"] = "IE=edge"
        # NFR-05: Same script and style types on every host
        if request.endpoint == "static":
            mimetype = STATIC_MIME_TYPES.get(os.path.splitext(request.path)[1].lower())
            if mimetype:
                response.mimetype = mimetype
        return response
    
    return app
