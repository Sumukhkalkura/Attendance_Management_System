"""Backend Performance Benchmark for NFR-02.

Measures response times across major pages and attendance information endpoints
under representative normal operating conditions:
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
import sqlite3
import random
from werkzeug.security import generate_password_hash

# Add repo to sys.path
sys.path.insert(0, os.path.abspath("."))
from app import create_app

DATASET_CONFIG = {
    "students": 50,
    "teachers": 5,
    "classes": 10,
    "subjects": 15,
    "attendance_records": 1500,
    "dates": 25,
}

def setup_benchmark_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "bench-key"})
    
    with app.app_context():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Insert admin and teachers
        pw = generate_password_hash("password123")
        cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", ("bench_admin", pw, "admin"))
        admin_id = cur.lastrowid
        
        teacher_ids = []
        for i in range(1, DATASET_CONFIG["teachers"] + 1):
            cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", (f"bench_teacher_{i}", pw, "teacher"))
            teacher_ids.append(cur.lastrowid)
            
        student_ids = []
        for i in range(1, DATASET_CONFIG["students"] + 1):
            cur.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)", (f"bench_student_{i}", pw, "student"))
            student_ids.append(cur.lastrowid)
            
        class_ids = []
        for i in range(1, DATASET_CONFIG["classes"] + 1):
            t_id = teacher_ids[(i - 1) % len(teacher_ids)]
            cur.execute("INSERT INTO classes (name, teacher_id) VALUES (?, ?)", (f"Class {i}", t_id))
            class_ids.append(cur.lastrowid)
            
        subject_ids = []
        for i in range(1, DATASET_CONFIG["subjects"] + 1):
            t_id = teacher_ids[(i - 1) % len(teacher_ids)]
            cur.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (f"Subject {i}", t_id))
            subject_ids.append(cur.lastrowid)
            
        # Class subjects (3 per class)
        for idx, c_id in enumerate(class_ids):
            for j in range(3):
                sub_id = subject_ids[(idx * 3 + j) % len(subject_ids)]
                cur.execute("INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (c_id, sub_id))

        # Enrollments: students distributed across classes and their subjects
        enrollments = []
        for idx, s_id in enumerate(student_ids):
            c_id = class_ids[idx % len(class_ids)]
            cur.execute("SELECT subject_id FROM class_subjects WHERE class_id = ?", (c_id,))
            c_subs = [r[0] for r in cur.fetchall()]
            for sub_id in c_subs:
                enrollments.append((s_id, c_id, sub_id))
        cur.executemany("INSERT OR IGNORE INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)", enrollments)
        
        # Attendance records
        dates = [f"2026-03-{d:02d}" for d in range(1, DATASET_CONFIG["dates"] + 1)]
        attendance_records = []
        statuses = ["Present", "Present", "Present", "Absent", "Late"]
        rec_idx = 0
        for d in dates:
            for enr in enrollments:
                s_id, c_id, sub_id = enr
                status = statuses[rec_idx % len(statuses)]
                attendance_records.append((s_id, sub_id, d, status))
                rec_idx += 1
                if len(attendance_records) >= DATASET_CONFIG["attendance_records"]:
                    break
            if len(attendance_records) >= DATASET_CONFIG["attendance_records"]:
                break
            
        cur.executemany("INSERT OR IGNORE INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)", attendance_records)
        conn.commit()
        conn.close()

    return app, student_ids[0], class_ids[0], subject_ids[0]

def run_benchmarks(app, student_id, class_id, subject_id):
    client = app.test_client()
    
    # Authenticate admin
    resp = client.post("/api/login", json={"username": "bench_admin", "password": "password123"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    
    teacher_client = app.test_client()
    teacher_client.post("/api/login", json={"username": "bench_teacher_1", "password": "password123"})
    
    student_client = app.test_client()
    student_client.post("/api/login", json={"username": "bench_student_1", "password": "password123"})
    
    scenarios = [
        ("Page: /login (unauthenticated)", lambda: app.test_client().get("/login")),
        ("Page: /dashboard (admin redirect)", lambda: client.get("/dashboard")),
        ("Page: /dashboard (teacher redirect)", lambda: teacher_client.get("/dashboard")),
        ("Page: /dashboard (student redirect)", lambda: student_client.get("/dashboard")),
        ("Page: /admin (admin dashboard)", lambda: client.get("/admin")),
        ("Page: /teacher (teacher dashboard)", lambda: teacher_client.get("/teacher")),
        ("Page: /student (student dashboard)", lambda: student_client.get("/student")),
        ("API: /api/classes", lambda: client.get("/api/classes")),
        ("API: /api/subjects", lambda: client.get("/api/subjects")),
        ("API: /api/users?role=student", lambda: client.get("/api/users?role=student")),
        (f"API: /api/roster?class_id={class_id}&subject_id={subject_id}", lambda: client.get(f"/api/roster?class_id={class_id}&subject_id={subject_id}")),
        (f"API: /api/attendance ({DATASET_CONFIG['attendance_records']} records)", lambda: client.get("/api/attendance")),
        (f"API: /api/attendance?student_id={student_id}", lambda: client.get(f"/api/attendance?student_id={student_id}")),
        (f"API: /api/attendance?class_id={class_id}", lambda: client.get(f"/api/attendance?class_id={class_id}")),
        (f"API: /api/attendance?subject_id={subject_id}", lambda: client.get(f"/api/attendance?subject_id={subject_id}")),
        ("API: /api/attendance?start_date=2026-03-01&end_date=2026-03-15", lambda: client.get("/api/attendance?start_date=2026-03-01&end_date=2026-03-15")),
        ("API: /api/attendance/percentages (all)", lambda: client.get("/api/attendance/percentages")),
        (f"API: /api/attendance/percentages?student_id={student_id}", lambda: client.get(f"/api/attendance/percentages?student_id={student_id}")),
        (f"API: /api/attendance/percentages?class_id={class_id}", lambda: client.get(f"/api/attendance/percentages?class_id={class_id}")),
        (f"API: /api/attendance/percentages?subject_id={subject_id}", lambda: client.get(f"/api/attendance/percentages?subject_id={subject_id}")),
        ("API: /api/attendance/alerts", lambda: client.get("/api/attendance/alerts")),
        (f"API: /api/attendance/alerts/student/{student_id}", lambda: client.get(f"/api/attendance/alerts/student/{student_id}")),
        (f"API: /api/attendance/alerts/class/{class_id}", lambda: client.get(f"/api/attendance/alerts/class/{class_id}")),
        (f"API: /api/attendance/alerts/subject/{subject_id}", lambda: client.get(f"/api/attendance/alerts/subject/{subject_id}")),
        ("API: /api/reports/attendance (full report)", lambda: client.get("/api/reports/attendance")),
        (f"API: /api/reports/attendance/student/{student_id}", lambda: client.get(f"/api/reports/attendance/student/{student_id}")),
        (f"API: /api/reports/attendance/class/{class_id}", lambda: client.get(f"/api/reports/attendance/class/{class_id}")),
        (f"API: /api/reports/attendance/subject/{subject_id}", lambda: client.get(f"/api/reports/attendance/subject/{subject_id}")),
        ("API: /api/reports/attendance/export (CSV export)", lambda: client.get("/api/reports/attendance/export")),
    ]
    
    results = []
    
    # Warm up
    for name, action in scenarios:
        action()
        
    # Measure 5 runs each
    for name, action in scenarios:
        timings = []
        status_codes = []
        for _ in range(5):
            t0 = time.perf_counter()
            r = action()
            t1 = time.perf_counter()
            timings.append((t1 - t0) * 1000)
            status_codes.append(r.status_code)
            
        avg_ms = sum(timings) / len(timings)
        min_ms = min(timings)
        max_ms = max(timings)
        results.append({
            "scenario": name,
            "status_code": status_codes[0],
            "avg_ms": avg_ms,
            "min_ms": min_ms,
            "max_ms": max_ms,
            "within_3s": max_ms < 3000.0
        })
        
    return results

if __name__ == "__main__":
    db_path = "backend_bench_temp.db"
    print("=" * 80)
    print("NFR-02 BACKEND PERFORMANCE BENCHMARK")
    print(f"Dataset: {DATASET_CONFIG['students']} students, {DATASET_CONFIG['classes']} classes, "
          f"{DATASET_CONFIG['subjects']} subjects, {DATASET_CONFIG['teachers']} teachers, "
          f"1 admin, {DATASET_CONFIG['attendance_records']} attendance records across {DATASET_CONFIG['dates']} dates.")
    print("Target SLA: < 3000.0 ms (3.0 seconds)")
    print("=" * 80)
    
    app, s_id, c_id, sub_id = setup_benchmark_db(db_path)
    results = run_benchmarks(app, s_id, c_id, sub_id)
    
    print("\n" + "-" * 105)
    print(f"{'Scenario / Operation':<65} | {'Status':<6} | {'Avg (ms)':<9} | {'Max (ms)':<9} | {'< 3.0s':<6}")
    print("-" * 105)
    for r in results:
        print(f"{r['scenario']:<65} | {r['status_code']:<6} | {r['avg_ms']:<9.2f} | {r['max_ms']:<9.2f} | {str(r['within_3s']):<6}")
    print("-" * 105)
    
    all_passed = all(r["within_3s"] for r in results)
    print(f"\nAll operations met the 3.0-second SLA: {all_passed}")
    
    if os.path.exists(db_path):
        os.remove(db_path)

