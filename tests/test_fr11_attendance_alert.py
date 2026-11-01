"""Tests for FR-11: Attendance Alert Functionality."""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash

from session_helpers import plant_session


@pytest.fixture
def fr11_data(client):
    """Seed users, classes, subjects, enrollments, and attendance records."""
    db_path = client.application.config["DATABASE"]
    ids = {}

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        # 1. Users
        users = [
            ("admin_fr11", "admin"),
            ("teacher1_fr11", "teacher"),
            ("teacher2_fr11", "teacher"),
            ("student1_fr11", "student"),
            ("student2_fr11", "student"),
            ("student3_fr11", "student"),
            ("student4_fr11", "student"),  # Will have zero attendance records
        ]
        for username, role in users:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (username, generate_password_hash("Pass123!"), role),
            )
            ids[username] = cursor.lastrowid

        # 2. Classes
        c1 = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            ("Class 10-A", ids["teacher1_fr11"]),
        ).lastrowid
        c2 = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            ("Class 10-B", ids["teacher2_fr11"]),
        ).lastrowid
        ids["class_10a"] = c1
        ids["class_10b"] = c2

        # 3. Subjects
        s_math = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Mathematics", ids["teacher1_fr11"]),
        ).lastrowid
        s_phys = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Physics", ids["teacher1_fr11"]),
        ).lastrowid
        s_hist = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("History", ids["teacher2_fr11"]),
        ).lastrowid
        ids["subject_math"] = s_math
        ids["subject_phys"] = s_phys
        ids["subject_hist"] = s_hist

        # 4. Class-Subjects
        db.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (c1, s_math))
        db.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (c1, s_phys))
        db.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (c2, s_hist))

        # 5. Enrollments
        students = ["student1_fr11", "student2_fr11", "student3_fr11", "student4_fr11"]
        for st in students:
            st_id = ids[st]
            db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)", (st_id, c1, s_math))
            db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)", (st_id, c1, s_phys))

        # 6. Attendance records for Mathematics (4 classes held)
        # student1: 4 Present -> 4/4 = 100.0%
        # student2: 3 Present, 1 Absent -> 3/4 = 75.0% (exactly at threshold 75%)
        # student3: 2 Present, 1 Absent, 1 Late -> 2/4 = 50.0% (below threshold 75%)
        # student4: 0 classes marked
        att_rows = [
            (ids["student1_fr11"], s_math, "2026-10-01", "Present"),
            (ids["student1_fr11"], s_math, "2026-10-02", "Present"),
            (ids["student1_fr11"], s_math, "2026-10-03", "Present"),
            (ids["student1_fr11"], s_math, "2026-10-04", "Present"),

            (ids["student2_fr11"], s_math, "2026-10-01", "Present"),
            (ids["student2_fr11"], s_math, "2026-10-02", "Present"),
            (ids["student2_fr11"], s_math, "2026-10-03", "Present"),
            (ids["student2_fr11"], s_math, "2026-10-04", "Absent"),

            (ids["student3_fr11"], s_math, "2026-10-01", "Present"),
            (ids["student3_fr11"], s_math, "2026-10-02", "Present"),
            (ids["student3_fr11"], s_math, "2026-10-03", "Absent"),
            (ids["student3_fr11"], s_math, "2026-10-04", "Late"),
        ]
        db.executemany(
            "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
            att_rows,
        )
        db.commit()

    return ids


def login(client, username):
    """Log in through /api/login."""
    res = client.post("/api/login", json={"username": username, "password": "Pass123!"})
    assert res.status_code == 200
    return res


# =====================================================================
# 1. Threshold Configuration & Defaults
# =====================================================================

def test_default_threshold_behavior(client, fr11_data):
    """Scenario 1 & 2: Default threshold is 75.0% and correctly returned."""
    login(client, "admin_fr11")

    res = client.get("/api/attendance/threshold")
    assert res.status_code == 200
    data = res.get_json()
    assert data["threshold"] == 75.0
    assert data["default_threshold"] == 75.0

    # Calling alerts without threshold uses default 75.0
    alert_res = client.get("/api/attendance/alerts")
    assert alert_res.status_code == 200
    alert_data = alert_res.get_json()
    assert alert_data["threshold"] == 75.0


