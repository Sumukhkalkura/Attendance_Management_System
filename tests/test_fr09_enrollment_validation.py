"""FR-09 tests added in Deliverable 3, Phase 2.

UT_FR-09_05 - Enrolling a user who is not an active student, or using an
unknown student/subject id, is rejected and creates no enrollment.
"""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from app import create_app

PASSWORD = "Admin01Pass!"


@pytest.fixture
def setup(tmp_path):
    database = tmp_path / "fr09_phase2.db"
    app = create_app({"TESTING": True, "DATABASE": str(database), "SECRET_KEY": "fr09-phase2-secret"})
    ids = {}
    with sqlite3.connect(database) as conn:
        pw = generate_password_hash(PASSWORD)
        for username, role, active in [
            ("Admin01", "admin", 1),
            ("Teacher01", "teacher", 1),
            ("S01", "student", 1),
            ("S_inactive", "student", 0),
        ]:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
                (username, pw, role, active),
            )
            ids[username] = cur.lastrowid
        ids["class"] = conn.execute("INSERT INTO classes (name) VALUES ('CSE-A')").lastrowid
        ids["subject"] = conn.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES ('DBMS', ?)", (ids["Teacher01"],)
        ).lastrowid
        conn.commit()
    client = app.test_client()
    assert client.post("/api/login", json={"username": "Admin01", "password": PASSWORD}).status_code == 200
    return app, client, ids


def enrollment_count(app):
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        return conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]


@pytest.mark.parametrize(
    "who, expected_status, expected_error",
    [
        ("Teacher01", 404, "Student not found"),
        ("Admin01", 404, "Student not found"),
        ("S_inactive", 400, "Student account is inactive"),
    ],
)
def test_ut_fr_09_05_only_active_students_can_be_enrolled(setup, who, expected_status, expected_error):
    app, client, ids = setup
    response = client.post(
        "/api/enrollments",
        json={"student_id": ids[who], "class_id": ids["class"], "subject_id": ids["subject"]},
    )
    assert response.status_code == expected_status
    assert response.get_json() == {"error": expected_error}
    assert enrollment_count(app) == 0


def test_ut_fr_09_05_unknown_student_or_subject_rejected(setup):
    app, client, ids = setup
    unknown_student = client.post(
        "/api/enrollments",
        json={"student_id": 99999, "class_id": ids["class"], "subject_id": ids["subject"]},
    )
    assert unknown_student.status_code == 404
    assert unknown_student.get_json() == {"error": "Student not found"}

    unknown_subject = client.post(
        "/api/enrollments",
        json={"student_id": ids["S01"], "class_id": ids["class"], "subject_id": 99999},
    )
    assert unknown_subject.status_code == 404
    assert unknown_subject.get_json() == {"error": "Subject not found"}

    assert enrollment_count(app) == 0


@pytest.mark.parametrize("bad_id", [0, -1, "1", 1.5, True, None])
def test_ut_fr_09_05_non_positive_or_non_integer_ids_rejected(setup, bad_id):
    app, client, ids = setup
    response = client.post(
        "/api/enrollments",
        json={"student_id": bad_id, "class_id": ids["class"], "subject_id": ids["subject"]},
    )
    assert response.status_code == 400
    assert enrollment_count(app) == 0


def test_ut_fr_09_05_control_valid_active_student_is_enrolled(setup):
    """Control case: the same request with an active student succeeds."""
    app, client, ids = setup
    response = client.post(
        "/api/enrollments",
        json={"student_id": ids["S01"], "class_id": ids["class"], "subject_id": ids["subject"]},
    )
    assert response.status_code == 201
    assert enrollment_count(app) == 1
