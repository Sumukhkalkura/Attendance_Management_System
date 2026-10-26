"""Tests for FR-05: Attendance Record Viewing."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def fr05_data(client):
    """Create isolated users, subjects, and attendance records."""
    db_path = client.application.config["DATABASE"]

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        users = [
            ("admin_fr05", "admin"),
            ("teacher_fr05", "teacher"),
            ("teacher_other_fr05", "teacher"),
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
                (username, generate_password_hash("pass123"), role),
            )

        user_ids = {
            username: db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()[0]
            for username, _ in users
        }

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

        attendance = [
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
            attendance,
        )

        db.commit()

    return {
        "users": user_ids,
        "subjects": subject_ids,
    }


def login(client, username):
    response = client.post(
        "/api/login",
        json={"username": username, "password": "pass123"},
    )
    assert response.status_code == 200


def test_fr05_admin_can_view_all_records(client, fr05_data):
    login(client, "admin_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 3
    assert len(data["records"]) == 3


def test_fr05_teacher_only_sees_assigned_subjects(client, fr05_data):
    login(client, "teacher_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] == 2
    assert all(
        record["subject_id"]
        == fr05_data["subjects"]["FR05 Mathematics"]
        for record in data["records"]
    )


def test_fr05_teacher_cannot_view_another_teachers_subject(
    client, fr05_data
):
    login(client, "teacher_fr05")

    other_subject = fr05_data["subjects"]["FR05 Science"]

    response = client.get(
        f"/api/attendance?subject_id={other_subject}"
    )

    assert response.status_code == 403


def test_fr05_student_only_sees_own_records(client, fr05_data):
    login(client, "student_a_fr05")

    response = client.get("/api/attendance")

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] == 2
    assert all(
        record["student_id"] == fr05_data["users"]["student_a_fr05"]
        for record in data["records"]
    )


def test_fr05_student_cannot_view_another_students_records(
    client, fr05_data
):
    login(client, "student_a_fr05")

    other_student = fr05_data["users"]["student_b_fr05"]

    response = client.get(
        f"/api/attendance?student_id={other_student}"
    )

    assert response.status_code == 403


def test_fr05_filter_by_subject(client, fr05_data):
    login(client, "admin_fr05")

    subject_id = fr05_data["subjects"]["FR05 Mathematics"]

    response = client.get(
        f"/api/attendance?subject_id={subject_id}"
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] == 2
    assert all(
        record["subject_id"] == subject_id
        for record in data["records"]
    )


def test_fr05_filter_by_date(client, fr05_data):
    login(client, "admin_fr05")

    response = client.get(
        "/api/attendance?attendance_date=2026-10-20"
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] == 2
    assert all(
        record["attendance_date"] == "2026-10-20"
        for record in data["records"]
    )


def test_fr05_empty_results(client, fr05_data):
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
        "attendance_date=not-a-date",
    ],
)
def test_fr05_invalid_filters_return_400(client, fr05_data, query):
    login(client, "admin_fr05")

    response = client.get(f"/api/attendance?{query}")

    assert response.status_code == 400


def test_fr05_requires_authentication(client, fr05_data):
    response = client.get("/api/attendance")

    assert response.status_code == 401