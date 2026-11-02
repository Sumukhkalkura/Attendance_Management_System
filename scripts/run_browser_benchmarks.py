"""Cross-Platform Browser-Based Performance Benchmark for NFR-02 using Playwright.

Measures real browser loading times across major pages and attendance views
using Playwright's managed Chromium browser (cross-platform on Linux, macOS, and Windows):
1. Login Page (/login)
2. Main Dashboard (/admin overview)
3. Student Attendance View (/student#history)
4. Class Attendance View (/teacher#mark with roster)
5. Subject Attendance View (/teacher#percentages)
6. Attendance Reporting Page (/admin#attendance with records and percentages)

Measurement Definitions:
- Navigation Timing (ms): Time from page.goto() initiation until the browser's load event.
- Main Content Visible (ms): Time until key shell and layout components are visible in the DOM.
- Attendance Information Fully Rendered (ms): Time until asynchronous API requests have resolved
  and the attendance records / percentages are populated as visible DOM elements.

SLA Target: All operations must complete in < 3.0 seconds (3,000 ms).
"""

import os
import sys
import time
import socket
import threading
import sqlite3
from werkzeug.serving import make_server
from werkzeug.security import generate_password_hash

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: The 'playwright' package is not installed.")
    print("Please install it with: pip install playwright")
    sys.exit(1)

sys.path.insert(0, os.path.abspath("."))
from app import create_app

REPETITIONS = 3
EVIDENCE_DIR = os.path.abspath("reports/screenshots")


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def seed_database(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "browser-bench-key"})
    
    with app.app_context():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        pw = generate_password_hash("password123")
        
        # Admin
        cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", ("admin_bench", pw, "admin"))
        
        # 5 Teachers
        t_ids = []
        for i in range(1, 6):
            cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", (f"teacher_{i}", pw, "teacher"))
            t_ids.append(cur.lastrowid)
            
        # 50 Students
        s_ids = []
        for i in range(1, 51):
            cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", (f"student_{i}", pw, "student"))
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
            
        # Class Subjects mapping
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
        
        # 1500 Attendance records across 25 dates
        dates = [f"2026-03-{d:02d}" for d in range(1, 26)]
        statuses = ["Present", "Present", "Present", "Absent", "Late"]
        records = []
        rec_idx = 0
        for d in dates:
            for enr in enrollments:
                s_id, c_id, sub_id = enr
                status = statuses[rec_idx % len(statuses)]
                records.append((s_id, sub_id, d, status))
                rec_idx += 1
                if len(records) >= 1500:
                    break
            if len(records) >= 1500:
                break
        cur.executemany("INSERT OR IGNORE INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)", records)
        conn.commit()
        conn.close()

    return app


