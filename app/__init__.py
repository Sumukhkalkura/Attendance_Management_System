
"""Attendance Management System application factory."""

import os
import secrets
from datetime import timedelta

from flask import Flask, jsonify, request

from .db import init_db
from .pages import pages
from .routes import api

STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


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

        # NFR-01: Security response headers
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        return response
    
    return app
