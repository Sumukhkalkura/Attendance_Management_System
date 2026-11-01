"""Test helper for signing a user in without going through /api/login."""

from app.db import get_db
from app.routes import _password_fingerprint


def plant_session(client, user_id):
    """Give the client the session a real login would issue for user_id."""
    with client.application.app_context():
        user = get_db().execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        fingerprint = _password_fingerprint(user["password_hash"])

    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id
        session["password_fingerprint"] = fingerprint
