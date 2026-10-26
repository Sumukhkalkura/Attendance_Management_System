import sqlite3

import pytest


@pytest.fixture
def attendance_client(tmp_path):
    from app import create_app

    database = tmp_path / "attendance_test.db"

    app = create_app({
        "TESTING": True,
        "DATABASE": str(database),
        "SECRET_KEY": "test-only",
    })

    connection = sqlite3.connect(database)

    connection.execute(
        """
        INSERT INTO users (
            username, password_hash, role, active
        )
        VALUES (?, ?, ?, ?)
        """,
        ("teacher1", "test-hash", "teacher", 1)
    )

    teacher_id = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        ("teacher1",)
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO users (
            username, password_hash, role, active
        )
        VALUES (?, ?, ?, ?)
        """,
        ("student1", "test-hash", "student", 1)
    )

    student_id = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        ("student1",)
    ).fetchone()[0]

    connection.execute(
        "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
        ("Mathematics", teacher_id)
    )

    subject_id = connection.execute(
        "SELECT id FROM subjects WHERE name = ?",
        ("Mathematics",)
    ).fetchone()[0]

    connection.commit()
    connection.close()

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = teacher_id

        yield client, database, student_id, subject_id


def test_fr04_percentage_calculation(attendance_client):
    client, database, student_id, subject_id = attendance_client

    connection = sqlite3.connect(database)

    records = [
        ("2026-10-01", "Present"),
        ("2026-10-02", "Present"),
        ("2026-10-03", "Present"),
        ("2026-10-04", "Absent"),
        ("2026-10-05", "Absent"),
    ]

    for attendance_date, status in records:
        connection.execute(
            """
            INSERT INTO attendance (
                student_id, subject_id, attendance_date, status
            )
            VALUES (?, ?, ?, ?)
            """,
            (student_id, subject_id, attendance_date, status)
        )

    connection.commit()
    connection.close()

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 200

    data = response.get_json()
    student = next(
        s for s in data["students"]
        if s["student_id"] == student_id
    )

    assert student["classes_attended"] == 3
    assert student["total_classes"] == 5
    assert student["attendance_percentage"] == 60.0


def test_fr04_zero_attendance(attendance_client):
    client, _, student_id, subject_id = attendance_client

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 200

    data = response.get_json()
    student = next(
        s for s in data["students"]
        if s["student_id"] == student_id
    )

    assert student["classes_attended"] == 0
    assert student["total_classes"] == 0
    assert student["attendance_percentage"] == 0.0


def test_fr04_unauthenticated_access(attendance_client):
    client, _, _, subject_id = attendance_client

    with client.session_transaction() as session:
        session.clear()

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 401
