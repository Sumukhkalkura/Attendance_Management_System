"""Real-browser compatibility tests for NFR-05.

SRS NFR-05 (Compatibility): "The system shall function correctly on commonly
used modern web browsers."  Backlog US-26 acceptance criterion: "Works
correctly in current Chrome, Edge and Firefox".

Unlike the User-Agent simulations in test_nfr05_implementation.py, these tests
drive the actual browser engines through Playwright against a live Flask
server and exercise the core workflow of every role:

* chrome  -> Google Chrome (Playwright channel "chrome", Blink)
* edge    -> Microsoft Edge (Playwright channel "msedge", Blink)
* firefox -> Mozilla Firefox (Playwright managed build, Gecko)

Every test also fails if the page raises an uncaught JavaScript error or logs
a console error, so a browser-specific script incompatibility cannot pass
silently.

Set NFR05_BROWSERS (comma separated, e.g. "firefox,edge") to run a subset.
Install the browsers with:
    python -m playwright install chromium firefox chrome msedge
"""

import os
import socket
import sqlite3
import threading
import time

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # pragma: no cover - reported as a test failure below
    sync_playwright = None

PASSWORD = "ValidPass123!"

# name -> (Playwright engine, release channel or None for the managed build)
SUPPORTED_BROWSERS = {
    "chrome": ("chromium", "chrome"),
    "edge": ("chromium", "msedge"),
    "firefox": ("firefox", None),
}

SELECTED_BROWSERS = [
    name.strip()
    for name in os.environ.get("NFR05_BROWSERS", ",".join(SUPPORTED_BROWSERS)).split(",")
    if name.strip()
]

# Each browser marks a different past date so the shared server stays isolated.
MARK_DATES = {"chrome": "2026-10-05", "edge": "2026-10-06", "firefox": "2026-10-07"}

# Measured browser versions, reported at the end of the module.
BROWSER_VERSIONS = {}


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Run the real application on a local port with a small seeded dataset."""
    db_path = str(tmp_path_factory.mktemp("nfr05_browser") / "nfr05.db")
    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "nfr05-browser-secret"})

    with sqlite3.connect(db_path) as conn:
        pw = generate_password_hash(PASSWORD)
        ids = {}
        for username, role in [
            ("nfr05_admin", "admin"),
            ("nfr05_teacher", "teacher"),
            ("nfr05_student_a", "student"),
            ("nfr05_student_b", "student"),
            ("nfr05_viewer", "student"),
        ]:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (username, pw, role),
            )
            ids[username] = cur.lastrowid

        teacher = ids["nfr05_teacher"]
        cur = conn.execute("INSERT INTO classes (name, teacher_id) VALUES (?, ?)", ("NFR05 Class", teacher))
        class_id = cur.lastrowid
        cur = conn.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", ("NFR05 Subject", teacher))
        subject_id = cur.lastrowid
        conn.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (class_id, subject_id))
        for student in ("nfr05_student_a", "nfr05_student_b"):
            conn.execute(
                "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
                (ids[student], class_id, subject_id),
            )

        # The viewer is in a separate class so marking by the teacher tests
        # cannot change the percentage the student test expects (3/4 = 75%).
        cur = conn.execute("INSERT INTO classes (name, teacher_id) VALUES (?, ?)", ("NFR05 Viewer Class", teacher))
        viewer_class = cur.lastrowid
        cur = conn.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", ("NFR05 Viewer Subject", teacher))
        viewer_subject = cur.lastrowid
        conn.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (viewer_class, viewer_subject))
        conn.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (ids["nfr05_viewer"], viewer_class, viewer_subject),
        )
        conn.executemany(
            "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
            [
                (ids["nfr05_viewer"], viewer_subject, "2026-09-01", "Present"),
                (ids["nfr05_viewer"], viewer_subject, "2026-09-02", "Present"),
                (ids["nfr05_viewer"], viewer_subject, "2026-09-03", "Present"),
                (ids["nfr05_viewer"], viewer_subject, "2026-09-04", "Absent"),
            ],
        )
        conn.commit()

    port = _find_free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield {"url": f"http://127.0.0.1:{port}", "db": db_path, "ids": ids, "subject_id": subject_id}

    server.shutdown()
    server.server_close()


@pytest.fixture(scope="module")
def playwright_instance():
    if sync_playwright is None:
        pytest.fail("The 'playwright' package is required for NFR-05: pip install -r requirements.txt")
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module", params=SELECTED_BROWSERS)
def browser(request, playwright_instance):
    name = request.param
    if name not in SUPPORTED_BROWSERS:
        pytest.fail(f"Unknown NFR05_BROWSERS entry {name!r}; expected one of {sorted(SUPPORTED_BROWSERS)}")

    engine, channel = SUPPORTED_BROWSERS[name]
    launcher = getattr(playwright_instance, engine)
    try:
        instance = launcher.launch(channel=channel, headless=True) if channel else launcher.launch(headless=True)
    except Exception as err:
        install = channel or engine
        pytest.fail(
            f"NFR-05 requires {name} but it could not be launched. "
            f"Install it with 'python -m playwright install {install}'. Original error: {err}"
        )

    instance.nfr05_name = name
    BROWSER_VERSIONS[name] = f"{engine}{'/' + channel if channel else ''} {instance.version}"
    yield instance
    instance.close()


@pytest.fixture
def page(browser):
    """A fresh browser context that records any JavaScript error on the page."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    pg = context.new_page()
    pg.set_default_timeout(10_000)
    errors = []
    pg.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    pg.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
    pg.js_errors = errors

    yield pg

    context.close()
    assert not errors, f"{browser.nfr05_name} reported JavaScript errors: {errors}"


