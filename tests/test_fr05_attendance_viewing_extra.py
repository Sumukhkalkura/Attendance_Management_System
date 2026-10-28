"""Acceptance tests for FR-05: Attendance Record Viewing."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def fr05_data(client):
    """Create isolated users, subjects, and attendance records."""
    db_path = client.application.config["DATABASE"]

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        # Create users.
        users = [
            ("admin_fr05", "admin"),
            ("teacher_fr05", "teacher"),
            ("teacher_other_fr05", "teacher"),
            ("teacher_unassigned_fr05", "teacher"),
            ("student_a_fr05", "student"),
            ("student_b_fr05", "student"),
        ]

        for username, role in users:
            db.execute(
                """
                INSERT INTO users
                    (username, password_hash, role, active)
                VALUES (?, ?, ?, 1)
                """,
                (
                    username,
                    generate_password_hash("pass123"),
                    role,
                ),
            )

        # Retrieve user IDs.
        user_ids = {
            username: db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()[0]
            for username, _ in users
        }

        # Create subjects owned by different teachers.
        db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("FR05 Mathematics", user_ids["teacher_fr05"]),
        )

        db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("FR05 Science", user_ids["teacher_other_fr05"]),
        )

        subject_ids = {
            name: db.execute(
                "SELECT id FROM subjects WHERE name = ?",
                (name,),
            ).fetchone()[0]
            for name in ("FR05 Mathematics", "FR05 Science")
        }

        # Create attendance records.
        attendance_rows = [
            (
                user_ids["student_a_fr05"],
                subject_ids["FR05 Mathematics"],
                "2026-10-20",
                "Present",
            ),
            (
                user_ids["student_a_fr05"],
                subject_ids["FR05 Mathematics"],
                "2026-10-21",
                "Absent",
            ),
            (
                user_ids["student_b_fr05"],
                subject_ids["FR05 Science"],
                "2026-10-20",
                "Late",
            ),
        ]

        db.executemany(
            """
            INSERT INTO attendance
                (student_id, subject_id, attendance_date, status)
            VALUES (?, ?, ?, ?)
            """,
            attendance_rows,
        )

        db.commit()

    return {
        "users": user_ids,
        "subjects": subject_ids,
    }


def login(client, username):
    """Log in a test user."""
    response = client.post(
        "/api/login",
        json={
            "username": username,
            "password": "pass123",
        },
    )

    assert response.status_code == 200


def test_fr05_admin_can_view_all_records(client, fr05_data):
    """Admins can view records across subjects and teachers."""
    login(client, "admin_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 3
    assert len(body["records"]) == 3

    subject_ids = {
        record["subject_id"]
        for record in body["records"]
    }

    assert subject_ids == set(fr05_data["subjects"].values())


def test_fr05_teacher_sees_only_assigned_subject_records(
    client, fr05_data
):
    """Teachers see records only for their assigned subjects."""
    login(client, "teacher_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 2

    for record in body["records"]:
        assert (
            record["subject_id"]
            == fr05_data["subjects"]["FR05 Mathematics"]
        )


def test_fr05_teacher_can_filter_assigned_subject(
    client, fr05_data
):
    """A teacher can filter records by their assigned subject."""
    login(client, "teacher_fr05")

    subject_id = fr05_data["subjects"]["FR05 Mathematics"]

    response = client.get(
        f"/api/attendance?subject_id={subject_id}"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 2
    assert all(
        record["subject_id"] == subject_id
        for record in body["records"]
    )


def test_fr05_teacher_cannot_filter_another_teachers_subject(
    client, fr05_data
):
    """A teacher cannot request another teacher's subject."""
    login(client, "teacher_fr05")

    subject_id = fr05_data["subjects"]["FR05 Science"]

    response = client.get(
        f"/api/attendance?subject_id={subject_id}"
    )

    assert response.status_code == 403


