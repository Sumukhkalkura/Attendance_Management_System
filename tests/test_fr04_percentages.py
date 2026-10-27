"""Tests for FR-04: Attendance Percentage Calculation."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def fr04_data(client):
    """Create isolated users, subjects, and attendance records."""
    app = client.application

    with app.app_context():
        db_path = app.config["DATABASE"]
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = ON")

        # -------------------------------------------------------------
        # Create users
        # -------------------------------------------------------------
        users = [
            ("admin_fr04", "admin"),
            ("teacher_fr04", "teacher"),
            ("teacher_other_fr04", "teacher"),
            ("teacher_unassigned_fr04", "teacher"),
            ("student_a_fr04", "student"),
            ("student_b_fr04", "student"),
            ("student_c_fr04", "student"),
        ]

        for username, role in users:
            connection.execute(
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

        # -------------------------------------------------------------
        # Create subjects owned by different teachers
        # -------------------------------------------------------------
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

        connection.execute(
            """
            INSERT INTO subjects (name, teacher_id)
            SELECT 'FR04 History', id
            FROM users
            WHERE username = 'teacher_other_fr04'
            """
        )

        # -------------------------------------------------------------
        # Retrieve IDs
        # -------------------------------------------------------------
        ids = {}

        usernames = [
            username for username, _ in users
        ]

        for username in usernames:
            ids[username] = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()[0]

        subject_names = [
            "FR04 Mathematics",
            "FR04 Science",
            "FR04 History",
        ]

        for subject_name in subject_names:
            ids[subject_name] = connection.execute(
                "SELECT id FROM subjects WHERE name = ?",
                (subject_name,),
            ).fetchone()[0]

        math_id = ids["FR04 Mathematics"]
        science_id = ids["FR04 Science"]

        # -------------------------------------------------------------
        # Initial attendance records
        #
        # Student A:
        #   Mathematics: 2 Present, 1 Absent
        #   Science:     1 Late
        #   Total:       2 / 4 = 50%
        #
        # Student B:
        #   Mathematics: 1 Present, 1 Absent
        #   Total:       1 / 2 = 50%
        #
        # Student C:
        #   No attendance records
        # -------------------------------------------------------------
        attendance_rows = [
            (
                ids["student_a_fr04"],
                math_id,
                "2026-10-01",
                "Present",
            ),
            (
                ids["student_a_fr04"],
                math_id,
                "2026-10-02",
                "Present",
            ),
            (
                ids["student_a_fr04"],
                math_id,
                "2026-10-03",
                "Absent",
            ),
            (
                ids["student_b_fr04"],
                math_id,
                "2026-10-01",
                "Present",
            ),
            (
                ids["student_b_fr04"],
                math_id,
                "2026-10-02",
                "Absent",
            ),
            (
                ids["student_a_fr04"],
                science_id,
                "2026-10-04",
                "Late",
            ),
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
    """Log in a test user."""
    response = client.post(
        "/api/login",
        json={
            "username": username,
            "password": "pass123",
        },
    )

    assert response.status_code == 200


def add_history_attendance(client, fr04_data):
    """Add a History attendance record owned by another teacher."""
    db_path = client.application.config["DATABASE"]

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO attendance
                (student_id, subject_id, attendance_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                fr04_data["student_b_fr04"],
                fr04_data["FR04 History"],
                "2026-10-05",
                "Present",
            ),
        )

        connection.commit()


# =====================================================================
# Existing FR-04 calculation tests
# =====================================================================

def test_fr04_percentages_calculate_correctly(client, fr04_data):
    """Calculate percentages correctly across all subjects for an admin."""
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
    """Filter attendance percentage calculations by subject."""
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

    student_a = students["student_a_fr04"]
    assert student_a["total_classes"] == 3
    assert student_a["classes_attended"] == 2
    assert student_a["attendance_percentage"] == 66.67

    student_b = students["student_b_fr04"]
    assert student_b["total_classes"] == 2
    assert student_b["classes_attended"] == 1
    assert student_b["attendance_percentage"] == 50.0

    student_c = students["student_c_fr04"]
    assert student_c["total_classes"] == 0
    assert student_c["attendance_percentage"] == 0.0


def test_fr04_late_is_not_counted_as_attended(client, fr04_data):
    """Preserve the existing behavior for Late attendance."""
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


# =====================================================================
# FR-04 administrator authorization tests
# =====================================================================

def test_fr04_admin_can_view_percentages_across_all_subjects(
    client, fr04_data
):
    """Admins can calculate percentages across different teachers' subjects."""
    add_history_attendance(client, fr04_data)

    login(client, "admin_fr04")

    response = client.get("/api/attendance/percentages")

    assert response.status_code == 200

    students = {
        student["student_name"]: student
        for student in response.get_json()["students"]
    }

    # Student B has:
    # Mathematics: 1 Present, 1 Absent
    # History:     1 Present
    student_b = students["student_b_fr04"]

    assert student_b["classes_attended"] == 2
    assert student_b["total_classes"] == 3
    assert student_b["attendance_percentage"] == 66.67


