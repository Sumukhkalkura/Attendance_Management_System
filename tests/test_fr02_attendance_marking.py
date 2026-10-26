"""Automated tests for FR-02: Attendance Marking.

Covers all 10 Test Plan cases:
- UT_FR-02_01: Mark Present
- UT_FR-02_02: Mark Absent
- UT_FR-02_03: Mark Late
- UT_FR-02_04: Missing date validation
- UT_FR-02_05: Missing status validation
- IT_FR-02_06: Load class roster
- IT_FR-02_07: Save complete roster (batch attendance)
- IT_FR-02_08: Unauthorized subject
- SYS_FR-02_09: Change attendance date
- SYS_FR-02_10: Invalid attendance status

Additional verification:
- Duplicate attendance submission handling
- Unauthenticated and student role unauthorized access
- Database disk persistence
- Atomic rollback on batch failure
"""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash
from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated test application and database for FR-02 tests."""
    database_path = tmp_path / "fr02_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(database_path),
        "SECRET_KEY": "fr02-test-secret-key",
    })

    with sqlite3.connect(database_path) as db:
        # Users: admin (1), teacher1 (2), teacher2 (3), student1 (4), student2 (5), student3 (6)
        users = [
            ("admin1", "admin123", "admin", 1),
            ("teacher1", "teacher123", "teacher", 1),
            ("teacher2", "teacher123", "teacher", 1),
            ("student1", "student123", "student", 1),
            ("student2", "student123", "student", 1),
            ("student3", "student123", "student", 1),
        ]
        for username, password, role, active in users:
            db.execute(
                """
                INSERT INTO users (username, password_hash, role, active)
                VALUES (?, ?, ?, ?)
                """,
                (username, generate_password_hash(password), role, active),
            )

        # Classes: CSE-A (1), CSE-B (2)
        db.execute("INSERT INTO classes (name) VALUES (?)", ("CSE-A",))
        db.execute("INSERT INTO classes (name) VALUES (?)", ("CSE-B",))

        # Subjects: DBMS (1, teacher1 id 2), OS (2, teacher2 id 3)
        db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("DBMS", 2),
        )
        db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("OS", 3),
        )

        # Enrollments:
        # CSE-A (id 1) for DBMS (id 1): student1 (4), student2 (5), student3 (6)
        # CSE-B (id 2) for OS (id 2): student1 (4)
        for student_id in (4, 5, 6):
            db.execute(
                "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
                (student_id, 1, 1),
            )
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (4, 2, 2),
        )
        db.commit()

    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password="teacher123"):
    """Authenticate a test user."""
    return client.post(
        "/api/login",
        json={"username": username, "password": password},
    )


# ---------------------------------------------------------------------------
# UT_FR-02_01: Mark Present
# ---------------------------------------------------------------------------

def test_ut_fr_02_01_mark_present(client):
    """Teacher marks an enrolled student Present -> 201 Created."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "class_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Attendance recorded successfully"
    assert data["record"]["status"] == "Present"
    assert data["record"]["student_id"] == 4
    assert data["record"]["subject_id"] == 1


# ---------------------------------------------------------------------------
# UT_FR-02_02: Mark Absent
# ---------------------------------------------------------------------------

def test_ut_fr_02_02_mark_absent(client):
    """Teacher marks an enrolled student Absent -> 201 Created."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "class_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Absent",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Attendance recorded successfully"
    assert data["record"]["status"] == "Absent"


# ---------------------------------------------------------------------------
# UT_FR-02_03: Mark Late
# ---------------------------------------------------------------------------

def test_ut_fr_02_03_mark_late(client):
    """Teacher marks an enrolled student Late -> 201 Created."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "class_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Late",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Attendance recorded successfully"
    assert data["record"]["status"] == "Late"


# ---------------------------------------------------------------------------
# UT_FR-02_04: Missing date validation
# ---------------------------------------------------------------------------

