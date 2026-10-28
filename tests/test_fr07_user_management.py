"""Automated tests for FR-07: User Management.

Covers:
- Administrator can create users with Admin, Teacher, and Student roles
- Known failing test: test_admin_can_create_all_roles[admin]
- Validation of required inputs (username, password, role, active)
- Duplicate username prevention (409 Conflict)
- Secure password hashing (passwords never stored in plain text, verified via check_password_hash)
- Administrator can view and list users, with role and active status filters
- Administrator can view individual user details
- Administrator can update user information (username, role, password, active)
- Administrator can activate and deactivate user accounts
- Inactive users cannot authenticate (login rejected)
- Active session is revoked if an account is deactivated
- Role-based access control (RBAC): teachers, students, and unauthenticated users
  are forbidden from user management operations.
"""

import sqlite3
import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated test application and database for FR-07 tests."""
    database_path = tmp_path / "fr07_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(database_path),
        "SECRET_KEY": "fr07-test-secret-key",
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
                INSERT INTO users (username, password_hash, role, active)
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
    """Log in a user via the API."""
    return client.post(
        "/api/login",
        json={
            "username": username,
            "password": password,
        },
    )


# =====================================================================
# FR-07: User Creation
# =====================================================================

@pytest.mark.parametrize("role", ["admin", "teacher", "student"])
def test_admin_can_create_all_roles(client, role):
    """Administrator can create accounts for Admin, Teacher, and Student roles."""
    login_resp = login(client, "admin1", "admin123")
    assert login_resp.status_code == 200

    username = f"new_{role}_user"
    password = f"Secure{role.capitalize()}Pass123!"

    response = client.post(
        "/api/users",
        json={
            "username": username,
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User created successfully"
    assert data["user"]["username"] == username
    assert data["user"]["role"] == role
    assert data["user"]["active"] == 1
    assert "id" in data["user"]
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Verify password was hashed and user can log in
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        row = db.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        assert row is not None
        assert row[0] != password
        assert check_password_hash(row[0], password)


@pytest.mark.parametrize("active_val,expected_active", [
    (1, 1),
    (0, 0),
    (True, 1),
    (False, 0),
])
def test_admin_can_create_user_with_explicit_active_flag(client, active_val, expected_active):
    """Administrator can set active status upon creation."""
    login(client, "admin1", "admin123")

    response = client.post(
        "/api/users",
        json={
            "username": f"active_test_{expected_active}",
            "password": "Password123!",
            "role": "student",
            "active": active_val,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["user"]["active"] == expected_active


def test_create_user_missing_body(client):
    """Rejects request with missing or non-dict body."""
    login(client, "admin1", "admin123")

    response = client.post(
        "/api/users",
        data="not-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


@pytest.mark.parametrize("payload", [
    {"password": "Pass", "role": "student"},
    {"username": "", "password": "Pass", "role": "student"},
    {"username": "   ", "password": "Pass", "role": "student"},
    {"username": "usr", "role": "student"},
    {"username": "usr", "password": "", "role": "student"},
    {"username": "usr", "password": "Pass"},
    {"username": "usr", "password": "Pass", "role": ""},
    {"username": "usr", "password": "Pass", "role": "superadmin"},
    {"username": "usr", "password": "Pass", "role": "guest"},
])
def test_create_user_invalid_inputs(client, payload):
    """Validates required input fields and allowed roles."""
    login(client, "admin1", "admin123")

    response = client.post("/api/users", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_user_invalid_active_flag(client):
    """Rejects non-boolean / non-0/1 active flags."""
    login(client, "admin1", "admin123")

    response = client.post(
        "/api/users",
        json={
            "username": "bad_active_user",
            "password": "Password123!",
            "role": "student",
            "active": "not-a-boolean",
        },
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_duplicate_username(client):
    """Prevents creating users with duplicate usernames (409 Conflict)."""
    login(client, "admin1", "admin123")

    # Attempt to create with already existing username "student1"
    response = client.post(
        "/api/users",
        json={
            "username": "student1",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


def test_password_is_securely_hashed(client):
    """Passwords must be hashed securely using Werkzeug hashing."""
    login(client, "admin1", "admin123")
    plain = "SuperSecretPlainText123"

    response = client.post(
        "/api/users",
        json={
            "username": "hash_check_user",
            "password": plain,
            "role": "teacher",
        },
    )
    assert response.status_code == 201

    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        stored_hash = db.execute(
            "SELECT password_hash FROM users WHERE username = 'hash_check_user'"
        ).fetchone()[0]
        assert plain not in stored_hash
        assert stored_hash.startswith("scrypt:") or stored_hash.startswith("pbkdf2:")


@pytest.mark.parametrize("role_user,role_pass", [
    ("teacher1", "teacher123"),
    ("student1", "student123"),
])
def test_create_user_forbidden_for_non_admins(client, role_user, role_pass):
    """Non-administrators cannot create user accounts."""
    login(client, role_user, role_pass)

    response = client.post(
        "/api/users",
        json={
            "username": "unauthorized_user",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert response.status_code == 403


def test_create_user_unauthenticated(client):
    """Unauthenticated users cannot create accounts."""
    response = client.post(
        "/api/users",
        json={
            "username": "no_auth_user",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert response.status_code == 401


# =====================================================================
# FR-07: User Listing & Viewing
# =====================================================================

def test_admin_can_list_all_users(client):
    """Administrator can list existing users without exposing password hashes."""
    login(client, "admin1", "admin123")

    response = client.get("/api/users")
    assert response.status_code == 200

    data = response.get_json()
    assert "users" in data
    users = data["users"]
    usernames = [u["username"] for u in users]

    assert "admin1" in usernames
    assert "teacher1" in usernames
    assert "student1" in usernames
    assert "inactive1" in usernames

    for u in users:
        assert "password" not in u
        assert "password_hash" not in u
        assert "id" in u
        assert "role" in u
        assert "active" in u


@pytest.mark.parametrize("role", ["admin", "teacher", "student"])
def test_admin_can_filter_users_by_role(client, role):
    """Administrator can filter user list by role."""
    login(client, "admin1", "admin123")

    response = client.get(f"/api/users?role={role}")
    assert response.status_code == 200

    users = response.get_json()["users"]
    assert len(users) > 0
    assert all(u["role"] == role for u in users)


def test_admin_list_users_invalid_role_filter(client):
    """Invalid role filter returns 400 Bad Request."""
    login(client, "admin1", "admin123")

    response = client.get("/api/users?role=invalid_role")
    assert response.status_code == 400


@pytest.mark.parametrize("flag,expected_active", [
    ("1", 1),
    ("0", 0),
    ("true", 1),
    ("false", 0),
])
def test_admin_can_filter_users_by_active_status(client, flag, expected_active):
    """Administrator can filter users by active status."""
    login(client, "admin1", "admin123")

    response = client.get(f"/api/users?active={flag}")
    assert response.status_code == 200

    users = response.get_json()["users"]
    assert len(users) > 0
    assert all(u["active"] == expected_active for u in users)


def test_admin_can_get_single_user(client):
    """Administrator can retrieve a specific user by ID."""
    login(client, "admin1", "admin123")

    response = client.get("/api/users/1")
    assert response.status_code == 200
    user = response.get_json()["user"]
    assert user["id"] == 1
    assert user["username"] == "admin1"
    assert user["role"] == "admin"
    assert user["active"] == 1
    assert "password_hash" not in user


def test_admin_get_nonexistent_user(client):
    """Requesting non-existent user ID returns 404."""
    login(client, "admin1", "admin123")

    response = client.get("/api/users/99999")
    assert response.status_code == 404


@pytest.mark.parametrize("role_user,role_pass", [
    ("teacher1", "teacher123"),
    ("student1", "student123"),
])
def test_view_users_forbidden_for_non_admins(client, role_user, role_pass):
    """Non-administrators cannot list or view user details."""
    login(client, role_user, role_pass)

    assert client.get("/api/users").status_code == 403
    assert client.get("/api/users/1").status_code == 403


def test_view_users_unauthenticated(client):
    """Unauthenticated requests to view users return 401."""
    assert client.get("/api/users").status_code == 401
    assert client.get("/api/users/1").status_code == 401


# =====================================================================
# FR-07: User Updating
# =====================================================================

def test_admin_can_update_username(client):
    """Administrator can update a user's username."""
    login(client, "admin1", "admin123")

    response = client.put(
        "/api/users/3",
        json={"username": "student_updated"},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == "student_updated"

    # Verify change in database
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        row = db.execute("SELECT username FROM users WHERE id = 3").fetchone()
        assert row[0] == "student_updated"


@pytest.mark.parametrize("new_role", ["admin", "teacher", "student"])
def test_admin_can_update_user_role(client, new_role):
    """Administrator can change a user's role to Admin, Teacher, or Student."""
    login(client, "admin1", "admin123")

    response = client.put(
        "/api/users/3",
        json={"role": new_role},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == new_role


def test_admin_can_update_user_password(client):
    """Administrator can update a user's password; verifies new login succeeds."""
    login(client, "admin1", "admin123")

    new_pass = "BrandNewPassword456!"
    response = client.put(
        "/api/users/3",
        json={"password": new_pass},
    )
    assert response.status_code == 200

    # Old password fails
    assert login(client, "student1", "student123").status_code == 401
    # New password succeeds
    assert login(client, "student1", new_pass).status_code == 200


def test_update_user_nonexistent_returns_404(client):
    """Updating a non-existent user returns 404."""
    login(client, "admin1", "admin123")

    response = client.put(
        "/api/users/99999",
        json={"username": "nobody"},
    )
    assert response.status_code == 404


def test_update_user_duplicate_username_returns_409(client):
    """Updating to an existing username returns 409 Conflict."""
    login(client, "admin1", "admin123")

    response = client.put(
        "/api/users/3",
        json={"username": "teacher1"},
    )
    assert response.status_code == 409


@pytest.mark.parametrize("payload", [
    {},
    {"username": ""},
    {"username": "   "},
    {"role": "invalid_role"},
    {"password": ""},
    {"extra_field": "disallowed"},
    {"active": "not-bool"},
])
def test_update_user_invalid_inputs(client, payload):
    """Rejects invalid update fields or empty inputs."""
    login(client, "admin1", "admin123")

    response = client.put("/api/users/3", json=payload)
    assert response.status_code == 400


@pytest.mark.parametrize("role_user,role_pass", [
    ("teacher1", "teacher123"),
    ("student1", "student123"),
])
def test_update_user_forbidden_for_non_admins(client, role_user, role_pass):
    """Non-administrators cannot update user accounts."""
    login(client, role_user, role_pass)

    response = client.put("/api/users/3", json={"username": "hacked"})
    assert response.status_code == 403


def test_update_user_unauthenticated(client):
    """Unauthenticated users cannot update user accounts."""
    response = client.put("/api/users/3", json={"username": "hacked"})
    assert response.status_code == 401


# =====================================================================
# FR-07: Account Activation & Deactivation
# =====================================================================

def test_admin_can_deactivate_and_activate_user(client):
    """Administrator can deactivate and subsequently reactivate an account."""
    login(client, "admin1", "admin123")

    # Deactivate active user (student1, id 3)
    deact_resp = client.patch("/api/users/3/deactivate")
    assert deact_resp.status_code == 200
    assert deact_resp.get_json()["message"] == "User deactivated successfully"
    assert deact_resp.get_json()["user"]["active"] == 0

    # Attempt to deactivate already inactive user returns 409
    already_deact = client.patch("/api/users/3/deactivate")
    assert already_deact.status_code == 409

    # Deactivated user cannot authenticate
    student_login = login(client, "student1", "student123")
    assert student_login.status_code == 401

    # Re-login as admin to reactivate
    login(client, "admin1", "admin123")
    act_resp = client.patch("/api/users/3/activate")
    assert act_resp.status_code == 200
    assert act_resp.get_json()["message"] == "User activated successfully"
    assert act_resp.get_json()["user"]["active"] == 1

    # Attempt to activate already active user returns 409
    already_act = client.patch("/api/users/3/activate")
    assert already_act.status_code == 409

    # Reactivated user can authenticate again
    student_relogin = login(client, "student1", "student123")
    assert student_relogin.status_code == 200


def test_deactivate_and_activate_nonexistent_user(client):
    """Deactivation or activation of non-existent user returns 404."""
    login(client, "admin1", "admin123")

    assert client.patch("/api/users/99999/deactivate").status_code == 404
    assert client.patch("/api/users/99999/activate").status_code == 404


@pytest.mark.parametrize("role_user,role_pass", [
    ("teacher1", "teacher123"),
    ("student1", "student123"),
])
def test_deactivate_and_activate_forbidden_for_non_admins(client, role_user, role_pass):
    """Non-administrators cannot deactivate or activate user accounts."""
    login(client, role_user, role_pass)

    assert client.patch("/api/users/3/deactivate").status_code == 403
    assert client.patch("/api/users/4/activate").status_code == 403


def test_deactivate_and_activate_unauthenticated(client):
    """Unauthenticated users cannot deactivate or activate user accounts."""
    assert client.patch("/api/users/3/deactivate").status_code == 401
    assert client.patch("/api/users/4/activate").status_code == 401


def test_active_session_revoked_on_deactivation(client):
    """
    If a logged-in user's account is deactivated by an administrator,
    their session is invalidated on their subsequent request.
    """
    # Student logs in
    login_resp = login(client, "student1", "student123")
    assert login_resp.status_code == 200

    # Verify student can access protected route
    assert client.get("/api/student/check").status_code == 200

    # Deactivate student directly in database (simulating admin action in parallel)
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE users SET active = 0 WHERE username = 'student1'")
        db.commit()

    # Next student request must be rejected and session cleared
    check_resp = client.get("/api/student/check")
    assert check_resp.status_code == 401

    # Following request without credentials also returns 401
    assert client.get("/api/me").status_code == 401
