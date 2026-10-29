"""Tests for FR-06: Attendance Reporting.

Covers:
- Student-wise attendance reports
- Class-wise attendance reports
- Subject-wise attendance reports
- Date-range filtering (inclusive bounds, omitted bounds, 1-day range)
- Combined student, class, subject, and date filters
- Validation: invalid date formats, start_date > end_date
- Nonexistent student, class, and subject (404)
- Invalid parameter types / values (400)
- Valid filter combination returning empty results (200, count 0, 0.0%)
- Summary accuracy: total, present, absent, late, percentage
- Role-based permissions: admin, teacher, student scoping
- Join deduplication check
- Alternative route aliases (/api/reports/attendance, /api/attendance/report, /api/attendance/reports)
"""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def fr06_setup(client):
    """Populate an isolated database with users, classes, subjects, enrollments, and attendance."""
    app = client.application
    db_path = app.config["DATABASE"]

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        # Users: admin, 2 teachers, 3 students
        users = [
            ("admin_fr06", "admin"),
            ("teacher1_fr06", "teacher"),
            ("teacher2_fr06", "teacher"),
            ("student1_fr06", "student"),
            ("student2_fr06", "student"),
            ("student3_fr06", "student"),
        ]
        user_ids = {}
        for username, role in users:
            cur = db.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (username, generate_password_hash("pass123"), role),
            )
            user_ids[username] = cur.lastrowid

        # Classes
        cur = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            ("Class 10-A", user_ids["teacher1_fr06"]),
        )
        class_10a_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            ("Class 10-B", user_ids["teacher2_fr06"]),
        )
        class_10b_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO classes (name) VALUES (?)",
            ("Class Empty",),
        )
        class_empty_id = cur.lastrowid

        # Subjects
        cur = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Mathematics", user_ids["teacher1_fr06"]),
        )
        math_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Physics", user_ids["teacher2_fr06"]),
        )
        physics_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Chemistry", user_ids["teacher1_fr06"]),
        )
        chemistry_id = cur.lastrowid

        # Class Subjects
        db.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (class_10a_id, math_id))
        db.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (class_10a_id, chemistry_id))
        db.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (class_10b_id, physics_id))

        # Enrollments:
        # student1 in Class 10-A for Math & Chemistry
        # student2 in Class 10-A for Math
        # student3 in Class 10-B for Physics
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
                   (user_ids["student1_fr06"], class_10a_id, math_id))
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
                   (user_ids["student1_fr06"], class_10a_id, chemistry_id))
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
                   (user_ids["student2_fr06"], class_10a_id, math_id))
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
                   (user_ids["student3_fr06"], class_10b_id, physics_id))

        # Attendance Records:
        # student1 Math:
        # 2026-10-10: Present
        # 2026-10-15: Absent
        # 2026-10-20: Late
        # 2026-10-25: Present
        # student1 Chemistry:
        # 2026-10-12: Present
        # student2 Math:
        # 2026-10-10: Absent
        # 2026-10-15: Present
        # student3 Physics:
        # 2026-10-10: Present
        # 2026-10-30: Present
        records = [
            (user_ids["student1_fr06"], math_id, "2026-10-10", "Present"),
            (user_ids["student1_fr06"], math_id, "2026-10-15", "Absent"),
            (user_ids["student1_fr06"], math_id, "2026-10-20", "Late"),
            (user_ids["student1_fr06"], math_id, "2026-10-25", "Present"),
            (user_ids["student1_fr06"], chemistry_id, "2026-10-12", "Present"),
            (user_ids["student2_fr06"], math_id, "2026-10-10", "Absent"),
            (user_ids["student2_fr06"], math_id, "2026-10-15", "Present"),
            (user_ids["student3_fr06"], physics_id, "2026-10-10", "Present"),
            (user_ids["student3_fr06"], physics_id, "2026-10-30", "Present"),
        ]
        db.executemany(
            "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
            records,
        )
        db.commit()

    return {
        "users": user_ids,
        "classes": {
            "10A": class_10a_id,
            "10B": class_10b_id,
            "empty": class_empty_id,
        },
        "subjects": {
            "math": math_id,
            "physics": physics_id,
            "chemistry": chemistry_id,
        },
    }


