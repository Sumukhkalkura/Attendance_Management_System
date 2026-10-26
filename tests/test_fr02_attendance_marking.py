"""Automated tests for FR-02: Attendance Marking."""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated test app with database pre-populated with users, classes, subjects, enrollments."""
    db_path = tmp_path / "fr02_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(db_path),
        "SECRET_KEY": "fr02-test-secret",
    })

    with sqlite3.connect(db_path) as db:
        # Users
        users = [
            ("admin1", "admin123", "admin", 1),
            ("teacher1", "teacher123", "teacher", 1),
            ("teacher2", "teacher123", "teacher", 1),
            ("student1", "student123", "student", 1),
            ("student2", "student123", "student", 1),
            ("student3", "student123", "student", 1),
            ("inactive_student", "student123", "student", 0),
        ]
        for username, password, role, active in users:
            db.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), role, active),
            )

        # Classes
        db.execute("INSERT INTO classes (id, name) VALUES (1, 'Class 10A')")
        db.execute("INSERT INTO classes (id, name) VALUES (2, 'Class 10B')")

        # Subjects: teacher1 (id=2) teaches Mathematics (id=1); teacher2 (id=3) teaches Physics (id=2)
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (1, 'Mathematics', 2)")
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (2, 'Physics', 3)")

        # Enrollments:
        # student1 (4) and student2 (5) in Class 10A for Mathematics (1)
        # student1 (4) and student3 (6) in Class 10B for Physics (2)
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (4, 1, 1)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (5, 1, 1)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (4, 2, 2)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (6, 2, 2)")

        db.commit()

    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password):
    """Log in user and establish session."""
    return client.post(
        "/api/login",
        json={"username": username, "password": password},
    )


# ---------------------------------------------------------------------
# Positive Tests: Marking Attendance
# ---------------------------------------------------------------------

def test_teacher_marks_single_student_attendance(client, app):
    """Authorized teacher marks attendance for an enrolled student."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["message"] == "Attendance recorded successfully"
    assert body["record"]["student_id"] == 4
    assert body["record"]["subject_id"] == 1
    assert body["record"]["attendance_date"] == "2026-10-26"
    assert body["record"]["status"] == "Present"

    # Verify persistence in database
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT * FROM attendance WHERE student_id = 4 AND subject_id = 1 AND attendance_date = '2026-10-26'"
        ).fetchone()
        assert row is not None
        assert row["status"] == "Present"


@pytest.mark.parametrize("status_input, expected_status", [
    ("Present", "Present"),
    ("Absent", "Absent"),
    ("Late", "Late"),
    ("present", "Present"),
    ("absent", "Absent"),
    ("late", "Late"),
])
def test_all_valid_statuses_supported(client, status_input, expected_status):
    """System supports Present, Absent, and Late attendance statuses."""
    login(client, "teacher1", "teacher123")

    # Use different dates to avoid unique constraint violations
    date_str = f"2026-10-{10 + hash(status_input) % 15}"
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": date_str,
            "status": status_input,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["record"]["status"] == expected_status


def test_batch_attendance_marking_for_session(client, app):
    """Teacher marks attendance for the full class session at once."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "class_id": 1,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "records": [
                {"student_id": 4, "status": "Present"},
                {"student_id": 5, "status": "Absent"},
            ],
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["message"] == "Attendance recorded successfully"
    assert body["count"] == 2
    assert len(body["records"]) == 2

    # Verify both records saved in database
    with sqlite3.connect(app.config["DATABASE"]) as db:
        rows = db.execute(
            "SELECT student_id, status FROM attendance WHERE subject_id = 1 AND attendance_date = '2026-10-26' ORDER BY student_id"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0] == (4, "Present")
        assert rows[1] == (5, "Absent")


def test_admin_can_mark_attendance(client):
    """Administrator is authorized to record attendance."""
    login(client, "admin1", "admin123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )

    assert response.status_code == 201


# ---------------------------------------------------------------------
# Authorization & Security Tests
# ---------------------------------------------------------------------

def test_unauthenticated_user_cannot_mark_attendance(client):
    """Unauthenticated requests must be rejected with 401."""
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_student_cannot_mark_attendance(client):
    """Students must not be allowed to mark attendance."""
    login(client, "student1", "student123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "Access denied"


def test_teacher_cannot_mark_attendance_for_unassigned_subject(client):
    """Teacher cannot mark attendance for a subject taught by another teacher."""
    login(client, "teacher1", "teacher123")  # teacher1 teaches subject 1, not subject 2

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 2,  # Physics taught by teacher2
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 403
    assert "Access denied" in response.get_json()["error"]


# ---------------------------------------------------------------------
# Validation & Error Handling Tests
# ---------------------------------------------------------------------

def test_missing_json_body(client):
    """Request without JSON payload returns 400."""
    login(client, "teacher1", "teacher123")
    response = client.post("/api/attendance")
    assert response.status_code == 400
    assert response.get_json()["error"] == "JSON request body required"


@pytest.mark.parametrize("missing_field", ["student_id", "subject_id", "attendance_date", "status"])
def test_missing_required_fields_rejected(client, missing_field):
    """Missing any mandatory field returns 400."""
    login(client, "teacher1", "teacher123")
    payload = {
        "student_id": 4,
        "subject_id": 1,
        "attendance_date": "2026-10-26",
        "status": "Present",
    }
    del payload[missing_field]

    response = client.post("/api/attendance", json=payload)
    assert response.status_code == 400


@pytest.mark.parametrize("invalid_status", ["Excused", "Sick", "Holiday", "yes", 123, ""])
def test_invalid_status_rejected(client, invalid_status):
    """Status outside of Present, Absent, Late returns 400."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": invalid_status,
        },
    )
    assert response.status_code == 400
    assert "Invalid attendance status" in response.get_json()["error"]


