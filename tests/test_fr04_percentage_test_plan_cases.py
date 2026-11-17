"""FR-04 tests added in Deliverable 3, Phase 2, using the Test Plan's own data.

The existing FR-04 tests use different datasets (2/4, 1/2, 0/1). These tests
reproduce the exact Test Plan scenarios on the percentage API:

* UT_FR-04_01  10 Present / 10 classes          -> 100%
* UT_FR-04_02  5 Present / 10 classes           -> 50%
* UT_FR-04_03  6 Present / 4 Absent             -> 60%
* UT_FR-04_04  8 Present / 2 Late (Late is held, not attended) -> 80%
* UT_FR-04_05  0 records                        -> 0%, no error
* SYS_FR-04_09 2 Present / 3 classes            -> 66.67 (2 decimals),
                and the alerts API reports the same rounded value
* IT_FR-04_06  percentage recalculates after a record is updated
* IT_FR-04_08  percentage over a selected date range (report summary)
"""

import sqlite3
from datetime import date, timedelta

import pytest
from werkzeug.security import generate_password_hash

from app import create_app

PASSWORD = "Admin01Pass!"


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "fr04_phase2.db"
    application = create_app({
        "TESTING": True,
        "DATABASE": str(database),
        "SECRET_KEY": "fr04-phase2-secret",
    })
    with sqlite3.connect(database) as conn:
        pw = generate_password_hash(PASSWORD)
        ids = {}
        for username, role in [("Admin01", "admin"), ("Teacher01", "teacher"), ("S01", "student")]:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (username, pw, role),
            )
            ids[username] = cur.lastrowid
        cur = conn.execute("INSERT INTO classes (name, teacher_id) VALUES ('CSE-A', ?)", (ids["Teacher01"],))
        class_id = cur.lastrowid
        cur = conn.execute("INSERT INTO subjects (name, teacher_id) VALUES ('DBMS', ?)", (ids["Teacher01"],))
        subject_id = cur.lastrowid
        conn.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (class_id, subject_id))
        conn.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (ids["S01"], class_id, subject_id),
        )
        conn.commit()
    application.config["FR04_IDS"] = {**ids, "class": class_id, "subject": subject_id}
    return application


def add_records(app, statuses, start=date(2026, 9, 1)):
    """Insert one record per status on consecutive dates; return the record ids."""
    ids = app.config["FR04_IDS"]
    record_ids = []
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        for offset, status in enumerate(statuses):
            cur = conn.execute(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
                (ids["S01"], ids["subject"], (start + timedelta(days=offset)).isoformat(), status),
            )
            record_ids.append(cur.lastrowid)
        conn.commit()
    return record_ids


def admin_client(app):
    client = app.test_client()
    assert client.post("/api/login", json={"username": "Admin01", "password": PASSWORD}).status_code == 200
    return client


def s01_percentage(client, app):
    response = client.get(f"/api/attendance/percentages?subject_id={app.config['FR04_IDS']['subject']}")
    assert response.status_code == 200
    (row,) = [s for s in response.get_json()["students"] if s["student_name"] == "S01"]
    return row


@pytest.mark.parametrize(
    "case_id, statuses, attended, total, expected",
    [
        ("UT_FR-04_01", ["Present"] * 10, 10, 10, 100.0),
        ("UT_FR-04_02", ["Present"] * 5 + ["Absent"] * 5, 5, 10, 50.0),
        ("UT_FR-04_03", ["Present"] * 6 + ["Absent"] * 4, 6, 10, 60.0),
        ("UT_FR-04_04", ["Present"] * 8 + ["Late"] * 2, 8, 10, 80.0),
        ("UT_FR-04_05", [], 0, 0, 0.0),
        ("SYS_FR-04_09", ["Present", "Present", "Absent"], 2, 3, 66.67),
    ],
)
def test_test_plan_percentage_datasets(app, case_id, statuses, attended, total, expected):
    add_records(app, statuses)
    row = s01_percentage(admin_client(app), app)

    assert row["classes_attended"] == attended, case_id
    assert row["total_classes"] == total, case_id
    assert row["attendance_percentage"] == expected, case_id


def test_sys_fr_04_09_rounding_is_consistent_between_percentage_and_alert_apis(app):
    add_records(app, ["Present", "Present", "Absent"])
    client = admin_client(app)

    from_percentages = s01_percentage(client, app)["attendance_percentage"]

    alerts = client.get(
        f"/api/attendance/alerts?subject_id={app.config['FR04_IDS']['subject']}&threshold=75"
    )
    assert alerts.status_code == 200
    (from_alerts,) = [s for s in alerts.get_json()["students"] if s["student_name"] == "S01"]

    assert from_percentages == 66.67
    assert from_alerts["attendance_percentage"] == 66.67


def test_it_fr_04_06_percentage_recalculates_after_update(app):
    record_ids = add_records(app, ["Present"] * 5 + ["Absent"] * 5)
    client = admin_client(app)
    assert s01_percentage(client, app)["attendance_percentage"] == 50.0

    # Present -> Absent (Test Plan data): 4/10
    first_present = record_ids[0]
    response = client.put(f"/api/attendance/{first_present}", json={"status": "Absent"})
    assert response.status_code == 200
    row = s01_percentage(client, app)
    assert (row["classes_attended"], row["total_classes"], row["attendance_percentage"]) == (4, 10, 40.0)

    # Absent -> Late does not count as attended: still 4/10
    first_absent = record_ids[5]
    assert client.put(f"/api/attendance/{first_absent}", json={"status": "Late"}).status_code == 200
    assert s01_percentage(client, app)["attendance_percentage"] == 40.0

    # Late -> Present: 5/10
    assert client.put(f"/api/attendance/{first_absent}", json={"status": "Present"}).status_code == 200
    assert s01_percentage(client, app)["attendance_percentage"] == 50.0


def test_it_fr_04_08_percentage_for_selected_date_range(app):
    # 2026-09-01 .. 2026-09-04 inside the range: P, P, P, A  -> 75%
    add_records(app, ["Present", "Present", "Present", "Absent"], start=date(2026, 9, 1))
    # 2026-09-11 .. 2026-09-12 outside the range: A, A
    add_records(app, ["Absent", "Absent"], start=date(2026, 9, 11))
    client = admin_client(app)
    student_id = app.config["FR04_IDS"]["S01"]

    in_range = client.get(
        f"/api/reports/attendance?student_id={student_id}&start_date=2026-09-01&end_date=2026-09-10"
    )
    assert in_range.status_code == 200
    data = in_range.get_json()
    assert data["total_records"] == 4
    assert data["present_count"] == 3
    assert data["attendance_percentage"] == 75.0
    assert all("2026-09-01" <= r["attendance_date"] <= "2026-09-10" for r in data["records"])

    # Control: without the range the outside absences count (3/6 = 50%).
    everything = client.get(f"/api/reports/attendance?student_id={student_id}").get_json()
    assert everything["total_records"] == 6
    assert everything["attendance_percentage"] == 50.0