def login(client, username, password="pass123"):
    """Helper to authenticate a client session."""
    res = client.post("/api/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.get_data(as_text=True)}"
    return res


# =====================================================================
# 1. Authentication & Route Accessibility
# =====================================================================

def test_reporting_requires_authentication(client):
    """Unauthenticated access to reporting endpoints returns 401."""
    res = client.get("/api/reports/attendance")
    assert res.status_code == 401
    assert "error" in res.get_json()

    res_alias = client.get("/api/attendance/report")
    assert res_alias.status_code == 401


# =====================================================================
# 2. Student-Wise Attendance Report
# =====================================================================

def test_student_wise_report_admin(client, fr06_setup):
    """Admin generates an attendance report for a specific student."""
    login(client, "admin_fr06")
    student1_id = fr06_setup["users"]["student1_fr06"]

    res = client.get(f"/api/reports/attendance?student_id={student1_id}")
    assert res.status_code == 200
    data = res.get_json()

    assert data["report_type"] == "attendance_report"
    assert data["filters"]["student_id"] == student1_id
    assert data["student"]["id"] == student1_id
    assert data["student"]["username"] == "student1_fr06"

    # student1 has 5 records (4 Math + 1 Chemistry)
    # Math: Present (2), Absent (1), Late (1)
    # Chemistry: Present (1)
    # Total: 5, Present: 3, Absent: 1, Late: 1 -> Percentage: 3/5 = 60.0%
    assert data["total_records"] == 5
    assert data["count"] == 5
    assert data["present_count"] == 3
    assert data["absent_count"] == 1
    assert data["late_count"] == 1
    assert data["attendance_percentage"] == 60.0
    assert len(data["records"]) == 5

    # Check record fields
    for rec in data["records"]:
        assert rec["student_id"] == student1_id
        assert rec["student_name"] == "student1_fr06"
        assert "subject_id" in rec
        assert "subject_name" in rec
        assert "attendance_date" in rec
        assert "status" in rec
        assert rec["class_name"] == "Class 10-A"


def test_student_wise_report_via_path_param(client, fr06_setup):
    """Student report works using /api/reports/attendance/student/<id>."""
    login(client, "admin_fr06")
    student2_id = fr06_setup["users"]["student2_fr06"]

    res = client.get(f"/api/reports/attendance/student/{student2_id}")
    assert res.status_code == 200
    data = res.get_json()

    # student2 has 2 records: 1 Present, 1 Absent -> 50.0%
    assert data["total_records"] == 2
    assert data["present_count"] == 1
    assert data["absent_count"] == 1
    assert data["late_count"] == 0
    assert data["attendance_percentage"] == 50.0


# =====================================================================
# 3. Class-Wise Attendance Report
# =====================================================================

def test_class_wise_report(client, fr06_setup):
    """Generate attendance report for a class; excludes other classes."""
    login(client, "admin_fr06")
    class_10a_id = fr06_setup["classes"]["10A"]
    class_10b_id = fr06_setup["classes"]["10B"]

    # Class 10-A includes student1 (5 records) and student2 (2 records) = 7 records
    res_10a = client.get(f"/api/reports/attendance?class_id={class_10a_id}")
    assert res_10a.status_code == 200
    data_10a = res_10a.get_json()

    assert data_10a["class"]["id"] == class_10a_id
    assert data_10a["class"]["name"] == "Class 10-A"
    assert data_10a["total_records"] == 7
    assert data_10a["present_count"] == 4  # student1: 3, student2: 1
    assert data_10a["absent_count"] == 2   # student1: 1, student2: 1
    assert data_10a["late_count"] == 1     # student1: 1
    assert data_10a["attendance_percentage"] == round((4 / 7) * 100, 2)
    assert all(r["class_id"] == class_10a_id for r in data_10a["records"])

    # Class 10-B includes only student3 (2 records)
    res_10b = client.get(f"/api/reports/attendance/class/{class_10b_id}")
    assert res_10b.status_code == 200
    data_10b = res_10b.get_json()
    assert data_10b["total_records"] == 2
    assert data_10b["present_count"] == 2
    assert data_10b["attendance_percentage"] == 100.0
    assert all(r["class_id"] == class_10b_id for r in data_10b["records"])


# =====================================================================
# 4. Subject-Wise Attendance Report
# =====================================================================

def test_subject_wise_report(client, fr06_setup):
    """Generate attendance report for a subject; excludes other subjects."""
    login(client, "admin_fr06")
    math_id = fr06_setup["subjects"]["math"]
    physics_id = fr06_setup["subjects"]["physics"]

    # Math records: student1 (4 records) + student2 (2 records) = 6 records
    res = client.get(f"/api/reports/attendance?subject_id={math_id}")
    assert res.status_code == 200
    data = res.get_json()

    assert data["subject"]["id"] == math_id
    assert data["subject"]["name"] == "Mathematics"
    assert data["total_records"] == 6
    assert all(r["subject_id"] == math_id for r in data["records"])
    # Present: student1(2) + student2(1) = 3
    # Absent: student1(1) + student2(1) = 2
    # Late: student1(1) = 1
    # Percentage: 3 / 6 = 50.0%
    assert data["present_count"] == 3
    assert data["absent_count"] == 2
    assert data["late_count"] == 1
    assert data["attendance_percentage"] == 50.0

    # Physics via path param
    res_phys = client.get(f"/api/reports/attendance/subject/{physics_id}")
    assert res_phys.status_code == 200
    assert res_phys.get_json()["total_records"] == 2


# =====================================================================
# 5. Date-Range Filtering
# =====================================================================

def test_date_range_filtering_inclusive(client, fr06_setup):
    """Date-range filtering includes records within start_date and end_date inclusively."""
    login(client, "admin_fr06")

    # Dates in test setup:
    # 2026-10-10: 3 records (student1 Math, student2 Math, student3 Physics)
    # 2026-10-12: 1 record  (student1 Chemistry)
    # 2026-10-15: 2 records (student1 Math, student2 Math)
    # 2026-10-20: 1 record  (student1 Math)
    # 2026-10-25: 1 record  (student1 Math)
    # 2026-10-30: 1 record  (student3 Physics)

    # Range 2026-10-12 to 2026-10-20 includes:
    # 2026-10-12 (1) + 2026-10-15 (2) + 2026-10-20 (1) = 4 records
    res = client.get("/api/reports/attendance?start_date=2026-10-12&end_date=2026-10-20")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 4
    dates = [r["attendance_date"] for r in data["records"]]
    assert all("2026-10-12" <= d <= "2026-10-20" for d in dates)
    assert "2026-10-10" not in dates
    assert "2026-10-25" not in dates
    assert "2026-10-30" not in dates


def test_date_range_single_day(client, fr06_setup):
    """When start_date == end_date, returns records only on that single date."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?start_date=2026-10-10&end_date=2026-10-10")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 3
    assert all(r["attendance_date"] == "2026-10-10" for r in data["records"])


def test_start_date_only(client, fr06_setup):
    """When only start_date is supplied, includes all records on or after start_date."""
    login(client, "admin_fr06")

    # Records on or after 2026-10-20: 2026-10-20 (1), 2026-10-25 (1), 2026-10-30 (1) = 3 records
    res = client.get("/api/reports/attendance?start_date=2026-10-20")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 3
    assert all(r["attendance_date"] >= "2026-10-20" for r in data["records"])


def test_end_date_only(client, fr06_setup):
    """When only end_date is supplied, includes all records on or before end_date."""
    login(client, "admin_fr06")

    # Records on or before 2026-10-12: 2026-10-10 (3) + 2026-10-12 (1) = 4 records
    res = client.get("/api/reports/attendance?end_date=2026-10-12")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 4
    assert all(r["attendance_date"] <= "2026-10-12" for r in data["records"])


# =====================================================================
# 6. Combined Filters
# =====================================================================

def test_combined_student_class_subject_date_filters(client, fr06_setup):
    """Combine student_id, class_id, subject_id, start_date, and end_date."""
    login(client, "admin_fr06")
    student1_id = fr06_setup["users"]["student1_fr06"]
    class_10a_id = fr06_setup["classes"]["10A"]
    math_id = fr06_setup["subjects"]["math"]

    # student1 + Class 10-A + Math + dates between 2026-10-11 and 2026-10-22
    # In this range, student1 has:
    # 2026-10-15: Absent
    # 2026-10-20: Late
    # Total: 2 records (0 Present, 1 Absent, 1 Late -> 0.0%)
    res = client.get(
        f"/api/reports/attendance?student_id={student1_id}&class_id={class_10a_id}"
        f"&subject_id={math_id}&start_date=2026-10-11&end_date=2026-10-22"
    )
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 2
    assert data["present_count"] == 0
    assert data["absent_count"] == 1
    assert data["late_count"] == 1
    assert data["attendance_percentage"] == 0.0
    for r in data["records"]:
        assert r["student_id"] == student1_id
        assert r["class_id"] == class_10a_id
        assert r["subject_id"] == math_id


# =====================================================================
# 7. Validation: Dates and Parameter Errors
# =====================================================================

def test_invalid_start_date_format(client, fr06_setup):
    """Invalid start_date returns 400."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?start_date=2026-13-40")
    assert res.status_code == 400
    assert "Invalid start_date format" in res.get_json()["error"]

    res2 = client.get("/api/reports/attendance?start_date=invalid-string")
    assert res2.status_code == 400


