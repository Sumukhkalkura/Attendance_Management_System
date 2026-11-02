"""Shared ``api`` blueprint for every REST endpoint, plus the health check.

Every feature module in ``app.api`` imports ``api`` from here and attaches
its routes to it. The blueprint is registered under ``/api`` by
``app.create_app``, so endpoint names stay ``api.<view function name>``.
"""

from flask import Blueprint, jsonify


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    """Check whether the API is running."""
    return jsonify(status="ok"), 200
