"""Automated tests for FR-13: Password Management."""

import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app

URL = "/api/me/password"
NEW_PASSWORD = "BrandNewPass456"

PASSWORDS = {
    "admin1": "admin-pass-123",
    "teacher1": "teacher-pass-123",
    "student1": "student-pass-123",
    "student2": "student2-pass-123",
}
ROLES = {
    "admin1": "admin",
    "teacher1": "teacher",
    "student1": "student",
    "student2": "student",
}


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "fr13_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(database_path),
        "SECRET_KEY": "fr13-test-secret",
    })

    with sqlite3.connect(database_path) as db:
        for username, password in PASSWORDS.items():
            db.execute(
                """
                INSERT INTO users (username, password_hash, role, active)
                VALUES (?, ?, ?, 1)
                """,
                (username, generate_password_hash(password), ROLES[username]),
            )
        db.commit()

    return application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username="student1", password=None):
    return client.post(
        "/api/login",
        json={
            "username": username,
            "password": password or PASSWORDS[username],
        },
    )


def change(client, username="student1", new_password=NEW_PASSWORD):
    return client.post(
        URL,
        json={
            "current_password": PASSWORDS[username],
            "new_password": new_password,
        },
    )


def stored_hash(app, username="student1"):
    with sqlite3.connect(app.config["DATABASE"]) as db:
        return db.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()[0]


def assert_password_unchanged(app, username="student1"):
    assert check_password_hash(stored_hash(app, username), PASSWORDS[username])


# Successful change


@pytest.mark.parametrize("username", ["admin1", "teacher1", "student1"])
def test_every_role_can_change_own_password(client, app, username):
    assert login(client, username).status_code == 200

    response = change(client, username)

    assert response.status_code == 200
    assert response.get_json() == {"message": "Password changed successfully"}
    assert check_password_hash(stored_hash(app, username), NEW_PASSWORD)


def test_new_password_accepted_after_change(client, app):
    login(client)
    change(client)

    response = login(app.test_client(), password=NEW_PASSWORD)

    assert response.status_code == 200


def test_old_password_rejected_after_change(client, app):
    login(client)
    change(client)

    response = login(app.test_client(), password=PASSWORDS["student1"])

    assert response.status_code == 401


def test_password_stored_as_hash(client, app):
    login(client)
    before = stored_hash(app)

    change(client)

    after = stored_hash(app)
    assert after != before
    assert after != NEW_PASSWORD
    assert NEW_PASSWORD not in after
    assert after.startswith(("scrypt:", "pbkdf2:"))


def test_password_of_exactly_minimum_length_is_accepted(client):
    login(client)

    assert change(client, new_password="12345678").status_code == 200


# Rejected input