def test_successful_threshold_configuration(client, fr11_data):
    """Scenario 1: Update threshold via configuration API."""
    login(client, "admin_fr11")

    # Set threshold to 80.0
    res = client.put("/api/attendance/threshold", json={"threshold": 80.0})
    assert res.status_code == 200
    data = res.get_json()
    assert data["threshold"] == 80.0

    # Verify GET threshold reflects the new value
    get_res = client.get("/api/attendance/threshold")
    assert get_res.status_code == 200
    assert get_res.get_json()["threshold"] == 80.0

    # Verify alerts now use 80.0 as default
    alert_res = client.get(f"/api/attendance/alerts?subject_id={fr11_data['subject_math']}")
    assert alert_res.status_code == 200
    alert_data = alert_res.get_json()
    assert alert_data["threshold"] == 80.0
    # At 80%, student2 (75%) is now below threshold!
    alert_names = [a["student_name"] for a in alert_data["alerts"]]
    assert "student2_fr11" in alert_names
    assert "student3_fr11" in alert_names


def test_threshold_modification_is_admin_only(client, fr11_data):
    """Review fix: Only admins can update the threshold; teachers/students get 403, unauthenticated gets 401."""
    # 1. Unauthenticated gets 401
    res_unauth = client.post("/api/attendance/threshold", json={"threshold": 80.0})
    assert res_unauth.status_code == 401

    res_unauth_put = client.put("/api/attendance/threshold", json={"threshold": 80.0})
    assert res_unauth_put.status_code == 401

    # 2. Teacher gets 403 Forbidden
    login(client, "teacher1_fr11")
    res_teacher = client.post("/api/attendance/threshold", json={"threshold": 80.0})
    assert res_teacher.status_code == 403
    assert res_teacher.get_json()["error"] == "Access denied"

    res_teacher_put = client.put("/api/attendance/threshold", json={"threshold": 80.0})
    assert res_teacher_put.status_code == 403
    assert res_teacher_put.get_json()["error"] == "Access denied"

    # 3. Student gets 403 Forbidden
    login(client, "student1_fr11")
    res_student = client.put("/api/attendance/threshold", json={"threshold": 80.0})
    assert res_student.status_code == 403
    assert res_student.get_json()["error"] == "Access denied"

    # 4. Admin gets 200 OK
    login(client, "admin_fr11")
    res_admin = client.put("/api/attendance/threshold", json={"threshold": 80.0})
    assert res_admin.status_code == 200
    assert res_admin.get_json()["threshold"] == 80.0


def test_threshold_persisted_in_database(client, fr11_data):
    """Review fix: Threshold update is persisted in SQLite settings table and avoids duplicates."""
    login(client, "admin_fr11")

    res = client.put("/api/attendance/threshold", json={"threshold": 82.5})
    assert res.status_code == 200

    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        row = db.execute("SELECT value FROM settings WHERE key = 'attendance_threshold'").fetchone()
        assert row is not None
        assert row[0] == "82.5"

        # Check no duplicate records on subsequent update
        client.put("/api/attendance/threshold", json={"threshold": 83.0})
        count = db.execute("SELECT COUNT(*) FROM settings WHERE key = 'attendance_threshold'").fetchone()[0]
        assert count == 1
        updated_row = db.execute("SELECT value FROM settings WHERE key = 'attendance_threshold'").fetchone()
        assert updated_row[0] == "83.0"


def test_threshold_persists_across_application_restart(client, fr11_data):
    """Review fix: Saved threshold remains available after creating a new Flask application instance."""
    from app import create_app

    db_path = client.application.config["DATABASE"]

    # Set threshold to 88.0 as admin on current client
    login(client, "admin_fr11")
    res = client.put("/api/attendance/threshold", json={"threshold": 88.0})
    assert res.status_code == 200
    assert res.get_json()["threshold"] == 88.0

    # Simulate restart by creating a brand-new application instance connected to the same database
    new_app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "test-only"})
    new_client = new_app.test_client()

    # Log in on new application instance
    login(new_client, "admin_fr11")

    # Verify GET /api/attendance/threshold returns 88.0
    get_res = new_client.get("/api/attendance/threshold")
    assert get_res.status_code == 200
    assert get_res.get_json()["threshold"] == 88.0

    # Verify alert calculation on new application instance uses the persisted 88.0 threshold
    sub_id = fr11_data["subject_math"]
    alert_res = new_client.get(f"/api/attendance/alerts?subject_id={sub_id}")
    assert alert_res.status_code == 200
    alert_data = alert_res.get_json()
    assert alert_data["threshold"] == 88.0

    # student2 (75%) is below 88%
    alert_names = [a["student_name"] for a in alert_data["alerts"]]
    assert "student2_fr11" in alert_names


