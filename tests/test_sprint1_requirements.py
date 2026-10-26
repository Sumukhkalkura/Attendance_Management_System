"""Sprint 1 acceptance-test checklist derived from the SRS/Test Plan.

Implement these tests as the corresponding endpoints are completed.
The skip markers are intentional: they must be removed before claiming
that the respective requirement is verified.
"""
import sqlite3
import pytest
from werkzeug.security import generate_password_hash


@pytest.mark.skip(reason='FR-01 pending: valid/invalid/blank login, role restrictions, timeout')
def test_fr01_authentication(client):
    raise NotImplementedError


@pytest.mark.skip(reason='FR-07/08/09 pending: admin user/class/subject/enrollment workflows')
def test_admin_management(client):
    raise NotImplementedError


def test_fr02_attendance_marking(client):
    """FR-02 acceptance test: Present/Absent/Late, date validation, assigned teacher."""
    db_path = client.application.config["DATABASE"]
    with sqlite3.connect(db_path) as db:
        db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
            ("teacher_fr02", generate_password_hash("pass123"), "teacher", 1),
        )
        teacher_id = db.execute("SELECT id FROM users WHERE username = 'teacher_fr02'").fetchone()[0]

        db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
            ("other_teacher", generate_password_hash("pass123"), "teacher", 1),
        )
        other_teacher_id = db.execute("SELECT id FROM users WHERE username = 'other_teacher'").fetchone()[0]

        db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, ?)",
            ("student_fr02", generate_password_hash("pass123"), "student", 1),
        )
        student_id = db.execute("SELECT id FROM users WHERE username = 'student_fr02'").fetchone()[0]

        db.execute("INSERT INTO classes (name) VALUES (?)", ("Class FR02",))
        class_id = db.execute("SELECT id FROM classes WHERE name = 'Class FR02'").fetchone()[0]

        db.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", ("Subject FR02", teacher_id))
        subject_id = db.execute("SELECT id FROM subjects WHERE name = 'Subject FR02'").fetchone()[0]

        db.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", ("Unassigned Subject", other_teacher_id))
        other_subject_id = db.execute("SELECT id FROM subjects WHERE name = 'Unassigned Subject'").fetchone()[0]

        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (student_id, class_id, subject_id),
        )
        db.commit()

    # 1. Login as assigned teacher
    client.post("/api/login", json={"username": "teacher_fr02", "password": "pass123"})

    # 2. Roster check
    roster_res = client.get(f"/api/roster?class_id={class_id}&subject_id={subject_id}")
    assert roster_res.status_code == 200
    assert roster_res.get_json()["count"] == 1

    # 3. Mark Present
    res_pres = client.post(
        "/api/attendance",
        json={"student_id": student_id, "subject_id": subject_id, "attendance_date": "2026-10-25", "status": "Present"},
    )
    assert res_pres.status_code == 201
    assert res_pres.get_json()["record"]["status"] == "Present"

    # 4. Mark Absent (different date)
    res_abs = client.post(
        "/api/attendance",
        json={"student_id": student_id, "subject_id": subject_id, "attendance_date": "2026-10-26", "status": "Absent"},
    )
    assert res_abs.status_code == 201
    assert res_abs.get_json()["record"]["status"] == "Absent"

    # 5. Mark Late (different date)
    res_late = client.post(
        "/api/attendance",
        json={"student_id": student_id, "subject_id": subject_id, "attendance_date": "2026-10-27", "status": "Late"},
    )
    assert res_late.status_code == 201
    assert res_late.get_json()["record"]["status"] == "Late"

    # 6. Date validation: invalid date rejected
    res_bad_date = client.post(
        "/api/attendance",
        json={
            "student_id": student_id,
            "subject_id": subject_id,
            "attendance_date": "invalid-date",
            "status": "Present",
        },
    )
    assert res_bad_date.status_code == 400

    # 7. Assigned teacher restriction: unassigned subject rejected (403)
    res_unassigned = client.post(
        "/api/attendance",
        json={
            "student_id": student_id,
            "subject_id": other_subject_id,
            "attendance_date": "2026-10-28",
            "status": "Present",
        },
    )
    assert res_unassigned.status_code == 403


@pytest.mark.skip(reason='FR-03 pending: update, persistence, duplicate protection, permissions')
def test_fr03_record_management(client):
    raise NotImplementedError


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