def test_ut_fr_02_04_missing_date_validation(client):
    """Leave date empty or omitted -> 400 Bad Request."""
    login(client, "teacher1", "teacher123")

    # Date omitted
    res_omitted = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "status": "Present",
        },
    )
    assert res_omitted.status_code == 400

    # Date empty string
    res_empty = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "",
            "status": "Present",
        },
    )
    assert res_empty.status_code == 400
    assert "attendance_date" in res_empty.get_json()["error"]


# ---------------------------------------------------------------------------
# UT_FR-02_05: Missing status validation
# ---------------------------------------------------------------------------

def test_ut_fr_02_05_missing_status_validation(client):
    """Leave status unselected or omitted -> 400 Bad Request."""
    login(client, "teacher1", "teacher123")

    # Status omitted
    res_omitted = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
        },
    )
    assert res_omitted.status_code == 400

    # Status empty string
    res_empty = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "",
        },
    )
    assert res_empty.status_code == 400
    assert "Invalid attendance status" in res_empty.get_json()["error"]


# ---------------------------------------------------------------------------
# IT_FR-02_06: Load class roster
# ---------------------------------------------------------------------------

def test_it_fr_02_06_load_class_roster(client):
    """Select class CSE-A and subject DBMS -> correct enrolled students appear."""
    login(client, "teacher1", "teacher123")

    response = client.get("/api/roster?class_id=1&subject_id=1")

    assert response.status_code == 200
    data = response.get_json()
    assert data["class_name"] == "CSE-A"
    assert data["subject_name"] == "DBMS"
    assert data["count"] == 3
    roster_usernames = [s["username"] for s in data["students"]]
    assert roster_usernames == ["student1", "student2", "student3"]


# ---------------------------------------------------------------------------
# IT_FR-02_07: Save complete roster (batch attendance)
# ---------------------------------------------------------------------------

def test_it_fr_02_07_save_complete_roster(client):
    """Save batch attendance for entire roster: student1 Present, student2 Absent, student3 Late."""
    login(client, "teacher1", "teacher123")

    batch_payload = {
        "class_id": 1,
        "subject_id": 1,
        "attendance_date": "2026-10-25",
        "records": [
            {"student_id": 4, "status": "Present"},
            {"student_id": 5, "status": "Absent"},
            {"student_id": 6, "status": "Late"},
        ],
    }

    response = client.post("/api/attendance", json=batch_payload)

    assert response.status_code == 201
    data = response.get_json()
    assert data["count"] == 3
    assert data["message"] == "Attendance recorded successfully"

    # Verify all records saved with corresponding statuses
    statuses = {r["student_id"]: r["status"] for r in data["records"]}
    assert statuses[4] == "Present"
    assert statuses[5] == "Absent"
    assert statuses[6] == "Late"


# ---------------------------------------------------------------------------
# IT_FR-02_08: Unauthorized subject
# ---------------------------------------------------------------------------

def test_it_fr_02_08_unauthorized_subject(client):
    """Teacher attempting to mark attendance for unassigned subject is denied 403 Forbidden."""
    # teacher1 teaches DBMS (id 1), but attempts to mark for OS (id 2, teacher2)
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 2,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )

    assert response.status_code == 403
    assert "not assigned" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# SYS_FR-02_09: Change attendance date
# ---------------------------------------------------------------------------

def test_sys_fr_02_09_change_attendance_date(client):
    """Records correspond accurately to the selected date when changing dates."""
    login(client, "teacher1", "teacher123")

    # Mark attendance for 2026-10-25
    client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )

    # Mark attendance for 2026-10-26
    client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Absent",
        },
    )

    # Roster on 2026-10-25 reflects Present
    roster_d1 = client.get("/api/roster?class_id=1&subject_id=1&attendance_date=2026-10-25")
    assert roster_d1.status_code == 200
    student1_d1 = next(s for s in roster_d1.get_json()["students"] if s["student_id"] == 4)
    assert student1_d1["status"] == "Present"

    # Roster on 2026-10-26 reflects Absent
    roster_d2 = client.get("/api/roster?class_id=1&subject_id=1&attendance_date=2026-10-26")
    assert roster_d2.status_code == 200
    student1_d2 = next(s for s in roster_d2.get_json()["students"] if s["student_id"] == 4)
    assert student1_d2["status"] == "Absent"

    # Roster on an unmarked date reflects None
    roster_d3 = client.get("/api/roster?class_id=1&subject_id=1&attendance_date=2026-10-27")
    assert roster_d3.status_code == 200
    student1_d3 = next(s for s in roster_d3.get_json()["students"] if s["student_id"] == 4)
    assert student1_d3["status"] is None


