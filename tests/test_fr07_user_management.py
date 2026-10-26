"""Tests for FR-07 user management endpoints."""

from uuid import uuid4

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

TEST_PASSWORD = "TestPassword-123!"


def _unique_username(prefix="fr07"):
    return f"{prefix}_{uuid4().hex[:12]}"


def _insert_user(client, role, username=None, password=TEST_PASSWORD, active=1):
    username = username or _unique_username(role)
    password_hash = generate_password_hash(password)

    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, ?)
            """,
            (username, password_hash, role, active),
        )
        db.commit()
        return cursor.lastrowid


def _authenticate_session(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id


def _admin_client(client):
    admin_id = _insert_user(client, "admin")
    _authenticate_session(client, admin_id)
    return admin_id


def _read_user(client, user_id):
    with client.application.app_context():
        row = get_db().execute(
            """
            SELECT id, username, password_hash, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        return dict(row) if row is not None else None


@pytest.mark.parametrize("role", ["student", "teacher"])
def test_admin_can_create_student_or_teacher(client, role):
    _admin_client(client)
    username = _unique_username(role)

    response = client.post(
        "/api/users",
        json={
            "username": username,
            "password": TEST_PASSWORD,
            "role": role,
        },
    )

    assert response.status_code == 201


def test_admin_can_list_users(client):
    _admin_client(client)
    _insert_user(client, "student")
    _insert_user(client, "teacher")

    response = client.get("/api/users")
    assert response.status_code == 200


def test_admin_can_update_username_or_role(client):
    _admin_client(client)
    user_id = _insert_user(client, "student")

    response = client.put(
        f"/api/users/{user_id}",
        json={"username": _unique_username("updated")},
    )

    assert response.status_code == 200


def test_admin_can_deactivate_user(client):
    _admin_client(client)
    user_id = _insert_user(client, "student")

    response = client.patch(f"/api/users/{user_id}/deactivate")
    assert response.status_code == 200


def test_duplicate_username_is_rejected(client):
    _admin_client(client)
    username = _unique_username("duplicate")
    _insert_user(client, "student", username=username)

    response = client.post(
        "/api/users",
        json={
            "username": username,
            "password": TEST_PASSWORD,
            "role": "teacher",
        },
    )

    assert response.status_code == 409