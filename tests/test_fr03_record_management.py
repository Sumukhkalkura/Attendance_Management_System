"""Comprehensive test suite for FR-03: Attendance Record Management.

Covers all 10 Test Plan cases:
- UT_FR-03_01: Save new attendance record
- UT_FR-03_02: Update existing attendance record
- UT_FR-03_03: Prevent duplicate record
- UT_FR-03_04: Missing student validation
- UT_FR-03_05: Missing subject validation
- IT_FR-03_06: Database persistence across connection reload
- IT_FR-03_07: Student update restriction
- IT_FR-03_08: Teacher authorization
- SYS_FR-03_09: Refresh after save
- SYS_FR-03_10: Database atomic rollback / failure handling

Additional test cases:
- Idempotent upsert via PUT /api/attendance
- Record deletion via DELETE /api/attendance/<id>
- Retrieval filters and student privacy via GET /api/attendance
- Input format and calendar validation
- Teacher helper endpoints (/api/teacher/classes, /api/teacher/subjects, /api/roster)
- Strict enrollment validation (unenrolled student rejection and zero enrollment rejection)
"""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash
from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated test application with standard seeded entities."""
    database_path = tmp_path / "fr03_test.db"

    application = create_app({
        "TESTING": True,
        "DATABASE": str(database_path),
        "SECRET_KEY": "fr03-test-secret-key",
    })

    with sqlite3.connect(database_path) as db:
        # Users
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

        # Classes
        db.execute("INSERT INTO classes (name) VALUES (?)", ("Class 10-A",))
        db.execute("INSERT INTO classes (name) VALUES (?)", ("Class Empty",))

        # Subjects
        # teacher1 (id 2) teaches Mathematics (id 1)
        # teacher2 (id 3) teaches Science (id 2)
        db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Mathematics", 2),
        )
        db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Science", 3),
        )

        # Enrollments
        # student1 (id 4) and student2 (id 5) in Class 10-A (id 1) for Math (id 1)
        # student1 (id 4) in Class 10-A (id 1) for Science (id 2)
        # student3 (id 6) is not enrolled in Class 10-A
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (4, 1, 1),
        )
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (5, 1, 1),
        )
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (4, 1, 2),
        )
        db.commit()

    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password="teacher123"):
    """Helper to authenticate a user."""
    return client.post(
        "/api/login",
        json={"username": username, "password": password},
    )


# ---------------------------------------------------------------------------
# UT_FR-03_01: Save new attendance record
# ---------------------------------------------------------------------------

def test_ut_fr_03_01_save_new_record(client):
    """Teacher marks attendance for an enrolled student -> 201 Created."""
    login_res = login(client, "teacher1", "teacher123")
    assert login_res.status_code == 200

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Attendance recorded successfully"
    assert "record" in data
    assert data["record"]["student_id"] == 4
    assert data["record"]["subject_id"] == 1
    assert data["record"]["attendance_date"] == "2026-10-25"
    assert data["record"]["status"] == "Present"
    assert data["record"]["id"] > 0


# ---------------------------------------------------------------------------
# UT_FR-03_02: Update existing attendance record
# ---------------------------------------------------------------------------

def test_ut_fr_03_02_update_existing_record_by_id(client):
    """Teacher updates an existing attendance record by ID -> 200 OK."""
    login(client, "teacher1", "teacher123")

    # Create initial record
    post_res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert post_res.status_code == 201
    record_id = post_res.get_json()["record"]["id"]

    # Update status to Absent
    put_res = client.put(
        f"/api/attendance/{record_id}",
        json={"status": "Absent"},
    )
    assert put_res.status_code == 200
    updated = put_res.get_json()
    assert updated["message"] == "Attendance record updated successfully"
    assert updated["record"]["status"] == "Absent"

    # Verify retrieval reflects update
    get_res = client.get(f"/api/attendance/{record_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["record"]["status"] == "Absent"


# ---------------------------------------------------------------------------
# UT_FR-03_03: Prevent duplicate record
# ---------------------------------------------------------------------------

def test_ut_fr_03_03_prevent_duplicate_record(client):
    """Duplicate attendance for same student, subject, date returns 409 Conflict."""
    login(client, "teacher1", "teacher123")

    first_res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert first_res.status_code == 201

    # Attempt duplicate submission without update_existing
    second_res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Absent",
        },
    )
    assert second_res.status_code == 409
    assert "already exists" in second_res.get_json()["error"]

    # Verify original record unchanged
    get_res = client.get("/api/attendance?student_id=4&subject_id=1&date=2026-10-25")
    assert get_res.status_code == 200
    records = get_res.get_json()["records"]
    assert len(records) == 1
    assert records[0]["status"] == "Present"


# ---------------------------------------------------------------------------
# UT_FR-03_04: Missing student validation
# ---------------------------------------------------------------------------

def test_ut_fr_03_04_missing_student_validation(client):
    """Reject missing student_id, nonexistent student, or non-student user."""
    login(client, "teacher1", "teacher123")

    # Missing student_id
    res_missing = client.post(
        "/api/attendance",
        json={
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_missing.status_code == 400

    # Nonexistent student_id
    res_nonexistent = client.post(
        "/api/attendance",
        json={
            "student_id": 9999,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_nonexistent.status_code == 404
    assert "Student not found" in res_nonexistent.get_json()["error"]

    # Referenced user is a teacher, not a student
    res_not_student = client.post(
        "/api/attendance",
        json={
            "student_id": 2,  # teacher1's user id
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_not_student.status_code == 400
    assert "not a student" in res_not_student.get_json()["error"]


# ---------------------------------------------------------------------------
# UT_FR-03_05: Missing subject validation
# ---------------------------------------------------------------------------

def test_ut_fr_03_05_missing_subject_validation(client):
    """Reject missing subject_id or nonexistent subject."""
    login(client, "teacher1", "teacher123")

    # Missing subject_id
    res_missing = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_missing.status_code == 400

    # Nonexistent subject_id
    res_nonexistent = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 9999,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_nonexistent.status_code == 404
    assert "Subject not found" in res_nonexistent.get_json()["error"]


# ---------------------------------------------------------------------------
# IT_FR-03_06: Database persistence across connection reload
# ---------------------------------------------------------------------------

def test_it_fr_03_06_database_persistence_across_connection_reload(client, app):
    """Saved record persists in database file when inspected via fresh connection."""
    login(client, "teacher1", "teacher123")

    response = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Late",
        },
    )
    assert response.status_code == 201
    created_id = response.get_json()["record"]["id"]

    # Open a direct, fresh SQLite connection to verify disk persistence
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT student_id, subject_id, attendance_date, status FROM attendance WHERE id = ?",
            (created_id,),
        ).fetchone()

    assert row is not None
    assert row["student_id"] == 4
    assert row["subject_id"] == 1
    assert row["attendance_date"] == "2026-10-25"
    assert row["status"] == "Late"

    # Verify a new test client also reads the persisted record
    fresh_client = app.test_client()
    login(fresh_client, "teacher1", "teacher123")
    get_res = fresh_client.get(f"/api/attendance/{created_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["record"]["status"] == "Late"


# ---------------------------------------------------------------------------
# IT_FR-03_07: Student update restriction
# ---------------------------------------------------------------------------

def test_it_fr_03_07_student_update_restriction(client):
    """Students are strictly forbidden from creating, updating, or deleting attendance."""
    # Seed record as teacher
    login(client, "teacher1", "teacher123")
    res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Absent",
        },
    )
    assert res.status_code == 201
    record_id = res.get_json()["record"]["id"]

    # Login as student
    login(client, "student1", "student123")

    # POST rejected (403)
    res_post = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-26",
            "status": "Present",
        },
    )
    assert res_post.status_code == 403

    # PUT by ID rejected (403)
    res_put = client.put(
        f"/api/attendance/{record_id}",
        json={"status": "Present"},
    )
    assert res_put.status_code == 403

    # PATCH by ID rejected (403)
    res_patch = client.patch(
        f"/api/attendance/{record_id}",
        json={"status": "Present"},
    )
    assert res_patch.status_code == 403

    # PUT by key rejected (403)
    res_put_key = client.put(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_put_key.status_code == 403

    # DELETE rejected (403)
    res_del = client.delete(f"/api/attendance/{record_id}")
    assert res_del.status_code == 403


# ---------------------------------------------------------------------------
# IT_FR-03_08: Teacher authorization
# ---------------------------------------------------------------------------

def test_it_fr_03_08_teacher_authorization(client):
    """Teachers can only manage attendance for subjects assigned to them."""
    # teacher1 is assigned to Math (id 1)
    # teacher2 is assigned to Science (id 2)

    login(client, "teacher1", "teacher123")

    # teacher1 attempts to record attendance for Science (id 2) -> 403 Forbidden
    res_unassigned = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 2,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_unassigned.status_code == 403
    assert "not assigned" in res_unassigned.get_json()["error"]

    # teacher2 successfully records attendance for Science (id 2) -> 201 Created
    login(client, "teacher2", "teacher123")
    res_assigned = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 2,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert res_assigned.status_code == 201
    science_record_id = res_assigned.get_json()["record"]["id"]

    # teacher1 attempts to update teacher2's science record -> 403 Forbidden
    login(client, "teacher1", "teacher123")
    res_update_denied = client.put(
        f"/api/attendance/{science_record_id}",
        json={"status": "Absent"},
    )
    assert res_update_denied.status_code == 403

    # teacher1 attempts to delete teacher2's science record -> 403 Forbidden
    res_del_denied = client.delete(f"/api/attendance/{science_record_id}")
    assert res_del_denied.status_code == 403

    # Admin can manage any subject
    login(client, "admin1", "admin123")
    res_admin_update = client.put(
        f"/api/attendance/{science_record_id}",
        json={"status": "Late"},
    )
    assert res_admin_update.status_code == 200
    assert res_admin_update.get_json()["record"]["status"] == "Late"


# ---------------------------------------------------------------------------
# SYS_FR-03_09: Refresh after save
# ---------------------------------------------------------------------------

def test_sys_fr_03_09_refresh_after_save(client):
    """Repeated queries after saving return consistent, single record without phantom rows."""
    login(client, "teacher1", "teacher123")

    save_res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Present",
        },
    )
    assert save_res.status_code == 201

    # Simulate UI refresh 1
    get_res1 = client.get(
        "/api/attendance?student_id=4&subject_id=1&date=2026-10-25"
    )
    assert get_res1.status_code == 200
    data1 = get_res1.get_json()
    assert data1["count"] == 1
    assert len(data1["records"]) == 1

    # Simulate UI refresh 2
    get_res2 = client.get(
        "/api/attendance?student_id=4&subject_id=1&date=2026-10-25"
    )
    assert get_res2.status_code == 200
    data2 = get_res2.get_json()
    assert data2["count"] == 1
    assert data1["records"][0]["id"] == data2["records"][0]["id"]


# ---------------------------------------------------------------------------
# SYS_FR-03_10: Database atomic failure handling
# ---------------------------------------------------------------------------

def test_sys_fr_03_10_database_atomic_rollback(client, app):
    """Database rolls back cleanly on error with zero partial writes."""
    login(client, "teacher1", "teacher123")

    # Seed one valid record
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

    # Attempt a batch save containing one valid record and one invalid (already exists duplicate)
    batch_res = client.post(
        "/api/attendance",
        json={
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "update_existing": False,
            "records": [
                {"student_id": 4, "status": "Absent"},  # Duplicate!
                {"student_id": 5, "status": "Present"},  # Valid student2
            ],
        },
    )
    # The batch should fail with 409 Conflict
    assert batch_res.status_code == 409

    # Verify student2's attendance was NOT created (atomic transaction)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        row = db.execute(
            "SELECT id FROM attendance WHERE student_id = 5 AND subject_id = 1 AND attendance_date = '2026-10-25'"
        ).fetchone()
        assert row is None


# ---------------------------------------------------------------------------
# Idempotent Upsert via PUT /api/attendance
# ---------------------------------------------------------------------------

def test_fr03_idempotent_upsert_by_key(client):
    """PUT /api/attendance creates record if absent (201) and updates if present (200)."""
    login(client, "teacher1", "teacher123")

    # Record does not exist yet -> should create with 201
    put_create = client.put(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-27",
            "status": "Present",
        },
    )
    assert put_create.status_code == 201
    data_create = put_create.get_json()
    assert data_create["message"] == "Attendance recorded successfully"
    assert data_create["record"]["status"] == "Present"
    record_id = data_create["record"]["id"]

    # Record exists -> should update with 200
    put_update = client.put(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-27",
            "status": "Late",
        },
    )
    assert put_update.status_code == 200
    data_update = put_update.get_json()
    assert data_update["message"] == "Attendance record updated successfully"
    assert data_update["record"]["id"] == record_id
    assert data_update["record"]["status"] == "Late"


# ---------------------------------------------------------------------------
# Record Deletion via DELETE /api/attendance/<id>
# ---------------------------------------------------------------------------

def test_fr03_record_deletion(client):
    """Teacher deletes an attendance record -> 200 OK, followed by 404 on subsequent access."""
    login(client, "teacher1", "teacher123")

    create_res = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-28",
            "status": "Present",
        },
    )
    assert create_res.status_code == 201
    rec_id = create_res.get_json()["record"]["id"]

    # Delete record
    del_res = client.delete(f"/api/attendance/{rec_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["message"] == "Attendance record deleted successfully"

    # Attempting to fetch deleted record returns 404
    get_res = client.get(f"/api/attendance/{rec_id}")
    assert get_res.status_code == 404

    # Deleting again returns 404
    del_again = client.delete(f"/api/attendance/{rec_id}")
    assert del_again.status_code == 404


# ---------------------------------------------------------------------------
# Query Filters & Student Privacy
# ---------------------------------------------------------------------------

def test_fr03_query_filters_and_student_privacy(client):
    """Verify filters on GET /api/attendance and student privacy enforcement."""
    login(client, "teacher1", "teacher123")

    # Create records for student1 and student2
    client.post(
        "/api/attendance",
        json={"student_id": 4, "subject_id": 1, "attendance_date": "2026-10-25", "status": "Present"},
    )
    client.post(
        "/api/attendance",
        json={"student_id": 5, "subject_id": 1, "attendance_date": "2026-10-25", "status": "Absent"},
    )
    client.post(
        "/api/attendance",
        json={"student_id": 4, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Late"},
    )

    # Filter by date
    res_date = client.get("/api/attendance?attendance_date=2026-10-25")
    assert res_date.status_code == 200
    assert len(res_date.get_json()["records"]) == 2

    # Filter by status
    res_status = client.get("/api/attendance?status=Late")
    assert res_status.status_code == 200
    assert len(res_status.get_json()["records"]) == 1
    assert res_status.get_json()["records"][0]["status"] == "Late"

    # Filter by class_id
    res_class = client.get("/api/attendance?class_id=1")
    assert res_class.status_code == 200
    assert len(res_class.get_json()["records"]) == 3

    # Student logs in
    login(client, "student1", "student123")

    # Student sees only their own attendance
    res_student = client.get("/api/attendance")
    assert res_student.status_code == 200
    for r in res_student.get_json()["records"]:
        assert r["student_id"] == 4

    # Student attempting to query another student's attendance gets 403
    res_privacy = client.get("/api/attendance?student_id=5")
    assert res_privacy.status_code == 403
    assert "students can only view their own attendance" in res_privacy.get_json()["error"]


# ---------------------------------------------------------------------------
# Status and Date Validation
# ---------------------------------------------------------------------------

def test_fr03_status_and_date_validation(client):
    """Invalid status values or dates are rejected with 400 Bad Request."""
    login(client, "teacher1", "teacher123")

    # Invalid status
    res_bad_status = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-10-25",
            "status": "Excused",
        },
    )
    assert res_bad_status.status_code == 400
    assert "Invalid attendance status" in res_bad_status.get_json()["error"]

    # Invalid date format
    res_bad_format = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "25-10-2026",
            "status": "Present",
        },
    )
    assert res_bad_format.status_code == 400
    assert "Invalid attendance_date format" in res_bad_format.get_json()["error"]

    # Invalid calendar date (Feb 31)
    res_bad_cal = client.post(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "attendance_date": "2026-02-31",
            "status": "Present",
        },
    )
    assert res_bad_cal.status_code == 400
    assert "Invalid attendance_date format" in res_bad_cal.get_json()["error"]


# ---------------------------------------------------------------------------
# Strict Enrollment Validation (Unenrolled & Zero Enrollment Checks)
# ---------------------------------------------------------------------------

def test_fr03_strict_enrollment_validation(client):
    """Enrollment is strictly verified when class_id is supplied on upsert and update."""
    login(client, "teacher1", "teacher123")

    # 1. student3 (id 6) is NOT enrolled in Class 10-A (id 1) for Math (id 1)
    res_unenrolled_upsert = client.put(
        "/api/attendance",
        json={
            "student_id": 6,
            "subject_id": 1,
            "class_id": 1,
            "attendance_date": "2026-10-29",
            "status": "Present",
        },
    )
    assert res_unenrolled_upsert.status_code == 400
    assert "not enrolled" in res_unenrolled_upsert.get_json()["error"].lower()

    # 2. Class Empty (id 2) has ZERO enrollments -> must be rejected with 400
    res_zero_enrollments = client.put(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "class_id": 2,
            "attendance_date": "2026-10-29",
            "status": "Present",
        },
    )
    assert res_zero_enrollments.status_code == 400
    assert "not enrolled" in res_zero_enrollments.get_json()["error"].lower()

    # 3. Valid enrolled student passes with class_id
    res_enrolled_upsert = client.put(
        "/api/attendance",
        json={
            "student_id": 4,
            "subject_id": 1,
            "class_id": 1,
            "attendance_date": "2026-10-29",
            "status": "Present",
        },
    )
    assert res_enrolled_upsert.status_code == 201
    rec_id = res_enrolled_upsert.get_json()["record"]["id"]

    # 4. Update with unenrolled class_id rejected with 400
    res_update_unenrolled = client.put(
        f"/api/attendance/{rec_id}",
        json={"class_id": 2, "status": "Absent"},
    )
    assert res_update_unenrolled.status_code == 400
    assert "not enrolled" in res_update_unenrolled.get_json()["error"].lower()


# ---------------------------------------------------------------------------
# Teacher Helper Routes: /api/teacher/classes, /api/teacher/subjects, /api/roster
# ---------------------------------------------------------------------------

def test_fr03_teacher_helper_routes(client):
    """Verify teacher helper endpoints for class roster and assigned subjects."""
    login(client, "teacher1", "teacher123")

    # Classes assigned to teacher1
    res_classes = client.get("/api/teacher/classes")
    assert res_classes.status_code == 200
    classes = res_classes.get_json()["classes"]
    assert len(classes) >= 1
    assert classes[0]["name"] == "Class 10-A"

    # Subjects assigned to teacher1
    res_subjects = client.get("/api/teacher/subjects")
    assert res_subjects.status_code == 200
    subjects = res_subjects.get_json()["subjects"]
    assert len(subjects) == 1
    assert subjects[0]["name"] == "Mathematics"

    # Roster for Class 10-A and Mathematics
    res_roster = client.get("/api/roster?class_id=1&subject_id=1")
    assert res_roster.status_code == 200
    roster_data = res_roster.get_json()
    assert roster_data["class_name"] == "Class 10-A"
    assert roster_data["subject_name"] == "Mathematics"
    assert roster_data["count"] == 2
    student_usernames = [s["username"] for s in roster_data["students"]]
    assert "student1" in student_usernames
    assert "student2" in student_usernames
