"""FR-01 / FR-13 authentication routes: login, current user, password change,
and the admin/teacher/student role-check endpoints.

Logout (FR-15) lives in ``session_routes`` because it is registered later
in the original URL order. Session helpers come from ``app.auth``.
"""

import sqlite3

from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..auth import login_required, start_user_session
from ..db import get_db
from ..validation import _is_encodable, MIN_PASSWORD_LENGTH
from .blueprint import api

# FR-01: User Login

@api.post("/login")
def login():
    """Authenticate an administrator, teacher, or student."""

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="JSON request body required"
        ), 400

    username = data.get("username")
    password = data.get("password")

    if (
        not isinstance(username, str)
        or not username.strip()
        or not isinstance(password, str)
        or not password
    ):
        return jsonify(
            error="Username and password are required"
        ), 400

    try:
        user = get_db().execute(
            """
            SELECT id, username, password_hash, role, active
            FROM users
            WHERE username = ?
            """,
            (username.strip(),)
        ).fetchone()

        if (
            user is None
            or not user["active"]
            or not check_password_hash(
                user["password_hash"], password
            )
        ):
            return jsonify(
                error="Invalid username or password"
            ), 401

    except (sqlite3.Error, ValueError):
        return jsonify(
            error="Authentication temporarily unavailable"
        ), 503

    start_user_session(user["id"], user["password_hash"])

    return jsonify(
        message="Login successful",
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    ), 200


# FR-01: Get Current User

@api.get("/me")
@login_required()
def current_user():
    """Return the logged-in user's details."""

    user = g.current_user

    return jsonify(
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    ), 200


# FR-13: Change Own Password

@api.post("/me/password")
@login_required()
def change_password():
    """
    Change the logged-in user's own password.

    The account always comes from the session; the request cannot name one.

    Expected JSON:
    {
        "current_password": "OldPassword123",
        "new_password": "NewPassword123"
    }

    An incorrect current password returns 400, not 401: the user is still
    authenticated, and the frontend treats 401 as an expired session.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="JSON request body required"
        ), 400

    if not set(data).issubset({"current_password", "new_password"}):
        return jsonify(
            error="Only current_password and new_password are accepted"
        ), 400

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if (
        not isinstance(current_password, str)
        or not current_password
        or not isinstance(new_password, str)
        or not new_password
    ):
        return jsonify(
            error="Current password and new password are required"
        ), 400

    if (
        len(new_password) < MIN_PASSWORD_LENGTH
        or not _is_encodable(new_password)
    ):
        return jsonify(
            error=(
                "New password must be a valid password of at least "
                f"{MIN_PASSWORD_LENGTH} characters"
            )
        ), 400

    user = g.current_user

    try:
        if (
            not _is_encodable(current_password)
            or not check_password_hash(
                user["password_hash"], current_password
            )
        ):
            return jsonify(
                error="Current password is incorrect"
            ), 400

        if check_password_hash(user["password_hash"], new_password):
            return jsonify(
                error="New password must be different from the current password"
            ), 400

        new_password_hash = generate_password_hash(new_password)

        db = get_db()
        db.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (new_password_hash, user["id"]),
        )
        db.commit()

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503

    except ValueError:
        return jsonify(
            error="Password change temporarily unavailable"
        ), 503

    # Every other session for this account now fails its fingerprint check;
    # this one is reissued so the user stays signed in.
    start_user_session(user["id"], new_password_hash)

    return jsonify(
        message="Password changed successfully"
    ), 200


# FR-01: Admin Authorization

@api.get("/admin/check")
@login_required(["admin"])
def admin_check():
    return jsonify(
        message="Administrator access granted"
    ), 200


# FR-01: Teacher Authorization

@api.get("/teacher/check")
@login_required(["teacher"])
def teacher_check():
    return jsonify(
        message="Teacher access granted"
    ), 200


# FR-01: Student Authorization

@api.get("/student/check")
@login_required(["student"])
def student_check():
    return jsonify(
        message="Student access granted"
    ), 200
