"""Sprint 1 acceptance-test checklist derived from the SRS/Test Plan.

Implement these tests as the corresponding endpoints are completed.
The skip markers are intentional: they must be removed before claiming
that the respective requirement is verified.
"""
import pytest

@pytest.mark.skip(reason='FR-01 pending: valid/invalid/blank login, role restrictions, timeout')
def test_fr01_authentication(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-07/08/09 pending: admin user/class/subject/enrollment workflows')
def test_admin_management(client):
    raise NotImplementedError

def test_fr02_attendance_marking(client):
    """FR-02 Acceptance: Present/Absent/Late, date validation, assigned teacher, duplicate prevention."""
    import sqlite3
    from werkzeug.security import generate_password_hash

    # Seed test entities in client database
    db_path = client.application.config['DATABASE']
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (1, "teacher1", generate_password_hash("teacher123"), "teacher", 1)
        )
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (2, "teacher2", generate_password_hash("teacher123"), "teacher", 1)
        )
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (3, "student1", generate_password_hash("student123"), "student", 1)
        )
        db.execute("INSERT INTO classes (id, name) VALUES (1, 'Class 1')")
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (1, 'Mathematics', 1)")
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (2, 'Physics', 2)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (3, 1, 1)")
        db.commit()

    # 1. Unauthenticated request rejected
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Present"
    })
    assert res.status_code == 401

    # 2. Login as student -> cannot mark attendance
    client.post("/api/login", json={"username": "student1", "password": "student123"})
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Present"
    })
    assert res.status_code == 403

    # 3. Login as teacher2 (unassigned to Mathematics) -> rejected
    client.post("/api/login", json={"username": "teacher2", "password": "teacher123"})
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Present"
    })
    assert res.status_code == 403

    # 4. Login as assigned teacher1
    client.post("/api/login", json={"username": "teacher1", "password": "teacher123"})

    # Date validation: invalid date rejected
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "invalid-date", "status": "Present"
    })
    assert res.status_code == 400

    # Status validation: invalid status rejected
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Unknown"
    })
    assert res.status_code == 400

    # Successful attendance marking (Present)
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Present"
    })
    assert res.status_code == 201
    assert res.get_json()["record"]["status"] == "Present"

    # Duplicate attendance prevention
    res = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-26", "status": "Absent"
    })
    assert res.status_code == 409

    # Additional dates and statuses (Absent, Late)
    res_absent = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-27", "status": "Absent"
    })
    assert res_absent.status_code == 201
    assert res_absent.get_json()["record"]["status"] == "Absent"

    res_late = client.post("/api/attendance", json={
        "student_id": 3, "subject_id": 1, "attendance_date": "2026-10-28", "status": "Late"
    })
    assert res_late.status_code == 201
    assert res_late.get_json()["record"]["status"] == "Late"

    # Verify persistence in SQLite
    with sqlite3.connect(db_path) as db:
        count = db.execute("SELECT COUNT(*) FROM attendance WHERE student_id = 3").fetchone()[0]
        assert count == 3


def test_fr03_record_management(client):
    """FR-03 Acceptance: retrieval, update, persistence, duplicate protection, permissions."""
    import sqlite3
    from werkzeug.security import generate_password_hash

    db_path = client.application.config['DATABASE']
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (1, "teacher1", generate_password_hash("teacher123"), "teacher", 1)
        )
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (2, "teacher2", generate_password_hash("teacher123"), "teacher", 1)
        )
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (3, "student1", generate_password_hash("student123"), "student", 1)
        )
        db.execute(
            "INSERT INTO users (id, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
            (4, "student2", generate_password_hash("student123"), "student", 1)
        )
        db.execute("INSERT INTO classes (id, name) VALUES (1, 'Class 1')")
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (1, 'Mathematics', 1)")
        db.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (2, 'Physics', 2)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (3, 1, 1)")
        db.execute("INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (4, 1, 1)")

        # Existing attendance records
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (1, 3, 1, '2026-10-24', 'Present')")
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (2, 3, 1, '2026-10-25', 'Absent')")
        db.execute("INSERT INTO attendance (id, student_id, subject_id, attendance_date, status) VALUES (3, 4, 1, '2026-10-24', 'Late')")
        db.commit()

    # 1. Retrieval by authorized teacher
    client.post("/api/login", json={"username": "teacher1", "password": "teacher123"})
    res = client.get("/api/attendance")
    assert res.status_code == 200
    assert res.get_json()["count"] == 3

    # Filter by student
    res_student = client.get("/api/attendance?student_id=3")
    assert res_student.status_code == 200
    assert res_student.get_json()["count"] == 2

    # Filter by date
    res_date = client.get("/api/attendance?date=2026-10-24")
    assert res_date.status_code == 200
    assert res_date.get_json()["count"] == 2

    # Retrieve single record by ID
    res_single = client.get("/api/attendance/1")
    assert res_single.status_code == 200
    assert res_single.get_json()["record"]["id"] == 1

    # 2. Update record
    res_up = client.put("/api/attendance/1", json={"status": "Late"})
    assert res_up.status_code == 200
    assert res_up.get_json()["record"]["status"] == "Late"

    # Verify update persisted
    with sqlite3.connect(db_path) as db:
        status = db.execute("SELECT status FROM attendance WHERE id = 1").fetchone()[0]
        assert status == "Late"

    # 3. Duplicate protection during update
    res_dup = client.put("/api/attendance/1", json={"attendance_date": "2026-10-25"})
    assert res_dup.status_code == 409

    # 4. Unauthorized users cannot update
    client.post("/api/login", json={"username": "student1", "password": "student123"})
    res_no_auth = client.put("/api/attendance/1", json={"status": "Present"})
    assert res_no_auth.status_code == 403

    client.post("/api/login", json={"username": "teacher2", "password": "teacher123"})
    res_unassigned = client.put("/api/attendance/1", json={"status": "Present"})
    assert res_unassigned.status_code == 403

    # 5. Delete record
    client.post("/api/login", json={"username": "teacher1", "password": "teacher123"})
    res_del = client.delete("/api/attendance/1")
    assert res_del.status_code == 200

    # Verify deletion in SQLite
    with sqlite3.connect(db_path) as db:
        deleted = db.execute("SELECT * FROM attendance WHERE id = 1").fetchone()
        assert deleted is None

@pytest.mark.skip(reason='FR-04 pending: 100%, 50%, zero records, late policy, filters')
def test_fr04_percentages(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-05 pending: student/teacher scopes, filters, empty results')
def test_fr05_viewing(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-15 pending: logout revokes access')
def test_fr15_logout(client):
    raise NotImplementedError

@pytest.mark.skip(reason='NFR-01 pending: permissions, session protection, HTTPS deployment')
def test_nfr01_security(client):
    raise NotImplementedError

@pytest.mark.skip(reason='NFR-03 pending: backup creation, restore, failure recovery')
def test_nfr03_reliability(client):
    raise NotImplementedError
