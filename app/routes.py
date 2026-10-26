"""FR-01: Authentication and FR-07: User Management."""

import sqlite3
from functools import wraps

from flask import Blueprint, jsonify, request, session, g
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from .db import get_db

api = Blueprint("api", __name__)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@api.get("/health")
def health():
    """Check whether the API is running."""
    return jsonify(status="ok"), 200


# --------------------------------------------------
# FR-01: AUTHENTICATION AND ROLE MANAGEMENT
# --------------------------------------------------

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
                    SELECT id, username, role, active
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()

            except sqlite3.Error:
                return jsonify(
                    error="Database temporarily unavailable"
                ), 503

            if user is None or not user["active"]:
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

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]

    return jsonify(
        message="Login successful",
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    ), 200


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


@api.get("/admin/check")
@login_required(["admin"])
def admin_check():
    """Check administrator access."""

    return jsonify(
        message="Administrator access granted"
    ), 200


@api.get("/teacher/check")
@login_required(["teacher"])
def teacher_check():
    """Check teacher access."""

    return jsonify(
        message="Teacher access granted"
    ), 200


@api.get("/student/check")
@login_required(["student"])
def student_check():
    """Check student access."""

    return jsonify(
        message="Student access granted"
    ), 200


# --------------------------------------------------
# FR-07: USER MANAGEMENT
# --------------------------------------------------

@api.post("/users")
@login_required(["admin"])
def create_user():
    """
    Create a student or teacher account.

    Expected JSON:
    {
        "username": "student01",
        "password": "StrongPassword123",
        "role": "student"
    }
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="JSON request body required"
        ), 400

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if (
        not isinstance(username, str)
        or not username.strip()
        or not isinstance(password, str)
        or not password
        or role not in ("student", "teacher")
    ):
        return jsonify(
            error="Username, password, and valid role are required"
        ), 400

    try:
        db = get_db()

        password_hash = generate_password_hash(password)

        cursor = db.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (username.strip(), password_hash, role)
        )

        db.commit()

        return jsonify(
            message="User created successfully",
            user={
                "id": cursor.lastrowid,
                "username": username.strip(),
                "role": role,
                "active": 1
            }
        ), 201

    except sqlite3.IntegrityError:
        get_db().rollback()

        return jsonify(
            error="Username already exists"
        ), 409

    except sqlite3.Error:
        get_db().rollback()

        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.get("/users")
@login_required(["admin"])
def list_users():
    """List student and teacher accounts."""

    try:
        users = get_db().execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE role IN ('student', 'teacher')
            ORDER BY id
            """
        ).fetchall()

        return jsonify(
            users=[
                {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "active": user["active"]
                }
                for user in users
            ]
        ), 200

    except sqlite3.Error:
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.put("/users/<int:user_id>")
@login_required(["admin"])
def update_user(user_id):
    """
    Update a student or teacher's username or role.

    Example JSON:
    {
        "username": "student02",
        "role": "student"
    }
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify(
            error="JSON request body required"
        ), 400

    allowed_fields = {"username", "role"}

    if not set(data).issubset(allowed_fields):
        return jsonify(
            error="Only username and role can be updated"
        ), 400

    username = data.get("username")
    role = data.get("role")

    if "username" in data and (
        not isinstance(username, str)
        or not username.strip()
    ):
        return jsonify(
            error="Username cannot be empty"
        ), 400

    if "role" in data and role not in (
        "student",
        "teacher"
    ):
        return jsonify(
            error="Role must be student or teacher"
        ), 400

    try:
        db = get_db()

        user = db.execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify(
                error="User not found"
            ), 404

        if user["role"] not in ("student", "teacher"):
            return jsonify(
                error="Only student and teacher accounts can be updated"
            ), 400

        new_username = (
            username.strip()
            if "username" in data
            else user["username"]
        )

        new_role = (
            role
            if "role" in data
            else user["role"]
        )

        db.execute(
            """
            UPDATE users
            SET username = ?, role = ?
            WHERE id = ?
            """,
            (new_username, new_role, user_id)
        )

        db.commit()

        return jsonify(
            message="User updated successfully",
            user={
                "id": user_id,
                "username": new_username,
                "role": new_role,
                "active": user["active"]
            }
        ), 200

    except sqlite3.IntegrityError:
        get_db().rollback()

        return jsonify(
            error="Username already exists"
        ), 409

    except sqlite3.Error:
        get_db().rollback()

        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.patch("/users/<int:user_id>/deactivate")
@login_required(["admin"])
def deactivate_user(user_id):
    """
    Deactivate a student or teacher without deleting records.
    """

    try:
        db = get_db()

        user = db.execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify(
                error="User not found"
            ), 404

        if user["role"] not in ("student", "teacher"):
            return jsonify(
                error="Only student and teacher accounts can be deactivated"
            ), 400

        if not user["active"]:
            return jsonify(
                error="User is already inactive"
            ), 409

        db.execute(
            """
            UPDATE users
            SET active = 0
            WHERE id = ?
            """,
            (user_id,)
        )

        db.commit()

        return jsonify(
            message="User deactivated successfully",
            user={
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "active": 0
            }
        ), 200

    except sqlite3.Error:
        get_db().rollback()

        return jsonify(
            error="Database temporarily unavailable"
        ), 503