"""Real-browser regression tests for the six failures fixed after Deliverable 3
testing.

* SYS_FR-04_11 - percentages are displayed with two decimals (83.33%, 58.33%, 100.00%)
* SYS_FR-05_10 - at 375 px the teacher records table needs no sideways scrolling,
                 status badges are not clipped and actions stay usable
* SYS_FR-06_08 - reports can be generated in the dashboard; an empty report shows a message
* SYS_FR-10_10 - class / date-range filters and Clear filters restore all rows
* SYS_FR-12_10 - reports can be exported from the dashboard; files match the report

Runs against a live Flask server with its own temporary SQLite database.
Browsers: REGRESSION_BROWSERS (comma separated; default "chrome").
Every test fails if the page logs a JavaScript or console error.
"""

import csv
import io
import json
import os
import socket
import sqlite3
import threading
from datetime import date, timedelta

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

PASSWORD = "ValidPass123!"
ENGINES = {"chrome": ("chromium", "chrome"), "chromium": ("chromium", None), "webkit": ("webkit", None),
           "firefox": ("firefox", None), "edge": ("chromium", "msedge")}
SELECTED = [b.strip() for b in os.environ.get("REGRESSION_BROWSERS", "chrome").split(",") if b.strip()]
DAYS = [date(2026, 9, 1) + timedelta(days=i) for i in range(12)]          # 2026-09-01 .. 2026-09-12
PATTERNS = {                                                             # Present count of 12
    "six_alice": 10,   # 83.33 %
    "six_bob": 7,      # 58.33 %
    "six_carol": 12,   # 100.00 %
}


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("six") / "six.db")
    app = create_app({"TESTING": True, "DATABASE": db, "SECRET_KEY": "six-failures"})
    ids = {}
    with sqlite3.connect(db) as conn:
        pw = generate_password_hash(PASSWORD)
        for name, role in [("six_admin", "admin"), ("six_teacher", "teacher"), ("six_other_teacher", "teacher"),
                           ("six_alice", "student"), ("six_bob", "student"), ("six_carol", "student")]:
            ids[name] = conn.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                                     (name, pw, role)).lastrowid
        t, o = ids["six_teacher"], ids["six_other_teacher"]
        ids["class_a"] = conn.execute("INSERT INTO classes (name, teacher_id) VALUES ('Six Class A', ?)", (t,)).lastrowid
        ids["class_b"] = conn.execute("INSERT INTO classes (name, teacher_id) VALUES ('Six Class B', ?)", (o,)).lastrowid
        ids["math"] = conn.execute("INSERT INTO subjects (name, teacher_id) VALUES ('Six Mathematics', ?)", (t,)).lastrowid
        ids["art"] = conn.execute("INSERT INTO subjects (name, teacher_id) VALUES ('Six Art', ?)", (o,)).lastrowid
        conn.execute("INSERT INTO class_subjects VALUES (?, ?)", (ids["class_a"], ids["math"]))
        conn.execute("INSERT INTO class_subjects VALUES (?, ?)", (ids["class_b"], ids["art"]))
        for student, present in PATTERNS.items():
            sid = ids[student]
            conn.execute("INSERT INTO enrollments VALUES (?, ?, ?)", (sid, ids["class_a"], ids["math"]))
            for i, day in enumerate(DAYS):
                status = "Present" if i < present else "Absent"
                conn.execute("INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
                             (sid, ids["math"], day.isoformat(), status))
        # another teacher's subject with records the first teacher must never see
        conn.execute("INSERT INTO enrollments VALUES (?, ?, ?)", (ids["six_bob"], ids["class_b"], ids["art"]))
        for day in DAYS[:4]:
            conn.execute("INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, 'Late')",
                         (ids["six_bob"], ids["art"], day.isoformat()))
        conn.commit()
    port = _free_port()
    srv = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield {"url": f"http://127.0.0.1:{port}", "ids": ids, "db": db}
    srv.shutdown()