# ---------------------------------------------------------------------------
# SYS_FR-02_10: Invalid attendance status
# ---------------------------------------------------------------------------

def test_sys_fr_02_10_invalid_attendance_status(client):
    """Unsupported attendance status like 'Excused' or 'Unknown' is rejected 400 Bad Request."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Excused",
        },
    )

    assert response.status_code == 400
    assert "Invalid attendance status" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# Duplicate Attendance Handling
# ---------------------------------------------------------------------------

def test_duplicate_attendance_handling(client):
    """Prevent duplicate record (409) unless update_existing=True is passed."""
    login(client, "teacher1", "teacher123")

    # Initial marking
    res1 = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res1.status_code == 201

    # Duplicate without update flag -> 409
    res_dup = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Absent",
        },
    )
    assert res_dup.status_code == 409

    # Duplicate with update_existing=True -> 200 OK update
    res_update = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Absent",
            "update_existing": True,
        },
    )
    assert res_update.status_code == 200
    assert res_update.get_json()["record"]["status"] == "Absent"


# ---------------------------------------------------------------------------
# Unauthorized Access: Unauthenticated & Student Role
# ---------------------------------------------------------------------------

def test_unauthorized_access(client):
    """Unauthenticated users (401) and student accounts (403) cannot mark attendance."""
    payload = {
        "student_id": 4,
        "subject_id": 1,
        "attendance_date": "2026-10-25",
        "status": "Present",
    }

    # Unauthenticated
    res_unauth = client.post("/api/attendance", json=payload)
    assert res_unauth.status_code == 401

    # Student account
    login(client, "student1", "student123")
    res_student = client.post("/api/attendance", json=payload)
    assert res_student.status_code == 403


# ---------------------------------------------------------------------------
# Database Persistence
# ---------------------------------------------------------------------------

def test_database_persistence(client, app):
    """Marked attendance persists to SQLite storage file."""
    login(client, "teacher1", "teacher123")

    res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res.status_code == 201

    with sqlite3.connect(app.config["DATABASE"]) as db:
        row = db.execute(
            "SELECT student_id, subject_id, attendance_date, status FROM attendance WHERE student_id = 4 AND subject_id = 1",
        ).fetchone()

    assert row is not None
    assert row[0] == 4
    assert row[1] == 1
    assert row[2] == "2026-10-25"
    assert row[3] == "Present"


# ---------------------------------------------------------------------------
# Database Failure Handling and Rollback
# ---------------------------------------------------------------------------

def test_batch_rollback_on_failure(client, app):
    """Batch submission with an error causes atomic rollback; zero records saved."""
    login(client, "teacher1", "teacher123")

    # Seed one existing record
    client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )

    # Attempt batch that includes duplicate student 4 without allow_update, plus new students 5 and 6
    batch_payload = {
        "class_id": 1,
        "subject_id": 1,
        "attendance_date": "2026-10-25",
        "update_existing": False,
        "records": [
            {"student_id": 4, "status": "Absent"},  # Duplicate
            {"student_id": 5, "status": "Present"},  # Valid
            {"student_id": 6, "status": "Late"},     # Valid
        ],
    }
    response = client.post("/api/attendance", json=batch_payload)
    assert response.status_code == 409

    # Verify student 5 and 6 were NOT recorded due to atomic rollback
    with sqlite3.connect(app.config["DATABASE"]) as db:
        row5 = db.execute(
            "SELECT id FROM attendance WHERE student_id = 5 AND subject_id = 1 AND attendance_date = '2026-10-25'",
        ).fetchone()
        assert row5 is None

        row6 = db.execute(
            "SELECT id FROM attendance WHERE student_id = 6 AND subject_id = 1 AND attendance_date = '2026-10-25'",
        ).fetchone()
        assert row6 is None
