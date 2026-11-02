"""Tests for NFR-02: Performance optimization and response time verification.

Acceptance criteria:
1. Major pages load within 3 seconds under normal operating conditions.
2. Attendance information loads within 3 seconds under normal operating conditions.
3. Performance is checked using representative usage scenarios.
"""

import sqlite3
import time
import pytest
from werkzeug.security import generate_password_hash

PERFORMANCE_THRESHOLD_SECONDS = 3.0


@pytest.fixture
def performance_dataset(client):
    """Seed a representative workload with students, classes, subjects, enrollments, and attendance."""
    db_path = client.application.config["DATABASE"]
    pw_hash = generate_password_hash("perf_pass123")

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        # 1 Admin
        cur.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
            ("perf_admin", pw_hash, "admin"),
        )
        admin_id = cur.lastrowid

        # 5 Teachers
        teacher_ids = []
        for i in range(1, 6):
            cur.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (f"perf_teacher_{i}", pw_hash, "teacher"),
            )
            teacher_ids.append(cur.lastrowid)

        # 50 Students
        student_ids = []
        for i in range(1, 51):
            cur.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (f"perf_student_{i}", pw_hash, "student"),
            )
            student_ids.append(cur.lastrowid)

        # 10 Classes
        class_ids = []
        for i in range(1, 11):
            t_id = teacher_ids[(i - 1) % len(teacher_ids)]
            cur.execute(
                "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
                (f"Perf Class {i}", t_id),
            )
            class_ids.append(cur.lastrowid)

        # 15 Subjects
        subject_ids = []
        for i in range(1, 16):
            t_id = teacher_ids[(i - 1) % len(teacher_ids)]
            cur.execute(
                "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
                (f"Perf Subject {i}", t_id),
            )
            subject_ids.append(cur.lastrowid)

        # Class Subjects mapping: 3 subjects per class
        for c_idx, c_id in enumerate(class_ids):
            for s_idx in range(3):
                sub_id = subject_ids[(c_idx * 3 + s_idx) % len(subject_ids)]
                cur.execute(
                    "INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
                    (c_id, sub_id),
                )

        # Enrollments: 50 students enrolled across classes & subjects
        enrollments = []
        for idx, s_id in enumerate(student_ids):
            c_id = class_ids[idx % len(class_ids)]
            cur.execute(
                "SELECT subject_id FROM class_subjects WHERE class_id = ?",
                (c_id,),
            )
            subs = [r[0] for r in cur.fetchall()]
            for sub_id in subs:
                enrollments.append((s_id, c_id, sub_id))

        cur.executemany(
            "INSERT OR IGNORE INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            enrollments,
        )

        # Attendance records: 1,500 records across multiple dates and statuses
        dates = [f"2026-03-{d:02d}" for d in range(1, 26)]
        statuses = ["Present", "Present", "Present", "Absent", "Late"]
        attendance_records = []
        rec_idx = 0
        for date in dates:
            for enr in enrollments:
                s_id, c_id, sub_id = enr
                status = statuses[rec_idx % len(statuses)]
                attendance_records.append((s_id, sub_id, date, status))
                rec_idx += 1
                if len(attendance_records) >= 1500:
                    break
            if len(attendance_records) >= 1500:
                break

        cur.executemany(
            "INSERT OR IGNORE INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
            attendance_records,
        )
        conn.commit()

    return {
        "admin_id": admin_id,
        "teacher_ids": teacher_ids,
        "student_ids": student_ids,
        "class_ids": class_ids,
        "subject_ids": subject_ids,
    }


def login_user(client, username, password="perf_pass123"):
    """Helper to log in a user and verify success."""
    resp = client.post("/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp


def measure_get(client, url):
    """Perform a GET request and return (response, elapsed_seconds)."""
    start_time = time.perf_counter()
    response = client.get(url)
    elapsed = time.perf_counter() - start_time
    return response, elapsed


# =====================================================================
# Acceptance Criteria 1: Major pages load within 3 seconds
# =====================================================================

def test_nfr02_major_page_login_loads_within_threshold(client, performance_dataset):
    """The unauthenticated login page must load within 3 seconds."""
    resp, elapsed = measure_get(client, "/login")
    assert resp.status_code == 200
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Login page took {elapsed:.4f}s"


def test_nfr02_major_page_dashboard_redirect_within_threshold(client, performance_dataset):
    """The /dashboard route must resolve and redirect within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/dashboard")
    assert resp.status_code == 302
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Dashboard route took {elapsed:.4f}s"


def test_nfr02_major_page_admin_dashboard_loads_within_threshold(client, performance_dataset):
    """The admin dashboard page must load within 3 seconds for an admin."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/admin")
    assert resp.status_code == 200
    assert "admin.html" in resp.get_data(as_text=True) or "Admin" in resp.get_data(as_text=True)
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Admin dashboard took {elapsed:.4f}s"


