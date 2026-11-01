"""Tests for NFR-04: Usability and Consistent User Interface."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def nfr04_users(client):
    """Create test users for all dashboard roles."""

    db_path = client.application.config["DATABASE"]

    users = [
        ("admin_nfr04", "admin"),
        ("teacher_nfr04", "teacher"),
        ("student_nfr04", "student"),
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


@pytest.mark.parametrize(
    "username, dashboard",
    [
        ("admin_nfr04", "/admin"),
        ("teacher_nfr04", "/teacher"),
        ("student_nfr04", "/student"),
    ],
)
def test_nfr04_all_dashboards_use_consistent_layout(
    client, nfr04_users, username, dashboard
):
    """All dashboards use the common base layout."""

    login(client, username)

    response = client.get(dashboard)

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'class="sidebar"' in html
    assert 'class="topbar"' in html
    assert 'class="content"' in html
    assert 'aria-label="Main navigation"' in html
    assert 'id="logoutButton"' in html
    assert 'id="changePasswordButton"' in html


@pytest.mark.parametrize(
    "username, dashboard, expected_links",
    [
        (
            "admin_nfr04",
            "/admin",
            [
                "Overview",
                "Users",
                "Classes",
                "Subjects",
                "Enrollments",
                "Attendance",
            ],
        ),
        (
            "teacher_nfr04",
            "/teacher",
            [
                "Overview",
                "Mark attendance",
                "Attendance records",
                "Percentages",
            ],
        ),
        (
            "student_nfr04",
            "/student",
            [
                "My attendance",
                "Attendance history",
            ],
        ),
    ],
)
def test_nfr04_navigation_labels_are_clear(
    client, nfr04_users, username, dashboard, expected_links
):
    """Each role has clearly named navigation links."""

    login(client, username)

    response = client.get(dashboard)

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    for label in expected_links:
        assert label in html


@pytest.mark.parametrize(
    "username, dashboard",
    [
        ("admin_nfr04", "/admin"),
        ("teacher_nfr04", "/teacher"),
        ("student_nfr04", "/student"),
    ],
)
def test_nfr04_navigation_controls_are_accessible(
    client, nfr04_users, username, dashboard
):
    """Navigation controls include accessibility attributes."""

    login(client, username)

    response = client.get(dashboard)

    html = response.get_data(as_text=True)

    assert 'id="menuToggle"' in html
    assert 'aria-label="Open navigation"' in html
    assert 'aria-controls="sidebar"' in html
    assert 'aria-expanded="false"' in html


def test_nfr04_dashboard_navigation_supports_section_switching(
    client, nfr04_users
):
    """Shared JavaScript supports navigation between dashboard sections."""

    login(client, "admin_nfr04")

    response = client.get("/admin")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'data-section="overview"' in html
    assert 'data-section="users"' in html
    assert 'data-section="classes"' in html

    js_response = client.get("/static/js/common.js")

    assert js_response.status_code == 200

    javascript = js_response.get_data(as_text=True)

    assert "hashchange" in javascript
    assert "initSections" in javascript
    assert 'setAttribute("aria-current", "page")' in javascript


def test_nfr04_all_dashboards_load_shared_resources(
    client, nfr04_users
):
    """Dashboards load the shared stylesheet and JavaScript."""

    login(client, "admin_nfr04")

    response = client.get("/admin")

    html = response.get_data(as_text=True)

    assert "/static/css/app.css" in html
    assert "/static/js/common.js" in html

    css_response = client.get("/static/css/app.css")

    assert css_response.status_code == 200

    js_response = client.get("/static/js/common.js")

    assert js_response.status_code == 200


def test_nfr04_interface_supports_responsive_layout(
    client, nfr04_users
):
    """Shared CSS contains responsive layout rules."""

    login(client, "admin_nfr04")

    response = client.get("/static/css/app.css")

    assert response.status_code == 200

    css = response.get_data(as_text=True)

    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 560px)" in css


def test_nfr04_interface_supports_keyboard_focus(
    client, nfr04_users
):
    """Interactive controls have visible keyboard focus styling."""

    login(client, "admin_nfr04")

    response = client.get("/static/css/app.css")

    css = response.get_data(as_text=True)

    assert ":focus-visible" in css
    assert ".nav-link:focus-visible" in css
    assert ".btn:focus-visible" in css


def test_nfr04_reduced_motion_is_supported(
    client, nfr04_users
):
    """The interface includes reduced-motion styling."""

    login(client, "admin_nfr04")

    response = client.get("/static/css/app.css")

    css = response.get_data(as_text=True)

    assert "@media (prefers-reduced-motion: reduce)" in css