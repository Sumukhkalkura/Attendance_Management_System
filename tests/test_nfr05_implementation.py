"""Tests for NFR-05: Cross-Browser Compatibility.

Validates that the Attendance Management System functions correctly and consistently
across commonly used modern web browsers (Chrome, Edge, Firefox, and Safari) on desktop
and mobile platforms, satisfying all acceptance criteria in the SRS and Backlog (US-26).
"""

import re
import sqlite3
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from session_helpers import plant_session

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Representative modern browser User-Agent strings
BROWSER_USER_AGENTS = {
    "chrome_windows": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "edge_windows": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    ),
    "firefox_linux": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    ),
    "safari_macos": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.3 Safari/605.1.15"
    ),
    "chrome_android": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36"
    ),
    "safari_ios": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1"
    ),
}


@pytest.fixture
def nfr05_users(client):
    """Create test users for each dashboard role."""
    db_path = client.application.config["DATABASE"]
    user_ids = {}

    with sqlite3.connect(db_path) as conn:
        for username, role in [
            ("admin_nfr05", "admin"),
            ("teacher_nfr05", "teacher"),
            ("student_nfr05", "student"),
        ]:
            cursor = conn.execute(
                """
                INSERT INTO users (username, password_hash, role, active)
                VALUES (?, ?, ?, 1)
                """,
                (username, generate_password_hash("ValidPass123!"), role),
            )
            user_ids[role] = cursor.lastrowid
        conn.commit()

    return user_ids


# -----------------------------------------------------------------------------
# 1. HTML5 Standards & Browser Directives
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("browser_name, user_agent", BROWSER_USER_AGENTS.items())
def test_nfr05_login_page_renders_for_all_supported_browsers(
    client, browser_name, user_agent
):
    """Login page returns valid HTML5 with doctype, charset, and viewport for all browsers."""
    response = client.get("/login", headers={"User-Agent": user_agent})

    assert response.status_code == 200
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)

    # Valid standard HTML5 doctype (case-insensitive)
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert '<meta charset="UTF-8">' in html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in html
    assert '<meta http-equiv="X-UA-Compatible" content="IE=edge">' in html
    assert '<link rel="stylesheet" href="/static/css/app.css">' in html
    assert '<script src="/static/js/login.js"></script>' in html


@pytest.mark.parametrize("browser_name, user_agent", BROWSER_USER_AGENTS.items())
def test_nfr05_x_ua_compatible_header_present_for_all_browsers(
    client, browser_name, user_agent
):
    """X-UA-Compatible header is delivered to ensure modern standards mode in Edge/Chromium."""
    response = client.get("/login", headers={"User-Agent": user_agent})

    assert response.status_code == 200
    assert response.headers.get("X-UA-Compatible") == "IE=edge"


@pytest.mark.parametrize("browser_name, user_agent", BROWSER_USER_AGENTS.items())
def test_nfr05_security_headers_consistent_across_browsers(
    client, browser_name, user_agent
):
    """Security and caching headers are delivered uniformly across all browsers."""
    response = client.get("/", headers={"User-Agent": user_agent})

    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("Cache-Control") == "no-store"


# -----------------------------------------------------------------------------
# 2. Static Assets MIME Types and Charsets
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "asset_path, expected_mimetype, expected_charset",
    [
        ("/static/css/app.css", "text/css", "utf-8"),
        ("/static/js/common.js", "application/javascript", "utf-8"),
        ("/static/js/login.js", "application/javascript", "utf-8"),
        ("/static/favicon.svg", "image/svg+xml", "utf-8"),
    ],
)
@pytest.mark.parametrize("browser_name, user_agent", BROWSER_USER_AGENTS.items())
def test_nfr05_static_assets_serve_correct_mime_types(
    client, browser_name, user_agent, asset_path, expected_mimetype, expected_charset
):
    """Static assets return correct MIME types and charsets regardless of requesting browser."""
    response = client.get(asset_path, headers={"User-Agent": user_agent})

    assert response.status_code == 200
    assert response.mimetype == expected_mimetype
    if expected_charset:
        assert expected_charset in response.headers.get("Content-Type", "").lower()


# -----------------------------------------------------------------------------
# 3. Cross-Browser CSS Standards Verification
# -----------------------------------------------------------------------------

def test_nfr05_css_vendor_prefixes_and_properties():
    """Shared stylesheet contains vendor-prefixed and standard cross-browser declarations."""
    css_path = PROJECT_ROOT / "app" / "static" / "css" / "app.css"
    assert css_path.exists(), "app.css stylesheet not found"

    css = css_path.read_text(encoding="utf-8")

    # Font smoothing: WebKit (Chrome/Edge/Safari) and Gecko (Firefox)
    assert "-webkit-font-smoothing: antialiased;" in css
    assert "-moz-osx-font-smoothing: grayscale;" in css

    # Text size adjust: WebKit and standard
    assert "-webkit-text-size-adjust: 100%;" in css
    assert "text-size-adjust: 100%;" in css

    # Backdrop filter: WebKit/Safari and standard
    assert "-webkit-backdrop-filter: blur(10px);" in css
    assert "backdrop-filter: blur(10px);" in css
    assert "-webkit-backdrop-filter: blur(2px);" in css
    assert "backdrop-filter: blur(2px);" in css

    # Responsive media queries for multi-device compatibility
    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 560px)" in css

    # Accessibility: focus-visible and reduced-motion
    assert ":focus-visible" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