def test_invalid_end_date_format(client, fr06_setup):
    """Invalid end_date returns 400."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?end_date=10-20-2026")
    assert res.status_code == 400
    assert "Invalid end_date format" in res.get_json()["error"]


def test_start_date_later_than_end_date(client, fr06_setup):
    """start_date after end_date is rejected with 400."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?start_date=2026-10-25&end_date=2026-10-10")
    assert res.status_code == 400
    assert "start_date cannot be later than end_date" in res.get_json()["error"]


def test_invalid_identifiers(client, fr06_setup):
    """Non-integer or non-positive identifiers return 400."""
    login(client, "admin_fr06")

    assert client.get("/api/reports/attendance?student_id=abc").status_code == 400
    assert client.get("/api/reports/attendance?student_id=-5").status_code == 400
    assert client.get("/api/reports/attendance?student_id=0").status_code == 400

    assert client.get("/api/reports/attendance?class_id=zero").status_code == 400
    assert client.get("/api/reports/attendance?class_id=-1").status_code == 400

    assert client.get("/api/reports/attendance?subject_id=xyz").status_code == 400
    assert client.get("/api/reports/attendance?subject_id=0").status_code == 400


def test_invalid_status_filter(client, fr06_setup):
    """Invalid status filter returns 400."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?status=Excused")
    assert res.status_code == 400
    assert "Invalid status filter" in res.get_json()["error"]


# =====================================================================
# 8. Nonexistent Entities (404)
# =====================================================================

def test_nonexistent_student_returns_404(client, fr06_setup):
    """Querying report for a student that does not exist returns 404."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?student_id=99999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "Student not found"