@pytest.fixture(scope="module", params=SELECTED)
def browser(request):
    if sync_playwright is None:
        pytest.fail("playwright is required")
    engine, channel = ENGINES[request.param]
    with sync_playwright() as p:
        launcher = getattr(p, engine)
        try:
            b = launcher.launch(channel=channel) if channel else launcher.launch()
        except Exception as err:  # noqa: BLE001
            pytest.fail(f"{request.param} could not be launched: {err}")
        b.regression_name = request.param
        yield b
        b.close()


@pytest.fixture
def make_page(browser):
    contexts = []

    def factory(width=1280, height=800):
        ctx = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True)
        page = ctx.new_page()
        page.set_default_timeout(10_000)
        page.errors = []
        page.on("pageerror", lambda exc: page.errors.append(f"pageerror: {exc}"))
        page.on("console", lambda m: page.errors.append(f"console.error: {m.text}") if m.type == "error" else None)
        contexts.append((ctx, page))
        return page

    yield factory
    for ctx, page in contexts:
        ctx.close()
        # failed logins and deliberate 401/403 probes produce expected resource errors
        unexpected = [e for e in page.errors if not any(code in e for code in ("401", "403"))]
        assert not unexpected, f"{browser.regression_name}: JavaScript / console errors: {unexpected}"


def login(page, base, user, path):
    page.goto(f"{base}/login")
    page.fill("#username", user)
    page.fill("#password", PASSWORD)
    page.click("#loginButton")
    page.wait_for_url(f"{base}{path}*")


def nav(page, section):
    page.click(f".nav-link[data-section='{section}']")
    expect(page.locator(f"#section-{section}")).to_be_visible()


def settled(page, tbody):
    page.wait_for_function(
        "s => { const t = document.querySelector(s); return t && t.children.length && !t.querySelector('.spinner'); }",
        arg=tbody)


def data_rows(page, tbody):
    return page.evaluate("s => [...document.querySelectorAll(s + ' > tr')].filter(r => !r.querySelector('td[colspan]'))"
                         ".map(r => [...r.children].map(td => td.innerText.trim()))", tbody)


# ---------------------------------------------------------------- SYS_FR-04_11

def test_format_percent_uses_two_decimals(make_page, server):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    values = page.evaluate("[83.3333333, 58.3333333, 100, 0, 1.005, 66.665, 99.999].map(App.formatPercent)")
    assert values == ["83.33%", "58.33%", "100.00%", "0.00%", "1.01%", "66.67%", "100.00%"]


def test_teacher_percentages_screen_shows_two_decimals(make_page, server):
    page = make_page()
    login(page, server["url"], "six_teacher", "/teacher")
    nav(page, "percentages")
    settled(page, "#percentTable")
    shown = {r[0].split("\n")[-1]: r[-1] for r in data_rows(page, "#percentTable")}
    assert shown == {"six_alice": "83.33%", "six_bob": "58.33%", "six_carol": "100.00%"}


def test_student_overall_percentage_two_decimals(make_page, server):
    page = make_page()
    login(page, server["url"], "six_alice", "/student")
    expect(page.locator("#overallPercent")).to_have_text("83.33%")


# ---------------------------------------------------------------- SYS_FR-05_10

@pytest.mark.parametrize("width,height", [(375, 812), (768, 1024), (1280, 800)])
def test_teacher_records_fit_without_sideways_scrolling(make_page, server, width, height):
    page = make_page(width, height)
    login(page, server["url"], "six_teacher", "/teacher")
    page.goto(f"{server['url']}/teacher#records")
    settled(page, "#recordsTable")
    m = page.evaluate("""() => {
        const vw = document.documentElement.clientWidth;
        const wrap = document.querySelector('#section-records .table-wrap');
        const clipped = [...document.querySelectorAll('#recordsTable .badge, #recordsTable button')]
            .filter(e => { const r = e.getBoundingClientRect(); return r.left < 0 || r.right > vw + 0.5; }).length;
        return {page: document.documentElement.scrollWidth - vw, wrap: wrap.scrollWidth - wrap.clientWidth, clipped,
                header: getComputedStyle(document.querySelector('#section-records thead')).position};
    }""")
    assert m["page"] <= 0, m
    assert m["wrap"] <= 0, m
    assert m["clipped"] == 0, m
    # desktop keeps the table header; phones use the labelled card layout
    assert (m["header"] == "absolute") == (width <= 640), m