def test_query_parameter_threshold_override(client, fr11_data):
    """Scenario 1: Specify threshold dynamically via query parameter."""
    login(client, "admin_fr11")

    # Override threshold to 60%
    res = client.get(f"/api/attendance/alerts?subject_id={fr11_data['subject_math']}&threshold=60")
    assert res.status_code == 200
    data = res.get_json()
    assert data["threshold"] == 60.0

    # At 60%: student3 (50%) is an alert, student2 (75%) and student1 (100%) are not
    alert_names = [a["student_name"] for a in data["alerts"]]
    assert alert_names == ["student3_fr11"]


# =====================================================================
# 2. Rejecting Invalid Thresholds
# =====================================================================

def test_reject_negative_threshold(client, fr11_data):
    """Scenario 3: Reject negative threshold values."""
    login(client, "admin_fr11")

    # Query param
    res1 = client.get("/api/attendance/alerts?threshold=-5")
    assert res1.status_code == 400
    assert "threshold" in res1.get_json()["error"].lower()

    res2 = client.get("/api/attendance/alerts?threshold=-0.01")
    assert res2.status_code == 400

    # Configuration endpoint
    res3 = client.post("/api/attendance/threshold", json={"threshold": -10})
    assert res3.status_code == 400


def test_reject_threshold_above_100(client, fr11_data):
    """Scenario 4: Reject threshold values greater than 100."""
    login(client, "admin_fr11")

    res1 = client.get("/api/attendance/alerts?threshold=100.01")
    assert res1.status_code == 400
    assert "threshold" in res1.get_json()["error"].lower()

    res2 = client.get("/api/attendance/alerts?threshold=150")
    assert res2.status_code == 400

    res3 = client.put("/api/attendance/threshold", json={"threshold": 105})
    assert res3.status_code == 400


def test_reject_malformed_threshold_values(client, fr11_data):
    """Scenario 5: Reject strings, empty values, booleans, and malformed inputs."""
    login(client, "admin_fr11")

    # Non-numeric string
    res_str = client.get("/api/attendance/alerts?threshold=invalid")
    assert res_str.status_code == 400

    # Empty string
    res_empty = client.get("/api/attendance/alerts?threshold=")
    assert res_empty.status_code == 400

    # Booleans (True / False should not be coerced to 1 / 0)
    res_bool = client.post("/api/attendance/threshold", json={"threshold": True})
    assert res_bool.status_code == 400

    # Null / None in JSON body
    res_null = client.post("/api/attendance/threshold", json={"threshold": None})
    assert res_null.status_code == 400

    # Missing threshold key
    res_missing = client.post("/api/attendance/threshold", json={})
    assert res_missing.status_code == 400

    # Non-dict JSON
    res_non_dict = client.post("/api/attendance/threshold", json="75")
    assert res_non_dict.status_code == 400


# =====================================================================
# 3. Calculation & Student Alert Identification
# =====================================================================

def test_correct_percentage_calculation(client, fr11_data):
    """Scenario 6: Verify attendance percentage = (present / total) * 100."""
    login(client, "admin_fr11")

    sub_id = fr11_data["subject_math"]
    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()

    students_by_name = {s["student_name"]: s for s in data["students"]}

    # student1: 4 Present / 4 Total = 100.0%
    s1 = students_by_name["student1_fr11"]
    assert s1["classes_attended"] == 4
    assert s1["total_classes"] == 4
    assert s1["attendance_percentage"] == 100.0

    # student2: 3 Present / 4 Total = 75.0%
    s2 = students_by_name["student2_fr11"]
    assert s2["classes_attended"] == 3
    assert s2["total_classes"] == 4
    assert s2["attendance_percentage"] == 75.0

    # student3: 2 Present, 1 Absent, 1 Late = 2/4 = 50.0% (Late is not attended)
    s3 = students_by_name["student3_fr11"]
    assert s3["classes_attended"] == 2
    assert s3["total_classes"] == 4
    assert s3["attendance_percentage"] == 50.0


def test_student_below_threshold_identified(client, fr11_data):
    """Scenario 7: Student below the threshold is identified in alerts."""
    login(client, "admin_fr11")

    sub_id = fr11_data["subject_math"]
    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()

    alert_students = [a["student_name"] for a in data["alerts"]]
    assert "student3_fr11" in alert_students


