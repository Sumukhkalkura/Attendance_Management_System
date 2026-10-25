
"""Foundation tests for the Attendance Management System.

These tests verify the application structure and basic behavior.
They do not prove that all Sprint 1 requirements are complete.
"""

import sqlite3

from app import create_app


# --------------------------------------------------
# Test 1: Application Home Page
# --------------------------------------------------

def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json()["application"] == (
        "Attendance Management System"
    )


# --------------------------------------------------
# Test 2: API Health Check
# --------------------------------------------------

def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


# --------------------------------------------------
# Test 3: Database Tables
# --------------------------------------------------

def test_database_schema(tmp_path):
    path = tmp_path / "schema.db"

    create_app({
        "TESTING": True,
        "DATABASE": str(path)
    })

    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table'"
            )
        }

    assert {
        "users",
        "classes",
        "subjects",
        "enrollments",
        "attendance"
    } <= tables


# --------------------------------------------------
# Test 4: Duplicate Attendance Prevention
# --------------------------------------------------

def test_duplicate_attendance_prevented(tmp_path):
    path = tmp_path / "schema.db"

    create_app({
        "TESTING": True,
        "DATABASE": str(path)
    })

    with sqlite3.connect(path) as db:
        db.execute(
            """
            INSERT INTO users(username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            ("s1", "test-placeholder", "student")
        )

        db.execute(
            "INSERT INTO subjects(name) VALUES (?)",
            ("DBMS",)
        )

        db.execute(
            """
            INSERT INTO attendance(
                student_id,
                subject_id,
                attendance_date,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (1, 1, "2026-10-24", "Present")
        )

        try:
            db.execute(
                """
                INSERT INTO attendance(
                    student_id,
                    subject_id,
                    attendance_date,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (1, 1, "2026-10-24", "Absent")
            )

        except sqlite3.IntegrityError:
            pass

        else:
            raise AssertionError(
                "Duplicate attendance was allowed"
            )


# --------------------------------------------------
# Test 5: FR-01 Login Input Validation
# --------------------------------------------------

def test_login_requires_credentials(client):
    """Login must reject requests without credentials."""

    response = client.post("/api/login")

    assert response.status_code == 400

    assert response.get_json()["error"] == (
        "JSON request body required"
    )


# --------------------------------------------------
# Test 6: FR-01 Reject Empty Credentials
# --------------------------------------------------

def test_login_rejects_empty_credentials(client):
    response = client.post(
        "/api/login",
        json={
            "username": "",
            "password": ""
        }
    )

    assert response.status_code == 400

    assert response.get_json()["error"] == (
        "Username and password are required"
    )


# --------------------------------------------------
# Test 7: FR-01 Reject Unknown User
# --------------------------------------------------

def test_login_rejects_unknown_user(client):
    response = client.post(
        "/api/login",
        json={
            "username": "unknown_user",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401

    assert response.get_json()["error"] == (
        "Invalid username or password"
    )


# --------------------------------------------------
# Test 8: FR-01 Protected Endpoint
# --------------------------------------------------

def test_protected_endpoint_requires_login(client):
    response = client.get("/api/me")

    assert response.status_code == 401

    assert response.get_json()["error"] == (
        "Authentication required"
    )


# --------------------------------------------------
# Test 9: FR-01 Admin Access Requires Login
# --------------------------------------------------

def test_admin_endpoint_requires_login(client):
    response = client.get("/api/admin/check")

    assert response.status_code == 401


# --------------------------------------------------
# Test 10: FR-01 Teacher Access Requires Login
# --------------------------------------------------

def test_teacher_endpoint_requires_login(client):
    response = client.get("/api/teacher/check")

    assert response.status_code == 401


# --------------------------------------------------
# Test 11: FR-01 Student Access Requires Login
# --------------------------------------------------

def test_student_endpoint_requires_login(client):
    response = client.get("/api/student/check")

    assert response.status_code == 401