def test_phone_records_actions_work_with_keyboard(make_page, server):
    page = make_page(375, 812)
    login(page, server["url"], "six_teacher", "/teacher")
    page.goto(f"{server['url']}/teacher#records")
    settled(page, "#recordsTable")
    first = page.locator("#recordsTable > tr").first
    expect(first.locator(".badge")).to_be_visible()
    # each cell is labelled with its column heading (CSS ::before shows the data-label)
    labels = page.evaluate("""() => [...document.querySelector('#recordsTable > tr').children]
        .map(td => [td.dataset.label, getComputedStyle(td, '::before').content])""")
    assert [l for l, _ in labels] == ["Date", "Student", "Subject", "Status", "Actions"]
    assert all(content == f'"{label}"' for label, content in labels), labels
    button = first.get_by_role("button", name="Correct status")
    button.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#editRecordDialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#editRecordDialog")).to_be_hidden()


# ---------------------------------------------------------------- SYS_FR-10_10

def test_teacher_filters_and_clear_filters(make_page, server):
    page = make_page()
    login(page, server["url"], "six_teacher", "/teacher")
    nav(page, "records")
    settled(page, "#recordsTable")
    total = len(data_rows(page, "#recordsTable"))
    assert total == 36                                     # 3 students x 12 days, own subject only

    page.select_option("#recordClass", label="Six Class A")
    page.fill("#recordFrom", "2026-09-03"); page.dispatch_event("#recordFrom", "change")
    page.fill("#recordTo", "2026-09-05"); page.dispatch_event("#recordTo", "change")
    page.select_option("#recordStatus", "Present")
    page.fill("#recordSearch", "six_bob")
    settled(page, "#recordsTable")
    rows = data_rows(page, "#recordsTable")
    assert len(rows) == 3 and all("six_bob" in r[1] and r[3] == "Present" for r in rows), rows

    page.click("#recordClear")
    settled(page, "#recordsTable")
    page.wait_for_function("n => document.querySelectorAll('#recordsTable > tr').length === n", arg=total)
    values = page.evaluate("['#recordSearch','#recordSubject','#recordClass','#recordDate','#recordFrom','#recordTo','#recordStatus']"
                           ".map(s => document.querySelector(s).value)")
    assert values == [""] * 7
    assert len(data_rows(page, "#recordsTable")) == total


def test_admin_class_and_date_range_filters_and_clear(make_page, server):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    nav(page, "attendance")
    settled(page, "#recordsTable")
    total = len(data_rows(page, "#recordsTable"))
    assert total == 40
    page.select_option("#recordClass", label="Six Class B")
    settled(page, "#recordsTable")
    rows = data_rows(page, "#recordsTable")
    assert len(rows) == 4 and all(r[2] == "Six Art" for r in rows)
    page.fill("#recordFrom", "2026-09-02"); page.dispatch_event("#recordFrom", "change")
    page.fill("#recordTo", "2026-09-03"); page.dispatch_event("#recordTo", "change")
    settled(page, "#recordsTable")
    assert len(data_rows(page, "#recordsTable")) == 2
    page.click("#recordClear")
    page.wait_for_function("n => document.querySelectorAll('#recordsTable > tr').length === n", arg=total)


# ---------------------------------------------------------------- SYS_FR-06_08

def generate(page):
    page.click("#reportGenerate")
    settled(page, "#reportTable")