def _login(page, base_url, username):
    page.goto(f"{base_url}/login")
    page.fill("#username", username)
    page.fill("#password", PASSWORD)
    page.click("#loginButton")


def _query(db_path, sql, params=()):
    with sqlite3.connect(db_path) as conn:
        return conn.execute(sql, params).fetchall()


# -----------------------------------------------------------------------------
# Login page: rendering, client-side validation, error handling, redirect
# -----------------------------------------------------------------------------

def test_login_page_validation_and_role_redirect(page, live_server):
    base = live_server["url"]
    response = page.goto(f"{base}/login")
    assert response.status == 200
    # Standards mode, not quirks mode, in every engine.
    assert page.evaluate("document.compatMode") == "CSS1Compat"
    assert page.evaluate("document.characterSet") == "UTF-8"

    # Empty submit: client-side validation uses toggleAttribute and the error box.
    page.click("#loginButton")
    expect(page.locator("#loginError")).to_be_visible()
    expect(page.locator("#loginErrorText")).to_have_text("Please enter both your username and password.")
    expect(page.locator("#username")).to_have_attribute("aria-invalid", "")

    # Password visibility toggle switches the input type.
    page.fill("#password", "secret")
    page.click("#passwordToggle")
    expect(page.locator("#password")).to_have_attribute("type", "text")
    page.click("#passwordToggle")
    expect(page.locator("#password")).to_have_attribute("type", "password")

    # Wrong credentials: server error is shown, user stays on the login page.
    page.fill("#username", "nfr05_teacher")
    page.fill("#password", "WrongPass999!")
    page.click("#loginButton")
    expect(page.locator("#loginError")).to_be_visible()
    assert page.url.endswith("/login")

    # Correct credentials: fetch login sets the session cookie and redirects by role.
    page.fill("#password", PASSWORD)
    page.click("#loginButton")
    page.wait_for_url(f"{base}/teacher*")
    expect(page.locator("#pageTitle")).to_have_text("Overview")

    # The expected browser console errors from the 401 response are not script errors.
    page.js_errors[:] = [e for e in page.js_errors if "401" not in e]


# -----------------------------------------------------------------------------
# Teacher: mark attendance, correct a record via <dialog>, log out
# -----------------------------------------------------------------------------

