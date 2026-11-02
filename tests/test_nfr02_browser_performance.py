"""Browser-based performance tests for NFR-02 using Playwright and headless Chrome.

Verifies that major pages and attendance views load and render within the 3.0-second SLA
under normal operating conditions:
- 50 students
- 10 classes
- 15 subjects
- 5 teachers
- 1 admin
- 1,500 attendance records across 25 dates
"""

import os
import sys
import time
import socket
import threading
import sqlite3
import pytest
from werkzeug.serving import make_server
from werkzeug.security import generate_password_hash

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_INSTALLED = True
except ImportError:
    PLAYWRIGHT_INSTALLED = False

from app import create_app

PERFORMANCE_SLA_SECONDS = 3.0

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
AVAILABLE_BROWSER = next((p for p in CHROME_PATHS if os.path.exists(p)), None)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def browser_server(tmp_path_factory):
    """Start a background Flask test server seeded with normal operating data."""
    if not PLAYWRIGHT_INSTALLED or not AVAILABLE_BROWSER:
        pytest.skip("Playwright or system browser not available in this test environment.")

    temp_dir = tmp_path_factory.mktemp("browser_perf_db")
    db_path = str(temp_dir / "browser_perf.db")

    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "browser-test-secret"})

    with app.app_context():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        pw = generate_password_hash("password123")

        # 1 Admin
        cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", ("b_admin", pw, "admin"))

        # 5 Teachers
        t_ids = []
        for i in range(1, 6):
            cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", (f"b_teacher_{i}", pw, "teacher"))
            t_ids.append(cur.lastrowid)

        # 50 Students
        s_ids = []
        for i in range(1, 51):
            cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", (f"b_student_{i}", pw, "student"))
            s_ids.append(cur.lastrowid)

        # 10 Classes
        c_ids = []
        for i in range(1, 11):
            t_id = t_ids[(i - 1) % len(t_ids)]
            cur.execute("INSERT INTO classes (name, teacher_id) VALUES (?, ?)", (f"Class {i}", t_id))
            c_ids.append(cur.lastrowid)

        # 15 Subjects
        sub_ids = []
        for i in range(1, 16):
            t_id = t_ids[(i - 1) % len(t_ids)]
            cur.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (f"Subject {i}", t_id))
            sub_ids.append(cur.lastrowid)

        # 3 Subjects per class
        for idx, c_id in enumerate(c_ids):
            for j in range(3):
                sub_id = sub_ids[(idx * 3 + j) % len(sub_ids)]
                cur.execute("INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (c_id, sub_id))

        # Enrollments
        enrollments = []
        for idx, s_id in enumerate(s_ids):
            c_id = c_ids[idx % len(c_ids)]
            cur.execute("SELECT subject_id FROM class_subjects WHERE class_id = ?", (c_id,))
            subs = [r[0] for r in cur.fetchall()]
            for sub_id in subs:
                enrollments.append((s_id, c_id, sub_id))
        cur.executemany("INSERT OR IGNORE INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)", enrollments)

        # 1,500 Attendance records
        dates = [f"2026-03-{d:02d}" for d in range(1, 26)]
        statuses = ["Present", "Present", "Present", "Absent", "Late"]
        records = []
        rec_idx = 0
        for d in dates:
            for enr in enrollments:
                s_id, c_id, sub_id = enr
                st = statuses[rec_idx % len(statuses)]
                records.append((s_id, sub_id, d, st))
                rec_idx += 1
                if len(records) >= 1500:
                    break
            if len(records) >= 1500:
                break
        cur.executemany("INSERT OR IGNORE INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)", records)
        conn.commit()
        conn.close()

    port = find_free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()


@pytest.fixture(scope="module")
def browser_instance():
    """Manage a headless browser instance."""
    if not PLAYWRIGHT_INSTALLED or not AVAILABLE_BROWSER:
        pytest.skip("Playwright or system browser not available in this test environment.")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=AVAILABLE_BROWSER, headless=True)
        # Warmup page
        warm = browser.new_page()
        warm.goto("about:blank")
        warm.close()
        yield browser
        browser.close()


def test_browser_login_page_renders_within_threshold(browser_instance, browser_server):
    """Browser test: Login page loads and renders in under 3.0 seconds."""
    ctx = browser_instance.new_context()
    page = ctx.new_page()
    try:
        t0 = time.perf_counter()
        resp = page.goto(f"{browser_server}/login", wait_until="load")
        nav_elapsed = time.perf_counter() - t0

        page.wait_for_selector("#loginForm", state="visible")
        render_elapsed = time.perf_counter() - t0

        assert resp.status == 200
        assert page.is_visible("#username")
        assert page.is_visible("#password")
        assert render_elapsed < PERFORMANCE_SLA_SECONDS, f"Login took {render_elapsed:.3f}s"
    finally:
        ctx.close()


