import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "security_test.db"),
        "SECRET_KEY": "test-security-key",
    })
    return app.test_client()


def test_security_headers(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == (
        "strict-origin-when-cross-origin"
    )
    assert "default-src 'self'" in response.headers[
        "Content-Security-Policy"
    ]
    assert response.headers["Cache-Control"] == "no-store"


def test_session_cookie_security(client):
    app = client.application

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_unauthenticated_admin_access_denied(client):
    response = client.get("/api/admin/check")

    assert response.status_code == 401


def test_unauthenticated_teacher_access_denied(client):
    response = client.get("/api/teacher/check")

    assert response.status_code == 401


def test_unauthenticated_student_access_denied(client):
    response = client.get("/api/student/check")

    assert response.status_code == 401


def test_session_expiration_configured(client):
    from datetime import timedelta

    assert client.application.config[
        "PERMANENT_SESSION_LIFETIME"
    ] == timedelta(minutes=30)