def test_admin_generates_report_matching_the_api(make_page, server):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    nav(page, "reports")
    page.select_option("#reportSubject", label="Six Mathematics")
    page.fill("#reportFrom", "2026-09-01")
    page.fill("#reportTo", "2026-09-06")
    generate(page)
    api = page.evaluate(f"fetch('/api/reports/attendance?subject_id={server['ids']['math']}&start_date=2026-09-01&end_date=2026-09-06')"
                        ".then(r => r.json())")
    assert page.inner_text("#reportTotal") == str(api["summary"]["total_records"]) == "18"
    assert page.inner_text("#reportPresent") == str(api["summary"]["present_count"])
    assert page.inner_text("#reportAbsent") == str(api["summary"]["absent_count"])
    assert page.inner_text("#reportPercent") == f"{api['summary']['attendance_percentage']:.2f}%"
    assert len(data_rows(page, "#reportTable")) == 18
    assert "Six Mathematics" in page.inner_text("#reportScope")


def test_empty_report_shows_message(make_page, server):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    nav(page, "reports")
    page.fill("#reportFrom", "2025-01-01")
    page.fill("#reportTo", "2025-01-31")
    generate(page)
    assert page.inner_text("#reportTotal") == "0"
    assert page.inner_text("#reportPercent") == "-"
    assert "No attendance records match this report" in page.inner_text("#reportTable")


def test_report_rejects_reversed_date_range(make_page, server):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    nav(page, "reports")
    page.fill("#reportFrom", "2026-09-10")
    page.fill("#reportTo", "2026-09-01")
    page.click("#reportGenerate")
    expect(page.locator("#reportError")).to_contain_text("From date")
    expect(page.locator("#reportResult")).to_be_hidden()


def test_teacher_reports_are_limited_to_own_subjects(make_page, server):
    page = make_page()
    login(page, server["url"], "six_teacher", "/teacher")
    nav(page, "reports")
    page.wait_for_function("() => document.querySelector('#reportSubject').options.length > 1")
    subjects = page.evaluate("[...document.querySelector('#reportSubject').options].map(o => o.text)")
    assert subjects == ["All subjects", "Six Mathematics"]
    generate(page)
    rows = data_rows(page, "#reportTable")
    assert len(rows) == 36 and all(r[3] == "Six Mathematics" for r in rows)
    art = server["ids"]["art"]
    status = page.evaluate(f"fetch('/api/reports/attendance?subject_id={art}').then(r => r.status)")
    export_status = page.evaluate(f"fetch('/api/reports/attendance/export/csv?subject_id={art}').then(r => r.status)")
    assert (status, export_status) == (403, 403)


# ---------------------------------------------------------------- SYS_FR-12_10

def test_export_downloads_match_the_report(make_page, server, tmp_path):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    nav(page, "reports")
    page.select_option("#reportStudent", label="six_alice")
    page.select_option("#reportSubject", label="Six Mathematics")
    generate(page)
    assert page.inner_text("#reportTotal") == "12"

    with page.expect_download() as info:
        page.click("#reportExportCsv")
    download = info.value
    assert download.suggested_filename == "attendance_report_student_six_alice.csv"
    path = tmp_path / download.suggested_filename
    download.save_as(path)
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    assert len(rows) == 12
    assert sum(1 for r in rows if "Present" in r.values()) == 10

    with page.expect_download() as info:
        page.click("#reportExportPdf")
    pdf = tmp_path / info.value.suggested_filename
    info.value.save_as(pdf)
    assert pdf.suffix == ".pdf" and pdf.read_bytes()[:5] == b"%PDF-"

    with page.expect_download() as info:
        page.click("#reportExportJson")
    data = json.loads(open(info.value.path(), encoding="utf-8").read())
    assert data["count"] == 12 and {r["student_name"] for r in data["records"]} == {"six_alice"}


def test_export_of_empty_report_is_refused_with_message(make_page, server):
    page = make_page()
    login(page, server["url"], "six_admin", "/admin")
    nav(page, "reports")
    page.fill("#reportFrom", "2025-01-01")
    page.fill("#reportTo", "2025-01-02")
    generate(page)
    downloads = []
    page.on("download", lambda d: downloads.append(d))
    page.click("#reportExportCsv")
    expect(page.locator("#toasts .toast.error")).to_contain_text("nothing to export")
    page.wait_for_timeout(300)
    assert downloads == []