def test_teacher_id_as_student_id_returns_404(client, fr06_setup):
    """Querying report using a user ID with role != student returns 404."""
    login(client, "admin_fr06")
    teacher1_id = fr06_setup["users"]["teacher1_fr06"]

    res = client.get(f"/api/reports/attendance?student_id={teacher1_id}")
    assert res.status_code == 404
    assert res.get_json()["error"] == "Student not found"


def test_nonexistent_class_returns_404(client, fr06_setup):
    """Querying report for a class that does not exist returns 404."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?class_id=99999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "Class not found"


def test_nonexistent_subject_returns_404(client, fr06_setup):
    """Querying report for a subject that does not exist returns 404."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?subject_id=99999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "Subject not found"


# =====================================================================
# 9. Empty Results (200 with 0 records)
# =====================================================================

def test_valid_filter_empty_results(client, fr06_setup):
    """Valid filter with no matching records returns 200 with empty list and zero counts."""
    login(client, "admin_fr06")
    class_empty_id = fr06_setup["classes"]["empty"]

    res = client.get(f"/api/reports/attendance?class_id={class_empty_id}")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 0
    assert data["count"] == 0
    assert data["present_count"] == 0
    assert data["absent_count"] == 0
    assert data["late_count"] == 0
    assert data["attendance_percentage"] == 0.0
    assert data["records"] == []


