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