def test_incorrect_current_password_rejected(client, app):
    login(client)

    response = client.post(
        URL,
        json={"current_password": "wrong-password", "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Current password is incorrect"}
    assert_password_unchanged(app)


def test_incorrect_current_password_keeps_session(client):
    login(client)

    client.post(
        URL,
        json={"current_password": "wrong-password", "new_password": NEW_PASSWORD},
    )

    assert client.get("/api/me").status_code == 200


@pytest.mark.parametrize("body", [
    {"new_password": NEW_PASSWORD},
    {"current_password": "", "new_password": NEW_PASSWORD},
    {"current_password": None, "new_password": NEW_PASSWORD},
    {"current_password": 12345678, "new_password": NEW_PASSWORD},
])
def test_missing_or_invalid_current_password_rejected(client, app, body):
    login(client)

    assert client.post(URL, json=body).status_code == 400
    assert_password_unchanged(app)


@pytest.mark.parametrize("value", [None, "", 12345678, ["NewPassword1"]])
def test_missing_or_invalid_new_password_rejected(client, app, value):
    login(client)

    response = client.post(
        URL,
        json={"current_password": PASSWORDS["student1"], "new_password": value},
    )

    assert response.status_code == 400
    assert_password_unchanged(app)


def test_absent_new_password_rejected(client, app):
    login(client)

    response = client.post(
        URL,
        json={"current_password": PASSWORDS["student1"]},
    )

    assert response.status_code == 400
    assert_password_unchanged(app)


@pytest.mark.parametrize("weak", ["a", "1234567"])
def test_weak_new_password_rejected(client, app, weak):
    login(client)

    response = change(client, new_password=weak)

    assert response.status_code == 400
    assert "at least 8 characters" in response.get_json()["error"]
    assert_password_unchanged(app)


def test_new_password_that_cannot_be_encoded_rejected(client, app):
    login(client)

    response = client.post(
        URL,
        data=(
            '{"current_password": "student-pass-123", '
            '"new_password": "abcdefgh\\ud800"}'
        ),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert_password_unchanged(app)


def test_current_password_that_cannot_be_encoded_rejected(client, app):
    login(client)

    response = client.post(
        URL,
        data='{"current_password": "\\ud800", "new_password": "BrandNewPass456"}',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert_password_unchanged(app)


def test_new_password_must_differ_from_current(client, app):
    login(client)
    before = stored_hash(app)

    response = change(client, new_password=PASSWORDS["student1"])

    assert response.status_code == 400
    assert stored_hash(app) == before


def test_wrong_current_password_reported_before_same_password_check(client):
    """The same-as-current check must not run for a wrong current password."""
    login(client)

    response = client.post(
        URL,
        json={
            "current_password": "wrong-password",
            "new_password": PASSWORDS["student1"],
        },
    )

    assert response.get_json() == {"error": "Current password is incorrect"}


@pytest.mark.parametrize("kwargs", [
    {},
    {"data": "not json", "content_type": "application/json"},
    {"json": ["current_password", "new_password"]},
])
def test_non_object_body_rejected(client, kwargs):
    login(client)

    assert client.post(URL, **kwargs).status_code == 400


# Authorization


def test_unauthenticated_request_rejected(client, app):
    response = change(client)

    assert response.status_code == 401
    assert_password_unchanged(app)


def test_request_after_logout_rejected(client, app):
    login(client)
    client.post("/api/logout")

    assert change(client).status_code == 401
    assert_password_unchanged(app)


@pytest.mark.parametrize("field", ["user_id", "id", "username"])
def test_cannot_target_another_account_through_request_body(client, app, field):
    login(client)
    target = 4 if field != "username" else "student2"

    response = client.post(
        URL,
        json={
            "current_password": PASSWORDS["student1"],
            "new_password": NEW_PASSWORD,
            field: target,
        },
    )

    assert response.status_code == 400
    assert_password_unchanged(app, "student2")
    assert_password_unchanged(app, "student1")


def test_other_users_current_password_does_not_authorize_change(client, app):
    login(client)

    response = client.post(
        URL,
        json={
            "current_password": PASSWORDS["student2"],
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 400
    assert_password_unchanged(app, "student1")
    assert_password_unchanged(app, "student2")


@pytest.mark.parametrize("method", ["put", "patch"])
def test_non_admin_cannot_use_admin_user_update(client, app, method):
    login(client)

    response = getattr(client, method)("/api/users/4", json={"password": NEW_PASSWORD})

    assert response.status_code == 403
    assert_password_unchanged(app, "student2")


def test_cross_site_request_rejected(client, app):
    login(client)

    response = client.post(
        URL,
        json={
            "current_password": PASSWORDS["student1"],
            "new_password": NEW_PASSWORD,
        },
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert_password_unchanged(app)


# No password exposure


def test_responses_do_not_contain_passwords_or_hashes(client, app):
    login(client)
    wrong = client.post(
        URL,
        json={"current_password": "wrong-password", "new_password": NEW_PASSWORD},
    )
    success = change(client)
    me = client.get("/api/me")

    for response in (wrong, success, me):
        body = response.get_data(as_text=True)
        assert NEW_PASSWORD not in body
        assert PASSWORDS["student1"] not in body
        assert "password_hash" not in body
        assert stored_hash(app) not in body


def test_session_cookie_does_not_contain_password_hash(client, app):
    login(client)
    change(client)

    with client.session_transaction() as session:
        values = [str(value) for value in session.values()]

    assert stored_hash(app) not in values


# Session invalidation


def test_current_session_survives_change(client):
    login(client)
    change(client)

    assert client.get("/api/me").status_code == 200


def test_other_sessions_invalidated_by_change(client, app):
    other_device = app.test_client()
    login(client)
    login(other_device)

    change(client)

    assert other_device.get("/api/me").status_code == 401
    assert other_device.get("/student").status_code == 302


def test_replayed_old_cookie_rejected_after_change(client, app):
    login(client)
    old_cookie = client.get_cookie("session").value
    change(client)

    replay = app.test_client()
    replay.set_cookie("session", old_cookie)

    assert replay.get("/api/me").status_code == 401


def test_failed_change_leaves_other_sessions_active(client, app):
    other_device = app.test_client()
    login(client)
    login(other_device)

    client.post(
        URL,
        json={"current_password": "wrong-password", "new_password": NEW_PASSWORD},
    )

    assert other_device.get("/api/me").status_code == 200


def test_other_users_sessions_unaffected(client, app):
    other_user = app.test_client()
    login(client)
    login(other_user, "student2")

    change(client)

    assert other_user.get("/api/me").status_code == 200


def test_admin_reset_invalidates_target_sessions(client, app):
    student = app.test_client()
    login(student)
    login(client, "admin1")

    response = client.patch("/api/users/3", json={"password": NEW_PASSWORD})

    assert response.status_code == 200
    assert student.get("/api/me").status_code == 401


def test_admin_editing_own_password_stays_signed_in(client):
    login(client, "admin1")

    response = client.patch("/api/users/1", json={"password": NEW_PASSWORD})

    assert response.status_code == 200
    assert client.get("/api/me").status_code == 200


def plant_legacy_session(client, user_id=3):
    """Give the client a validly signed pre-FR-13 session: no fingerprint."""
    with client.session_transaction() as session:
        session.clear()
        session.permanent = True
        session["user_id"] = user_id


def test_session_without_fingerprint_rejected_by_api(client):
    plant_legacy_session(client)

    assert client.get("/api/me").status_code == 401


def test_session_without_fingerprint_rejected_by_pages(client):
    plant_legacy_session(client)

    response = client.get("/student")

    assert response.status_code == 302
    assert "/student" not in response.headers["Location"]


def test_session_without_fingerprint_cannot_change_password(client, app):
    plant_legacy_session(client)

    assert change(client).status_code == 401
    assert_password_unchanged(app)


def test_rejected_legacy_session_is_cleared(client):
    plant_legacy_session(client)
    client.get("/api/me")

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_legacy_session_rejected_after_password_change(client, app):
    """A pre-FR-13 cookie must not outlive a password change."""
    stolen = app.test_client()
    plant_legacy_session(stolen)
    login(client)

    change(client)

    assert stolen.get("/api/me").status_code == 401


def test_session_with_wrong_fingerprint_rejected(client):
    login(client)

    with client.session_transaction() as session:
        session["password_fingerprint"] = ""

    assert client.get("/api/me").status_code == 401


def test_login_after_legacy_session_rejected_works(client):
    plant_legacy_session(client)
    client.get("/api/me")

    assert login(client).status_code == 200
    assert client.get("/api/me").status_code == 200


# Existing authentication and logout behaviour


def test_login_and_me_still_work(client):
    assert login(client).status_code == 200

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == "student1"
    assert "password_hash" not in response.get_json()["user"]


def test_logout_still_works_after_change(client):
    login(client)
    change(client)

    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/me").status_code == 401


def test_role_permissions_intact_after_change(client):
    login(client)
    change(client)

    assert client.get("/api/student/check").status_code == 200
    assert client.get("/api/admin/check").status_code == 403
    assert client.get("/api/teacher/check").status_code == 403


# Frontend


@pytest.mark.parametrize("username, page", [
    ("admin1", "/admin"),
    ("teacher1", "/teacher"),
    ("student1", "/student"),
])
def test_dashboards_offer_change_password(client, username, page):
    login(client, username)

    html = client.get(page).get_data(as_text=True)

    assert 'id="changePasswordButton"' in html
    assert 'id="passwordDialog"' in html
    assert 'name="current_password"' in html
    assert 'name="new_password"' in html