def run_browser_benchmark():
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    db_path = "browser_bench_temp.db"
    app = seed_database(db_path)
    port = find_free_port()
    
    server = make_server("127.0.0.1", port, app, threaded=True)
    server.daemon_threads = True
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()
    time.sleep(0.5)
    base_url = f"http://127.0.0.1:{port}"
    
    print("=" * 95)
    print("NFR-02 CROSS-PLATFORM BROWSER PERFORMANCE BENCHMARK (PLAYWRIGHT CHROMIUM)")
    print(f"Server URL: {base_url}")
    print("Browser: Playwright Managed Headless Chromium")
    print("Dataset: 50 students, 10 classes, 15 subjects, 5 teachers, 1 admin, 1500 attendance records")
    print(f"Repetitions per test: {REPETITIONS}")
    print("Target SLA: < 3,000 ms (3.0 seconds) for all phases")
    print("=" * 95)
    
    results = []
    
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as err:
                print("\nError: Failed to launch Playwright managed Chromium.")
                print("Please ensure browser binaries are installed by running:")
                print("  python -m playwright install chromium")
                print("Or on Linux:")
                print("  python -m playwright install --with-deps chromium")
                print(f"Details: {err}")
                server.shutdown()
                sys.exit(1)
            
            # Warmup browser instance
            warm_page = browser.new_page()
            warm_page.goto("about:blank")
            warm_page.close()
            
            # Test 1: Login Page
            login_nav, login_content = [], []
            for rep in range(REPETITIONS):
                ctx = browser.new_context()
                page = ctx.new_page()
                t0 = time.perf_counter()
                resp = page.goto(f"{base_url}/login", wait_until="load")
                t_nav = (time.perf_counter() - t0) * 1000
                page.wait_for_selector("#loginForm", state="visible")
                t_content = (time.perf_counter() - t0) * 1000
                login_nav.append(t_nav)
                login_content.append(t_content)
                if rep == 0:
                    page.screenshot(path=os.path.join(EVIDENCE_DIR, "login_page.png"))
                ctx.close()
                
            results.append({
                "page": "1. Login Page (/login)",
                "nav_avg": sum(login_nav) / len(login_nav),
                "nav_max": max(login_nav),
                "content_avg": sum(login_content) / len(login_content),
                "content_max": max(login_content),
                "render_avg": sum(login_content) / len(login_content),
                "render_max": max(login_content),
                "within_3s": max(login_content) < 3000.0,
            })
            
            # Test 2: Main Dashboard (Admin Overview)
            admin_nav, admin_content, admin_rendered = [], [], []
            for rep in range(REPETITIONS):
                ctx = browser.new_context()
                page = ctx.new_page()
                page.goto(f"{base_url}/login")
                page.fill("#username", "admin_bench")
                page.fill("#password", "password123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{base_url}/admin*")
                
                t0 = time.perf_counter()
                page.goto(f"{base_url}/admin", wait_until="load")
                t_nav = (time.perf_counter() - t0) * 1000
                page.wait_for_selector(".main", state="visible")
                t_content = (time.perf_counter() - t0) * 1000
                page.wait_for_selector("#statStudents", state="visible")
                page.wait_for_selector("#statOverall", state="visible")
                page.wait_for_selector("#lowAttendanceTable tr", state="visible")
                t_render = (time.perf_counter() - t0) * 1000
                admin_nav.append(t_nav)
                admin_content.append(t_content)
                admin_rendered.append(t_render)
                if rep == 0:
                    page.screenshot(path=os.path.join(EVIDENCE_DIR, "admin_dashboard_overview.png"))
                ctx.close()
                
            results.append({
                "page": "2. Main Dashboard (/admin overview)",
                "nav_avg": sum(admin_nav) / len(admin_nav),
                "nav_max": max(admin_nav),
                "content_avg": sum(admin_content) / len(admin_content),
                "content_max": max(admin_content),
                "render_avg": sum(admin_rendered) / len(admin_rendered),
                "render_max": max(admin_rendered),
                "within_3s": max(admin_rendered) < 3000.0,
            })
            
            # Test 3: Student Attendance View (/student#history)
            stud_nav, stud_content, stud_rendered = [], [], []
            for rep in range(REPETITIONS):
                ctx = browser.new_context()
                page = ctx.new_page()
                page.goto(f"{base_url}/login")
                page.fill("#username", "student_1")
                page.fill("#password", "password123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{base_url}/student*")
                
                t0 = time.perf_counter()
                page.click("a[data-section='history']")
                page.wait_for_selector("#section-history", state="visible")
                t_content = (time.perf_counter() - t0) * 1000
                page.wait_for_selector("#historyTable tr", state="visible")
                t_render = (time.perf_counter() - t0) * 1000
                stud_nav.append(0.0)
                stud_content.append(t_content)
                stud_rendered.append(t_render)
                if rep == 0:
                    page.screenshot(path=os.path.join(EVIDENCE_DIR, "student_attendance_view.png"))
                ctx.close()
                
            results.append({
                "page": "3. Student Attendance View (/student#history)",
                "nav_avg": sum(stud_nav) / len(stud_nav),
                "nav_max": max(stud_nav),
                "content_avg": sum(stud_content) / len(stud_content),
                "content_max": max(stud_content),
                "render_avg": sum(stud_rendered) / len(stud_rendered),
                "render_max": max(stud_rendered),
                "within_3s": max(stud_rendered) < 3000.0,
            })
            
            # Test 4: Class Attendance View (/teacher#mark class roster)
            class_nav, class_content, class_rendered = [], [], []
            for rep in range(REPETITIONS):
                ctx = browser.new_context()
                page = ctx.new_page()
                page.goto(f"{base_url}/login")
                page.fill("#username", "teacher_1")
                page.fill("#password", "password123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{base_url}/teacher*")
                
                t0 = time.perf_counter()
                page.click("a[data-section='mark']")
                page.wait_for_selector("#section-mark", state="visible")
                t_content = (time.perf_counter() - t0) * 1000
                
                page.select_option("#markClass", index=1)
                page.select_option("#markSubject", index=1)
                page.fill("#markDate", "2026-03-10")
                page.click("#loadRosterButton")
                page.wait_for_selector("#rosterCard", state="visible")
                page.wait_for_selector("#rosterTable tr", state="visible")
                t_render = (time.perf_counter() - t0) * 1000
                
                class_nav.append(0.0)
                class_content.append(t_content)
                class_rendered.append(t_render)
                if rep == 0:
                    page.screenshot(path=os.path.join(EVIDENCE_DIR, "class_attendance_view.png"))
                ctx.close()
                
            results.append({
                "page": "4. Class Attendance View (/teacher#mark roster)",
                "nav_avg": sum(class_nav) / len(class_nav),
                "nav_max": max(class_nav),
                "content_avg": sum(class_content) / len(class_content),
                "content_max": max(class_content),
                "render_avg": sum(class_rendered) / len(class_rendered),
                "render_max": max(class_rendered),
                "within_3s": max(class_rendered) < 3000.0,
            })
            
            # Test 5: Subject Attendance View (/teacher#percentages)
            sub_nav, sub_content, sub_rendered = [], [], []
            for rep in range(REPETITIONS):
                ctx = browser.new_context()
                page = ctx.new_page()
                page.goto(f"{base_url}/login")
                page.fill("#username", "teacher_1")
                page.fill("#password", "password123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{base_url}/teacher*")
                
                t0 = time.perf_counter()
                page.click("a[data-section='percentages']")
                page.wait_for_selector("#section-percentages", state="visible")
                t_content = (time.perf_counter() - t0) * 1000
                page.wait_for_selector("#percentTable tr", state="visible")
                t_render = (time.perf_counter() - t0) * 1000
                sub_nav.append(0.0)
                sub_content.append(t_content)
                sub_rendered.append(t_render)
                if rep == 0:
                    page.screenshot(path=os.path.join(EVIDENCE_DIR, "subject_attendance_view.png"))
                ctx.close()
                
            results.append({
                "page": "5. Subject Attendance View (/teacher#percentages)",
                "nav_avg": sum(sub_nav) / len(sub_nav),
                "nav_max": max(sub_nav),
                "content_avg": sum(sub_content) / len(sub_content),
                "content_max": max(sub_content),
                "render_avg": sum(sub_rendered) / len(sub_rendered),
                "render_max": max(sub_rendered),
                "within_3s": max(sub_rendered) < 3000.0,
            })
            
            # Test 6: Attendance Reporting Page (/admin#attendance)
            rep_nav, rep_content, rep_rendered = [], [], []
            for rep in range(REPETITIONS):
                ctx = browser.new_context()
                page = ctx.new_page()
                page.goto(f"{base_url}/login")
                page.fill("#username", "admin_bench")
                page.fill("#password", "password123")
                page.click("button[type='submit']")
                page.wait_for_url(f"{base_url}/admin*")
                
                t0 = time.perf_counter()
                page.click("a[data-section='attendance']")
                page.wait_for_selector("#section-attendance", state="visible")
                t_content = (time.perf_counter() - t0) * 1000
                page.wait_for_selector("#percentTable tr", state="visible")
                page.wait_for_selector("#recordsTable tr", state="visible")
                t_render = (time.perf_counter() - t0) * 1000
                rep_nav.append(0.0)
                rep_content.append(t_content)
                rep_rendered.append(t_render)
                if rep == 0:
                    page.screenshot(path=os.path.join(EVIDENCE_DIR, "attendance_reporting_page.png"))
                ctx.close()
                
            results.append({
                "page": "6. Attendance Reporting Page (/admin#attendance)",
                "nav_avg": sum(rep_nav) / len(rep_nav),
                "nav_max": max(rep_nav),
                "content_avg": sum(rep_content) / len(rep_content),
                "content_max": max(rep_content),
                "render_avg": sum(rep_rendered) / len(rep_rendered),
                "render_max": max(rep_rendered),
                "within_3s": max(rep_rendered) < 3000.0,
            })
            
            browser.close()

    finally:
        server.shutdown()
        server.server_close()
        if os.path.exists(db_path):
            os.remove(db_path)

    print("\n" + "-" * 115)
    print(f"{'Page / View Tested':<45} | {'Nav Avg (ms)':<12} | {'Content Avg':<12} | {'Render Avg (ms)':<15} | {'Render Max (ms)':<15} | {'< 3.0s':<6}")
    print("-" * 115)
    for r in results:
        print(f"{r['page']:<45} | {r['nav_avg']:<12.1f} | {r['content_avg']:<12.1f} | {r['render_avg']:<15.1f} | {r['render_max']:<15.1f} | {str(r['within_3s']):<6}")
    print("-" * 115)
    
    all_passed = all(r["within_3s"] for r in results)
    print(f"\nAll browser views rendered within 3.0-second target: {all_passed}")
    print(f"Screenshots saved to: {EVIDENCE_DIR}")
    
    if not all_passed:
        sys.exit(1)
        
    return results


if __name__ == "__main__":
    run_browser_benchmark()