def test_student_above_threshold_not_identified(client, fr11_data):
    """Scenario 8: Student above threshold is not included in alerts."""
    login(client, "admin_fr11")

    sub_id = fr11_data["subject_math"]
    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()

    alert_students = [a["student_name"] for a in data["alerts"]]
    assert "student1_fr11" not in alert_students


def test_student_exactly_at_threshold_not_identified(client, fr11_data):
    """Scenario 9: Student exactly at threshold must not be flagged as below threshold."""
    login(client, "admin_fr11")

    sub_id = fr11_data["subject_math"]
    # Threshold is exactly 75.0%, student2 is exactly 75.0%
    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75.0")
    assert res.status_code == 200
    data = res.get_json()

    alert_students = [a["student_name"] for a in data["alerts"]]
    assert "student2_fr11" not in alert_students

    # Check student2 record flags
    students_by_name = {s["student_name"]: s for s in data["students"]}
    s2 = students_by_name["student2_fr11"]
    assert s2["attendance_percentage"] == 75.0
    assert s2["below_threshold"] is False
    assert s2["is_alert"] is False
    assert s2["alert_status"] == "NORMAL"


def test_boundary_strict_inequality(client, fr11_data):
    """Verify strict inequality: 75.0 is safe at 75, but alerted at 75.01."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    # At 75.0: student2 (75%) is NOT alerted
    r1 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75.0")
    assert "student2_fr11" not in [a["student_name"] for a in r1.get_json()["alerts"]]

    # At 75.01: student2 (75.00%) IS alerted (75.00 < 75.01)
    r2 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75.01")
    assert "student2_fr11" in [a["student_name"] for a in r2.get_json()["alerts"]]

    # At 74.99: student2 (75.00%) is NOT alerted (75.00 < 74.99 is False)
    r3 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=74.99")
    assert "student2_fr11" not in [a["student_name"] for a in r3.get_json()["alerts"]]


def test_multiple_students_different_percentages(client, fr11_data):
    """Scenario 10: Multiple students with different percentages and sorting."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    # At 80% threshold: student3 (50%) and student2 (75%) should be alerted
    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=80")
    assert res.status_code == 200
    data = res.get_json()

    alerts = data["alerts"]
    assert len(alerts) == 2
    # Verify lowest attendance first
    assert alerts[0]["student_name"] == "student3_fr11"
    assert alerts[0]["attendance_percentage"] == 50.0
    assert alerts[1]["student_name"] == "student2_fr11"
    assert alerts[1]["attendance_percentage"] == 75.0


def test_zero_eligible_attendance(client, fr11_data):
    """Scenario 11: Student with zero eligible attendance handled without division by zero."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()

    students_by_name = {s["student_name"]: s for s in data["students"]}
    s4 = students_by_name["student4_fr11"]

    assert s4["total_classes"] == 0
    assert s4["classes_attended"] == 0
    assert s4["attendance_percentage"] == 0.0
    # By default, zero-record students are not flagged as truant alerts
    assert s4["below_threshold"] is False
    assert s4["is_alert"] is False
    assert s4["alert_status"] == "NO_RECORDS"
    assert "student4_fr11" not in [a["student_name"] for a in data["alerts"]]


def test_zero_eligible_attendance_with_include_zero_flag(client, fr11_data):
    """Scenario 11: Student with zero eligible attendance included when include_zero=true."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75&include_zero=true")
    assert res.status_code == 200
    data = res.get_json()

    alert_names = [a["student_name"] for a in data["alerts"]]
    assert "student4_fr11" in alert_names
    students_by_name = {s["student_name"]: s for s in data["students"]}
    s4 = students_by_name["student4_fr11"]
    assert s4["below_threshold"] is True
    assert s4["is_alert"] is True


def test_empty_database_and_no_attendance_records(client):
    """Scenario 12: Empty database or no attendance records returns clean empty response."""
    # A fresh client has an empty database
    # Create an admin user to login
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'admin', 1)",
            ("empty_admin", generate_password_hash("Pass123!")),
        )
        db.commit()

    login(client, "empty_admin")

    res = client.get("/api/attendance/alerts")
    assert res.status_code == 200
    data = res.get_json()

    assert data["count"] == 0
    assert data["alerts_count"] == 0
    assert data["total_students"] == 0
    assert data["alerts"] == []
    assert data["students"] == []
    assert data["threshold"] == 75.0


