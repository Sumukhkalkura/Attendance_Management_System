import sqlite3

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def fr04_data(client):
    app = client.application

    with app.app_context():
        db_path = app.config["DATABASE"]
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = ON")

        # Create users.
        connection.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, 1)
            """,
            ("admin_fr04", generate_password_hash("pass123"), "admin"),
        )

        connection.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, 1)
            """,
            ("teacher_fr04", generate_password_hash("pass123"), "teacher"),
        )

        connection.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, 1)
            """,
            ("student_a_fr04", generate_password_hash("pass123"), "student"),
        )

        connection.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, 1)
            """,
            ("student_b_fr04", generate_password_hash("pass123"), "student"),
        )

        connection.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, 1)
            """,
            ("student_c_fr04", generate_password_hash("pass123"), "student"),
        )

        connection.execute(
            """
            INSERT INTO subjects (name, teacher_id)
            SELECT 'FR04 Mathematics', id
            FROM users
            WHERE username = 'teacher_fr04'
            """
        )

        connection.execute(
            """
            INSERT INTO subjects (name, teacher_id)
            SELECT 'FR04 Science', id
            FROM users
            WHERE username = 'teacher_fr04'
            """
        )

        ids = {}

        for username in (
            "admin_fr04",
            "teacher_fr04",
            "student_a_fr04",
            "student_b_fr04",
            "student_c_fr04",
        ):
            ids[username] = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()[0]

        for subject_name in ("FR04 Mathematics", "FR04 Science"):
            ids[subject_name] = connection.execute(
                "SELECT id FROM subjects WHERE name = ?",
                (subject_name,),
            ).fetchone()[0]

        math_id = ids["FR04 Mathematics"]
        science_id = ids["FR04 Science"]

        # Student A: 2 Present, 1 Absent -> 66.67%.
        # Student B: 1 Present, 1 Absent -> 50%.
        # Student C: no attendance records -> 0%.
        attendance_rows = [
            (ids["student_a_fr04"], math_id, "2026-10-01", "Present"),
            (ids["student_a_fr04"], math_id, "2026-10-02", "Present"),
            (ids["student_a_fr04"], math_id, "2026-10-03", "Absent"),
            (ids["student_b_fr04"], math_id, "2026-10-01", "Present"),
            (ids["student_b_fr04"], math_id, "2026-10-02", "Absent"),
            (ids["student_a_fr04"], science_id, "2026-10-04", "Late"),
        ]

        connection.executemany(
            """
            INSERT INTO attendance
                (student_id, subject_id, attendance_date, status)
            VALUES (?, ?, ?, ?)
            """,
            attendance_rows,
        )

        connection.commit()
        connection.close()

    return ids


def login(client, username):
    response = client.post(
        "/api/login",
        json={"username": username, "password": "pass123"},
    )
    assert response.status_code == 200


def test_fr04_percentages_calculate_correctly(client, fr04_data):
    login(client, "admin_fr04")

    response = client.get("/api/attendance/percentages")

    assert response.status_code == 200

    body = response.get_json()
    assert body["count"] == 3

    students = {
        student["student_name"]: student
        for student in body["students"]
    }

    student_a = students["student_a_fr04"]
    assert student_a["classes_attended"] == 2
    assert student_a["total_classes"] == 4
    assert student_a["attendance_percentage"] == 50.0

    student_b = students["student_b_fr04"]
    assert student_b["classes_attended"] == 1
    assert student_b["total_classes"] == 2
    assert student_b["attendance_percentage"] == 50.0

    student_c = students["student_c_fr04"]
    assert student_c["classes_attended"] == 0
    assert student_c["total_classes"] == 0
    assert student_c["attendance_percentage"] == 0.0


def test_fr04_subject_filter(client, fr04_data):
    login(client, "admin_fr04")

    subject_id = fr04_data["FR04 Mathematics"]
    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 200

    body = response.get_json()
    students = {
        student["student_name"]: student
        for student in body["students"]
    }

    assert students["student_a_fr04"]["total_classes"] == 3
    assert students["student_a_fr04"]["attendance_percentage"] == 66.67

    assert students["student_b_fr04"]["total_classes"] == 2
    assert students["student_b_fr04"]["attendance_percentage"] == 50.0

    assert students["student_c_fr04"]["total_classes"] == 0


def test_fr04_late_is_not_counted_as_attended(client, fr04_data):
    login(client, "admin_fr04")

    subject_id = fr04_data["FR04 Science"]
    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 200

    students = {
        student["student_name"]: student
        for student in response.get_json()["students"]
    }

    student_a = students["student_a_fr04"]
    assert student_a["classes_attended"] == 0
    assert student_a["total_classes"] == 1
    assert student_a["attendance_percentage"] == 0.0


def test_fr04_requires_authentication(client, fr04_data):
    response = client.get("/api/attendance/percentages")
    assert response.status_code == 401


def test_fr04_student_cannot_access_percentages(client, fr04_data):
    login(client, "student_a_fr04")

    response = client.get("/api/attendance/percentages")
    assert response.status_code == 403


@pytest.mark.parametrize("subject_id", ["abc", "0", "-1"])
def test_fr04_rejects_invalid_subject_id(client, fr04_data, subject_id):
    login(client, "admin_fr04")

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 400