def test_browser_main_dashboard_overview_renders_within_threshold(browser_instance, browser_server):
    """Browser test: Admin dashboard and stat cards render in under 3.0 seconds."""
    ctx = browser_instance.new_context()
    page = ctx.new_page()
    try:
        # Authenticate
        page.goto(f"{browser_server}/login")
        page.fill("#username", "b_admin")
        page.fill("#password", "password123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{browser_server}/admin*")

        # Measure dashboard reload and data rendering
        t0 = time.perf_counter()
        page.goto(f"{browser_server}/admin", wait_until="load")
        page.wait_for_selector(".main", state="visible")
        page.wait_for_selector("#section-overview", state="visible")
        page.wait_for_selector("#statStudents", state="visible")
        page.wait_for_selector("#statOverall", state="visible")
        page.wait_for_selector("#lowAttendanceTable tr", state="visible")
        render_elapsed = time.perf_counter() - t0

        assert render_elapsed < PERFORMANCE_SLA_SECONDS, f"Admin dashboard took {render_elapsed:.3f}s"
    finally:
        ctx.close()


def test_browser_student_attendance_view_renders_within_threshold(browser_instance, browser_server):
    """Browser test: Student attendance history loads and populates in under 3.0 seconds."""
    ctx = browser_instance.new_context()
    page = ctx.new_page()
    try:
        page.goto(f"{browser_server}/login")
        page.fill("#username", "b_student_1")
        page.fill("#password", "password123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{browser_server}/student*")

        t0 = time.perf_counter()
        page.click("a[data-section='history']")
        page.wait_for_selector("#section-history", state="visible")
        page.wait_for_selector("#historyTable tr", state="visible")
        render_elapsed = time.perf_counter() - t0

        assert page.locator("#historyTable tr").count() > 0
        assert render_elapsed < PERFORMANCE_SLA_SECONDS, f"Student history took {render_elapsed:.3f}s"
    finally:
        ctx.close()


def test_browser_class_attendance_view_renders_within_threshold(browser_instance, browser_server):
    """Browser test: Teacher class attendance roster loads and renders in under 3.0 seconds."""
    ctx = browser_instance.new_context()
    page = ctx.new_page()
    try:
        page.goto(f"{browser_server}/login")
        page.fill("#username", "b_teacher_1")
        page.fill("#password", "password123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{browser_server}/teacher*")

        t0 = time.perf_counter()
        page.click("a[data-section='mark']")
        page.wait_for_selector("#section-mark", state="visible")
        page.select_option("#markClass", index=1)
        page.select_option("#markSubject", index=1)
        page.fill("#markDate", "2026-03-10")
        page.click("#loadRosterButton")
        page.wait_for_selector("#rosterCard", state="visible")
        page.wait_for_selector("#rosterTable tr", state="visible")
        render_elapsed = time.perf_counter() - t0

        assert page.locator("#rosterTable tr").count() > 0
        assert render_elapsed < PERFORMANCE_SLA_SECONDS, f"Class roster took {render_elapsed:.3f}s"
    finally:
        ctx.close()


def test_browser_subject_attendance_view_renders_within_threshold(browser_instance, browser_server):
    """Browser test: Teacher subject attendance percentages load and render in under 3.0 seconds."""
    ctx = browser_instance.new_context()
    page = ctx.new_page()
    try:
        page.goto(f"{browser_server}/login")
        page.fill("#username", "b_teacher_1")
        page.fill("#password", "password123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{browser_server}/teacher*")

        t0 = time.perf_counter()
        page.click("a[data-section='percentages']")
        page.wait_for_selector("#section-percentages", state="visible")
        page.wait_for_selector("#percentTable tr", state="visible")
        render_elapsed = time.perf_counter() - t0

        assert page.locator("#percentTable tr").count() > 0
        assert render_elapsed < PERFORMANCE_SLA_SECONDS, f"Subject percentages took {render_elapsed:.3f}s"
    finally:
        ctx.close()


def test_browser_attendance_reporting_page_renders_within_threshold(browser_instance, browser_server):
    """Browser test: Admin attendance reporting page (records & percentages) renders in under 3.0 seconds."""
    ctx = browser_instance.new_context()
    page = ctx.new_page()
    try:
        page.goto(f"{browser_server}/login")
        page.fill("#username", "b_admin")
        page.fill("#password", "password123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{browser_server}/admin*")

        t0 = time.perf_counter()
        page.click("a[data-section='attendance']")
        page.wait_for_selector("#section-attendance", state="visible")
        page.wait_for_selector("#percentTable tr", state="visible")
        page.wait_for_selector("#recordsTable tr", state="visible")
        render_elapsed = time.perf_counter() - t0

        assert page.locator("#percentTable tr").count() > 0
        assert page.locator("#recordsTable tr").count() > 0
        assert render_elapsed < PERFORMANCE_SLA_SECONDS, f"Attendance reporting took {render_elapsed:.3f}s"
    finally:
        ctx.close()

