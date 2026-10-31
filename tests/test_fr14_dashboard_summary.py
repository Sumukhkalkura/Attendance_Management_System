"""Tests for FR-14: Role-Based Dashboard Summary."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def fr14_users(client):
    """Create test users for all three dashboard roles."""

    db_path = client.application.config["DATABASE"]

    users = [
        ("admin_fr14", "admin"),
        ("teacher_fr14", "teacher"),
        ("student_fr14", "student"),
    ]

    with sqlite3.connect(db_path) as connection:
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

    return users


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


def test_fr14_dashboard_requires_authentication(client):
    """Unauthenticated users cannot access the dashboard."""

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@pytest.mark.parametrize(
    "username, expected_location",
    [
        ("admin_fr14", "/admin"),
        ("teacher_fr14", "/teacher"),
        ("student_fr14", "/student"),
    ],
)
def test_fr14_dashboard_redirects_by_role(
    client, fr14_users, username, expected_location
):
    """Users are redirected to their role-specific dashboard."""

    login(client, username)

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert expected_location in response.headers["Location"]


@pytest.mark.parametrize(
    "username, dashboard_url, expected_elements",
    [
        (
            "admin_fr14",
            "/admin",
            [
                "statStudents",
                "statTeachers",
                "statClasses",
                "statSubjects",
                "statOverall",
                "lowAttendanceTable",
            ],
        ),
        (
            "teacher_fr14",
            "/teacher",
            [
                "statSubjects",
                "statClasses",
                "statStudents",
                "statAverage",
                "subjectList",
                "lowTable",
            ],
        ),
        (
            "student_fr14",
            "/student",
            [
                "overallRing",
                "overallPercent",
                "countPresent",
                "countAbsent",
                "countLate",
                "subjectBreakdown",
                "recentList",
            ],
        ),
    ],
)
def test_fr14_dashboard_displays_role_relevant_summary(
    client, fr14_users, username, dashboard_url, expected_elements
):
    """Each role receives a dashboard with its relevant summary elements."""

    login(client, username)

    response = client.get(dashboard_url)

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    for element in expected_elements:
        assert element in html


@pytest.mark.parametrize(
    "username, wrong_dashboard, correct_dashboard",
    [
        ("admin_fr14", "/student", "/admin"),
        ("teacher_fr14", "/admin", "/teacher"),
        ("student_fr14", "/teacher", "/student"),
    ],
)
def test_fr14_users_cannot_open_another_roles_dashboard(
    client, fr14_users, username, wrong_dashboard, correct_dashboard
):
    """Users are redirected away from dashboards belonging to other roles."""

    login(client, username)

    response = client.get(wrong_dashboard)

    assert response.status_code == 302
    assert correct_dashboard in response.headers["Location"]
@pytest.fixture
def fr14_attendance_data(client):
    """Create sample database records for dashboard testing."""

    db_path = client.application.config["DATABASE"]
    ids = {}

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        users = [
            ("admin_data_fr14", "admin"),
            ("teacher_one_fr14", "teacher"),
            ("teacher_two_fr14", "teacher"),
            ("student_one_fr14", "student"),
            ("student_two_fr14", "student"),
        ]

        for username, role in users:
            cursor = connection.execute(
                """
                INSERT INTO users
                    (username, password_hash, role, active)
                VALUES (?, ?, ?, 1)
                """,
                (username, generate_password_hash("pass123"), role),
            )
            ids[username] = cursor.lastrowid

        for name, teacher in [
            ("FR14 Class One", "teacher_one_fr14"),
            ("FR14 Class Two", "teacher_two_fr14"),
        ]:
            cursor = connection.execute(
                "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
                (name, ids[teacher]),
            )
            ids[name] = cursor.lastrowid

        for name, teacher in [
            ("FR14 Mathematics", "teacher_one_fr14"),
            ("FR14 Physics", "teacher_two_fr14"),
        ]:
            cursor = connection.execute(
                "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
                (name, ids[teacher]),
            )
            ids[name] = cursor.lastrowid

        # Enroll students in their respective classes and subjects.
        for student in ("student_one_fr14", "student_two_fr14"):
            connection.execute(
                """
                INSERT INTO enrollments
                    (student_id, class_id, subject_id)
                VALUES (?, ?, ?)
                """,
                (
                    ids[student],
                    ids["FR14 Class One"],
                    ids["FR14 Mathematics"],
                ),
            )

        connection.execute(
            """
            INSERT INTO enrollments
                (student_id, class_id, subject_id)
            VALUES (?, ?, ?)
            """,
            (
                ids["student_one_fr14"],
                ids["FR14 Class Two"],
                ids["FR14 Physics"],
            ),
        )

        attendance = [
            (ids["student_one_fr14"], ids["FR14 Mathematics"], "2026-10-01", "Present"),
            (ids["student_one_fr14"], ids["FR14 Mathematics"], "2026-10-02", "Absent"),
            (ids["student_one_fr14"], ids["FR14 Mathematics"], "2026-10-03", "Late"),
            (ids["student_one_fr14"], ids["FR14 Physics"], "2026-10-04", "Present"),
            (ids["student_two_fr14"], ids["FR14 Mathematics"], "2026-10-01", "Present"),
            (ids["student_two_fr14"], ids["FR14 Mathematics"], "2026-10-02", "Present"),
        ]

        connection.executemany(
            """
            INSERT INTO attendance
                (student_id, subject_id, attendance_date, status)
            VALUES (?, ?, ?, ?)
            """,
            attendance,
        )

    return ids


def test_fr14_admin_dashboard_summary_matches_database_records(
    client, fr14_attendance_data
):
    """Verify admin dashboard statistics using actual database records."""

    login(client, "admin_data_fr14")

    users = client.get("/api/users").get_json()["users"]
    classes = client.get("/api/classes").get_json()["classes"]
    subjects = client.get("/api/subjects").get_json()["subjects"]
    percentages = client.get(
        "/api/attendance/percentages"
    ).get_json()["students"]

    assert sum(u["role"] == "student" for u in users) == 2
    assert sum(u["role"] == "teacher" for u in users) == 2
    assert len(classes) == 2
    assert len(subjects) == 2

    students = {s["student_name"]: s for s in percentages}

    assert students["student_one_fr14"]["total_classes"] == 4
    assert students["student_one_fr14"]["classes_attended"] == 2
    assert students["student_one_fr14"]["attendance_percentage"] == 50.0

    assert students["student_two_fr14"]["total_classes"] == 2
    assert students["student_two_fr14"]["classes_attended"] == 2
    assert students["student_two_fr14"]["attendance_percentage"] == 100.0

    attended = sum(s["classes_attended"] for s in percentages)
    total = sum(s["total_classes"] for s in percentages)

    assert attended == 4
    assert total == 6
    assert round(attended / total * 100, 1) == 66.7


def test_fr14_teacher_dashboard_summary_matches_assigned_records(
    client, fr14_attendance_data
):
    """Verify teacher dashboard statistics use only assigned subjects."""

    login(client, "teacher_one_fr14")

    subjects = client.get("/api/teacher/subjects").get_json()["subjects"]
    classes = client.get("/api/teacher/classes").get_json()["classes"]
    percentages = client.get(
        "/api/attendance/percentages"
    ).get_json()["students"]

    assert [s["name"] for s in subjects] == ["FR14 Mathematics"]
    assert [c["name"] for c in classes] == ["FR14 Class One"]

    tracked = [s for s in percentages if s["total_classes"] > 0]

    assert len(tracked) == 2

    students = {s["student_name"]: s for s in tracked}

    assert students["student_one_fr14"]["total_classes"] == 3
    assert students["student_one_fr14"]["classes_attended"] == 1
    assert students["student_one_fr14"]["attendance_percentage"] == 33.33

    assert students["student_two_fr14"]["total_classes"] == 2
    assert students["student_two_fr14"]["classes_attended"] == 2
    assert students["student_two_fr14"]["attendance_percentage"] == 100.0

    attended = sum(s["classes_attended"] for s in tracked)
    total = sum(s["total_classes"] for s in tracked)

    assert attended == 3
    assert total == 5
    assert round(attended / total * 100, 1) == 60.0


def test_fr14_teacher_cannot_view_another_teachers_subject(
    client, fr14_attendance_data
):
    """Verify teacher dashboard data is restricted to assigned subjects."""

    login(client, "teacher_one_fr14")

    response = client.get(
        "/api/attendance/percentages"
        f"?subject_id={fr14_attendance_data['FR14 Physics']}"
    )

    assert response.status_code == 403


def test_fr14_student_dashboard_summary_matches_own_records(
    client, fr14_attendance_data
):
    """Verify student dashboard counts and percentage."""

    login(client, "student_one_fr14")

    response = client.get("/api/attendance")

    assert response.status_code == 200

    records = response.get_json()["records"]

    assert len(records) == 4

    assert {
    record["student_name"] for record in records
    } == {"student_one_fr14"}

    present = sum(r["status"] == "Present" for r in records)
    absent = sum(r["status"] == "Absent" for r in records)
    late = sum(r["status"] == "Late" for r in records)

    assert present == 2
    assert absent == 1
    assert late == 1

    percentage = round(present / len(records) * 100, 2)

    assert percentage == 50.0

    subjects = {}

    for record in records:
        subjects.setdefault(record["subject_name"], []).append(
            record["status"]
        )

    assert subjects["FR14 Mathematics"] == [
        "Late", "Absent", "Present"
    ]

    assert subjects["FR14 Physics"] == ["Present"]


def test_fr14_student_cannot_view_another_students_attendance(
    client, fr14_attendance_data
):
    """Verify students cannot access another student's dashboard data."""

    login(client, "student_one_fr14")

    response = client.get(
        "/api/attendance"
        f"?student_id={fr14_attendance_data['student_two_fr14']}"
    )

    assert response.status_code == 403