def test_date_range_empty_results(client, fr06_setup):
    """Date range with no records returns 200 with 0 count."""
    login(client, "admin_fr06")

    res = client.get("/api/reports/attendance?start_date=2025-01-01&end_date=2025-01-31")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_records"] == 0
    assert data["records"] == []


# =====================================================================
# 10. Role-Based Permissions
# =====================================================================

def test_student_can_generate_own_report(client, fr06_setup):
    """Student can view their own report; omitted student_id defaults to self."""
    login(client, "student1_fr06")
    student1_id = fr06_setup["users"]["student1_fr06"]

    res = client.get("/api/reports/attendance")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_records"] == 5
    assert all(r["student_id"] == student1_id for r in data["records"])


def test_student_cannot_view_other_student_report(client, fr06_setup):
    """Student attempting to view another student's report is rejected with 403."""
    login(client, "student1_fr06")
    student2_id = fr06_setup["users"]["student2_fr06"]

    res = client.get(f"/api/reports/attendance?student_id={student2_id}")
    assert res.status_code == 403
    assert "Access denied" in res.get_json()["error"]


def test_teacher_subject_restriction(client, fr06_setup):
    """Teacher can view report for their own subject, but not another teacher's subject."""
    login(client, "teacher1_fr06")
    math_id = fr06_setup["subjects"]["math"]
    physics_id = fr06_setup["subjects"]["physics"]

    # teacher1 teaches Math: allowed
    res_ok = client.get(f"/api/reports/attendance?subject_id={math_id}")
    assert res_ok.status_code == 200

    # teacher1 does not teach Physics: rejected (403)
    res_denied = client.get(f"/api/reports/attendance?subject_id={physics_id}")
    assert res_denied.status_code == 403
    assert "Access denied" in res_denied.get_json()["error"]


def test_teacher_unspecified_subject_scopes_to_assigned(client, fr06_setup):
    """Teacher requesting report without subject_id only sees records from assigned subjects."""
    login(client, "teacher1_fr06")
    physics_id = fr06_setup["subjects"]["physics"]

    res = client.get("/api/reports/attendance")
    assert res.status_code == 200
    data = res.get_json()

    # teacher1 teaches Math and Chemistry, NOT Physics
    assert all(r["subject_id"] != physics_id for r in data["records"])


# =====================================================================
# 11. Alternative Route Aliases
# =====================================================================

def test_alternative_report_endpoint_aliases(client, fr06_setup):
    """Verify /api/attendance/report and /api/attendance/reports return identical report."""
    login(client, "admin_fr06")
    student1_id = fr06_setup["users"]["student1_fr06"]

    res1 = client.get(f"/api/reports/attendance?student_id={student1_id}")
    res2 = client.get(f"/api/attendance/report?student_id={student1_id}")
    res3 = client.get(f"/api/attendance/reports?student_id={student1_id}")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200

    assert res1.get_json()["total_records"] == res2.get_json()["total_records"]
    assert res2.get_json()["total_records"] == res3.get_json()["total_records"]


# =====================================================================
# 12. Regression: Existing Attendance Endpoints & Date Range Support
# =====================================================================

def test_api_attendance_date_range_regression(client, fr06_setup):
    """GET /api/attendance supports start_date and end_date filters consistently."""
    login(client, "admin_fr06")

    res = client.get("/api/attendance?start_date=2026-10-12&end_date=2026-10-20")
    assert res.status_code == 200
    records = res.get_json()["records"]
    assert len(records) == 4
    assert all("2026-10-12" <= r["attendance_date"] <= "2026-10-20" for r in records)