def test_teacher_marks_corrects_attendance_and_logs_out(page, browser, live_server):
    base, db = live_server["url"], live_server["db"]
    mark_date = MARK_DATES[browser.nfr05_name]

    _login(page, base, "nfr05_teacher")
    page.wait_for_url(f"{base}/teacher*")

    # Hash navigation to the marking section.
    page.click(".nav-link[data-section='mark']")
    expect(page.locator("#section-mark")).to_be_visible()
    expect(page.locator("#section-overview")).to_be_hidden()

    page.select_option("#markClass", label="NFR05 Class")
    page.select_option("#markSubject", label="NFR05 Subject")
    page.fill("#markDate", mark_date)  # native <input type="date">
    page.click("#loadRosterButton")
    expect(page.locator("#rosterTable input[type=radio]")).to_have_count(6)

    page.click("#allAbsent")
    expect(page.locator("#countAbsent")).to_have_text("2")
    page.locator("#rosterTable label.seg-present").first.click()
    expect(page.locator("#countPresent")).to_have_text("1")
    expect(page.locator("#countAbsent")).to_have_text("1")

    page.click("#saveAttendance")
    expect(page.locator("#toasts .toast.success")).to_contain_text("Saved attendance for 2 student(s).")

    rows = _query(
        db,
        "SELECT u.username, a.status FROM attendance a JOIN users u ON u.id = a.student_id "
        "WHERE a.attendance_date = ? ORDER BY u.username",
        (mark_date,),
    )
    assert sorted(status for _, status in rows) == ["Absent", "Present"]

    # Correct one record through the native <dialog> (showModal / close).
    page.click(".nav-link[data-section='records']")
    page.fill("#recordDate", mark_date)
    page.dispatch_event("#recordDate", "change")
    expect(page.locator("#recordsTable tr")).to_have_count(2)
    page.locator("#recordsTable tr", has_text="nfr05_student_a").get_by_role("button", name="Correct status").click()
    dialog = page.locator("#editRecordDialog")
    expect(dialog).to_be_visible()
    assert page.evaluate("document.getElementById('editRecordDialog').open") is True
    dialog.locator("select[name=status]").select_option("Late")
    dialog.get_by_role("button", name="Save change").click()
    expect(dialog).to_be_hidden()
    expect(page.locator("#toasts")).to_contain_text("Attendance record updated.")

    status = _query(
        db,
        "SELECT a.status FROM attendance a JOIN users u ON u.id = a.student_id "
        "WHERE u.username = 'nfr05_student_a' AND a.attendance_date = ?",
        (mark_date,),
    )
    assert status == [("Late",)]

    # Logout uses the confirmation <dialog>, then protected pages need a new login.
    page.click("#logoutButton")
    expect(page.locator("#confirmDialog")).to_be_visible()
    page.click("#confirmButton")
    page.wait_for_url(f"{base}/login*")
    page.goto(f"{base}/teacher")
    assert "/login" in page.url


# -----------------------------------------------------------------------------
# Student: overview percentage and history rendering
# -----------------------------------------------------------------------------

def test_student_views_own_attendance(page, live_server):
    base = live_server["url"]
    _login(page, base, "nfr05_viewer")
    page.wait_for_url(f"{base}/student*")

    expect(page.locator("#overallPercent")).to_contain_text("75")
    expect(page.locator("#countPresent")).to_have_text("3")
    expect(page.locator("#countAbsent")).to_have_text("1")
    expect(page.locator("#countTotal")).to_have_text("4")

    page.click(".nav-link[data-section='history']")
    expect(page.locator("#historyTable tr")).to_have_count(4)
    expect(page.locator("#historyTable")).to_contain_text("NFR05 Viewer Subject")


# -----------------------------------------------------------------------------
# Admin: create a user through the form dialog
# -----------------------------------------------------------------------------

def test_admin_creates_user_through_dialog(page, browser, live_server):
    base, db = live_server["url"], live_server["db"]
    username = f"nfr05_new_{browser.nfr05_name}"

    _login(page, base, "nfr05_admin")
    page.wait_for_url(f"{base}/admin*")
    page.click(".nav-link[data-section='users']")
    page.click("#newUserButton")

    dialog = page.locator("#userDialog")
    expect(dialog).to_be_visible()
    dialog.locator("input[name=username]").fill(username)
    dialog.locator("select[name=role]").select_option("student")
    dialog.locator("input[name=password]").fill(PASSWORD)
    dialog.locator("button[type=submit]").click()
    expect(dialog).to_be_hidden()
    expect(page.locator("#usersTable")).to_contain_text(username)

    assert _query(db, "SELECT role, active FROM users WHERE username = ?", (username,)) == [("student", 1)]


# -----------------------------------------------------------------------------
# Layout: usable at desktop and phone widths without horizontal scrolling
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("width, height", [(1280, 800), (375, 812)])
def test_dashboard_layout_has_no_horizontal_overflow(page, live_server, width, height):
    base = live_server["url"]
    page.set_viewport_size({"width": width, "height": height})
    _login(page, base, "nfr05_teacher")
    page.wait_for_url(f"{base}/teacher*")
    expect(page.locator("#statSubjects")).to_have_text("2")

    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 0, f"Page scrolls horizontally by {overflow}px at {width}px wide"

    if width < 768:
        # On phones the sidebar is behind the menu toggle.
        toggle = page.locator("#menuToggle")
        expect(toggle).to_be_visible()
        toggle.click()
        expect(toggle).to_have_attribute("aria-expanded", "true")
        page.click(".nav-link[data-section='percentages']")
        expect(page.locator("#section-percentages")).to_be_visible()
        expect(toggle).to_have_attribute("aria-expanded", "false")


def test_report_tested_browser_versions():
    """Record the exact engine versions exercised, for the NFR-05 evidence."""
    assert set(BROWSER_VERSIONS) == set(SELECTED_BROWSERS), (
        f"Not every selected browser was exercised: {BROWSER_VERSIONS}"
    )
    for name, version in sorted(BROWSER_VERSIONS.items()):
        print(f"NFR-05 tested {name}: {version}")
