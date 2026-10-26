"""Automated tests for FR-03: Attendance Record Management."""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create isolated test application and database populated with test records."""
    db_path = tmp_path / "fr03_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(db_path),
        "SECRET_KEY": "fr03-test-secret",
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
        ]
        for username, password, role, active in users:
            db.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), role, active),
            )

        # Classes
        db.execute("INSERT INTO classes (id, name) VALUES (1, 'Class 10A')")
        db.execute("INSERT INTO classes (id, name) VALUES (2, 'Class 10B')")

        # Subjects: teacher1 (2) teaches Mathematics (1); teacher2 (3) teaches Physics (2)
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (1, 'Mathematics', 2)")
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (2, 'Physics', 3)")

        # Enrollments:
        # student1 (4) and student2 (5) enrolled in Class 10A Mathematics (1)
        # student1 (4) enrolled in Class 10B Physics (2)
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (4, 1, 1)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (5, 1, 1)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (4, 2, 2)")

        # Seed attendance records
        # Record 1: student1, Mathematics, 2026-10-24, Present
        # Record 2: student1, Mathematics, 2026-10-25, Absent
        # Record 3: student2, Mathematics, 2026-10-24, Late
        # Record 4: student1, Physics, 2026-10-24, Present
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (1, 4, 1, '2026-10-24', 'Present')")
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (2, 4, 1, '2026-10-25', 'Absent')")
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (3, 5, 1, '2026-10-24', 'Late')")
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (4, 4, 2, '2026-10-24', 'Present')")

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
# Record Retrieval Tests (GET /api/attendance)
# ---------------------------------------------------------------------

def test_teacher_retrieves_assigned_subject_attendance(client):
    """Teacher retrieves attendance records for their assigned subject."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 3
    # All records belong to subject 1 (Mathematics)
    assert all(r["subject_id"] == 1 for r in body["records"])


def test_filter_attendance_by_student(client):
    """Teacher filters attendance by specific student ID."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance?student_id=4")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 2
    assert all(r["student_id"] == 4 for r in body["records"])


def test_filter_attendance_by_date(client):
    """Teacher filters attendance by date."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance?date=2026-10-24")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 2
    assert all(r["attendance_date"] == "2026-10-24" for r in body["records"])


def test_filter_attendance_by_status(client):
    """Teacher filters attendance by status."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance?status=Late")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 1
    assert body["records"][0]["student_id"] == 5
    assert body["records"][0]["status"] == "Late"


def test_filter_attendance_by_class(client):
    """Attendance filtered by class ID."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance?class_id=1")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 3


def test_get_single_attendance_record_by_id(client):
    """Retrieve single attendance record by ID."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance/1")

    assert response.status_code == 200
    rec = response.get_json()["record"]
    assert rec["id"] == 1
    assert rec["student_id"] == 4
    assert rec["status"] == "Present"


def test_get_nonexistent_attendance_record(client):
    """Requesting non-existent record ID returns 404."""
    login(client, "teacher1", "teacher123")
    response = client.get("/api/attendance/9999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Attendance record not found"


# ---------------------------------------------------------------------
# Role Restrictions on Retrieval
# ---------------------------------------------------------------------

def test_student_can_only_view_own_attendance(client):
    """Student viewing attendance only sees their own records."""
    login(client, "student2", "student123")  # student2 has ID 5
    response = client.get("/api/attendance")

    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 1
    assert body["records"][0]["student_id"] == 5


def test_student_requesting_other_student_attendance_denied(client):
    """Student attempting to view another student's records receives 403."""
    login(client, "student2", "student123")  # student2 is ID 5
    response = client.get("/api/attendance?student_id=4")

    assert response.status_code == 403
    assert "Access denied" in response.get_json()["error"]


def test_teacher_cannot_view_unassigned_subject(client):
    """Teacher cannot view attendance records for another teacher's subject."""
    login(client, "teacher1", "teacher123")  # teaches subject 1, not subject 2
    response = client.get("/api/attendance?subject_id=2")

    assert response.status_code == 403
    assert "Access denied" in response.get_json()["error"]


# ---------------------------------------------------------------------
# Updating Attendance Records (PUT/PATCH /api/attendance/<id>)
# ---------------------------------------------------------------------

