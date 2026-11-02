"""FR-07 user management: create, list, view, update, deactivate and
activate user accounts (administrators only).
"""

import sqlite3

from flask import g, jsonify, request
from werkzeug.security import generate_password_hash

from ..auth import login_required, start_user_session
from ..db import get_db
from ..validation import VALID_ROLES
from .blueprint import api

# =====================================================================
# FR-07: User Management
# =====================================================================

@api.post("/users")
@login_required(["admin"])
def create_user():
    """
    Create an admin, teacher, or student account.

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
        or role not in VALID_ROLES
    ):
        return jsonify(
            error="Username, password, and valid role are required"
        ), 400

    active = 1
    if "active" in data:
        raw_active = data["active"]
        if isinstance(raw_active, bool):
            active = 1 if raw_active else 0
        elif isinstance(raw_active, int) and raw_active in (0, 1):
            active = raw_active
        else:
            return jsonify(error="Active status must be a boolean or 0/1"), 400

    try:
        db = get_db()
        password_hash = generate_password_hash(password)

        cursor = db.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, ?)
            """,
            (username.strip(), password_hash, role, active),
        )
        db.commit()

        return jsonify(
            message="User created successfully",
            user={
                "id": cursor.lastrowid,
                "username": username.strip(),
                "role": role,
                "active": active,
            },
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
    """List user accounts with optional role and active filtering."""
    db = get_db()
    role = request.args.get("role")
    active = request.args.get("active")

    query = "SELECT id, username, role, active FROM users"
    conditions = []
    params = []

    if role:
        cleaned_role = role.strip().lower()
        if cleaned_role not in VALID_ROLES:
            return jsonify(error="Invalid role filter"), 400
        conditions.append("role = ?")
        params.append(cleaned_role)

    if active is not None:
        if active.lower() in ("true", "1"):
            conditions.append("active = 1")
        elif active.lower() in ("false", "0"):
            conditions.append("active = 0")
        else:
            return jsonify(error="Invalid active filter"), 400

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id"

    try:
        users = db.execute(query, params).fetchall()
        return jsonify(
            users=[
                {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "active": user["active"],
                }
                for user in users
            ]
        ), 200

    except sqlite3.Error:
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.get("/users/<int:user_id>")
@login_required(["admin"])
def get_user(user_id):
    """Retrieve details for a specific user."""
    try:
        user = get_db().execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            return jsonify(error="User not found"), 404

        return jsonify(
            user={
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "active": user["active"],
            }
        ), 200

    except sqlite3.Error:
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.route("/users/<int:user_id>", methods=["PUT", "PATCH"])
@login_required(["admin"])
def update_user(user_id):
    """
    Update a user's information (username, role, password, active).
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify(
            error="JSON request body required"
        ), 400

    allowed_fields = {"username", "role", "password", "active"}

    if not set(data).issubset(allowed_fields):
        return jsonify(
            error="Only valid user fields can be updated"
        ), 400

    username = data.get("username")
    role = data.get("role")
    password = data.get("password")
    active = data.get("active")

    if "username" in data and (
        not isinstance(username, str)
        or not username.strip()
    ):
        return jsonify(
            error="Username cannot be empty"
        ), 400

    if "role" in data and role not in VALID_ROLES:
        return jsonify(
            error="Role must be admin, teacher, or student"
        ), 400

    if "password" in data and (
        not isinstance(password, str)
        or not password
    ):
        return jsonify(
            error="Password cannot be empty"
        ), 400

    if "active" in data:
        if isinstance(active, bool):
            active = 1 if active else 0
        elif isinstance(active, int) and active in (0, 1):
            pass
        else:
            return jsonify(error="Active status must be a boolean or 0/1"), 400

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

        new_active = (
            active
            if "active" in data
            else user["active"]
        )

        if "password" in data:
            new_password_hash = generate_password_hash(password)
            db.execute(
                """
                UPDATE users
                SET username = ?, role = ?, active = ?, password_hash = ?
                WHERE id = ?
                """,
                (new_username, new_role, new_active, new_password_hash, user_id),
            )

            # An admin editing their own account stays signed in.
            if user_id == g.current_user["id"]:
                start_user_session(user_id, new_password_hash)
        else:
            db.execute(
                """
                UPDATE users
                SET username = ?, role = ?, active = ?
                WHERE id = ?
                """,
                (new_username, new_role, new_active, user_id),
            )

        db.commit()

        return jsonify(
            message="User updated successfully",
            user={
                "id": user_id,
                "username": new_username,
                "role": new_role,
                "active": new_active,
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


@api.route("/users/<int:user_id>/deactivate", methods=["POST", "PATCH"])
@login_required(["admin"])
def deactivate_user(user_id):
    """
    Deactivate a user account without deleting records.
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
                "active": 0,
            }
        ), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.route("/users/<int:user_id>/activate", methods=["POST", "PATCH"])
@login_required(["admin"])
def activate_user(user_id):
    """
    Activate a user account.
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

        if user["active"]:
            return jsonify(
                error="User is already active"
            ), 409

        db.execute(
            """
            UPDATE users
            SET active = 1
            WHERE id = ?
            """,
            (user_id,)
        )
        db.commit()

        return jsonify(
            message="User activated successfully",
            user={
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "active": 1,
            }
        ), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503