# -----------------------------------------------------------------------------
# 4. JavaScript Cross-Browser Standards Verification
# -----------------------------------------------------------------------------

def test_nfr05_javascript_files_use_strict_mode_and_standards():
    """All frontend JavaScript modules enforce strict mode and standard DOM methods."""
    js_dir = PROJECT_ROOT / "app" / "static" / "js"
    js_files = ["common.js", "login.js", "admin.js", "teacher.js", "student.js"]

    for filename in js_files:
        filepath = js_dir / filename
        assert filepath.exists(), f"{filename} not found"
        code = filepath.read_text(encoding="utf-8")

        # Must enforce strict mode
        assert '"use strict";' in code or "'use strict';" in code, (
            f"{filename} must contain 'use strict';"
        )

        # Avoid obsolete proprietary DOM methods
        assert "document.all" not in code
        assert "attachEvent" not in code
        assert "window.event" not in code


def test_nfr05_javascript_polyfiils_and_resilience():
    """Client scripts include cross-browser polyfills for DOM methods and modal dialogs."""
    common_code = (PROJECT_ROOT / "app" / "static" / "js" / "common.js").read_text(
        encoding="utf-8"
    )
    login_code = (PROJECT_ROOT / "app" / "static" / "js" / "login.js").read_text(
        encoding="utf-8"
    )

    # replaceChildren polyfill in common.js
    assert "replaceChildren" in common_code
    # toggleAttribute polyfill in common.js and login.js
    assert "toggleAttribute" in common_code
    assert "toggleAttribute" in login_code

    # Dialog showModal defensive fallback
    assert "typeof dialog.showModal === \"function\"" in common_code
    assert "typeof dialog.close === \"function\"" in common_code


# -----------------------------------------------------------------------------
# 5. Cookie Security & SameSite Attributes Across Browsers
# -----------------------------------------------------------------------------

def test_nfr05_session_cookie_settings(client):
    """Session cookies use HttpOnly and SameSite=Lax for modern browser compliance."""
    app = client.application

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


# -----------------------------------------------------------------------------
# 6. Browser-Specific Fetch & Origin Request Handling
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "browser_name, extra_headers",
    [
        (
            "chrome_edge_fetch",
            {
                "User-Agent": BROWSER_USER_AGENTS["chrome_windows"],
                "Origin": "http://localhost",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
            },
        ),
        (
            "firefox_fetch",
            {
                "User-Agent": BROWSER_USER_AGENTS["firefox_linux"],
                "Origin": "http://localhost",
                "Referer": "http://localhost/login",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
            },
        ),
        (
            "safari_fetch",
            {
                "User-Agent": BROWSER_USER_AGENTS["safari_macos"],
                "Origin": "http://localhost",
                "Referer": "http://localhost/login",
            },
        ),
    ],
)
def test_nfr05_browser_login_api_requests(client, nfr05_users, browser_name, extra_headers):
    """API login requests succeed under Chrome, Firefox, and Safari request header styles."""
    response = client.post(
        "/api/login",
        json={"username": "teacher_nfr05", "password": "ValidPass123!"},
        headers=extra_headers,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["role"] == "teacher"
    assert data["user"]["username"] == "teacher_nfr05"


def test_nfr05_cross_site_origin_rejected_across_browsers(client):
    """State-changing requests with hostile cross-site Origin are safely rejected."""
    response = client.post(
        "/api/login",
        json={"username": "teacher_nfr05", "password": "ValidPass123!"},
        headers={
            "User-Agent": BROWSER_USER_AGENTS["chrome_windows"],
            "Origin": "https://malicious-site.example.com",
        },
    )

    assert response.status_code == 403
    assert response.get_json().get("error") == "Cross-site request rejected"


# -----------------------------------------------------------------------------
# 7. Role Dashboards Rendering Across Modern Browsers
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "role, endpoint",
    [
        ("admin", "/admin"),
        ("teacher", "/teacher"),
        ("student", "/student"),
    ],
)
@pytest.mark.parametrize("browser_name, user_agent", BROWSER_USER_AGENTS.items())
def test_nfr05_dashboards_render_for_all_browsers(
    client, nfr05_users, role, endpoint, browser_name, user_agent
):
    """Role dashboards render successfully with standard layout and scripts for all browsers."""
    plant_session(client, nfr05_users[role])

    response = client.get(endpoint, headers={"User-Agent": user_agent})

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert '<!DOCTYPE html>' in html
    assert '<meta http-equiv="X-UA-Compatible" content="IE=edge">' in html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in html
    assert f'id="sidebar"' in html
    assert f'/static/js/{role}.js' in html
    assert '/static/js/common.js' in html


