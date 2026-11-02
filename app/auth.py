"""Shared authentication and session helpers.

Responsibilities:

- FR-13: bind a login session to the account's current password, so that
  changing the password invalidates every other existing session
  (``_password_fingerprint``, ``start_user_session``,
  ``session_matches_password``).
- FR-01: role-based access control for API views (``login_required``).

These helpers are used by the API blueprint (``app.routes``) and the frontend
page blueprint (``app.pages``). They contain no routes of their own.
``app.routes`` re-exports every name defined here for backward compatibility.
"""

import hashlib
import hmac
import sqlite3
from functools import wraps

from flask import current_app, g, jsonify, session

from .db import get_db


# =====================================================================
# FR-13: Session binding to the account password
# =====================================================================

def _password_fingerprint(password_hash):
    """
    Derive a value that changes whenever the stored password hash changes.

    Flask session cookies are signed but readable by the client, so the hash
    itself must never be placed in the session.
    """
    return hmac.new(
        str(current_app.secret_key).encode(),
        password_hash.encode(),
        hashlib.sha256,
    ).hexdigest()


def start_user_session(user_id, password_hash):
    """Start a fresh login session bound to the current password."""
    session.clear()
    session.permanent = True
    session["user_id"] = user_id
    session["password_fingerprint"] = _password_fingerprint(password_hash)


def session_matches_password(password_hash):
    """
    Return False unless the session was issued for the current password.

    A session with no fingerprint is rejected: it cannot be shown to postdate
    the last password change, and activity would keep renewing it indefinitely.
    """
    fingerprint = session.get("password_fingerprint")

    return isinstance(fingerprint, str) and hmac.compare_digest(
        fingerprint.encode(), _password_fingerprint(password_hash).encode()
    )


# =====================================================================
# FR-01: Role-Based Access Control
# =====================================================================

def login_required(allowed_roles=None):
    """Allow access only to authenticated, authorized users."""

    def decorator(view_function):

        @wraps(view_function)
        def wrapped(*args, **kwargs):

            user_id = session.get("user_id")

            if user_id is None:
                return jsonify(
                    error="Authentication required"
                ), 401

            try:
                user = get_db().execute(
                    """
                    SELECT id, username, password_hash, role, active
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()

            except sqlite3.Error:
                return jsonify(
                    error="Database temporarily unavailable"
                ), 503

            if (
                user is None
                or not user["active"]
                or not session_matches_password(user["password_hash"])
            ):
                session.clear()
                return jsonify(
                    error="Authentication required"
                ), 401

            if (
                allowed_roles is not None
                and user["role"] not in allowed_roles
            ):
                return jsonify(
                    error="Access denied"
                ), 403

            g.current_user = user

            return view_function(*args, **kwargs)

        return wrapped

    return decorator