# =====================================================================
# FR-04 teacher authorization and isolation tests
# =====================================================================

def test_fr04_authorized_teacher_can_view_assigned_subject(
    client, fr04_data
):
    """A teacher can calculate percentages for their assigned subject."""
    login(client, "teacher_fr04")

    subject_id = fr04_data["FR04 Mathematics"]

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 200

    students = {
        student["student_name"]: student
        for student in response.get_json()["students"]
    }

    student_a = students["student_a_fr04"]

    assert student_a["classes_attended"] == 2
    assert student_a["total_classes"] == 3
    assert student_a["attendance_percentage"] == 66.67


def test_fr04_teacher_can_view_another_assigned_subject(
    client, fr04_data
):
    """A teacher can access a second subject assigned to the same teacher."""
    login(client, "teacher_fr04")

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


def test_fr04_teacher_cannot_view_another_teachers_subject(
    client, fr04_data
):
    """A teacher cannot request percentages for an unassigned subject."""
    login(client, "teacher_fr04")

    subject_id = fr04_data["FR04 History"]

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 403


def test_fr04_teacher_without_filter_sees_only_assigned_subjects(
    client, fr04_data
):
    """Without a subject filter, teacher calculations exclude foreign subjects."""
    add_history_attendance(client, fr04_data)

    login(client, "teacher_fr04")

    response = client.get("/api/attendance/percentages")

    assert response.status_code == 200

    students = {
        student["student_name"]: student
        for student in response.get_json()["students"]
    }

    # History belongs to teacher_other_fr04 and must not be counted.
    student_b = students["student_b_fr04"]

    assert student_b["classes_attended"] == 1
    assert student_b["total_classes"] == 2
    assert student_b["attendance_percentage"] == 50.0

    # Student A has three Mathematics records and one Science record.
    student_a = students["student_a_fr04"]

    assert student_a["classes_attended"] == 2
    assert student_a["total_classes"] == 4
    assert student_a["attendance_percentage"] == 50.0


def test_fr04_teacher_with_no_assigned_subjects_sees_no_foreign_records(
    client, fr04_data
):
    """A teacher with no subjects must not see other teachers' attendance."""
    add_history_attendance(client, fr04_data)

    login(client, "teacher_unassigned_fr04")

    response = client.get("/api/attendance/percentages")

    assert response.status_code == 200

    students = {
        student["student_name"]: student
        for student in response.get_json()["students"]
    }

    assert len(students) == 3

    for student in students.values():
        assert student["classes_attended"] == 0
        assert student["total_classes"] == 0
        assert student["attendance_percentage"] == 0.0


# =====================================================================
# FR-04 authentication and permissions tests
# =====================================================================

def test_fr04_requires_authentication(client, fr04_data):
    """Unauthenticated users cannot access attendance percentages."""
    response = client.get("/api/attendance/percentages")

    assert response.status_code == 401


def test_fr04_student_cannot_access_percentages(client, fr04_data):
    """Students cannot access the administrator/teacher percentage endpoint."""
    login(client, "student_a_fr04")

    response = client.get("/api/attendance/percentages")

    assert response.status_code == 403


@pytest.mark.parametrize("subject_id", ["abc", "0", "-1"])
def test_fr04_rejects_invalid_subject_id(
    client, fr04_data, subject_id
):
    """Invalid subject identifiers are rejected."""
    login(client, "admin_fr04")

    response = client.get(
        f"/api/attendance/percentages?subject_id={subject_id}"
    )

    assert response.status_code == 400
