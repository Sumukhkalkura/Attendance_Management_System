
import pytest

from test_fr01_authentication import app as auth_app


@pytest.fixture
def client(auth_app):
    return auth_app.test_client()


def login(client, username="admin1", password="admin123"):
    return client.post(
        "/api/login",
        json={
            "username": username,
            "password": password,
        },
    )


def test_logout_success(client):
    response = login(client)
    assert response.status_code == 200

    response = client.post("/api/logout")
    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_without_login(client):
    response = client.post("/api/logout")
    assert response.status_code == 401


def test_protected_route_after_logout(client):
    response = login(client)
    assert response.status_code == 200

    response = client.post("/api/logout")
    assert response.status_code == 200

    response = client.get("/api/admin/check")
    assert response.status_code == 401