def test_authorized_teacher_updates_record_status(client, app):
    """Authorized teacher successfully updates attendance status."""
    login(client, "teacher1", "teacher123")

    response = client.put(
        "/api/attendance/1",
        json={"status": "Late"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["message"] == "Attendance record updated successfully"
    assert body["record"]["id"] == 1
    assert body["record"]["status"] == "Late"

    # Verify update in database
    with sqlite3.connect(app.config["DATABASE"]) as db:
        row = db.execute("SELECT status FROM attendance WHERE id = 1").fetchone()
        assert row[0] == "Late"


def test_update_record_status_via_patch(client):
    """PATCH method also updates the record successfully."""
    login(client, "teacher1", "teacher123")

    response = client.patch(
        "/api/attendance/1",
        json={"status": "Absent"},
    )

    assert response.status_code == 200
    assert response.get_json()["record"]["status"] == "Absent"


def test_update_record_by_key(client, app):
    """Teacher updates attendance record by composite key (student, subject, date)."""
    login(client, "teacher1", "teacher123")

    response = client.put(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-24",
            "status": "Late",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["record"]["status"] == "Late"

    with sqlite3.connect(app.config["DATABASE"]) as db:
        status = db.execute(
            "SELECT status FROM attendance WHERE student_id = 4 AND subject_id = 1 AND attendance_date = '2026-10-24'"
        ).fetchone()[0]
        assert status == "Late"


def test_update_with_invalid_status_rejected(client):
    """Updating to an invalid status returns 400."""
    login(client, "teacher1", "teacher123")

    response = client.put(
        "/api/attendance/1",
        json={"status": "HalfDay"},
    )

    assert response.status_code == 400
    assert "Invalid attendance status" in response.get_json()["error"]


def test_update_nonexistent_record(client):
    """Updating a nonexistent record returns 404."""
    login(client, "teacher1", "teacher123")

    response = client.put(
        "/api/attendance/9999",
        json={"status": "Late"},
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Attendance record not found"


def test_student_cannot_update_record(client):
    """Unauthorized student attempting to update attendance receives 403."""
    login(client, "student1", "student123")

    response = client.put(
        "/api/attendance/1",
        json={"status": "Present"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Access denied"


def test_unassigned_teacher_cannot_update_record(client):
    """Teacher cannot update records for subjects they do not teach."""
    login(client, "teacher1", "teacher123")  # Record 4 is Physics, taught by teacher2

    response = client.put(
        "/api/attendance/4",
        json={"status": "Absent"},
    )

    assert response.status_code == 403
    assert "Access denied" in response.get_json()["error"]


def test_update_date_causing_duplicate_rejected(client):
    """Updating a record's date to a date that already has attendance returns 409."""
    login(client, "teacher1", "teacher123")

    # Record 1 is student 4, subject 1, 2026-10-24
    # Record 2 is student 4, subject 1, 2026-10-25
    # Updating Record 1's date to 2026-10-25 should conflict with Record 2
    response = client.put(
        "/api/attendance/1",
        json={"attendance_date": "2026-10-25"},
    )

    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


# ---------------------------------------------------------------------
# Record Deletion Tests (DELETE /api/attendance/<id>)
# ---------------------------------------------------------------------

def test_authorized_teacher_deletes_record(client, app):
    """Authorized teacher can delete an attendance record."""
    login(client, "teacher1", "teacher123")

    response = client.delete("/api/attendance/1")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Attendance record deleted successfully"

    # Verify deletion in database
    with sqlite3.connect(app.config["DATABASE"]) as db:
        row = db.execute("SELECT * FROM attendance WHERE id = 1").fetchone()
        assert row is None


def test_delete_nonexistent_record(client):
    """Deleting a non-existent record returns 404."""
    login(client, "teacher1", "teacher123")

    response = client.delete("/api/attendance/9999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Attendance record not found"


def test_student_cannot_delete_record(client):
    """Student attempting to delete attendance receives 403."""
    login(client, "student1", "student123")

    response = client.delete("/api/attendance/1")
    assert response.status_code == 403


def test_unassigned_teacher_cannot_delete_record(client):
    """Teacher cannot delete attendance record for another teacher's subject."""
    login(client, "teacher1", "teacher123")  # Record 4 is Physics (teacher2)

    response = client.delete("/api/attendance/4")
    assert response.status_code == 403