def test_correct_alert_response_structure(client, fr11_data):
    """Scenario 13: Verify complete response structure and expected keys."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()

    expected_top_keys = {"threshold", "count", "alerts_count", "total_students", "alerts", "students", "filters", "subject"}
    for key in expected_top_keys:
        assert key in data, f"Missing key '{key}' in alert response"

    # Verify student item keys
    for student in data["students"]:
        expected_student_keys = {
            "student_id",
            "student_name",
            "username",
            "classes_attended",
            "total_classes",
            "attendance_percentage",
            "threshold",
            "is_alert",
            "below_threshold",
            "alert_status",
        }
        for skey in expected_student_keys:
            assert skey in student, f"Missing key '{skey}' in student dictionary"


def test_clear_indication_of_low_attendance(client, fr11_data):
    """Scenario 14: Clear visual / API indication of low attendance vs normal."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    res = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()

    students = {s["student_name"]: s for s in data["students"]}

    # Student 3 is below threshold: clearly indicated
    s3 = students["student3_fr11"]
    assert s3["below_threshold"] is True
    assert s3["is_alert"] is True
    assert s3["alert_status"] == "BELOW_THRESHOLD"

    # Student 1 meets threshold: clearly indicated
    s1 = students["student1_fr11"]
    assert s1["below_threshold"] is False
    assert s1["is_alert"] is False
    assert s1["alert_status"] == "NORMAL"


# =====================================================================
# 4. Scoping & Role-Based Authorization
# =====================================================================

def test_subject_scoping(client, fr11_data):
    """Attendance alert calculated within specific subject scope."""
    login(client, "admin_fr11")

    # Add a physics attendance where student3 is present
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, '2026-10-05', 'Present')",
            (fr11_data["student3_fr11"], fr11_data["subject_phys"]),
        )
        db.commit()

    # Math: student3 has 2/4 = 50% (Alert)
    r_math = client.get(f"/api/attendance/alerts?subject_id={fr11_data['subject_math']}&threshold=75")
    assert r_math.status_code == 200
    assert "student3_fr11" in [a["student_name"] for a in r_math.get_json()["alerts"]]

    # Physics: student3 has 1/1 = 100% (Not an alert!)
    r_phys = client.get(f"/api/attendance/alerts?subject_id={fr11_data['subject_phys']}&threshold=75")
    assert r_phys.status_code == 200
    assert "student3_fr11" not in [a["student_name"] for a in r_phys.get_json()["alerts"]]


