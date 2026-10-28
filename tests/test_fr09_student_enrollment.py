"""Tests for FR-09 student enrollment."""

import pytest

from app.db import get_db


def create_user(client, role, username):
    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, 1)
            """,
            (username, "test_hash", role),
        )
        db.commit()
        return cursor.lastrowid


def create_class(client, name="Test Class"):
    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO classes (name) VALUES (?)",
            (name,),
        )
        db.commit()
        return cursor.lastrowid


def create_subject(client, name="Test Subject"):
    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO subjects (name) VALUES (?)",
            (name,),
        )
        db.commit()
        return cursor.lastrowid


def login_as(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id


@pytest.fixture
def enrollment_setup(client):
    admin_id = create_user(client, "admin", "fr09_admin")
    student_id = create_user(client, "student", "fr09_student")
    teacher_id = create_user(client, "teacher", "fr09_teacher")
    class_id = create_class(client)
    subject_id = create_subject(client)

    return {
        "admin_id": admin_id,
        "student_id": student_id,
        "teacher_id": teacher_id,
        "class_id": class_id,
        "subject_id": subject_id,
    }


def test_admin_can_enroll_student(client, enrollment_setup):
    data = enrollment_setup
    login_as(client, data["admin_id"])

    response = client.post(
        "/api/enrollments",
        json={
            "student_id": data["student_id"],
            "class_id": data["class_id"],
            "subject_id": data["subject_id"],
        },
    )

    assert response.status_code == 201

    with client.application.app_context():
        row = get_db().execute(
            """
            SELECT student_id, class_id, subject_id
            FROM enrollments
            WHERE student_id = ? AND class_id = ? AND subject_id = ?
            """,
            (
                data["student_id"],
                data["class_id"],
                data["subject_id"],
            ),
        ).fetchone()

    assert row is not None


def test_duplicate_enrollment_is_rejected(client, enrollment_setup):
    data = enrollment_setup
    login_as(client, data["admin_id"])

    payload = {
        "student_id": data["student_id"],
        "class_id": data["class_id"],
        "subject_id": data["subject_id"],
    }

    first = client.post("/api/enrollments", json=payload)
    second = client.post("/api/enrollments", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.parametrize(
    "role",
    ["teacher", "student"],
)
def test_non_admin_cannot_enroll_student(
    client, enrollment_setup, role
):
    data = enrollment_setup
    user_id = (
        data["teacher_id"]
        if role == "teacher"
        else data["student_id"]
    )
    login_as(client, user_id)

    response = client.post(
        "/api/enrollments",
        json={
            "student_id": data["student_id"],
            "class_id": data["class_id"],
            "subject_id": data["subject_id"],
        },
    )

    assert response.status_code == 403


def test_missing_fields_are_rejected(client, enrollment_setup):
    login_as(client, enrollment_setup["admin_id"])

    response = client.post(
        "/api/enrollments",
        json={"student_id": enrollment_setup["student_id"]},
    )

    assert response.status_code == 400


def test_nonexistent_class_is_rejected(client, enrollment_setup):
    data = enrollment_setup
    login_as(client, data["admin_id"])

    response = client.post(
        "/api/enrollments",
        json={
            "student_id": data["student_id"],
            "class_id": 999999,
            "subject_id": data["subject_id"],
        },
    )

    assert response.status_code == 404