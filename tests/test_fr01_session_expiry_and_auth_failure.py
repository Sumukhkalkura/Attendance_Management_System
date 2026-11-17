"""FR-01 / NFR-01 tests added in Deliverable 3, Phase 2.

Covers two Test Plan cases that had no automated test:

* SYS_FR-01_09 - Session timeout: login is required again after 30 minutes
  of inactivity (PERMANENT_SESSION_LIFETIME), while activity keeps the
  session alive.
* SYS_FR-01_10 - Authentication failure handling: when the user database
  cannot be opened, login fails safely with HTTP 503 and no technical detail.

Expiry is tested on the server side. Flask stores the session in a signed
cookie whose signature carries a timestamp; on every request the server
rejects a signature older than PERMANENT_SESSION_LIFETIME. The test moves
only the signer's clock (itsdangerous TimestampSigner.get_timestamp), so the
application, Werkzeug and pytest keep using the real time.
"""

import os
import sqlite3
from datetime import timedelta

import pytest
from itsdangerous.timed import TimestampSigner
from werkzeug.security import generate_password_hash

from app import create_app

PASSWORD = "Teacher01Pass!"


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "fr01_phase2.db"
    application = create_app({
        "TESTING": True,
        "DATABASE": str(database),
        "SECRET_KEY": "fr01-phase2-secret",
    })
    with sqlite3.connect(database) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'teacher', 1)",
            ("Teacher01", generate_password_hash(PASSWORD)),
        )
        conn.commit()
    return application


@pytest.fixture
def signer_clock(monkeypatch):
    """Control the clock used to sign and verify session cookies."""
    real = TimestampSigner.get_timestamp
    state = {"offset": 0}

    def shifted(self):
        return real(self) + state["offset"]

    monkeypatch.setattr(TimestampSigner, "get_timestamp", shifted)
    return state


def login(client):
    return client.post("/api/login", json={"username": "Teacher01", "password": PASSWORD})


def test_sys_fr_01_09_session_lifetime_is_thirty_minutes(app):
    assert app.permanent_session_lifetime == timedelta(minutes=30)


def test_sys_fr_01_09_idle_session_expires_after_thirty_minutes(app, signer_clock):
    client = app.test_client()
    assert login(client).status_code == 200
    assert client.get("/api/me").status_code == 200

    # 31 minutes without any request.
    signer_clock["offset"] = 31 * 60

    me = client.get("/api/me")
    assert me.status_code == 401
    assert me.get_json() == {"error": "Authentication required"}

    page = client.get("/teacher")
    assert page.status_code == 302
    assert page.headers["Location"].endswith("/login")


def test_sys_fr_01_09_session_still_valid_just_before_timeout(app, signer_clock):
    client = app.test_client()
    assert login(client).status_code == 200

    signer_clock["offset"] = 29 * 60

    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["username"] == "Teacher01"


def test_sys_fr_01_09_activity_renews_the_inactivity_window(app, signer_clock):
    """The timeout counts inactivity, not time since login."""
    client = app.test_client()
    assert login(client).status_code == 200

    # A request every 29 minutes keeps the session alive past 30 minutes
    # after login, because each response re-issues the cookie.
    for minutes in (29, 58, 87):
        signer_clock["offset"] = minutes * 60
        assert client.get("/api/me").status_code == 200, minutes

    # Then 31 idle minutes after the last request: expired.
    signer_clock["offset"] = (87 + 31) * 60
    assert client.get("/api/me").status_code == 401


def test_sys_fr_01_10_login_with_unavailable_database_fails_safely(app):
    database = app.config["DATABASE"]
    # Make the database impossible to open: replace the file with a directory.
    os.remove(database)
    os.mkdir(database)

    client = app.test_client()
    response = login(client)

    assert response.status_code == 503
    assert response.get_json() == {"error": "Authentication temporarily unavailable"}

    body = response.get_data(as_text=True)
    for detail in ("Traceback", "sqlite", "OperationalError", database):
        assert detail not in body

    # No session may be created by a failed login.
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_sys_fr_01_10_valid_login_works_when_database_is_available(app):
    """Control case: the same credentials succeed when the database is readable."""
    response = login(app.test_client())
    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == "teacher"
