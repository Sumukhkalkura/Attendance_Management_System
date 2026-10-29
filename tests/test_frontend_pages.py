"""Tests for the frontend pages, CSRF origin checks, enrollment listing and
removal, and the demo data seed script."""

import re
import sqlite3
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from app.db import get_db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PROJECT_ROOT / "app" / "templates"


def create_user(client, role, username, active=1):
    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash("Password123"), role, active),
        )
        db.commit()
        return cursor.lastrowid


def login_as(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id


@pytest.fixture
def users(client):
    return {
        role: create_user(client, role, f"page_{role}")
        for role in ("admin", "teacher", "student")
    }


# --------------------------------------------------
# Page routes and role redirects
# --------------------------------------------------

def test_login_page_renders_with_external_assets(client):
    response = client.get("/login")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/static/css/app.css" in html
    assert "/static/js/login.js" in html


@pytest.mark.parametrize("path", ["/dashboard", "/admin", "/teacher", "/student"])
def test_pages_redirect_to_login_when_signed_out(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


@pytest.mark.parametrize("role", ["admin", "teacher", "student"])
def test_dashboard_redirects_to_role_page(client, users, role):
    login_as(client, users[role])

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/{role}")


@pytest.mark.parametrize("role", ["admin", "teacher", "student"])
def test_role_page_renders_for_its_role(client, users, role):
    login_as(client, users[role])

    response = client.get(f"/{role}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f"page_{role}" in html
    assert f"/static/js/{role}.js" in html


@pytest.mark.parametrize("role,other", [
    ("student", "admin"), ("student", "teacher"),
    ("teacher", "admin"), ("teacher", "student"),
    ("admin", "teacher"),
])
def test_role_page_redirects_other_roles(client, users, role, other):
    login_as(client, users[role])

    response = client.get(f"/{other}")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/{role}")


def test_login_page_redirects_signed_in_user(client, users):
    login_as(client, users["teacher"])

    response = client.get("/login")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/teacher")


def test_inactive_user_is_sent_to_login(client):
    user_id = create_user(client, "student", "page_inactive", active=0)
    login_as(client, user_id)

    response = client.get("/student")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_page_login_flow_uses_real_authentication(client, users):
    response = client.post("/api/login", json={"username": "page_student", "password": "Password123"})
    assert response.status_code == 200

    response = client.get("/dashboard")
    assert response.headers["Location"].endswith("/student")

    assert client.post("/api/logout").status_code == 200
    assert client.get("/student").headers["Location"].endswith("/login")


def test_pages_keep_security_headers(client):
    response = client.get("/login")

    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Frame-Options"] == "DENY"


@pytest.mark.parametrize("asset", [
    "css/app.css", "js/common.js", "js/login.js",
    "js/admin.js", "js/teacher.js", "js/student.js",
])
def test_static_assets_are_served(client, asset):
    response = client.get(f"/static/{asset}")

    assert response.status_code == 200
    response.close()


@pytest.mark.parametrize("template", sorted(p.name for p in TEMPLATES.glob("*.html")))
def test_templates_have_no_inline_code_blocked_by_csp(template):
    """The CSP (default-src 'self') blocks inline styles, scripts and handlers."""
    html = (TEMPLATES / template).read_text()

    assert "<style" not in html
    assert re.search(r"<script(?![^>]*\bsrc=)", html) is None
    assert re.search(r"\sstyle=", html) is None
    assert re.search(r"\son[a-z]+=", html) is None


# --------------------------------------------------
# NFR-01: CSRF origin checks
# --------------------------------------------------

def test_cross_site_post_is_rejected(client, users):
    login_as(client, users["admin"])

    response = client.post(
        "/api/users",
        json={"username": "csrf_user", "password": "Password123", "role": "student"},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Cross-site request rejected"


def test_cross_site_referer_is_rejected(client, users):
    login_as(client, users["admin"])

    response = client.post(
        "/api/logout",
        headers={"Referer": "https://evil.example/page"},
    )

    assert response.status_code == 403


def test_same_origin_post_is_allowed(client, users):
    login_as(client, users["admin"])

    response = client.post(
        "/api/users",
        json={"username": "same_origin_user", "password": "Password123", "role": "student"},
        headers={"Origin": "http://localhost"},
    )

    assert response.status_code == 201


def test_lookalike_origin_is_rejected(client, users):
    login_as(client, users["admin"])

    response = client.post(
        "/api/logout",
        headers={"Origin": "http://localhost.evil.example"},
    )

    assert response.status_code == 403


def test_cross_site_get_is_not_blocked(client):
    response = client.get("/api/health", headers={"Origin": "https://evil.example"})

    assert response.status_code == 200


# --------------------------------------------------
# FR-09: Listing and removing enrollments
# --------------------------------------------------

@pytest.fixture
def enrolled(client, users):
    with client.application.app_context():
        db = get_db()
        class_id = db.execute("INSERT INTO classes (name) VALUES ('Page Class')").lastrowid
        subject_id = db.execute("INSERT INTO subjects (name) VALUES ('Page Subject')").lastrowid
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (users["student"], class_id, subject_id),
        )
        db.commit()

    return {"student_id": users["student"], "class_id": class_id, "subject_id": subject_id}


def test_list_enrollments_requires_admin(client, users, enrolled):
    assert client.get("/api/enrollments").status_code == 401

    login_as(client, users["teacher"])
    assert client.get("/api/enrollments").status_code == 403


def test_list_enrollments_returns_names(client, users, enrolled):
    login_as(client, users["admin"])

    response = client.get("/api/enrollments")
    data = response.get_json()

    assert response.status_code == 200
    assert data["count"] == 1
    assert data["enrollments"][0] == {
        **enrolled,
        "student_name": "page_student",
        "class_name": "Page Class",
        "subject_name": "Page Subject",
    }


def test_list_enrollments_filters(client, users, enrolled):
    login_as(client, users["admin"])

    match = client.get(f"/api/enrollments?class_id={enrolled['class_id']}").get_json()
    no_match = client.get(f"/api/enrollments?class_id={enrolled['class_id'] + 99}").get_json()

    assert match["count"] == 1
    assert no_match["count"] == 0
    assert client.get("/api/enrollments?class_id=abc").status_code == 400


def test_delete_enrollment(client, users, enrolled):
    login_as(client, users["admin"])

    response = client.delete("/api/enrollments", json=enrolled)

    assert response.status_code == 200
    assert client.get("/api/enrollments").get_json()["count"] == 0
    assert client.delete("/api/enrollments", json=enrolled).status_code == 404


def test_delete_enrollment_validation_and_auth(client, users, enrolled):
    login_as(client, users["teacher"])
    assert client.delete("/api/enrollments", json=enrolled).status_code == 403

    login_as(client, users["admin"])
    assert client.delete("/api/enrollments", json={"student_id": 1}).status_code == 400
    assert client.delete("/api/enrollments").status_code == 400


# --------------------------------------------------
# Demo data seed script
# --------------------------------------------------

def test_seed_is_repeatable_and_preserves_existing_data(tmp_path, monkeypatch):
    db_path = tmp_path / "seed.db"

    # Keep the real credentials file untouched during the test.
    import scripts.seed_demo_data as seed_module
    monkeypatch.setattr(seed_module, "CREDENTIALS_FILE", tmp_path / "creds.txt")

    from app import create_app
    app = create_app({"DATABASE": str(db_path)})
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES ('existing', 'keep-me', 'admin')"
        )
        db.commit()

    monkeypatch.setenv("DEMO_PASSWORD", "Seed-Test-Password")
    seed_module.seed(str(db_path))

    def table_counts():
        connection = sqlite3.connect(db_path)
        try:
            return {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("users", "classes", "subjects", "enrollments", "attendance")
            }
        finally:
            connection.close()

    first = table_counts()
    seed_module.seed(str(db_path))
    second = table_counts()

    assert first == second
    assert first["users"] == 1 + 1 + 2 + 8
    assert first["attendance"] > 0

    connection = sqlite3.connect(db_path)
    assert connection.execute(
        "SELECT password_hash FROM users WHERE username = 'existing'"
    ).fetchone()[0] == "keep-me"
    connection.close()

    client = app.test_client()
    response = client.post("/api/login", json={"username": "aarav", "password": "Seed-Test-Password"})
    assert response.status_code == 200
    records = client.get("/api/attendance").get_json()["records"]
    assert records and all(r["student_name"] == "aarav" for r in records)
