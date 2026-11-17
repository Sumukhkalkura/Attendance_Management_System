"""Automated execution of the 19 manual validation checklist scenarios.

Drives the real frontend with Playwright against an ISOLATED demo database
(validation_demo.db) served on port 5001, following the steps written in
docs/manual_validation/*_Checklist.md.

These are AUTOMATED results only. They never replace the human manual
validation recorded in the checklists, which stays NOT RUN until a team
member performs it.

Usage:
    python scripts/run_manual_validation_automation.py

Outputs (docs/evidence/manual_validation_automation/):
    results.json, setup.log, server.log, screenshots/*.png, logs/*.log
"""

import json
import hashlib
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.request
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "evidence" / "manual_validation_automation"      # override with --out
SHOTS = OUT / "screenshots"
LOGS = OUT / "logs"


def set_output(directory):
    """Write a run to another evidence directory (earlier runs are never overwritten)."""
    global OUT, SHOTS, LOGS
    OUT = (ROOT / directory).resolve()
    SHOTS, LOGS = OUT / "screenshots", OUT / "logs"


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))
DB = ROOT / "validation_demo.db"
PROD_DB = ROOT / "attendance.db"
BASE = "http://127.0.0.1:5001"
PY = sys.executable

ADMIN, TEACHER = "demo.admin", "prof.mehta"
STUDENT = "aarav"            # student used for read-only student flows
PW_STUDENT = "meera"         # student whose password is changed and restored
NEW_USER_PW = "ManualPass123"
CHANGED_PW = "ManualNewPass1"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def demo_password():
    for line in (ROOT / "demo_credentials.txt").read_text().splitlines():
        if line.startswith("password:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("demo_credentials.txt has no password line")


# =============================================================================
# Result recording
# =============================================================================

class Case:
    def __init__(self, case_id, tester, title, expected):
        self.id, self.tester, self.title, self.expected = case_id, tester, title, expected
        self.steps, self.shots, self.notes, self.logs = [], [], [], []
        self.status = None
        self.human = None            # None = no human judgement needed, else reason
        self.browser = None
        self.started = datetime.now().isoformat(timespec="seconds")
        self.finished = None
        self.error = None
        self._n = 0

    def step(self, text, ok=None, observed=""):
        """ok=True/False is a verified check; ok=None is an action/observation."""
        self.steps.append({"step": text, "ok": ok, "observed": observed})
        mark = {True: "PASS", False: "FAIL", None: "...."}[ok]
        print(f"   [{mark}] {text}" + (f" -> {observed}" if observed else ""))
        return ok

    def check(self, text, cond, observed=""):
        return self.step(text, bool(cond), observed)

    def shot(self, page, label, full=True):
        self._n += 1
        name = f"{self.id}_{self._n:02d}_{label}.png"
        page.screenshot(path=str(SHOTS / name), full_page=full)
        self.shots.append(rel(SHOTS / name))

    def to_dict(self):
        failed = [s for s in self.steps if s["ok"] is False]
        return {
            "id": self.id, "tester": self.tester, "title": self.title, "expected": self.expected,
            "status": self.status, "human_review": self.human, "browser": self.browser,
            "started": self.started, "finished": self.finished, "error": self.error,
            "checks_total": sum(1 for s in self.steps if s["ok"] is not None),
            "checks_failed": len(failed), "steps": self.steps, "screenshots": self.shots,
            "logs": self.logs, "notes": self.notes,
        }


# =============================================================================
# Browser helpers
# =============================================================================

class Session:
    """One browser context per case, with console / error / network logging."""

    def __init__(self, browser, case, label="main", viewport=(1280, 800)):
        self.case = case
        self.ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(10_000)
        self.lines = []
        self.page_errors = []
        name = f"{case.id}_{label}.log"
        self.path = LOGS / name
        case.logs.append(rel(LOGS / name))
        p = self.page
        p.on("console", lambda m: self._log(f"console.{m.type}: {m.text}"))
        p.on("pageerror", self._pageerror)
        p.on("requestfailed", lambda r: self._log(f"requestfailed: {r.method} {r.url} {r.failure}"))
        p.on("response", self._response)
        p.on("framenavigated", lambda f: self._log(f"navigated: {f.url}") if f == p.main_frame else None)

    def _ts(self):
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _log(self, text):
        self.lines.append(f"{self._ts()} {text}")

    def _pageerror(self, exc):
        self.page_errors.append(str(exc))
        self._log(f"pageerror: {exc}")

    def _response(self, r):
        cc = r.headers.get("cache-control", "")
        if r.status >= 400 or r.request.resource_type == "document":
            self._log(f"response: {r.status} {r.request.method} {r.url} cache-control={cc!r}")

    def note(self, text):
        self._log(f"STEP: {text}")

    def close(self):
        self.path.write_text("\n".join(self.lines) + "\n")
        self.ctx.close()


def login(page, username, password, expect_ok=True):
    page.goto(f"{BASE}/login")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("#loginButton")
    if expect_ok:
        page.wait_for_url(re.compile(r".*/(admin|teacher|student).*"))
        page.wait_for_load_state("networkidle")
    else:
        page.locator("#loginError").wait_for(state="visible")


def logout(page):
    page.click("#logoutButton")
    page.locator("#confirmDialog").wait_for(state="visible")
    page.click("#confirmButton")
    page.wait_for_url(re.compile(r".*/login.*"))


def nav(page, section):
    page.click(f".nav-link[data-section='{section}']")
    page.locator(f"#section-{section}").wait_for(state="visible")


def settle(page, tbody):
    """Wait until a table body no longer shows the loading spinner."""
    page.wait_for_function(
        "sel => { const t = document.querySelector(sel); return t && t.children.length > 0"
        " && !t.querySelector('.spinner'); }", arg=tbody)
    page.wait_for_timeout(150)


def table(page, tbody):
    """Return data rows as lists of cell texts (state rows excluded)."""
    return page.evaluate(
        """sel => [...document.querySelectorAll(sel + ' > tr')]
              .filter(tr => !tr.querySelector('td[colspan]'))
              .map(tr => [...tr.children].map(td => td.innerText.trim()))""", tbody)


def state_text(page, tbody):
    return page.evaluate(
        "sel => { const s = document.querySelector(sel + ' .state'); return s ? s.innerText.trim() : ''; }", tbody)


def cell_name(cell):
    """avatarCell text is 'initial\\nname[\\nsub]'; return the name line."""
    parts = [p for p in cell.split("\n") if p.strip()]
    return parts[1] if len(parts) > 1 else parts[0]


def toast(page, text, kind="success", timeout=6000):
    loc = page.locator(f"#toasts .toast.{kind}", has_text=text)
    loc.first.wait_for(state="visible", timeout=timeout)
    return loc.first.inner_text().strip()


def last_toast(page, kind, timeout=6000):
    loc = page.locator(f"#toasts .toast.{kind}").last
    loc.wait_for(state="visible", timeout=timeout)
    return loc.inner_text().strip()


def row_with(page, tbody, *texts):
    loc = page.locator(f"{tbody} > tr")
    for t in texts:
        loc = loc.filter(has_text=t)
    return loc


def user_row(page, username):
    """Users table row whose username cell is exactly `username`."""
    idx = page.evaluate(
        """u => [...document.querySelectorAll('#usersTable > tr')].findIndex(tr => {
               const n = tr.querySelector('.cell-user > div > div'); return n && n.textContent === u; })""",
        username)
    return page.locator("#usersTable > tr").nth(idx) if idx >= 0 else None


def usernames(page):
    return page.evaluate(
        "() => [...document.querySelectorAll('#usersTable .cell-user > div > div:first-child')].map(n => n.textContent)")


def select_label(page, sel, label):
    page.select_option(sel, label=label)


def options(page, sel):
    return page.evaluate("s => [...document.querySelector(s).options].map(o => [o.value, o.text])", sel)


def fmt_pct(page, value):
    return page.evaluate("v => App.formatPercent(v)", value)


def pct_value(text):
    m = re.search(r"([\d.]+)%", text)
    return float(m.group(1)) if m else None


def api_fetch(page, path):
    return page.evaluate(
        """async p => { const r = await fetch(p, {credentials: 'same-origin'});
                       let body = null; try { body = await r.json(); } catch (e) {}
                       return {status: r.status, cache: r.headers.get('cache-control'), body}; }""", path)


# =============================================================================
# Sumukh
# =============================================================================

def sys_fr07_10(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, ADMIN, pw); c.step("Log in as demo.admin", None, p.url)
        nav(p, "users"); settle(p, "#usersTable"); c.step("Open Users", None, f"{len(table(p, '#usersTable'))} users listed")
        c.shot(p, "users_list")

        p.click("#newUserButton")
        dlg = p.locator("#userDialog"); dlg.wait_for(state="visible")
        dlg.locator("input[name=password]").fill(NEW_USER_PW)
        dlg.locator("button[type=submit]").click()
        p.wait_for_timeout(300)
        v = p.evaluate("""() => { const i = document.querySelector('#userDialog input[name=username]');
                                  return {missing: i.validity.valueMissing, msg: i.validationMessage,
                                          open: document.getElementById('userDialog').open,
                                          box: document.querySelector('#userDialog .form-error').textContent}; }""")
        c.check("Submit New user with an empty username -> validation error, dialog stays open",
                v["missing"] and v["open"] and v["msg"],
                f"native validation message: {v['msg']!r}; dialog open={v['open']}; form-error box={v['box']!r}")
        c.shot(p, "empty_username_validation")

        dlg.locator("input[name=username]").fill("manual_s1")
        dlg.locator("select[name=role]").select_option("student")
        dlg.locator("input[name=password]").fill(NEW_USER_PW)
        dlg.locator("button[type=submit]").click()
        t = toast(p, "manual_s1")
        dlg.wait_for(state="hidden")
        c.check("Create student 'manual_s1' (8+ char password)", "manual_s1" in usernames(p), f"toast: {t!r}")

        p.fill("#userSearch", "manual")
        names = usernames(p)
        c.check("Search 'manual' lists only matching users", names and all("manual" in n for n in names), f"rows: {names}")
        c.shot(p, "search_manual")
        p.fill("#userSearch", "")

        for role, badge in (("student", "Student"), ("teacher", "Teacher"), ("admin", "Admin")):
            p.select_option("#userRoleFilter", role)
            rows = table(p, "#usersTable")
            c.check(f"Role filter '{role}' shows only {badge} rows", rows and all(r[1] == badge for r in rows),
                    f"{len(rows)} row(s)")
        p.select_option("#userRoleFilter", "")
        for val, badge in (("1", "Active"), ("0", "Inactive")):
            p.select_option("#userStatusFilter", val)
            rows = table(p, "#usersTable")
            st = state_text(p, "#usersTable")
            c.check(f"Status filter '{badge}' shows only {badge} rows",
                    all(r[2] == badge for r in rows) and (rows or st),
                    f"{len(rows)} row(s)" + (f"; empty state: {st!r}" if not rows else ""))
        p.select_option("#userStatusFilter", "1"); p.select_option("#userRoleFilter", "student")
        c.shot(p, "filters_student_active")
        p.select_option("#userStatusFilter", ""); p.select_option("#userRoleFilter", "")

        user_row(p, "manual_s1").get_by_role("button", name="Edit").click()
        dlg.wait_for(state="visible")
        title = p.inner_text("#userDialogTitle")
        dlg.locator("input[name=username]").fill("manual_s1b")
        dlg.locator("button[type=submit]").click()
        t = toast(p, "Updated manual_s1b")
        names = usernames(p)
        c.check("Edit 'manual_s1' -> 'manual_s1b'; table updates",
                "manual_s1b" in names and "manual_s1" not in names, f"dialog title {title!r}; toast {t!r}")

        user_row(p, "manual_s1b").get_by_role("button", name="Deactivate").click()
        p.locator("#confirmDialog").wait_for(state="visible")
        ct = p.inner_text("#confirmTitle"); p.click("#confirmButton")
        t = toast(p, "deactivated")
        badge = user_row(p, "manual_s1b").locator("td").nth(2).inner_text()
        c.check("Deactivate 'manual_s1b' (confirmation dialog)", badge == "Inactive", f"confirm {ct!r}; toast {t!r}; badge {badge!r}")
        c.shot(p, "deactivated")

        logout(p); c.step("Log out", None, p.url)
        login(p, "manual_s1b", NEW_USER_PW, expect_ok=False)
        err = p.inner_text("#loginErrorText")
        c.check("Login as deactivated 'manual_s1b' must fail", p.url.endswith("/login"), f"error shown: {err!r}")
        c.shot(p, "deactivated_login_refused")

        login(p, ADMIN, pw); nav(p, "users"); settle(p, "#usersTable")
        user_row(p, "manual_s1b").get_by_role("button", name="Activate").click()
        p.locator("#confirmDialog").wait_for(state="visible"); p.click("#confirmButton")
        t = toast(p, "activated")
        badge = user_row(p, "manual_s1b").locator("td").nth(2).inner_text()
        c.check("Log in as demo.admin again and reactivate the account", badge == "Active", f"toast {t!r}")
        c.shot(p, "reactivated")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
        c.human = ("Optional: the empty-username error is the browser's native validation bubble, which "
                   "headless screenshots cannot capture; a person should confirm it is visible.")
    finally:
        s.close()


def sys_fr08_10(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, ADMIN, pw); c.step("Log in as demo.admin", None)
        nav(p, "classes"); settle(p, "#classesTable")
        p.click("#newClassButton"); dlg = p.locator("#classDialog"); dlg.wait_for(state="visible")
        dlg.locator("input[name=name]").fill("Manual Class"); dlg.locator("button[type=submit]").click()
        t = toast(p, 'Created class "Manual Class"'); dlg.wait_for(state="hidden")
        c.check("Open Classes; create class 'Manual Class'", row_with(p, "#classesTable", "Manual Class").count() == 1, f"toast {t!r}")

        row_with(p, "#classesTable", "Manual Class").get_by_role("button", name="Edit class").click()
        dlg.wait_for(state="visible"); dlg.locator("select[name=teacher_id]").select_option(label=TEACHER)
        dlg.locator("button[type=submit]").click(); toast(p, 'Updated class "Manual Class"'); dlg.wait_for(state="hidden")
        cells = row_with(p, "#classesTable", "Manual Class").locator("td").all_inner_texts()
        c.check("Edit it and assign teacher prof.mehta", cells[1].strip() == TEACHER, f"row: {cells[:3]}")
        c.shot(p, "class_created_edited")

        nav(p, "subjects"); settle(p, "#subjectsTable")
        p.click("#newSubjectButton"); sd = p.locator("#subjectDialog"); sd.wait_for(state="visible")
        sd.locator("input[name=name]").fill("Manual Subject"); sd.locator("select[name=teacher_id]").select_option(label=TEACHER)
        sd.locator("button[type=submit]").click(); t = toast(p, 'Created subject "Manual Subject"'); sd.wait_for(state="hidden")
        cells = row_with(p, "#subjectsTable", "Manual Subject").locator("td").all_inner_texts()
        c.check("Open Subjects; create 'Manual Subject' assigned to prof.mehta", cells[1].strip() == TEACHER, f"toast {t!r}")
        c.shot(p, "subject_created")

        nav(p, "classes"); settle(p, "#classesTable")
        row_with(p, "#classesTable", "Manual Class").get_by_role("button", name="Manage subjects").click()
        md = p.locator("#classSubjectsDialog"); md.wait_for(state="visible")
        md.locator("select[name=subject_id]").select_option(label="Manual Subject")
        md.locator("button[type=submit]").click(); t = toast(p, "Subject added to class")
        chips = p.locator("#classSubjectChips .chip").all_inner_texts()
        c.shot(p, "link_subject_dialog", full=False)
        md.get_by_role("button", name="Done").click(); md.wait_for(state="hidden")
        cells = row_with(p, "#classesTable", "Manual Class").locator("td").all_inner_texts()
        c.check("Link 'Manual Subject' to 'Manual Class'", "Manual Subject" in cells[2], f"chips {chips}; toast {t!r}")

        p.click("#newClassButton"); dlg.wait_for(state="visible")
        dlg.locator("input[name=name]").fill("Manual Class"); dlg.locator("button[type=submit]").click()
        p.wait_for_function("() => document.querySelector('#classDialog .form-error').textContent.length > 0")
        err = p.inner_text("#classDialog .form-error")
        c.check("Create duplicate 'Manual Class' -> error shown", err and p.evaluate("document.getElementById('classDialog').open"),
                f"error: {err!r}")
        c.shot(p, "duplicate_class_error", full=False)
        dlg.get_by_role("button", name="Cancel").click()
        n = row_with(p, "#classesTable", "Manual Class").count()
        c.check("Duplicate was not created", n == 1, f"{n} 'Manual Class' row(s)")

        p.fill("#classSearch", "Manual"); rows = table(p, "#classesTable")
        c.check("Class search 'Manual' lists only matching classes", rows and all("Manual" in r[0] for r in rows), f"{[r[0] for r in rows]}")
        p.fill("#classSearch", "Year 2"); rows = table(p, "#classesTable")
        c.check("Class search 'Year 2' lists only matching classes", rows and all("Year 2" in r[0] for r in rows), f"{[r[0] for r in rows]}")
        p.fill("#classSearch", "")
        nav(p, "subjects"); settle(p, "#subjectsTable")
        p.fill("#subjectSearch", "Manual"); rows = table(p, "#subjectsTable")
        c.check("Subject search 'Manual' lists only matching subjects", rows and all("Manual" in r[0] for r in rows), f"{[r[0] for r in rows]}")
        c.shot(p, "subject_search")

        logout(p); login(p, TEACHER, pw)
        p.wait_for_function("() => !document.querySelector('#subjectList .spinner') && document.querySelector('#subjectList li')")
        subj = p.locator("#subjectList li").all_inner_texts()
        c.check("Log in as prof.mehta; 'Manual Subject' appears in Overview", any("Manual Subject" in x for x in subj), f"{subj}")
        c.shot(p, "teacher_overview_manual_subject")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def it_fr09_09(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, ADMIN, pw); nav(p, "enrollments"); settle(p, "#enrollmentsTable")
        select_label(p, "#enrollmentClassFilter", "Manual Class")
        before = table(p, "#enrollmentsTable")
        c.step("Admin > Enrollments: note enrollments in Manual Class / Manual Subject", None,
               f"{len(before)} before: {[cell_name(r[0]) for r in before]}")
        select_label(p, "#enrollStudent", STUDENT); select_label(p, "#enrollClass", "Manual Class")
        select_label(p, "#enrollSubject", "Manual Subject"); p.click("#enrollButton")
        t = toast(p, "Student enrolled")
        after = [cell_name(r[0]) for r in table(p, "#enrollmentsTable")]
        c.check(f"Enroll exactly one student ({STUDENT})", after == [STUDENT], f"toast {t!r}; Manual Class rows {after}")
        c.shot(p, "one_student_enrolled")

        logout(p); login(p, TEACHER, pw); nav(p, "mark")
        p.wait_for_function("() => document.querySelector('#markClass').options.length > 1")
        cls = [o[1] for o in options(p, "#markClass")]
        c.check("Manual Class offered in Mark attendance", "Manual Class" in cls, f"classes: {cls}")
        select_label(p, "#markClass", "Manual Class"); select_label(p, "#markSubject", "Manual Subject")
        c.step("Select Manual Class, Manual Subject, today's date; click Load", None, p.input_value("#markDate"))
        p.click("#loadRosterButton"); settle(p, "#rosterTable")
        roster = [cell_name(r[0]) for r in table(p, "#rosterTable")]
        c.check("Only the enrolled student is listed and nobody else", roster == [STUDENT], f"roster: {roster}")
        c.shot(p, "roster_only_enrolled")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_fr09_10(c, b, pw):
    s = Session(b, c); p = s.page
    stu = "diya"
    try:
        login(p, ADMIN, pw); nav(p, "enrollments"); settle(p, "#enrollmentsTable")
        total0 = p.inner_text("#enrollmentCount")
        select_label(p, "#enrollStudent", stu); select_label(p, "#enrollClass", "Manual Class")
        select_label(p, "#enrollSubject", "Manual Subject"); p.click("#enrollButton")
        t = toast(p, "Student enrolled")
        n = row_with(p, "#enrollmentsTable", stu, "Manual Class", "Manual Subject").count()
        c.check(f"Enroll {stu} in Manual Class / Manual Subject; appears in list", n == 1,
                f"toast {t!r}; count {total0!r} -> {p.inner_text('#enrollmentCount')!r}")
        c.shot(p, "enrolled")

        select_label(p, "#enrollStudent", stu); p.click("#enrollButton")
        err = last_toast(p, "error")
        c.check("Enroll the same combination again -> error", err, f"error toast: {err!r}")
        c.shot(p, "duplicate_error", full=False)

        p.fill("#enrollmentSearch", stu); rows = table(p, "#enrollmentsTable")
        c.check(f"Search '{stu}' lists only {stu}'s enrollments", rows and all(cell_name(r[0]) == stu for r in rows), f"{len(rows)} row(s)")
        p.fill("#enrollmentSearch", "")
        select_label(p, "#enrollmentClassFilter", "BSc Computer Science - Year 2"); rows = table(p, "#enrollmentsTable")
        c.check("Class filter 'Year 2' lists only that class", rows and all(r[1] == "BSc Computer Science - Year 2" for r in rows), f"{len(rows)} row(s)")
        select_label(p, "#enrollmentClassFilter", "Manual Class"); rows = table(p, "#enrollmentsTable")
        c.check("Class filter 'Manual Class' lists only that class", rows and all(r[1] == "Manual Class" for r in rows),
                f"{[cell_name(r[0]) for r in rows]}")
        c.shot(p, "class_filter")

        row_with(p, "#enrollmentsTable", stu, "Manual Class").get_by_role("button", name="Remove enrollment").click()
        p.locator("#confirmDialog").wait_for(state="visible"); ct = p.inner_text("#confirmMessage"); p.click("#confirmButton")
        t = toast(p, "Enrollment removed")
        n = row_with(p, "#enrollmentsTable", stu, "Manual Class").count()
        c.check("Remove the enrollment; it disappears", n == 0, f"confirm {ct!r}; toast {t!r}")
        c.shot(p, "removed")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_fr13_10(c, b, pw):
    s = Session(b, c); p = s.page
    changed = False
    try:
        login(p, PW_STUDENT, pw); c.step(f"Log in as demo student {PW_STUDENT}", None)
        dlg = p.locator("#passwordDialog")

        def submit(cur, new):
            p.click("#changePasswordButton"); dlg.wait_for(state="visible")
            dlg.locator("input[name=current_password]").fill(cur)
            dlg.locator("input[name=new_password]").fill(new)
            dlg.locator("input[name=confirm_password]").fill(new)
            dlg.get_by_role("button", name="Change password").click()
            p.wait_for_timeout(600)
            return p.evaluate("""() => { const d = document.getElementById('passwordDialog');
                const n = d.querySelector('input[name=new_password]');
                return {open: d.open, box: d.querySelector('.form-error').textContent,
                        tooShort: n.validity.tooShort, msg: n.validationMessage}; }""")

        r = submit("Wrong-Current-000", CHANGED_PW)
        c.check("Wrong current password -> error", r["open"] and r["box"], f"error: {r['box']!r}")
        c.shot(p, "wrong_current", full=False)
        dlg.get_by_role("button", name="Cancel").click()

        r = submit(pw, "Abc1234")
        shown = r["box"] or r["msg"]
        c.check("Correct current + 7-character new password -> error", r["open"] and shown,
                f"form-error={r['box']!r}; native tooShort={r['tooShort']} message={r['msg']!r}")
        c.shot(p, "seven_char_rejected", full=False)
        dlg.get_by_role("button", name="Cancel").click()

        p.click("#changePasswordButton"); dlg.wait_for(state="visible")
        dlg.locator("input[name=current_password]").fill(pw)
        dlg.locator("input[name=new_password]").fill(CHANGED_PW)
        dlg.locator("input[name=confirm_password]").fill(CHANGED_PW)
        dlg.get_by_role("button", name="Change password").click()
        t = toast(p, "Your password has been changed"); changed = True
        dlg.wait_for(state="hidden")
        c.check("Correct current + new 8+ char password -> success message", True, f"toast {t!r}")
        c.shot(p, "changed")

        logout(p)
        login(p, PW_STUDENT, pw, expect_ok=False)
        c.check("Log in with the old password must fail", p.url.endswith("/login"), p.inner_text("#loginErrorText"))
        login(p, PW_STUDENT, CHANGED_PW)
        c.check("Log in with the new password must work", "/student" in p.url, p.url)
        c.shot(p, "new_password_login")

        p.click("#changePasswordButton"); dlg.wait_for(state="visible")
        dlg.locator("input[name=current_password]").fill(CHANGED_PW)
        dlg.locator("input[name=new_password]").fill(pw)
        dlg.locator("input[name=confirm_password]").fill(pw)
        dlg.get_by_role("button", name="Change password").click()
        t = toast(p, "Your password has been changed"); changed = False
        logout(p); login(p, PW_STUDENT, pw)
        c.check("Change the password back (original password works again)", "/student" in p.url, f"toast {t!r}")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        if changed:
            c.notes.append("WARNING: password for meera was left changed; restore it manually.")
        s.close()


# =============================================================================
# Jagadeesh
# =============================================================================

def sys_fr01_08(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, TEACHER, pw)
        doc = p.request.get(f"{BASE}/teacher")
        c.step("Log in as prof.mehta (teacher)", None, f"/teacher Cache-Control: {doc.headers.get('cache-control')!r}")
        nav(p, "records"); settle(p, "#recordsTable")
        n = len(table(p, "#recordsTable"))
        api = api_fetch(p, "/api/attendance")
        c.step("Open Attendance records", None, f"{n} rows; /api/attendance Cache-Control {api['cache']!r}")
        c.shot(p, "records_before_logout")
        logout(p); c.step("Click Log out and confirm", None, p.url)

        for i in (1, 2):
            p.go_back(); p.wait_for_load_state("networkidle"); p.wait_for_timeout(400)
            rows = p.evaluate("() => document.querySelectorAll('#recordsTable > tr:not(:has(td[colspan]))').length")
            c.check(f"Press Back ({i}): no attendance data shown", rows == 0, f"url {p.url}; record rows visible {rows}")
            c.shot(p, f"after_back_{i}")
        p.reload(); p.wait_for_load_state("networkidle")
        c.check("Reload the page -> login page", "/login" in p.url, p.url)
        p.goto(f"{BASE}/teacher")
        c.check("Type /teacher in the address bar -> redirected to /login", "/login" in p.url, p.url)
        api = api_fetch(p, "/api/attendance")
        c.check("API request after logout returns 401", api["status"] == 401, f"status {api['status']}; body {api['body']}")
        c.check("Responses carry Cache-Control: no-store",
                "no-store" in (doc.headers.get("cache-control") or "") and "no-store" in (api["cache"] or ""),
                f"/teacher {doc.headers.get('cache-control')!r}; /api/attendance {api['cache']!r}")
        c.shot(p, "teacher_url_redirected")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_fr03_13(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, TEACHER, pw); nav(p, "records"); settle(p, "#recordsTable")
        rows = table(p, "#recordsTable")
        target = next(r for r in rows if r[3] != "Late")
        key = (target[0], cell_name(target[1]), target[2])
        c.step("Open Attendance records; pick a record", None, f"{len(rows)} rows; record {key} status {target[3]!r}")

        def find():
            for i, r in enumerate(table(p, "#recordsTable")):
                if (r[0], cell_name(r[1]), r[2]) == key:
                    return i, r
            return None, None

        i, _ = find()
        p.locator("#recordsTable > tr").nth(i).get_by_role("button", name="Correct status").click()
        dlg = p.locator("#editRecordDialog"); dlg.wait_for(state="visible")
        dlg.locator("select[name=status]").select_option("Late")
        dlg.get_by_role("button", name="Save change").click()
        t = toast(p, "Attendance record updated"); settle(p, "#recordsTable")
        i, r = find()
        c.check("Correct status -> Late; table shows Late", r and r[3] == "Late", f"toast {t!r}; row {r}")
        c.shot(p, "status_corrected")

        p.locator("#recordsTable > tr").nth(i).get_by_role("button", name="Delete record").click()
        cd = p.locator("#confirmDialog"); cd.wait_for(state="visible")
        msg = p.inner_text("#confirmMessage")
        c.check("Click delete -> confirmation dialog appears", cd.is_visible(), f"{p.inner_text('#confirmTitle')!r}: {msg!r}")
        c.shot(p, "delete_confirm", full=False)
        cd.get_by_role("button", name="Cancel").click(); cd.wait_for(state="hidden")
        i2, _ = find()
        c.check("Cancel -> the record is still there", i2 is not None)

        n_before = len(table(p, "#recordsTable"))
        p.locator("#recordsTable > tr").nth(i2).get_by_role("button", name="Delete record").click()
        cd.wait_for(state="visible"); p.click("#confirmButton")
        t = toast(p, "Attendance record deleted"); settle(p, "#recordsTable")
        i3, _ = find(); n_after = len(table(p, "#recordsTable"))
        c.check("Delete and confirm -> record disappears and a message is shown", i3 is None and n_after == n_before - 1,
                f"toast {t!r}; rows {n_before} -> {n_after}")
        c.shot(p, "record_deleted")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_fr10_10(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, TEACHER, pw); nav(p, "records"); settle(p, "#recordsTable")
        all_rows = table(p, "#recordsTable"); n_all = len(all_rows)
        c.step("Log in as prof.mehta; open Attendance records", None, f"{n_all} rows")
        p.fill("#recordSearch", "kabir"); rows = table(p, "#recordsTable")
        c.check("Search 'kabir' -> only kabir's rows", rows and all(cell_name(r[1]) == "kabir" for r in rows), f"{len(rows)} rows")
        c.shot(p, "teacher_search")
        p.fill("#recordSearch", "")

        subj = options(p, "#recordSubject")[1]
        p.select_option("#recordSubject", subj[0]); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        c.check(f"Subject filter '{subj[1]}' -> table updates", rows and all(r[2] == subj[1] for r in rows), f"{len(rows)} rows")
        iso = api_fetch(p, f"/api/attendance?subject_id={subj[0]}")["body"]["records"][0]["attendance_date"]
        p.fill("#recordDate", iso); p.dispatch_event("#recordDate", "change"); settle(p, "#recordsTable")
        shown = p.evaluate("d => App.formatDate(d)", iso); rows = table(p, "#recordsTable")
        c.check(f"Then date {iso} -> table updates", rows and all(r[0] == shown and r[2] == subj[1] for r in rows), f"{len(rows)} rows")
        p.select_option("#recordStatus", "Present"); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        st = state_text(p, "#recordsTable")
        c.check("Then status Present -> table updates", all(r[3] == "Present" for r in rows) and (rows or st), f"{len(rows)} rows")
        c.shot(p, "teacher_filters")

        p.fill("#recordSearch", "a")
        clear = p.locator("#section-records").get_by_role("button", name=re.compile("clear", re.I))
        c.check("'Clear filters' control present on the teacher Attendance records screen", clear.count() == 1)
        clear.first.click(); settle(p, "#recordsTable")
        values = p.evaluate("""() => ['#recordSearch','#recordSubject','#recordClass','#recordDate','#recordFrom','#recordTo','#recordStatus']
                              .map(s => document.querySelector(s) ? document.querySelector(s).value : null)""")
        n = len(table(p, "#recordsTable"))
        c.check("Click 'Clear filters' -> every filter reset and all rows restored", n == n_all and values == [""] * 7,
                f"{n} rows (all = {n_all}); filter values after clearing {values}")
        c.shot(p, "teacher_cleared")

        cls = options(p, "#recordClass")[1]
        p.select_option("#recordClass", cls[0]); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        expected = api_fetch(p, f"/api/attendance?class_id={cls[0]}")["body"]["count"]
        c.check(f"Class filter '{cls[1]}' -> table matches the API", rows and len(rows) == expected, f"{len(rows)} rows (API {expected})")
        dates = sorted({r["attendance_date"] for r in api_fetch(p, "/api/attendance")["body"]["records"]})
        frm, to = dates[0], dates[min(2, len(dates) - 1)]
        p.fill("#recordFrom", frm); p.dispatch_event("#recordFrom", "change")
        p.fill("#recordTo", to); p.dispatch_event("#recordTo", "change"); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        expected = api_fetch(p, f"/api/attendance?class_id={cls[0]}&start_date={frm}&end_date={to}")["body"]["count"]
        c.check(f"Date range {frm} to {to} (with class filter) -> table matches the API", rows and len(rows) == expected,
                f"{len(rows)} rows (API {expected})")
        c.shot(p, "teacher_class_and_range")
        p.click("#recordClear"); settle(p, "#recordsTable")
        c.check("Clear filters after class and date-range filters -> all rows restored", len(table(p, "#recordsTable")) == n_all)

        logout(p); login(p, ADMIN, pw); nav(p, "attendance"); settle(p, "#recordsTable")
        n_admin = len(table(p, "#recordsTable"))
        subj = options(p, "#recordSubject")[1]
        p.select_option("#recordSubject", subj[0]); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        c.check(f"Admin: subject filter '{subj[1]}'", rows and all(r[2] == subj[1] for r in rows), f"{len(rows)} rows")
        p.fill("#recordDate", iso); p.dispatch_event("#recordDate", "change"); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        c.check(f"Admin: date {iso}", rows and all(r[0] == shown for r in rows), f"{len(rows)} rows")
        p.select_option("#recordStatus", "Absent"); settle(p, "#recordsTable"); rows = table(p, "#recordsTable")
        c.check("Admin: status Absent", all(r[3] == "Absent" for r in rows) and (rows or state_text(p, "#recordsTable")), f"{len(rows)} rows")
        c.shot(p, "admin_filters")
        p.click("#recordClear"); settle(p, "#recordsTable"); n = len(table(p, "#recordsTable"))
        c.check("Admin: 'Clear filters' restores all rows", n == n_admin, f"{n} rows (all = {n_admin})")
        c.shot(p, "admin_cleared")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
        c.notes.append("The student History screen keeps its subject, status and date filters; they are exercised in UT_FR-05_04.")
    finally:
        s.close()


def _lows(p, tbody, has_attended_col):
    out = {}
    for r in table(p, tbody):
        out[cell_name(r[0])] = pct_value(r[-1])
    return out


def sys_fr11_10(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        for user, low_tb, limit, sect in ((TEACHER, "#lowTable", 6, "percentages"), (ADMIN, "#lowAttendanceTable", 8, "attendance")):
            login(p, user, pw); settle(p, low_tb)
            low = _lows(p, low_tb, user == ADMIN)
            c.step(f"{user}: Overview 'Students needing attention'", None, f"{low}")
            c.shot(p, f"{user.split('.')[0]}_overview_alerts")
            nav(p, sect); settle(p, "#percentTable")
            pct = {cell_name(r[0]): (pct_value(r[-1]), int(r[2])) for r in table(p, "#percentTable")}
            below = {k: v[0] for k, v in pct.items() if v[0] is not None and v[1] > 0 and v[0] < 75}
            expected = dict(sorted(below.items(), key=lambda kv: kv[1])[:limit])
            c.check(f"{user}: every student below 75% is listed, none at/above 75%",
                    set(low) == set(expected) and all(v < 75 for v in low.values()),
                    f"below 75% on Percentages: {below}; listed: {sorted(low)} (overview shows at most {limit})")
            c.shot(p, f"{user.split('.')[0]}_percentages")
            if not below:
                c.step("Nobody below 75%: step 4 (mark absences) would be needed", None, "not needed")
            logout(p)
        login(p, ADMIN, pw)
        found = p.evaluate("() => [...document.querySelectorAll('input,select,label')].filter(e => /threshold/i.test(e.id + e.name + e.textContent)).length")
        c.step("Record that there is no screen to change the 75% threshold (known gap G-04)", None,
               f"threshold controls found in admin dashboard: {found}")
        c.notes.append("The 'Everyone is on track' empty state was not exercised: in the seeded data both dashboards have students below 75%.")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_fr04_11(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, TEACHER, pw); nav(p, "percentages"); settle(p, "#percentTable")
        subj = options(p, "#percentSubject")[1]
        with p.expect_response(lambda r: "percentages?subject_id=" in r.url) as resp:
            p.select_option("#percentSubject", subj[0])
        api = {x["student_name"]: x for x in resp.value.json()["students"]}
        settle(p, "#percentTable")
        rows = table(p, "#percentTable")
        c.step(f"Open Percentages; pick subject '{subj[1]}'", None, f"{len(rows)} students")
        c.shot(p, "percentages_subject")
        # one student with a non-integer percentage and one other, so rounding is exercised
        picks = sorted(rows, key=lambda r: float(api[cell_name(r[0])]["attendance_percentage"]).is_integer())[:2]
        for r in picks:
            name, shown = cell_name(r[0]), r[-1]
            nav(p, "records"); settle(p, "#recordsTable")
            p.select_option("#recordSubject", subj[0]); settle(p, "#recordsTable")
            p.fill("#recordSearch", name)
            recs = [x[3] for x in table(p, "#recordsTable")]
            P, A, L = recs.count("Present"), recs.count("Absent"), recs.count("Late")
            calc = round(P / (P + A + L) * 100, 2)
            c.step(f"Records for {name} / {subj[1]}: count statuses", None, f"Present {P}, Absent {A}, Late {L}")
            c.shot(p, f"records_{name}")
            apiv = api[name]["attendance_percentage"]
            c.check(f"{name}: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended)",
                    abs(apiv - calc) < 1e-9, f"hand calc {calc}; API {apiv}")
            two_dp = f"{calc:.2f}".rstrip("0").rstrip(".") + "%"
            c.check(f"{name}: Percentages screen shows the same value rounded to 2 decimals",
                    pct_value(shown) == calc, f"screen {shown!r}; 2-dp value {calc} ({two_dp})")
            nav(p, "percentages"); settle(p, "#percentTable")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_nfr02_06(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        cdp = s.ctx.new_cdp_session(p)
        cdp.send("Network.enable"); cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
        c.step("Disable the browser cache (DevTools 'Disable cache' via CDP)", None)
        login(p, TEACHER, pw)
        t0 = time.perf_counter(); p.reload(wait_until="load")
        settle(p, "#lowTable"); data_ms = (time.perf_counter() - t0) * 1000
        load = p.evaluate("() => performance.getEntriesByType('navigation')[0].loadEventEnd")
        times = {"overview (Load event)": load, "overview (data shown)": data_ms}
        c.shot(p, "overview")
        for sec, ready in (("mark", "() => document.querySelector('#markClass').options.length > 1"),
                           ("records", None), ("percentages", None)):
            t0 = time.perf_counter(); nav(p, sec)
            if ready: p.wait_for_function(ready)
            else: settle(p, "#recordsTable" if sec == "records" else "#percentTable")
            times[sec] = (time.perf_counter() - t0) * 1000
            c.shot(p, sec)
        for k, v in times.items():
            c.check(f"{k} under 3 seconds", v < 3000, f"{v:.0f} ms")
        c.notes.append(json.dumps({k: round(v) for k, v in times.items()}))
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
        c.human = "Optional: timings were taken on this Mac; repeat on the demo machine if it is a different computer."
    finally:
        s.close()


def sys_fr15_06(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        for user, path in ((ADMIN, "/admin"), (STUDENT, "/student"), (TEACHER, "/teacher")):
            login(p, user, pw); logout(p)
            visible = p.locator("#loginButton").is_visible()
            c.check(f"{user}: Log out + confirm -> login page", p.url.endswith("/login") and visible, p.url)
            c.shot(p, f"{user.split('.')[0]}_logged_out")
            p.goto(BASE + path)
            c.check(f"{user}: signed-out state ({path} redirects to /login)", "/login" in p.url, p.url)
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


# =============================================================================
# Tharith
# =============================================================================

def ut_fr05_04(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, STUDENT, pw); nav(p, "history"); settle(p, "#historyTable")
        n = len(table(p, "#historyTable"))
        c.step("Log in as a demo student; open Attendance history", None, f"{n} records")
        p.fill("#historyDate", "2020-01-05"); p.dispatch_event("#historyDate", "change")
        rows, st = table(p, "#historyTable"), state_text(p, "#historyTable")
        c.check("Choose a date with no attendance (Sun 2020-01-05) -> clear 'no records' message",
                not rows and st, f"message: {st!r}; count line {p.inner_text('#historyCount')!r}")
        c.shot(p, "empty_state")
        api = api_fetch(p, "/api/attendance?attendance_date=2020-01-05")
        c.check("API returns an empty list for that date", api["status"] == 200 and api["body"].get("records") == [],
                f"{api['status']} {api['body']}")
        clear = p.locator("#section-history").get_by_role("button", name=re.compile("clear", re.I)).count()
        c.step("Click Clear filters (if shown)", None, "no Clear filters button is shown on the student History screen")
        p.fill("#historyDate", ""); p.dispatch_event("#historyDate", "change")
        c.check("Clearing the date by hand returns the records", len(table(p, "#historyTable")) == n,
                f"{len(table(p, '#historyTable'))} records (clear button present: {bool(clear)})")
        c.shot(p, "records_back")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
        c.human = "Judge whether the empty-state message is 'clear' to a student (wording judgement)."
    finally:
        s.close()


OVERFLOW_JS = """() => {
  const vw = document.documentElement.clientWidth;
  const page = document.documentElement.scrollWidth - vw;
  const wraps = [...document.querySelectorAll('.table-wrap')].filter(w => w.offsetParent)
      .map(w => w.scrollWidth - w.clientWidth).filter(d => d > 0);
  const outside = [...document.querySelectorAll('main *')].filter(e => {
      if (!e.offsetParent || e.closest('.table-wrap')) return false;
      const r = e.getBoundingClientRect(); return r.width > 0 && r.right > vw + 1; }).length;
  const clipped = [...document.querySelectorAll('.table-wrap .badge, .table-wrap button')].filter(e => {
      if (!e.offsetParent) return false;
      const r = e.getBoundingClientRect(); return r.left < 0 || r.right > vw + 0.5; }).length;
  return {page, wraps, outside, clipped};
}"""


def sys_fr05_10(c, b, pw):
    widths = ((375, 812), (768, 1024), (1280, 800))
    for user, pages in ((STUDENT, ("/student#overview", "/student#history")), (TEACHER, ("/teacher#records",))):
        s = Session(b, c, label=user.split(".")[0])
        p = s.page
        try:
            login(p, user, pw)
            for w, h in widths:
                p.set_viewport_size({"width": w, "height": h})
                for path in pages:
                    p.goto(BASE + path); p.wait_for_load_state("networkidle"); p.wait_for_timeout(300)
                    m = p.evaluate(OVERFLOW_JS)
                    tag = path.split("/")[1].replace("#", "_")
                    c.check(f"{tag} at {w}px: no page-level sideways scrolling", m["page"] <= 0,
                            f"page overflow {m['page']}px; elements past right edge {m['outside']}")
                    c.check(f"{tag} at {w}px: tables fit without their own sideways scroll", not m["wraps"],
                            f"table-wrap overflow {m['wraps']} px")
                    c.check(f"{tag} at {w}px: no status badge or action button cut off", m["clipped"] == 0,
                            f"{m['clipped']} clipped")
                    c.shot(p, f"{tag}_{w}px")
            c.check(f"{user}: no uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
        finally:
            s.close()
    c.human = "Readability and 'nothing overlaps' are visual judgements; review the screenshots or repeat on a device."


def sys_fr14_08(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, STUDENT, pw); p.wait_for_function("() => document.querySelector('#countTotal').textContent !== '–'")
        card = {k: p.inner_text(f"#{k}") for k in ("overallPercent", "countPresent", "countAbsent", "countLate", "countTotal")}
        c.shot(p, "student_overview")
        nav(p, "history"); settle(p, "#historyTable")
        st = [r[2] for r in table(p, "#historyTable")]
        P, A, L, T = st.count("Present"), st.count("Absent"), st.count("Late"), len(st)
        calc = fmt_pct(p, round(P / T * 10000) / 100) if T else "–"
        c.check("Student: My attendance numbers match the History records",
                (card["countPresent"], card["countAbsent"], card["countLate"], card["countTotal"], card["overallPercent"])
                == (str(P), str(A), str(L), str(T), calc),
                f"cards {card}; counted from history P{P} A{A} L{L} T{T} -> {calc}")
        logout(p)

        login(p, TEACHER, pw); settle(p, "#lowTable")
        card = {k: p.inner_text(f"#{k}") for k in ("statSubjects", "statClasses", "statStudents", "statAverage")}
        c.shot(p, "teacher_overview")
        nav(p, "percentages"); settle(p, "#percentTable")
        rows = table(p, "#percentTable"); att = sum(int(r[1]) for r in rows); tot = sum(int(r[2]) for r in rows)
        n_subj = len(options(p, "#percentSubject")) - 1
        nav(p, "mark"); p.wait_for_function("() => document.querySelector('#markClass').options.length > 1")
        n_cls = len(options(p, "#markClass")) - 1
        avg = fmt_pct(p, round(att / tot * 10000) / 100) if tot else "–"   # two-decimal display (FR-04)
        c.check("Teacher: Overview cards match Percentages / Mark attendance screens",
                (card["statSubjects"], card["statClasses"], card["statStudents"], card["statAverage"])
                == (str(n_subj), str(n_cls), str(len(rows)), avg),
                f"cards {card}; screens: subjects {n_subj}, classes {n_cls}, students {len(rows)}, average {avg} ({att}/{tot})")
        logout(p)

        login(p, ADMIN, pw); p.wait_for_function("() => !document.querySelector('#statClasses .skeleton')")
        card = {k: p.inner_text(f"#{k}") for k in ("statStudents", "statTeachers", "statClasses", "statSubjects")}
        c.shot(p, "admin_overview")
        nav(p, "users"); settle(p, "#usersTable")
        p.select_option("#userRoleFilter", "student"); n_st = len(table(p, "#usersTable"))
        p.select_option("#userRoleFilter", "teacher"); n_te = len(table(p, "#usersTable"))
        nav(p, "classes"); settle(p, "#classesTable"); n_c = len(table(p, "#classesTable"))
        nav(p, "subjects"); settle(p, "#subjectsTable"); n_s = len(table(p, "#subjectsTable"))
        c.check("Admin: Overview counts match the Users, Classes and Subjects lists",
                (card["statStudents"], card["statTeachers"], card["statClasses"], card["statSubjects"])
                == (str(n_st), str(n_te), str(n_c), str(n_s)),
                f"cards {card}; lists: students {n_st}, teachers {n_te}, classes {n_c}, subjects {n_s}")
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


def sys_fr15_07(c, b, pw):
    s = Session(b, c); p = s.page
    try:
        login(p, STUDENT, pw); nav(p, "history"); settle(p, "#historyTable")
        c.step("Log in as a demo student; open Attendance history", None, f"{len(table(p, '#historyTable'))} records")
        logout(p); c.step("Log out and confirm", None, p.url)
        p.go_back(); p.wait_for_load_state("networkidle"); p.wait_for_timeout(400)
        rows = p.evaluate("() => document.querySelectorAll('#historyTable > tr:not(:has(td[colspan]))').length")
        c.check("Press Back: attendance data is not shown", rows == 0, f"url {p.url}; record rows visible {rows}")
        c.check("Press Back: user is on the login page", "/login" in p.url, p.url)
        c.shot(p, "after_back")
        p.reload(); p.wait_for_load_state("networkidle")
        c.check("Reload -> login page", "/login" in p.url, p.url)
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
    finally:
        s.close()


FOCUS_JS = """() => {
  const e = document.activeElement; if (!e || e === document.body) return null;
  const cs = getComputedStyle(e.matches('.segmented input') ? e.nextElementSibling : e);
  const lbl = e.getAttribute('aria-label') || (e.labels && e.labels[0] && e.labels[0].innerText) || e.innerText || e.value || '';
  return {tag: e.tagName.toLowerCase(), id: e.id, cls: e.className, name: lbl.trim().slice(0, 40),
          fv: e.matches(':focus-visible'), outline: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0,
          shadow: cs.boxShadow !== 'none'};
}"""


def it_nfr04_04(c, b, pw):
    s = Session(b, c); p = s.page; kb = p.keyboard
    try:
        p.goto(f"{BASE}/login")
        for _ in range(10):
            kb.press("Tab")
            if p.evaluate("document.activeElement.id") == "username": break
        kb.type(ADMIN); kb.press("Tab"); kb.type(pw); kb.press("Enter")
        p.wait_for_url(re.compile(".*/admin.*")); p.wait_for_load_state("networkidle")
        c.check("Log in as demo.admin using only the keyboard", "/admin" in p.url, p.url)

        seen = []
        for _ in range(12):
            kb.press("Tab"); f = p.evaluate(FOCUS_JS)
            if not f: continue
            seen.append(f)
            if f["id"] == "logoutButton": break
        side = [f for f in seen if "nav-link" in f["cls"] or f["id"] in ("changePasswordButton", "logoutButton")]
        bad = [f["name"] or f["id"] for f in side if not (f["fv"] and (f["outline"] or f["shadow"]))]
        c.check("Tab through the sidebar: visible focus style on every item", side and not bad,
                f"{len(side)} items: {[f['name'] for f in side]}; without focus style: {bad}")
        unl = [f for f in seen if not f["name"]]
        c.check("Every focused control has an accessible name", not unl, f"unnamed: {unl}")

        for _ in range(12):
            kb.press("Shift+Tab")
            if p.evaluate("document.activeElement.dataset.section") == "users": break
        c.shot(p, "focus_nav_users", full=False)
        kb.press("Enter"); p.locator("#section-users").wait_for(state="visible")
        c.check("Open a section with Enter (Users)", p.is_visible("#section-users"))
        for _ in range(15):
            kb.press("Tab")
            if p.evaluate("document.activeElement.id") == "newUserButton": break
        kb.press("Enter"); p.wait_for_timeout(300)
        opened = p.evaluate("document.getElementById('userDialog').open")
        c.shot(p, "dialog_opened_keyboard", full=False)
        kb.press("Escape"); p.wait_for_timeout(300)
        closed = not p.evaluate("document.getElementById('userDialog').open")
        c.check("Open a dialog with the keyboard and close it with Esc", opened and closed, f"opened {opened}; closed by Esc {closed}")
        s.close()

        s = Session(b, c, label="teacher"); p = s.page; kb = p.keyboard
        p.goto(f"{BASE}/login"); p.focus("#username"); kb.type(TEACHER); kb.press("Tab"); kb.type(pw); kb.press("Enter")
        p.wait_for_url(re.compile(".*/teacher.*")); p.wait_for_load_state("networkidle")
        p.focus(".nav-link[data-section='mark']"); kb.press("Enter")
        p.wait_for_function("() => document.querySelector('#markClass').options.length > 1")
        for _ in range(20):
            kb.press("Tab")
            if p.evaluate("document.activeElement.id") == "markClass": break
        kb.type("BSc Computer Science - Year 1")
        cls = p.input_value("#markClass"); kb.press("Tab"); kb.type("Programming")
        sub = p.input_value("#markSubject")
        c.check("Choose class and subject with the keyboard", cls and sub,
                f"class value {cls!r}, subject value {sub!r}")
        reached = False
        for _ in range(10):   # the native date input has several Tab stops (month/day/year)
            kb.press("Tab")
            if p.evaluate("document.activeElement.id") == "loadRosterButton":
                reached = True; break
        c.check("Reach 'Load students' with Tab", reached, p.evaluate("document.activeElement.id || document.activeElement.tagName"))
        kb.press("Enter"); settle(p, "#rosterTable")
        for _ in range(10):
            kb.press("Tab")
            if p.evaluate("!!document.activeElement.closest('.segmented')"): break
        f = p.evaluate(FOCUS_JS)
        before = p.evaluate("document.activeElement.value")
        kb.press("ArrowRight")
        after = p.evaluate("document.activeElement.value + ':' + document.activeElement.checked")
        c.check("Select attendance statuses with the keyboard (arrow keys in the status group)",
                before == "Present" and after == "Absent:true" and f["fv"] and (f["outline"] or f["shadow"]),
                f"focused {f['name']!r} ({before}); after ArrowRight {after}; focus style {f['outline'] or f['shadow']}")
        c.shot(p, "roster_keyboard_status", full=False)
        c.step("Attendance was not saved (keyboard check only)", None)
        c.check("No uncaught JavaScript errors", not s.page_errors, str(s.page_errors))
        c.human = "Whether the focus outline is clearly visible, and screen-reader use, need a person (visual/assistive judgement)."
    finally:
        s.close()


def sys_nfr04_06(c, b, pw):
    """Not automatable: needs a person who has not used the app. Only a task-completion smoke is run."""
    s = Session(b, c); p = s.page
    try:
        t0 = time.perf_counter()
        login(p, STUDENT, pw); p.wait_for_function("() => document.querySelector('#countTotal').textContent !== '–'")
        overall = p.inner_text("#overallPercent"); sub = p.locator("#subjectBreakdown .subject-row-head").first.inner_text()
        c.step("Smoke - student: find overall and one subject's attendance", None, f"{overall}; {sub!r}")
        c.shot(p, "student_task"); logout(p)
        login(p, TEACHER, pw); nav(p, "mark")
        p.wait_for_function("() => document.querySelector('#markClass').options.length > 1")
        select_label(p, "#markClass", "BSc Computer Science - Year 2"); select_label(p, "#markSubject", "Database Systems")
        p.click("#loadRosterButton"); settle(p, "#rosterTable"); p.click("#saveAttendance")
        t = toast(p, "Saved attendance")
        nav(p, "records"); settle(p, "#recordsTable")
        p.locator("#recordsTable > tr").first.get_by_role("button", name="Correct status").click()
        d = p.locator("#editRecordDialog"); d.wait_for(state="visible")
        d.locator("select[name=status]").select_option("Late"); d.get_by_role("button", name="Save change").click()
        toast(p, "Attendance record updated")
        c.step("Smoke - teacher: mark today's attendance and correct one status", None, t)
        c.shot(p, "teacher_task"); logout(p)
        login(p, ADMIN, pw); nav(p, "users"); settle(p, "#usersTable")
        p.click("#newUserButton"); u = p.locator("#userDialog"); u.wait_for(state="visible")
        u.locator("input[name=username]").fill("usability_s1"); u.locator("input[name=password]").fill(NEW_USER_PW)
        u.locator("button[type=submit]").click(); toast(p, "usability_s1")
        nav(p, "enrollments"); settle(p, "#enrollmentsTable")
        select_label(p, "#enrollStudent", "usability_s1"); select_label(p, "#enrollClass", "BSc Computer Science - Year 1")
        select_label(p, "#enrollSubject", "Programming Fundamentals"); p.click("#enrollButton"); toast(p, "Student enrolled")
        c.step("Smoke - admin: create a student and enroll them", None, "usability_s1 enrolled in Year 1 / Programming Fundamentals")
        c.shot(p, "admin_task")
        c.notes.append(f"Scripted task flows completed in {time.perf_counter() - t0:.1f} s (machine speed, not human effort).")
        c.status = "NOT RUN"
        c.human = ("Required: a person who has not used the app must perform the tasks unaided and record time, "
                   "hesitation and comments. Automation cannot measure usability; the smoke only shows the tasks can be completed.")
    finally:
        s.close()


def sys_nfr05_08(c, b_unused, pw, pw_obj):
    safari = Path("/Applications/Safari.app").exists()
    c.browser = "Safari application: not automatable by Playwright (supplementary run: Playwright WebKit)"
    c.step("Open the Safari application on a Mac", None,
           f"Safari.app installed: {safari}. Playwright cannot drive the Safari application. safaridriver is present, "
           "but using it needs 'Allow Remote Automation' and 'sudo safaridriver --enable' (a system setting change) "
           "plus a WebDriver client; this was not set up without approval.")
    c.status = "BLOCKED"
    c.human = "Required: a person must run the admin, teacher and student tasks in the real Safari application."
    try:
        wk = pw_obj.webkit.launch(headless=True)
    except Exception as err:  # noqa: BLE001
        c.notes.append(f"Supplementary WebKit run not possible: {err}")
        return
    c.notes.append(f"Supplementary engine-level run in Playwright WebKit {wk.version} (NOT the Safari application).")
    s = Session(wk, c, label="webkit_supplementary"); p = s.page
    try:
        login(p, ADMIN, pw); nav(p, "users"); settle(p, "#usersTable")
        p.click("#newUserButton"); u = p.locator("#userDialog"); u.wait_for(state="visible")
        u.locator("input[name=username]").fill("webkit_s1"); u.locator("input[name=password]").fill(NEW_USER_PW)
        u.locator("button[type=submit]").click(); toast(p, "webkit_s1")
        c.step("[WebKit] admin: create a user; log out", None, "created webkit_s1"); c.shot(p, "webkit_admin"); logout(p)
        login(p, TEACHER, pw); nav(p, "mark"); p.wait_for_function("() => document.querySelector('#markClass').options.length > 1")
        select_label(p, "#markClass", "BSc Computer Science - Year 1"); select_label(p, "#markSubject", "Programming Fundamentals")
        p.click("#loadRosterButton"); settle(p, "#rosterTable"); p.click("#saveAttendance"); t = toast(p, "Saved attendance")
        nav(p, "records"); settle(p, "#recordsTable")
        p.locator("#recordsTable > tr").first.get_by_role("button", name="Correct status").click()
        d = p.locator("#editRecordDialog"); d.wait_for(state="visible")
        d.locator("select[name=status]").select_option("Absent"); d.get_by_role("button", name="Save change").click()
        toast(p, "Attendance record updated")
        c.step("[WebKit] teacher: mark attendance; correct one status; log out", None, t); c.shot(p, "webkit_teacher"); logout(p)
        login(p, STUDENT, pw); p.wait_for_function("() => document.querySelector('#countTotal').textContent !== '–'")
        c.shot(p, "webkit_student_overview"); nav(p, "history"); settle(p, "#historyTable")
        c.step("[WebKit] student: view My attendance and Attendance history", None, f"{len(table(p, '#historyTable'))} records")
        c.shot(p, "webkit_student_history")
        csp = [l for l in s.lines if "Refused to apply" in l or "Content Security Policy" in l or "Content-Security-Policy" in l]
        errs = [l for l in s.lines if "console.error" in l]
        c.step("[WebKit] console errors (D-01 'Refused to apply a stylesheet')", None,
               f"{len(errs)} console.error line(s); {len(csp)} CSP-related; page errors {len(s.page_errors)}")
        c.notes.append(f"WebKit CSP-related console lines: {len(csp)}" + (f"; first: {csp[0][:200]}" if csp else ""))
    finally:
        s.close(); wk.close()


CASES = [
    ("SYS_FR-07_10", "Sumukh", sys_fr07_10), ("SYS_FR-08_10", "Sumukh", sys_fr08_10),
    ("IT_FR-09_09", "Sumukh", it_fr09_09), ("SYS_FR-09_10", "Sumukh", sys_fr09_10),
    ("SYS_FR-13_10", "Sumukh", sys_fr13_10),
    ("SYS_FR-01_08", "Jagadeesh", sys_fr01_08), ("SYS_FR-03_13", "Jagadeesh", sys_fr03_13),
    ("SYS_FR-10_10", "Jagadeesh", sys_fr10_10), ("SYS_FR-11_10", "Jagadeesh", sys_fr11_10),
    ("SYS_FR-15_06", "Jagadeesh", sys_fr15_06), ("SYS_FR-04_11", "Jagadeesh", sys_fr04_11),
    ("SYS_NFR-02_06", "Jagadeesh", sys_nfr02_06),
    ("UT_FR-05_04", "Tharith", ut_fr05_04), ("SYS_FR-05_10", "Tharith", sys_fr05_10),
    ("SYS_FR-14_08", "Tharith", sys_fr14_08), ("SYS_FR-15_07", "Tharith", sys_fr15_07),
    ("IT_NFR-04_04", "Tharith", it_nfr04_04), ("SYS_NFR-04_06", "Tharith", sys_nfr04_06),
    ("SYS_NFR-05_08", "Tharith", sys_nfr05_08),
]


# =============================================================================
# Setup and main
# =============================================================================

def setup(log):
    if DB.exists():
        raise SystemExit(f"{DB.name} already exists; remove it deliberately before re-running.")
    r = subprocess.run([PY, "scripts/seed_demo_data.py", "--database", DB.name], cwd=ROOT, capture_output=True, text=True)
    log.append(f"$ python scripts/seed_demo_data.py --database {DB.name}  (exit {r.returncode})")
    pw = demo_password()
    log.append(r.stdout.strip().replace(pw, "<REDACTED>")); log.append(r.stderr.strip().replace(pw, "<REDACTED>"))
    if r.returncode:
        raise SystemExit("seeding failed")


def start_server():
    log = open(OUT / "server.log", "w")
    proc = subprocess.Popen(
        [PY, "-c", f"from app import create_app; create_app({{'DATABASE': '{DB.name}'}}).run(port=5001)"],
        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(50):
        try:
            if urllib.request.urlopen(f"{BASE}/login", timeout=1).status == 200:
                return proc, log
        except Exception:  # noqa: BLE001
            time.sleep(0.2)
    proc.terminate(); raise SystemExit("server did not start on port 5001")


def load_catalog():
    sys.path.insert(0, str(ROOT / "scripts"))
    import case_catalog as cat  # read-only use
    return cat


def run():
    for d in (OUT, SHOTS, LOGS):
        d.mkdir(parents=True, exist_ok=True)
    cat = load_catalog()
    setup_log = [f"Run started {datetime.now().isoformat(timespec='seconds')}"]
    prod_before = sha256(PROD_DB)
    setup_log.append(f"attendance.db sha256 before: {prod_before}")
    setup(setup_log)
    pw = demo_password()
    server, server_log = start_server()
    setup_log.append(f"Flask started: create_app({{'DATABASE': '{DB.name}'}}).run(port=5001), pid {server.pid}")
    results, meta = [], {}
    try:
        with sync_playwright() as pwr:
            try:
                browser = pwr.chromium.launch(channel="chrome", headless=True)
                bname = f"Google Chrome {browser.version} (Playwright channel 'chrome', headless)"
            except Exception as err:  # noqa: BLE001
                setup_log.append(f"Google Chrome unavailable ({err}); falling back to Playwright Chromium")
                browser = pwr.chromium.launch(headless=True)
                bname = f"Playwright Chromium {browser.version} (headless)"
            meta["browser"] = bname
            setup_log.append(f"Browser: {bname}")
            for cid, tester, fn in CASES:
                tc = cat._BY_ID[cid]
                c = Case(cid, tester, tc["scenario"], tc["expected"])
                c.browser = bname
                print(f"\n== {cid} ({tester}) {tc['scenario']}")
                try:
                    if fn is sys_nfr05_08:
                        fn(c, browser, pw, pwr)
                    else:
                        fn(c, browser, pw)
                except Exception as err:  # noqa: BLE001
                    c.error = f"{type(err).__name__}: {err}".splitlines()[0][:400]
                    c.step("Automation stopped with an error", False, c.error)
                    (LOGS / f"{cid}_traceback.log").write_text(traceback.format_exc())
                    c.logs.append(rel(LOGS / f"{cid}_traceback.log"))
                if c.status is None:
                    c.status = "FAIL" if any(s["ok"] is False for s in c.steps) else "PASS"
                c.finished = datetime.now().isoformat(timespec="seconds")
                print(f"   => {c.status}")
                results.append(c.to_dict())
            browser.close()
    finally:
        server.terminate(); server.wait(timeout=10); server_log.close()
    prod_after = sha256(PROD_DB)
    setup_log.append(f"attendance.db sha256 after:  {prod_after}  (unchanged: {prod_before == prod_after})")
    setup_log.append(f"Run finished {datetime.now().isoformat(timespec='seconds')}")
    (OUT / "setup.log").write_text("\n".join(x for x in setup_log if x) + "\n")
    meta.update({"run_date": date.today().isoformat(), "base_url": BASE, "database": DB.name,
                 "attendance_db_unchanged": prod_before == prod_after, "attendance_db_sha256": prod_after})
    (OUT / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    print("\nSummary:", {s: sum(r["status"] == s for r in results) for s in ("PASS", "FAIL", "BLOCKED", "NOT RUN")})


def render_report():
    """Write docs/Manual_Validation_Automation_Report.md from results.json and the catalogue text."""
    cat = load_catalog()
    meta, by_id = cat.load_manual_results()
    results = [by_id[cid] for cid, _, _ in CASES]
    ev = cat.MANUAL_RUN_DIR
    counts = {s: sum(r["status"] == s for r in results) for s in ("PASS", "FAIL", "BLOCKED", "NOT RUN")}
    shots = sum(len(r["screenshots"]) for r in results)
    logs = sorted({l for r in results for l in r["logs"]})
    defects = [d for d in cat.DEFECTS if d[0] in ("MV-01", "MV-02", "MV-03", "D-01", "D-02", "D-03")]
    _, original = cat.load_manual_results(cat.ORIGINAL_MANUAL_RUN_DIR)
    attempt_dir = "docs/evidence/regression/manual_validation_automation_attempt1"
    attempt = cat.load_manual_results(attempt_dir)[1] if (ROOT / attempt_dir / "results.json").exists() else {}
    L = []
    a = L.append
    a("# Manual Validation Automation Report")
    a("")
    a(f"**Run of record:** {'regression run after the six fixes' if cat.IS_REGRESSION_RUN else 'original run'}  ")
    a("**Project:** Attendance Management System - Deliverable 3  ")
    a(f"**Execution date:** {meta['run_date']} ({results[0]['started']} to {results[-1]['finished']}, local time)  ")
    a("**Scope:** the 19 cases in `docs/manual_validation/{Sumukh,Jagadeesh,Tharith}_Checklist.md`  ")
    a("**Harness:** `scripts/run_manual_validation_automation.py`  ")
    a(f"**Raw results:** `{ev}/results.json`")
    a("")
    a("> **How these results are used.** The instructor approved automated browser execution as evidence for the manual "
      "validation deliverable, so these results are recorded in the checklists, the Test Case Document and the "
      "System Validation Report. **No person performed these steps**; the named team member is the responsible test owner. "
      "Aspects that need human judgement are listed as *not assessed by automation*; no human observation is claimed.")
    a("")
    a("## 1. Environment")
    a("")
    a("| Item | Value |")
    a("|---|---|")
    a(f"| Browser | {meta['browser']} (all cases except the WebKit supplement in SYS_NFR-05_08) |")
    a(f"| Application | Flask on {meta['base_url']}: `create_app({{'DATABASE': 'validation_demo.db'}}).run(port=5001)` (as in the checklist setup) |")
    a("| Database | `validation_demo.db`, newly seeded with `scripts/seed_demo_data.py --database validation_demo.db` (11 users, 2 classes, 4 subjects, 16 enrollments, 192 attendance records); git-ignored |")
    a(f"| attendance.db | Not used. SHA-256 before and after the run: `{meta['attendance_db_sha256']}` (unchanged: {meta['attendance_db_unchanged']}) |")
    a("| Production code | " + ("Changed for the six fixes before this run (`app/static/js/`, `app/static/css/app.css`, "
      "`app/templates/`); no backend or security-policy change" if cat.IS_REGRESSION_RUN else "Not modified") + " |")
    a("| Credentials | Demo password read from git-ignored `demo_credentials.txt`; redacted from all evidence files |")
    a("| Mode | Headless, 1280x800 unless the case sets another size; one fresh browser context per case |")
    a("")
    a("## 2. Run history")
    a("")
    a("Earlier runs are kept unchanged in their own directories. The run of record is the last row.")
    a("")
    a("| Run | Directory | Executed | PASS | FAIL | BLOCKED | NOT RUN | Note |")
    a("|---|---|---|---|---|---|---|---|")
    def _row(label, directory, res, note):
        rs = list(res.values())
        c = {x: sum(r["status"] == x for r in rs) for x in ("PASS", "FAIL", "BLOCKED", "NOT RUN")}
        when = f"{rs[0]['started']} to {rs[-1]['finished']}" if rs else "-"
        a(f"| {label} | `{directory}` | {when} | {c['PASS']} | {c['FAIL']} | {c['BLOCKED']} | {c['NOT RUN']} | {note} |")
    _row("Original run (before the fixes)", cat.ORIGINAL_MANUAL_RUN_DIR, original, "Three FAILs: MV-01, MV-02, MV-03")
    if cat.IS_REGRESSION_RUN:
        if attempt:
            _row("Regression attempt 1 (superseded)", attempt_dir, attempt,
                 "Superseded: the harness's own reference value for SYS_FR-14_08 still used one-decimal rounding; see SUPERSEDED.txt")
        _row("Regression run of record (after the fixes)", ev, by_id, "Run reported in all documents")
        a("")
        a("| Test Case ID | Owner | Original run | Regression run |")
        a("|---|---|---|---|")
        for cid, owner_, _ in CASES:
            a(f"| {cid} | {owner_} | {original[cid]['status']} | **{by_id[cid]['status']}** |")
    a("")
    a("## 3. Summary")
    a("")
    a("| Measure | Count |")
    a("|---|---|")
    a(f"| Scenarios executed end-to-end by automation | {counts['PASS'] + counts['FAIL']} of 19 |")
    a(f"| PASS | {counts['PASS']} |")
    a(f"| FAIL | {counts['FAIL']} ({', '.join(d[0] for d in defects)}) |")
    a(f"| BLOCKED | {counts['BLOCKED']} (SYS_NFR-05_08: the Safari application cannot be driven by Playwright) |")
    a(f"| NOT RUN | {counts['NOT RUN']} (SYS_NFR-04_06: needs a human participant) |")
    a(f"| Cases with aspects not assessed by automation | {len(cat.MANUAL_LIMITS)} |")
    a(f"| Screenshots | {shots} |")
    a(f"| Browser logs | {len(logs)} |")
    a("")
    a("| # | Test Case ID | Test owner | Description | Status |")
    a("|---|---|---|---|---|")
    for i, r in enumerate(results, 1):
        a(f"| {i} | {r['id']} | {r['tester']} | {r['title']} | **{r['status']}** |")
    a("")
    a("## 4. Defects found in the original run and their current status")
    a("")
    a("These are recorded in the defect register of the Test Case Document and the System Validation Report.")
    a("")
    a("| ID | Req. | Severity | Finding | Test impact | Status |")
    a("|---|---|---|---|---|---|")
    for d in defects:
        a("| " + " | ".join(str(x).replace("|", "/") for x in d) + " |")
    a("")
    if cat.IS_REGRESSION_RUN:
        a("All six defects are fixed and verified in the regression run. The supplementary WebKit run in SYS_NFR-05_08 now uses "
          "Playwright WebKit build r2388 (Playwright 1.65.2) and logs no CSP errors; it remains engine-level evidence, not a "
          "Safari test. Gap G-04 (no threshold screen) is unchanged.")
    else:
        a("Also re-observed: D-01 (26 'Refused to apply a stylesheet' CSP console errors in Playwright WebKit; not evidence about the "
          "Safari application), gap G-03 (no class or date-range filter) and gap G-04 (no threshold screen).")
    a("")
    a("## 5. Not assessed by automation")
    a("")
    a("| Case | Not assessed |")
    a("|---|---|")
    for cid, text in cat.MANUAL_LIMITS.items():
        a(f"| {cid} | {text} |")
    a("")
    a("## 6. Scenario details")
    a("")
    for r in results:
        a(f"### {r['id']} - {r['title']}")
        a("")
        a("| Field | Value |")
        a("|---|---|")
        a(f"| Test Case ID | {r['id']} |")
        a(f"| Responsible test owner | {r['tester']} |")
        a(f"| Expected result | {r['expected']} |")
        a(f"| Actual result | {(cat.run_actual(r) if cat.IS_REGRESSION_RUN else cat.MANUAL_ACTUAL[r['id']]).replace('|', '/')} |")
        a(f"| Status | **{r['status']}** ({r['checks_total'] - r['checks_failed']}/{r['checks_total']} checks met) |")
        a(f"| Not assessed by automation | {cat.MANUAL_LIMITS.get(r['id'], 'Nothing beyond the expected result.')} |")
        a(f"| Execution method | Playwright automation (no person performed the steps) |")
        a(f"| Browser | {r['browser']} |")
        a(f"| Executed | {r['started']} to {r['finished']} |")
        a(f"| Screenshots | {', '.join('`' + x.split('/')[-1] + '`' for x in r['screenshots']) or 'None'} |")
        a(f"| Logs | {', '.join('`' + x.split('/')[-1] + '`' for x in r['logs'])} |")
        a("")
        a("Steps executed:")
        a("")
        for i, st in enumerate(r["steps"], 1):
            tag = {True: "PASS", False: "**FAIL**", None: "done"}[st["ok"]]
            obs = st["observed"].replace("|", "/").replace("\n", " ")
            a(f"{i}. [{tag}] {st['step']}" + (f" - {obs}" if obs else ""))
        for n in r["notes"]:
            a(f"- Note: {n}")
        a("")
    a("## 7. Evidence inventory")
    a("")
    a(f"All paths are relative to `{ev}/`.")
    a("")
    a("| File | Content |")
    a("|---|---|")
    a("| `results.json` | Machine-readable results for all 19 scenarios |")
    a("| `setup.log` | Seeding output, server command, browser version, attendance.db hashes (password redacted) |")
    a("| `server.log` | Flask request log for the run |")
    a(f"| `screenshots/` | {shots} PNG files named `<TestCaseID>_<n>_<label>.png` |")
    a(f"| `logs/` | {len(logs)} browser logs (console messages, page errors, failed requests, HTTP 4xx/5xx, document responses with Cache-Control, navigations) |")
    a("")
    a("## 8. Data changed in validation_demo.db (only)")
    a("")
    a("Users manual_s1b (renamed from manual_s1), usability_s1 and webkit_s1; class Manual Class; subject Manual Subject; "
      "aarav enrolled in Manual Class / Manual Subject; usability_s1 enrolled in Year 1 / Programming Fundamentals; one record "
      "for aarav / Programming Fundamentals / 16 Nov 2026 deleted; today's attendance saved for Year 2 / Database Systems and "
      "Year 1 / Programming Fundamentals, with one correction each; meera's password changed and restored.")
    a("")
    a("## 9. Limitations")
    a("")
    a("- Headless Chrome on macOS; native validation bubbles and select pop-ups are not visible in screenshots, so validity state was checked instead.")
    a("- Progress bars animate, so some screenshots show bars part-way; values were checked from the text.")
    a("- Load times were measured with the browser cache disabled via the DevTools protocol on the development Mac.")
    a("- Firefox and Edge were not used (see G-09). The Safari application was not tested (BLOCKED); WebKit is engine-level evidence only.")
    a("- Re-run: delete `validation_demo.db`, then `python scripts/run_manual_validation_automation.py`; "
      "`--report` only re-renders this report from `results.json`.")
    (ROOT / cat.MANUAL_REPORT).write_text("\n".join(L) + "\n")
    print(f"wrote {cat.MANUAL_REPORT}: {counts}")


if __name__ == "__main__":
    if "--out" in sys.argv:
        set_output(sys.argv[sys.argv.index("--out") + 1])
        if (OUT / "results.json").exists():
            raise SystemExit(f"{rel(OUT)} already holds a run; choose a new directory (evidence is never overwritten).")
    if "--report" in sys.argv:
        render_report()
    elif "--no-report" in sys.argv:
        run()
    else:
        run()
        render_report()