def test_api_attendance_invalid_date_range_regression(client, fr06_setup):
    """GET /api/attendance rejects start_date > end_date with 400."""
    login(client, "admin_fr06")

    res = client.get("/api/attendance?start_date=2026-10-25&end_date=2026-10-10")
    assert res.status_code == 400
    assert "start_date cannot be later than end_date" in res.get_json()["error"]


# =====================================================================
# 13. Additional Edge Cases: Status Filtering & Deduplication
# =====================================================================

def test_status_filter_in_reporting(client, fr06_setup):
    """Filter report records by attendance status (Present, Absent, Late)."""
    login(client, "admin_fr06")

    res_present = client.get("/api/reports/attendance?status=Present")
    assert res_present.status_code == 200
    data_present = res_present.get_json()
    assert all(r["status"] == "Present" for r in data_present["records"])
    assert data_present["present_count"] == len(data_present["records"])
    assert data_present["absent_count"] == 0
    assert data_present["late_count"] == 0
    assert data_present["attendance_percentage"] == 100.0

    res_absent = client.get("/api/reports/attendance?status=Absent")
    assert res_absent.status_code == 200
    data_absent = res_absent.get_json()
    assert all(r["status"] == "Absent" for r in data_absent["records"])
    assert data_absent["present_count"] == 0
    assert data_absent["absent_count"] == len(data_absent["records"])
    assert data_absent["attendance_percentage"] == 0.0


def test_no_duplicate_records_on_multiple_enrollments(client):
    """Ensure joining enrollments and classes never creates duplicate attendance records."""
    app = client.application
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute("INSERT INTO users (username, password_hash, role, active) VALUES ('admin_dup', 'hash', 'admin', 1)")
        admin_id = db.execute("SELECT id FROM users WHERE username = 'admin_dup'").fetchone()[0]
        db.execute("INSERT INTO users (username, password_hash, role, active) VALUES ('student_dup', 'hash', 'student', 1)")
        student_id = db.execute("SELECT id FROM users WHERE username = 'student_dup'").fetchone()[0]

        db.execute("INSERT INTO classes (name) VALUES ('Class D1')")
        c1_id = db.execute("SELECT id FROM classes WHERE name = 'Class D1'").fetchone()[0]
        db.execute("INSERT INTO classes (name) VALUES ('Class D2')")
        c2_id = db.execute("SELECT id FROM classes WHERE name = 'Class D2'").fetchone()[0]

        db.execute("INSERT INTO subjects (name) VALUES ('Subject Dup')")
        s_id = db.execute("SELECT id FROM subjects WHERE name = 'Subject Dup'").fetchone()[0]

        # Enroll student in both classes for this subject
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)", (student_id, c1_id, s_id))
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)", (student_id, c2_id, s_id))

        # Single attendance record
        db.execute(
            "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, '2026-10-25', 'Present')",
            (student_id, s_id)
        )
        db.commit()

    # Login as admin
    with client.session_transaction() as sess:
        sess["user_id"] = admin_id

    # Report without class filter: should have exactly 1 record, not 2
    res = client.get(f"/api/reports/attendance?student_id={student_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_records"] == 1
    assert len(data["records"]) == 1
    assert data["records"][0]["status"] == "Present"


def test_records_outside_filters_are_strictly_excluded(client, fr06_setup):
    """Verify that records outside student, class, and date filters are excluded."""
    login(client, "admin_fr06")
    student2_id = fr06_setup["users"]["student2_fr06"]
    class_10a_id = fr06_setup["classes"]["10A"]

    # student2 Math records in Class 10-A on 2026-10-10 and 2026-10-15
    res = client.get(
        f"/api/reports/attendance?student_id={student2_id}&class_id={class_10a_id}&start_date=2026-10-14&end_date=2026-10-16"
    )
    assert res.status_code == 200
    data = res.get_json()

    # Only 2026-10-15 record matches
    assert data["total_records"] == 1
    assert data["records"][0]["attendance_date"] == "2026-10-15"
    assert data["records"][0]["student_id"] == student2_id
    assert data["records"][0]["status"] == "Present"