def test_fr05_teacher_without_subject_filter_cannot_see_foreign_records(
    client, fr05_data
):
    """Unfiltered teacher results remain restricted to assigned subjects."""
    login(client, "teacher_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200

    records = response.get_json()["records"]

    assert records
    assert all(
        record["subject_id"]
        == fr05_data["subjects"]["FR05 Mathematics"]
        for record in records
    )

    # The Science record belongs to another teacher.
    assert not any(
        record["subject_id"]
        == fr05_data["subjects"]["FR05 Science"]
        for record in records
    )


def test_fr05_teacher_without_assigned_subjects_sees_no_records(
    client, fr05_data
):
    """Teachers without subjects cannot see other teachers' records."""
    login(client, "teacher_unassigned_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200
    assert response.get_json() == {
        "count": 0,
        "records": [],
    }


def test_fr05_student_can_view_own_records(client, fr05_data):
    """Students can view their own attendance."""
    login(client, "student_a_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 2

    own_id = fr05_data["users"]["student_a_fr05"]

    assert all(
        record["student_id"] == own_id
        for record in body["records"]
    )


def test_fr05_student_cannot_view_another_students_records(
    client, fr05_data
):
    """Students cannot use student_id to access another student's records."""
    login(client, "student_a_fr05")

    other_student_id = fr05_data["users"]["student_b_fr05"]

    response = client.get(
        f"/api/attendance?student_id={other_student_id}"
    )

    assert response.status_code == 403


def test_fr05_student_cannot_view_another_subject_owned_by_teacher(
    client, fr05_data
):
    """Student requests cannot bypass student record isolation."""
    login(client, "student_a_fr05")

    other_subject_id = fr05_data["subjects"]["FR05 Science"]

    response = client.get(
        f"/api/attendance?subject_id={other_subject_id}"
    )

    # No Science records belong to student A. The request is a valid
    # filter, but must never return another student's attendance.
    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 0
    assert body["records"] == []


def test_fr05_admin_can_filter_by_subject(client, fr05_data):
    """Admins can filter records by subject."""
    login(client, "admin_fr05")

    subject_id = fr05_data["subjects"]["FR05 Mathematics"]

    response = client.get(
        f"/api/attendance?subject_id={subject_id}"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 2

    assert all(
        record["subject_id"] == subject_id
        for record in body["records"]
    )


def test_fr05_admin_can_filter_by_date(client, fr05_data):
    """Admins can filter records by attendance date."""
    login(client, "admin_fr05")

    response = client.get(
        "/api/attendance?attendance_date=2026-10-20"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 2

    assert all(
        record["attendance_date"] == "2026-10-20"
        for record in body["records"]
    )


def test_fr05_admin_can_filter_by_student(client, fr05_data):
    """Admins can filter records by student ID."""
    login(client, "admin_fr05")

    student_id = fr05_data["users"]["student_a_fr05"]

    response = client.get(
        f"/api/attendance?student_id={student_id}"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 2

    assert all(
        record["student_id"] == student_id
        for record in body["records"]
    )


def test_fr05_combined_filters(client, fr05_data):
    """Subject, date, and student filters can be combined."""
    login(client, "admin_fr05")

    student_id = fr05_data["users"]["student_a_fr05"]
    subject_id = fr05_data["subjects"]["FR05 Mathematics"]

    response = client.get(
        "/api/attendance"
        f"?student_id={student_id}"
        f"&subject_id={subject_id}"
        "&attendance_date=2026-10-20"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["count"] == 1

    record = body["records"][0]

    assert record["student_id"] == student_id
    assert record["subject_id"] == subject_id
    assert record["attendance_date"] == "2026-10-20"
    assert record["status"] == "Present"


def test_fr05_empty_results(client, fr05_data):
    """Valid filters with no matching records return an empty list."""
    login(client, "admin_fr05")

    response = client.get(
        "/api/attendance?attendance_date=2026-12-31"
    )

    assert response.status_code == 200

    assert response.get_json() == {
        "count": 0,
        "records": [],
    }


@pytest.mark.parametrize(
    "query",
    [
        "subject_id=abc",
        "subject_id=0",
        "subject_id=-1",
        "student_id=abc",
        "student_id=0",
        "student_id=-1",
        "attendance_date=not-a-date",
    ],
)
def test_fr05_invalid_filters_return_400(client, fr05_data, query):
    """Invalid query parameters are rejected."""
    login(client, "admin_fr05")

    response = client.get(f"/api/attendance?{query}")

    assert response.status_code == 400


def test_fr05_unknown_subject_returns_404(client, fr05_data):
    """A nonexistent subject returns 404."""
    login(client, "admin_fr05")

    response = client.get("/api/attendance?subject_id=999999")

    assert response.status_code == 404


def test_fr05_unknown_student_returns_404(client, fr05_data):
    """A nonexistent student returns 404."""
    login(client, "admin_fr05")

    response = client.get("/api/attendance?student_id=999999")

    assert response.status_code == 404


def test_fr05_requires_authentication(client, fr05_data):
    """Unauthenticated users cannot access attendance records."""
    response = client.get("/api/attendance")

    assert response.status_code == 401
