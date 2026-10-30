"""Tests for FR-10: Attendance Search & Filter."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

PASSWORD_HASH = generate_password_hash("pass123")

R1 = ("student_1", "FR10 Math", "2026-10-20")
R2 = ("student_1", "FR10 Math", "2026-10-21")
R3 = ("student_1", "FR10 Physics", "2026-10-20")
R4 = ("student_2", "FR10 Math", "2026-10-20")
R5 = ("student_2", "FR10 Physics", "2026-10-21")
R6 = ("student_3", "FR10 Math", "2026-10-20")
R7 = ("student_1", "FR10 Art", "2026-10-22")


@pytest.fixture
def fr10_data(client):
    """Create classes where enrollment depends on the student and subject.

    student_2 is in 10A for Physics but 10B for Math, student_3 is in both
    classes for Math, and student_1 has an Art record with no enrollment.
    """
    db_path = client.application.config["DATABASE"]

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        users = {}
        for username, role in [
            ("admin_1", "admin"),
            ("teacher_1", "teacher"),
            ("teacher_2", "teacher"),
            ("student_1", "student"),
            ("student_2", "student"),
            ("student_3", "student"),
        ]:
            users[username] = db.execute(
                """
                INSERT INTO users
                    (username, password_hash, role, active)
                VALUES (?, ?, ?, 1)
                """,
                (username, PASSWORD_HASH, role),
            ).lastrowid

        subjects = {}
        for name, teacher in [
            ("FR10 Math", "teacher_1"),
            ("FR10 Art", "teacher_1"),
            ("FR10 Physics", "teacher_2"),
        ]:
            subjects[name] = db.execute(
                "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
                (name, users[teacher]),
            ).lastrowid

        classes = {
            name: db.execute(
                "INSERT INTO classes (name) VALUES (?)", (name,)
            ).lastrowid
            for name in ("FR10 10A", "FR10 10B", "FR10 Empty")
        }

        db.executemany(
            "INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
            [
                (classes["FR10 10A"], subjects["FR10 Math"]),
                (classes["FR10 10A"], subjects["FR10 Physics"]),
                (classes["FR10 10B"], subjects["FR10 Math"]),
            ],
        )

        db.executemany(
            """
            INSERT INTO enrollments (student_id, class_id, subject_id)
            VALUES (?, ?, ?)
            """,
            [
                (users[student], classes[class_name], subjects[subject])
                for student, class_name, subject in [
                    ("student_1", "FR10 10A", "FR10 Math"),
                    ("student_1", "FR10 10A", "FR10 Physics"),
                    ("student_2", "FR10 10B", "FR10 Math"),
                    ("student_2", "FR10 10A", "FR10 Physics"),
                    ("student_3", "FR10 10A", "FR10 Math"),
                    ("student_3", "FR10 10B", "FR10 Math"),
                ]
            ],
        )

        db.executemany(
            """
            INSERT INTO attendance
                (student_id, subject_id, attendance_date, status)
            VALUES (?, ?, ?, ?)
            """,
            [
                (users[student], subjects[subject], date, status)
                for (student, subject, date), status in [
                    (R1, "Present"),
                    (R2, "Absent"),
                    (R3, "Late"),
                    (R4, "Present"),
                    (R5, "Present"),
                    (R6, "Late"),
                    (R7, "Present"),
                ]
            ],
        )

        db.commit()

    return {
        "users": users,
        "subjects": subjects,
        "class_a": classes["FR10 10A"],
        "class_b": classes["FR10 10B"],
        "class_empty": classes["FR10 Empty"],
    }


def login(client, username):
    response = client.post(
        "/api/login",
        json={"username": username, "password": "pass123"},
    )
    assert response.status_code == 200


def search(client, **filters):
    return client.get("/api/attendance", query_string=filters)


def record_keys(response):
    """Return records as a sorted list so duplicates are not hidden."""
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == len(data["records"])
    return sorted(
        (r["student_name"], r["subject_name"], r["attendance_date"])
        for r in data["records"]
    )


# ---------------------------------------------------------------------
# class_id filtering
# ---------------------------------------------------------------------

def test_fr10_filter_by_class_matches_student_and_subject(client, fr10_data):
    login(client, "admin_1")

    class_a = search(client, class_id=fr10_data["class_a"])
    class_b = search(client, class_id=fr10_data["class_b"])

    assert record_keys(class_a) == sorted([R1, R2, R3, R5, R6])
    assert record_keys(class_b) == sorted([R4, R6])


def test_fr10_class_filter_excludes_subject_student_is_not_enrolled_for(
    client, fr10_data
):
    login(client, "admin_1")

    response = search(client, class_id=fr10_data["class_a"])

    assert R4 not in record_keys(response)  # student_2 takes Math in 10B
    assert R7 not in record_keys(response)  # no Art enrollment


def test_fr10_multiple_enrollments_do_not_duplicate_records(client, fr10_data):
    login(client, "admin_1")

    for class_id in (fr10_data["class_a"], fr10_data["class_b"]):
        response = search(
            client,
            class_id=class_id,
            student_id=fr10_data["users"]["student_3"],
        )
        assert record_keys(response) == [R6]


def test_fr10_no_filter_still_returns_unenrolled_records(client, fr10_data):
    login(client, "admin_1")

    assert record_keys(search(client)) == sorted(
        [R1, R2, R3, R4, R5, R6, R7]
    )


def test_fr10_response_format_is_unchanged(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_b"],
        student_id=fr10_data["users"]["student_2"],
    )

    data = response.get_json()
    assert set(data) == {"count", "records"}
    record = data["records"][0]
    assert record == {
        "id": record["id"],
        "attendance_id": record["id"],
        "student_id": fr10_data["users"]["student_2"],
        "student_name": "student_2",
        "subject_id": fr10_data["subjects"]["FR10 Math"],
        "subject_name": "FR10 Math",
        "attendance_date": "2026-10-20",
        "status": "Present",
    }


def test_fr10_results_keep_date_then_student_order(client, fr10_data):
    login(client, "admin_1")

    records = search(client, class_id=fr10_data["class_a"]).get_json()[
        "records"
    ]

    assert [
        (r["attendance_date"], r["student_name"]) for r in records
    ] == [
        ("2026-10-21", "student_1"),
        ("2026-10-21", "student_2"),
        ("2026-10-20", "student_1"),
        ("2026-10-20", "student_1"),
        ("2026-10-20", "student_3"),
    ]


# ---------------------------------------------------------------------
# Combined filters
# ---------------------------------------------------------------------

def test_fr10_class_and_subject(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        subject_id=fr10_data["subjects"]["FR10 Physics"],
    )

    assert record_keys(response) == sorted([R3, R5])


def test_fr10_class_and_student(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        student_id=fr10_data["users"]["student_2"],
    )

    assert record_keys(response) == [R5]


def test_fr10_class_and_date(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        attendance_date="2026-10-20",
    )

    assert record_keys(response) == sorted([R1, R3, R6])


def test_fr10_class_and_date_range(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        start_date="2026-10-21",
        end_date="2026-10-22",
    )

    assert record_keys(response) == sorted([R2, R5])


def test_fr10_class_and_status(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client, class_id=fr10_data["class_a"], status="Late"
    )

    assert record_keys(response) == sorted([R3, R6])


def test_fr10_all_filters_combined(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        student_id=fr10_data["users"]["student_1"],
        subject_id=fr10_data["subjects"]["FR10 Math"],
        start_date="2026-10-20",
        end_date="2026-10-21",
        status="Absent",
    )

    assert record_keys(response) == [R2]


def test_fr10_filters_without_class_still_work(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        student_id=fr10_data["users"]["student_1"],
        subject_id=fr10_data["subjects"]["FR10 Math"],
        attendance_date="2026-10-21",
    )

    assert record_keys(response) == [R2]


# ---------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------

def test_fr10_class_without_enrollments_returns_empty(client, fr10_data):
    login(client, "admin_1")

    response = search(client, class_id=fr10_data["class_empty"])

    assert response.status_code == 200
    assert response.get_json() == {"count": 0, "records": []}


@pytest.mark.parametrize(
    "filters",
    [
        {"attendance_date": "2030-01-01"},
        {"status": "Absent", "student_id_key": "student_2"},
    ],
)
def test_fr10_filters_excluding_all_class_records_return_empty(
    client, fr10_data, filters
):
    login(client, "admin_1")

    filters = dict(filters)
    student = filters.pop("student_id_key", None)
    if student:
        filters["student_id"] = fr10_data["users"][student]

    response = search(client, class_id=fr10_data["class_b"], **filters)

    assert response.status_code == 200
    assert response.get_json() == {"count": 0, "records": []}


def test_fr10_student_not_in_class_returns_empty(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_b"],
        student_id=fr10_data["users"]["student_1"],
    )

    assert record_keys(response) == []


def test_fr10_subject_not_in_class_returns_empty(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client,
        class_id=fr10_data["class_b"],
        subject_id=fr10_data["subjects"]["FR10 Physics"],
    )

    assert record_keys(response) == []


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "",
        "0",
        "-1",
        "1.5",
        "1 OR 1=1",
        str(2 ** 63),
        "9" * 40,
    ],
)
def test_fr10_invalid_class_id_returns_400(client, fr10_data, value):
    login(client, "admin_1")

    response = search(client, class_id=value)

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "class_id must be a positive integer"
    }


@pytest.mark.parametrize("username", ["admin_1", "teacher_1", "student_1"])
def test_fr10_nonexistent_class_returns_404(client, fr10_data, username):
    login(client, username)

    response = search(client, class_id=999999)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Class not found"}


def test_fr10_largest_sqlite_integer_is_handled_as_missing_class(
    client, fr10_data
):
    login(client, "admin_1")

    assert search(client, class_id=2 ** 63 - 1).status_code == 404


def test_fr10_invalid_filter_alongside_class_returns_400(client, fr10_data):
    login(client, "admin_1")

    class_id = fr10_data["class_a"]

    assert search(
        client, class_id=class_id, attendance_date="nope"
    ).status_code == 400
    assert search(
        client, class_id=class_id, subject_id="nope"
    ).status_code == 400
    assert search(
        client,
        class_id=class_id,
        start_date="2026-10-22",
        end_date="2026-10-20",
    ).status_code == 400


def test_fr10_nonexistent_subject_with_class_returns_404(client, fr10_data):
    login(client, "admin_1")

    response = search(
        client, class_id=fr10_data["class_a"], subject_id=999999
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Subject not found"}


# ---------------------------------------------------------------------
# Role-based access
# ---------------------------------------------------------------------

def test_fr10_filter_requires_authentication(client, fr10_data):
    response = search(client, class_id=fr10_data["class_a"])

    assert response.status_code == 401


def test_fr10_teacher_class_filter_limited_to_assigned_subjects(
    client, fr10_data
):
    login(client, "teacher_1")

    response = search(client, class_id=fr10_data["class_a"])

    assert record_keys(response) == sorted([R1, R2, R6])


def test_fr10_teacher_with_no_subjects_in_class_gets_empty_results(
    client, fr10_data
):
    login(client, "teacher_2")

    response = search(client, class_id=fr10_data["class_b"])

    assert record_keys(response) == []


def test_fr10_teacher_cannot_use_class_to_reach_other_subject(
    client, fr10_data
):
    login(client, "teacher_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        subject_id=fr10_data["subjects"]["FR10 Physics"],
    )

    assert response.status_code == 403


def test_fr10_teacher_filtering_by_student_stays_within_own_subjects(
    client, fr10_data
):
    login(client, "teacher_2")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        student_id=fr10_data["users"]["student_1"],
    )

    assert record_keys(response) == [R3]


def test_fr10_student_class_filter_returns_only_own_records(
    client, fr10_data
):
    login(client, "student_2")

    assert record_keys(
        search(client, class_id=fr10_data["class_a"])
    ) == [R5]
    assert record_keys(
        search(client, class_id=fr10_data["class_b"])
    ) == [R4]


def test_fr10_student_gets_empty_results_for_class_they_are_not_in(
    client, fr10_data
):
    login(client, "student_1")

    response = search(client, class_id=fr10_data["class_b"])

    assert record_keys(response) == []


def test_fr10_student_cannot_use_class_to_view_other_student(
    client, fr10_data
):
    login(client, "student_1")

    response = search(
        client,
        class_id=fr10_data["class_a"],
        student_id=fr10_data["users"]["student_2"],
    )

    assert response.status_code == 403


def test_fr10_access_denial_precedes_class_lookup(client, fr10_data):
    login(client, "student_1")

    response = search(
        client,
        class_id=999999,
        student_id=fr10_data["users"]["student_2"],
    )

    assert response.status_code == 403
