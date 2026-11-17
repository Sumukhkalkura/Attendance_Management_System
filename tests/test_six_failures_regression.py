"""Page-level regression tests for the six failures fixed after Deliverable 3
testing (SYS_FR-04_11, SYS_FR-05_10, SYS_FR-06_08, SYS_FR-10_10, SYS_FR-12_10,
SYS_NFR-05_04).

These tests check what the server delivers: navigation, controls, scripts and
security headers. The behaviour in a real browser is tested in
tests/test_six_failures_browser.py.
"""

import pytest
from werkzeug.security import generate_password_hash

from app.db import get_db
from session_helpers import plant_session


def make_user(client, role, username):
    with client.application.app_context():
        db = get_db()
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
            (username, generate_password_hash("Password123"), role),
        )
        db.commit()
        return cur.lastrowid


@pytest.fixture
def pages(client):
    html = {}
    for role in ("admin", "teacher", "student"):
        plant_session(client, make_user(client, role, f"six_{role}"))
        html[role] = client.get(f"/{role}").get_data(as_text=True)
    return html


# -- SYS_FR-06_08 / SYS_FR-12_10: reporting and export screen ---------------

@pytest.mark.parametrize("role", ["admin", "teacher"])
def test_reports_section_and_navigation_for_admin_and_teacher(pages, role):
    html = pages[role]
    assert 'data-section="reports"' in html
    assert 'id="section-reports"' in html
    for control in ("reportStudent", "reportClass", "reportSubject", "reportFrom", "reportTo", "reportStatus",
                    "reportGenerate", "reportTable"):
        assert f'id="{control}"' in html, control
    # only the export formats the backend implements (app/api/exports.py)
    for fmt in ("csv", "pdf", "json"):
        assert f'data-format="{fmt}"' in html
    assert html.count("data-format=") == 3
    assert "/static/js/reports.js" in html


def test_student_dashboard_has_no_reports_screen(pages):
    assert 'data-section="reports"' not in pages["student"]
    assert "/static/js/reports.js" not in pages["student"]


def test_reports_script_served_as_javascript(client):
    response = client.get("/static/js/reports.js")
    assert response.status_code == 200
    assert response.mimetype == "application/javascript"
    source = response.get_data(as_text=True)
    assert "/api/reports/attendance" in source
    assert "/api/reports/attendance/export/" in source


# -- SYS_FR-10_10: filters --------------------------------------------------

@pytest.mark.parametrize("role", ["admin", "teacher"])
def test_records_toolbar_has_class_range_and_clear_controls(pages, role):
    html = pages[role]
    for control in ("recordSearch", "recordSubject", "recordClass", "recordDate", "recordFrom", "recordTo",
                    "recordStatus", "recordClear"):
        assert f'id="{control}"' in html, control
    assert "Clear filters" in html


# -- SYS_NFR-05_04: the security policy is not weakened ---------------------

def test_content_security_policy_stays_restrictive(client):
    csp = client.get("/login").headers["Content-Security-Policy"]
    assert csp == "default-src 'self'; frame-ancestors 'none'"
    assert "unsafe-inline" not in csp and "*" not in csp
