
"""Automated tests for FR-01: Authentication and Role Management."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated application and database for FR-01 tests."""
    database_path = tmp_path / "fr01_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(database_path),
        "SECRET_KEY": "fr01-test-secret",
    })

    users = [
        ("admin1", "admin123", "admin", 1),
        ("teacher1", "teacher123", "teacher", 1),
        ("student1", "student123", "student", 1),
        ("inactive1", "inactive123", "student", 0),
    ]

    with sqlite3.connect(database_path) as db:
        for username, password, role, active in users:
            db.execute(
                """
                INSERT INTO users
                    (username, password_hash, role, active)
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    generate_password_hash(password),
                    role,
                    active,
                ),
            )
        db.commit()

    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password):
    """Submit login credentials."""
    return client.post(
        "/api/login",
        json={
            "username": username,
            "password": password,
        },
    )


# Successful authentication for all three roles

@pytest.mark.parametrize(
    "username,password,role",
    [
        ("admin1", "admin123", "admin"),
        ("teacher1", "teacher123", "teacher"),
        ("student1", "student123", "student"),
    ],
)
def test_successful_login(client, username, password, role):
    response = login(client, username, password)

    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful"
    assert response.get_json()["user"]["username"] == username
    assert response.get_json()["user"]["role"] == role


# Invalid login attempts

def test_wrong_password(client):
    response = login(client, "admin1", "wrongpassword")

    assert response.status_code == 401
    assert response.get_json()["error"] == (
        "Invalid username or password"
    )


def test_unknown_username(client):
    response = login(client, "unknown", "password123")

    assert response.status_code == 401


def test_inactive_account_cannot_login(client):
    response = login(client, "inactive1", "inactive123")

    assert response.status_code == 401


def test_missing_credentials(client):
    response = client.post("/api/login", json={})

    assert response.status_code == 400


def test_invalid_json_body(client):
    response = client.post(
        "/api/login",
        data="not valid json",
        content_type="application/json",
    )

    assert response.status_code == 400


# Authenticated user information

def test_authenticated_user_details(client):
    login(client, "student1", "student123")

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == "student"


def test_unauthenticated_user_details(client):
    response = client.get("/api/me")

    assert response.status_code == 401


# Role-based access control

@pytest.mark.parametrize(
    "username,password,allowed_endpoint",
    [
        ("admin1", "admin123", "/api/admin/check"),
        ("teacher1", "teacher123", "/api/teacher/check"),
        ("student1", "student123", "/api/student/check"),
    ],
)
def test_correct_role_access(
    client, username, password, allowed_endpoint
):
    login(client, username, password)

    response = client.get(allowed_endpoint)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "username,password,denied_endpoint",
    [
        ("admin1", "admin123", "/api/teacher/check"),
        ("admin1", "admin123", "/api/student/check"),
        ("teacher1", "teacher123", "/api/admin/check"),
        ("teacher1", "teacher123", "/api/student/check"),
        ("student1", "student123", "/api/admin/check"),
        ("student1", "student123", "/api/teacher/check"),
    ],
)
def test_wrong_role_denied(
    client, username, password, denied_endpoint
):
    login(client, username, password)

    response = client.get(denied_endpoint)

    assert response.status_code == 403


# Session handling

def test_session_created_after_login(client):
    login(client, "admin1", "admin123")

    with client.session_transaction() as session:
        assert "user_id" in session
        assert session.permanent is True


def test_session_replaced_when_different_user_logs_in(client):
    login(client, "admin1", "admin123")
    login(client, "student1", "student123")

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == "student"


def test_inactive_user_loses_existing_access(client, app):
    login(client, "student1", "student123")

    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute(
            "UPDATE users SET active = 0 WHERE username = ?",
            ("student1",),
        )
        db.commit()

    response = client.get("/api/me")

    assert response.status_code == 401


def test_no_plaintext_password_returned(client):
    response = login(client, "admin1", "admin123")

    assert response.status_code == 200
    assert "password" not in response.get_json()["user"]
    assert "password_hash" not in response.get_json()["user"]

from datetime import datetime, timedelta, timezone
from flask.sessions import SecureCookieSessionInterface