@pytest.mark.parametrize("invalid_date", ["2026/10/26", "26-10-2026", "2026-02-30", "yesterday", ""])
def test_invalid_date_format_rejected(client, invalid_date):
    """Dates not in YYYY-MM-DD or invalid calendar dates return 400."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": invalid_date,
            "status": "Present",
        },
    )
    assert response.status_code == 400
    assert "Invalid attendance_date format" in response.get_json()["error"]


def test_nonexistent_student_rejected(client):
    """Referencing a student ID that does not exist returns 404."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 9999,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 404
    assert "Student not found" in response.get_json()["error"]


def test_nonexistent_subject_rejected(client):
    """Referencing a subject ID that does not exist returns 404."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 9999,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 404
    assert "Subject not found" in response.get_json()["error"]


def test_nonexistent_class_rejected(client):
    """Referencing a class ID that does not exist returns 404."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "class_id": 9999,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 404
    assert "Class not found" in response.get_json()["error"]


def test_marking_attendance_for_teacher_user_rejected(client):
    """Referencing a user who is not a student returns 400."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "student_id": 2,  # teacher1 ID
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert response.status_code == 400
    assert "not a student" in response.get_json()["error"]


def test_duplicate_attendance_marking_rejected(client):
    """Recording duplicate attendance for same student, subject, and date returns 409."""
    login(client, "teacher1", "teacher123")

    payload = {
        "student_id": 4,
        "subject_id": 1,
        "attendance_date": "2026-10-26",
        "status": "Present",
    }
    first_res = client.post("/api/attendance", json=payload)
    assert first_res.status_code == 201

    second_res = client.post("/api/attendance", json=payload)
    assert second_res.status_code == 409
    assert "already exists" in second_res.get_json()["error"]


def test_batch_marking_duplicate_student_in_submission_rejected(client):
    """Duplicate student in batch submission returns 400."""
    login(client, "teacher1", "teacher123")
    response = client.post(
        "/api/attendance",
        json={
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "records": [
                {"student_id": 4, "status": "Present"},
                {"student_id": 4, "status": "Absent"},
            ],
        },
    )
    assert response.status_code == 400
    assert "Duplicate attendance entry" in response.get_json()["error"]


def test_batch_marking_atomic_rollback(client, app):
    """If one record in batch fails, entire batch is rolled back (no partial writes)."""
    login(client, "teacher1", "teacher123")

    # Second student has invalid status
    response = client.post(
        "/api/attendance",
        json={
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "records": [
                {"student_id": 4, "status": "Present"},
                {"student_id": 5, "status": "InvalidStatus"},
            ],
        },
    )
    assert response.status_code == 400

    # Verify student 4 was NOT inserted
    with sqlite3.connect(app.config["DATABASE"]) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM attendance WHERE subject_id = 1 AND attendance_date = '2026-10-26'"
        ).fetchone()[0]
        assert count == 0


# ---------------------------------------------------------------------
# Helper Endpoints (US-06: Select Class, Subject, Date)
# ---------------------------------------------------------------------

def test_teacher_classes_list(client):
    """Teacher receives only classes assigned through subjects and enrollments."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/teacher/classes")
    assert response.status_code == 200
    classes = response.get_json()["classes"]
    assert len(classes) == 1
    assert classes[0]["name"] == "Class 10A"


def test_teacher_subjects_list(client):
    """Teacher receives only subjects assigned to them."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/teacher/subjects")
    assert response.status_code == 200
    subjects = response.get_json()["subjects"]
    assert len(subjects) == 1
    assert subjects[0]["name"] == "Mathematics"


def test_roster_loading(client):
    """Roster endpoint returns enrolled students for class and subject."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/roster?class_id=1&subject_id=1")
    assert response.status_code == 200
    body = response.get_json()
    assert body["class_name"] == "Class 10A"
    assert body["subject_name"] == "Mathematics"
    assert body["count"] == 2
    student_ids = {s["student_id"] for s in body["students"]}
    assert student_ids == {4, 5}