# -----------------------------------------------------------------------------
# 8. Report Export & Download Headers Across Browsers (FR-12 & NFR-05)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fmt, expected_mimetype, filename_ext",
    [
        ("csv", "text/csv", ".csv"),
        ("pdf", "application/pdf", ".pdf"),
        ("json", "application/json", ".json"),
    ],
)
@pytest.mark.parametrize("browser_name, user_agent", BROWSER_USER_AGENTS.items())
def test_nfr05_export_downloads_across_browsers(
    client, nfr05_users, browser_name, user_agent, fmt, expected_mimetype, filename_ext
):
    """File exports return standard attachment headers and content types for all browsers."""
    plant_session(client, nfr05_users["admin"])

    response = client.get(
        f"/api/reports/attendance/export/{fmt}",
        headers={"User-Agent": user_agent},
    )

    assert response.status_code == 200
    assert response.mimetype == expected_mimetype

    disposition = response.headers.get("Content-Disposition", "")
    assert disposition.startswith("attachment;")
    assert f"filename=" in disposition
    assert filename_ext in disposition


# -----------------------------------------------------------------------------
# 9. End-to-End Persona Workflows Across Modern Browsers
# -----------------------------------------------------------------------------

def test_nfr05_e2e_chrome_workflow(client, nfr05_users):
    """End-to-end workflow simulating Google Chrome: Admin logs in, creates a user, logs out."""
    headers = {
        "User-Agent": BROWSER_USER_AGENTS["chrome_windows"],
        "Origin": "http://localhost",
    }

    # 1. Login
    res_login = client.post(
        "/api/login",
        json={"username": "admin_nfr05", "password": "ValidPass123!"},
        headers=headers,
    )
    assert res_login.status_code == 200

    # 2. Access Admin Dashboard
    res_dash = client.get("/admin", headers=headers)
    assert res_dash.status_code == 200
    assert "admin_nfr05" in res_dash.get_data(as_text=True)

    # 3. Create a student user (FR-07)
    res_create = client.post(
        "/api/users",
        json={"username": "new_student_chrome", "password": "Password123!", "role": "student"},
        headers=headers,
    )
    assert res_create.status_code == 201

    # 4. Logout (FR-15)
    res_logout = client.post("/api/logout", headers=headers)
    assert res_logout.status_code == 200


def test_nfr05_e2e_edge_workflow(client, nfr05_users):
    """End-to-end workflow simulating Microsoft Edge: Teacher logs in, checks records, logs out."""
    headers = {
        "User-Agent": BROWSER_USER_AGENTS["edge_windows"],
        "Origin": "http://localhost",
    }

    # 1. Login
    res_login = client.post(
        "/api/login",
        json={"username": "teacher_nfr05", "password": "ValidPass123!"},
        headers=headers,
    )
    assert res_login.status_code == 200

    # 2. Access Teacher Dashboard
    res_dash = client.get("/teacher", headers=headers)
    assert res_dash.status_code == 200

    # 3. Check attendance API
    res_filter = client.get("/api/attendance", headers=headers)
    assert res_filter.status_code == 200

    # 4. Logout
    res_logout = client.post("/api/logout", headers=headers)
    assert res_logout.status_code == 200


def test_nfr05_e2e_firefox_workflow(client, nfr05_users):
    """End-to-end workflow simulating Mozilla Firefox: Student logs in, changes password, logs out."""
    headers = {
        "User-Agent": BROWSER_USER_AGENTS["firefox_linux"],
        "Origin": "http://localhost",
    }

    # 1. Login
    res_login = client.post(
        "/api/login",
        json={"username": "student_nfr05", "password": "ValidPass123!"},
        headers=headers,
    )
    assert res_login.status_code == 200

    # 2. Student Dashboard
    res_dash = client.get("/student", headers=headers)
    assert res_dash.status_code == 200

    # 3. Change password (FR-13)
    res_pw = client.post(
        "/api/me/password",
        json={"current_password": "ValidPass123!", "new_password": "UpdatedPass123!"},
        headers=headers,
    )
    assert res_pw.status_code == 200

    # 4. Logout
    res_logout = client.post("/api/logout", headers=headers)
    assert res_logout.status_code == 200


def test_nfr05_e2e_safari_workflow(client, nfr05_users):
    """End-to-end workflow simulating Apple Safari: Teacher logs in, exports attendance, logs out."""
    headers = {
        "User-Agent": BROWSER_USER_AGENTS["safari_macos"],
        "Origin": "http://localhost",
    }

    # 1. Login
    res_login = client.post(
        "/api/login",
        json={"username": "teacher_nfr05", "password": "ValidPass123!"},
        headers=headers,
    )
    assert res_login.status_code == 200

    # 2. Export report in CSV format
    res_export = client.get("/api/reports/attendance/export/csv", headers=headers)
    assert res_export.status_code == 200
    assert res_export.mimetype == "text/csv"

    # 3. Logout
    res_logout = client.post("/api/logout", headers=headers)
    assert res_logout.status_code == 200