def test_nfr02_major_page_teacher_dashboard_loads_within_threshold(client, performance_dataset):
    """The teacher dashboard page must load within 3 seconds for a teacher."""
    login_user(client, "perf_teacher_1")
    resp, elapsed = measure_get(client, "/teacher")
    assert resp.status_code == 200
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Teacher dashboard took {elapsed:.4f}s"


def test_nfr02_major_page_student_dashboard_loads_within_threshold(client, performance_dataset):
    """The student dashboard page must load within 3 seconds for a student."""
    login_user(client, "perf_student_1")
    resp, elapsed = measure_get(client, "/student")
    assert resp.status_code == 200
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Student dashboard took {elapsed:.4f}s"


# =====================================================================
# Acceptance Criteria 2: Attendance information loads within 3 seconds
# =====================================================================

def test_nfr02_attendance_records_retrieval_within_threshold(client, performance_dataset):
    """Full attendance records retrieval must load within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/api/attendance")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "records" in data
    assert data["count"] > 0
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Full attendance query took {elapsed:.4f}s"


def test_nfr02_attendance_student_filter_within_threshold(client, performance_dataset):
    """Retrieving attendance filtered by student must load within 3 seconds."""
    login_user(client, "perf_admin")
    s_id = performance_dataset["student_ids"][0]
    resp, elapsed = measure_get(client, f"/api/attendance?student_id={s_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "records" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Student attendance query took {elapsed:.4f}s"


def test_nfr02_attendance_class_filter_within_threshold(client, performance_dataset):
    """Retrieving attendance filtered by class must load within 3 seconds."""
    login_user(client, "perf_admin")
    c_id = performance_dataset["class_ids"][0]
    resp, elapsed = measure_get(client, f"/api/attendance?class_id={c_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "records" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Class attendance query took {elapsed:.4f}s"


def test_nfr02_attendance_subject_filter_within_threshold(client, performance_dataset):
    """Retrieving attendance filtered by subject must load within 3 seconds."""
    login_user(client, "perf_admin")
    sub_id = performance_dataset["subject_ids"][0]
    resp, elapsed = measure_get(client, f"/api/attendance?subject_id={sub_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "records" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Subject attendance query took {elapsed:.4f}s"


def test_nfr02_attendance_date_range_filter_within_threshold(client, performance_dataset):
    """Retrieving attendance filtered by date range must load within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(
        client, "/api/attendance?start_date=2026-03-01&end_date=2026-03-15"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "records" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Date range attendance query took {elapsed:.4f}s"


def test_nfr02_attendance_percentages_within_threshold(client, performance_dataset):
    """Attendance percentages calculations must load within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/api/attendance/percentages")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "students" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Attendance percentages took {elapsed:.4f}s"


def test_nfr02_attendance_alerts_within_threshold(client, performance_dataset):
    """Attendance alert calculations must load within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/api/attendance/alerts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "alerts" in data or "students_below_threshold" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Attendance alerts took {elapsed:.4f}s"


def test_nfr02_attendance_report_generation_within_threshold(client, performance_dataset):
    """Attendance report generation must compile within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/api/reports/attendance")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "records" in data
    assert "summary" in data
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Report generation took {elapsed:.4f}s"


def test_nfr02_attendance_export_generation_within_threshold(client, performance_dataset):
    """Attendance export (CSV) generation must load within 3 seconds."""
    login_user(client, "perf_admin")
    resp, elapsed = measure_get(client, "/api/reports/attendance/export?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("Content-Type", "")
    assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"Export generation took {elapsed:.4f}s"


# =====================================================================
# Acceptance Criteria 3: Performance verified using representative scenarios
# =====================================================================

def test_nfr02_representative_teacher_workflow_scenario(client, performance_dataset):
    """Representative Teacher Workflow:
    1. Login as teacher
    2. Load teacher dashboard
    3. Retrieve assigned classes
    4. Retrieve assigned subjects
    5. Retrieve roster for class and subject
    6. Retrieve class attendance
    7. Retrieve attendance percentages for assigned subject
    All steps must individually and cumulatively perform efficiently well within 3 seconds each.
    """
    # 1. Login
    t0 = time.perf_counter()
    login_resp = login_user(client, "perf_teacher_1")
    assert time.perf_counter() - t0 < PERFORMANCE_THRESHOLD_SECONDS

    # 2. Teacher Dashboard
    resp, el_dash = measure_get(client, "/teacher")
    assert resp.status_code == 200
    assert el_dash < PERFORMANCE_THRESHOLD_SECONDS

    # 3. Assigned Classes
    resp, el_cls = measure_get(client, "/api/teacher/classes")
    assert resp.status_code == 200
    assert el_cls < PERFORMANCE_THRESHOLD_SECONDS

    # 4. Assigned Subjects
    resp, el_sub = measure_get(client, "/api/teacher/subjects")
    assert resp.status_code == 200
    assert el_sub < PERFORMANCE_THRESHOLD_SECONDS

    # 5. Class Roster
    c_id = performance_dataset["class_ids"][0]
    sub_id = performance_dataset["subject_ids"][0]
    resp, el_roster = measure_get(client, f"/api/roster?class_id={c_id}&subject_id={sub_id}")
    assert resp.status_code == 200
    assert el_roster < PERFORMANCE_THRESHOLD_SECONDS

    # 6. Class Attendance
    resp, el_att = measure_get(client, f"/api/attendance?class_id={c_id}")
    assert resp.status_code == 200
    assert el_att < PERFORMANCE_THRESHOLD_SECONDS

    # 7. Attendance Percentages
    resp, el_pct = measure_get(client, f"/api/attendance/percentages?subject_id={sub_id}")
    assert resp.status_code == 200
    assert el_pct < PERFORMANCE_THRESHOLD_SECONDS


def test_nfr02_representative_admin_reporting_scenario(client, performance_dataset):
    """Representative Admin Workflow:
    1. Login as admin
    2. Load admin dashboard
    3. Query student directory
    4. Generate class attendance report
    5. Generate subject attendance report
    6. Query low-attendance alerts
    7. Export attendance report to CSV
    All steps must load within 3 seconds.
    """
    login_user(client, "perf_admin")

    c_id = performance_dataset["class_ids"][0]
    sub_id = performance_dataset["subject_ids"][0]

    scenarios = [
        ("/admin", 200),
        ("/api/users?role=student", 200),
        (f"/api/reports/attendance/class/{c_id}", 200),
        (f"/api/reports/attendance/subject/{sub_id}", 200),
        ("/api/attendance/alerts", 200),
        (f"/api/reports/attendance/class/{c_id}/export?format=csv", 200),
    ]

    for endpoint, expected_status in scenarios:
        resp, elapsed = measure_get(client, endpoint)
        assert resp.status_code == expected_status, f"{endpoint} returned {resp.status_code}"
        assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"{endpoint} took {elapsed:.4f}s"


def test_nfr02_representative_student_viewing_scenario(client, performance_dataset):
    """Representative Student Workflow:
    1. Login as student
    2. Load student dashboard
    3. Query personal attendance history
    4. Query personal attendance alerts
    All steps must load within 3 seconds.
    """
    s_id = performance_dataset["student_ids"][0]
    login_user(client, "perf_student_1")

    scenarios = [
        ("/student", 200),
        (f"/api/attendance?student_id={s_id}", 200),
        (f"/api/attendance/alerts/student/{s_id}", 200),
    ]

    for endpoint, expected_status in scenarios:
        resp, elapsed = measure_get(client, endpoint)
        assert resp.status_code == expected_status
        assert elapsed < PERFORMANCE_THRESHOLD_SECONDS, f"{endpoint} took {elapsed:.4f}s"


def test_nfr02_database_indexes_active(client):
    """Verify that performance optimization indexes exist on critical tables."""
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        # Check indexes on attendance
        cur.execute("PRAGMA index_list(attendance)")
        att_indexes = {row[1] for row in cur.fetchall()}
        assert "idx_attendance_subject_date" in att_indexes
        assert "idx_attendance_student_date" in att_indexes
        assert "idx_attendance_date" in att_indexes
        assert "idx_attendance_status" in att_indexes

        # Check indexes on enrollments
        cur.execute("PRAGMA index_list(enrollments)")
        enr_indexes = {row[1] for row in cur.fetchall()}
        assert "idx_enrollments_class" in enr_indexes
        assert "idx_enrollments_subject" in enr_indexes

        # Check index on users role
        cur.execute("PRAGMA index_list(users)")
        usr_indexes = {row[1] for row in cur.fetchall()}
        assert "idx_users_role" in usr_indexes

        # Check index on classes and subjects teacher_id
        cur.execute("PRAGMA index_list(classes)")
        cls_indexes = {row[1] for row in cur.fetchall()}
        assert "idx_classes_teacher" in cls_indexes

        cur.execute("PRAGMA index_list(subjects)")
        sub_indexes = {row[1] for row in cur.fetchall()}
        assert "idx_subjects_teacher" in sub_indexes