def test_class_scoping(client, fr11_data):
    """Attendance alert calculated within specific class scope."""
    login(client, "admin_fr11")
    c1 = fr11_data["class_10a"]

    res = client.get(f"/api/attendance/alerts?class_id={c1}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()
    assert "class" in data
    assert data["class"]["id"] == c1


def test_student_scoping(client, fr11_data):
    """Attendance alert filtered for a specific student."""
    login(client, "admin_fr11")
    st_id = fr11_data["student3_fr11"]

    res = client.get(f"/api/attendance/alerts?student_id={st_id}&threshold=75")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_students"] == 1
    assert data["students"][0]["student_name"] == "student3_fr11"
    assert data["count"] == 1
    assert data["alerts"][0]["student_name"] == "student3_fr11"


def test_teacher_role_isolation(client, fr11_data):
    """Teacher can view assigned subjects, denied access to other teachers' subjects."""
    login(client, "teacher1_fr11")

    # Teacher 1 can access Math
    res_ok = client.get(f"/api/attendance/alerts?subject_id={fr11_data['subject_math']}")
    assert res_ok.status_code == 200

    # Teacher 1 CANNOT access History (owned by teacher2)
    res_forbidden = client.get(f"/api/attendance/alerts?subject_id={fr11_data['subject_hist']}")
    assert res_forbidden.status_code == 403


def test_student_role_isolation(client, fr11_data):
    """Student can view their own alerts, denied access to other students."""
    login(client, "student1_fr11")

    # Student 1 can view own alerts
    res_own = client.get("/api/attendance/alerts")
    assert res_own.status_code == 200
    data = res_own.get_json()
    assert data["total_students"] == 1
    assert data["students"][0]["student_name"] == "student1_fr11"

    # Student 1 cannot view Student 2's alerts
    res_forbidden = client.get(f"/api/attendance/alerts?student_id={fr11_data['student2_fr11']}")
    assert res_forbidden.status_code == 403


def test_unauthenticated_rejected(client, fr11_data):
    """Unauthenticated requests are rejected with 401."""
    res = client.get("/api/attendance/alerts")
    assert res.status_code == 401

    res_thresh = client.get("/api/attendance/threshold")
    assert res_thresh.status_code == 401


# =====================================================================
# 5. Reactivity & Route Aliases
# =====================================================================

def test_reactivity_on_attendance_updates(client, fr11_data):
    """When attendance records are created or updated, alerts update immediately."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]
    st_id = fr11_data["student3_fr11"]

    # Initially student3 is at 50% (Alert at 75%)
    r1 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&student_id={st_id}&threshold=75")
    assert r1.get_json()["count"] == 1
    assert r1.get_json()["alerts"][0]["attendance_percentage"] == 50.0

    # Update record on 2026-10-03 from Absent to Present
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        rec_id = db.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND subject_id = ? AND attendance_date = '2026-10-03'",
            (st_id, sub_id),
        ).fetchone()[0]

    update_res = client.put(f"/api/attendance/{rec_id}", json={"status": "Present"})
    assert update_res.status_code == 200

    # Also update 2026-10-04 from Late to Present -> 4/4 = 100%
    with sqlite3.connect(db_path) as db:
        rec_id2 = db.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND subject_id = ? AND attendance_date = '2026-10-04'",
            (st_id, sub_id),
        ).fetchone()[0]

    update_res2 = client.put(f"/api/attendance/{rec_id2}", json={"status": "Present"})
    assert update_res2.status_code == 200

    # Query alerts again: student3 is now 100%, NO LONGER AN ALERT!
    r2 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&student_id={st_id}&threshold=75")
    assert r2.status_code == 200
    assert r2.get_json()["count"] == 0
    assert r2.get_json()["students"][0]["attendance_percentage"] == 100.0
    assert r2.get_json()["students"][0]["below_threshold"] is False


def test_threshold_change_updates_alerts_without_touching_records(client, fr11_data):
    """Changing the threshold updates alert results without altering database records."""
    login(client, "admin_fr11")
    sub_id = fr11_data["subject_math"]

    # At 75%: student2 (75.0%) is not an alert
    r1 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=75")
    assert "student2_fr11" not in [a["student_name"] for a in r1.get_json()["alerts"]]

    # At 76%: student2 (75.0%) becomes an alert
    r2 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=76")
    assert "student2_fr11" in [a["student_name"] for a in r2.get_json()["alerts"]]

    # At 40%: student3 (50.0%) is no longer an alert
    r3 = client.get(f"/api/attendance/alerts?subject_id={sub_id}&threshold=40")
    assert len(r3.get_json()["alerts"]) == 0


def test_route_aliases(client, fr11_data):
    """Verify all route aliases work properly."""
    login(client, "admin_fr11")

    # Canonical and aliases
    paths = [
        "/api/attendance/alerts",
        "/api/attendance/alert",
        "/api/alerts/attendance",
        f"/api/attendance/alerts/student/{fr11_data['student3_fr11']}",
        f"/api/attendance/alerts/class/{fr11_data['class_10a']}",
        f"/api/attendance/alerts/subject/{fr11_data['subject_math']}",
    ]

    for p in paths:
        res = client.get(p)
        assert res.status_code == 200, f"Failed for path {p}"
        assert "alerts" in res.get_json()


# =====================================================================
# 6. Regression Tests for Existing Attendance Functionality
# =====================================================================

def test_regression_existing_attendance_functionality(client, fr11_data):
    """Scenario 15: Existing marking, percentages, and reporting continue to function."""
    login(client, "admin_fr11")

    # 1. Percentages (FR-04)
    pct_res = client.get("/api/attendance/percentages")
    assert pct_res.status_code == 200
    assert "students" in pct_res.get_json()

    # 2. Reporting (FR-06)
    rep_res = client.get(f"/api/reports/attendance?subject_id={fr11_data['subject_math']}")
    assert rep_res.status_code == 200
    assert rep_res.get_json()["report_type"] == "attendance_report"

    # 3. Attendance records (FR-03)
    rec_res = client.get(f"/api/attendance?subject_id={fr11_data['subject_math']}")
    assert rec_res.status_code == 200
    assert rec_res.get_json()["count"] > 0

