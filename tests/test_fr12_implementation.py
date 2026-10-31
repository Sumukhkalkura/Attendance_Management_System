"""Automated tests for FR-12: Report Export.

Covers:
- Acceptance Criteria from SRS & Issue #12:
  1. Authorized users can export a generated attendance report.
  2. The exported file uses a supported format (CSV, PDF, JSON).
  3. The exported report contains the correct attendance data matching the on-screen report.
- Role-Based Access Control (RBAC):
  - Unauthenticated requests return 401 Unauthorized.
  - Administrator can export across all scopes (student, class, subject, date range, all).
  - Teacher can export for their assigned subjects/classes, but is rejected with 403 on unassigned subjects.
  - Student can export their own attendance records, but is rejected with 403 on other students' data.
- Format validations:
  - CSV format: text/csv Content-Type, Content-Disposition header, valid CSV structure.
  - PDF format: application/pdf Content-Type, Content-Disposition header, valid PDF 1.4 binary structure.
  - JSON format: application/json Content-Type, Content-Disposition header.
  - Unsupported format returns 400 Bad Request with supported formats listed.
- Filter Scoping:
  - Student filter, class filter, subject filter, date range filter, status filter, combined filters.
- Input validation:
  - Invalid date format returns 400.
  - start_date > end_date returns 400.
  - Invalid or non-positive IDs return 400.
  - Non-existent IDs return 404.
  - Invalid status filter returns 400.
- Empty report handling:
  - Generates valid file with 0 records and accurate summary.
- Multi-page PDF generation:
  - Large record set paginated cleanly with valid xrefs and page counts.
- Database consistency:
  - Updated attendance records are immediately reflected in export.
"""

import csv
import io
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

try:
    import pypdf
except ImportError:
    pypdf = None


@pytest.fixture
def fr12_setup(client):
    """Seed test database with users, classes, subjects, enrollments, and attendance."""
    app = client.application
    db_path = app.config["DATABASE"]

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        # 1. Users
        users = [
            ("admin_fr12", "admin"),
            ("teacher1_fr12", "teacher"),
            ("teacher2_fr12", "teacher"),
            ("student1_fr12", "student"),
            ("student2_fr12", "student"),
            ("student3_fr12", "student"),
        ]
        user_ids = {}
        for username, role in users:
            cur = db.execute(
                "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
                (username, generate_password_hash("pass123"), role),
            )
            user_ids[username] = cur.lastrowid

        # 2. Classes
        cur = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            ("Class 10-A", user_ids["teacher1_fr12"]),
        )
        class_10a_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            ("Class 10-B", user_ids["teacher2_fr12"]),
        )
        class_10b_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO classes (name) VALUES (?)",
            ("Class Empty",),
        )
        class_empty_id = cur.lastrowid

        # 3. Subjects
        cur = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Mathematics", user_ids["teacher1_fr12"]),
        )
        math_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Physics", user_ids["teacher2_fr12"]),
        )
        physics_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            ("Chemistry", user_ids["teacher1_fr12"]),
        )
        chemistry_id = cur.lastrowid

        # 4. Class Subjects
        db.execute(
            "INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
            (class_10a_id, math_id),
        )
        db.execute(
            "INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
            (class_10a_id, chemistry_id),
        )
        db.execute(
            "INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
            (class_10b_id, physics_id),
        )

        # 5. Enrollments
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (user_ids["student1_fr12"], class_10a_id, math_id),
        )
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (user_ids["student1_fr12"], class_10a_id, chemistry_id),
        )
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (user_ids["student2_fr12"], class_10a_id, math_id),
        )
        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (user_ids["student3_fr12"], class_10b_id, physics_id),
        )

        # 6. Attendance records
        records = [
            (user_ids["student1_fr12"], math_id, "2026-10-10", "Present"),
            (user_ids["student1_fr12"], math_id, "2026-10-15", "Absent"),
            (user_ids["student1_fr12"], math_id, "2026-10-20", "Late"),
            (user_ids["student1_fr12"], math_id, "2026-10-25", "Present"),
            (user_ids["student1_fr12"], chemistry_id, "2026-10-12", "Present"),
            (user_ids["student2_fr12"], math_id, "2026-10-10", "Absent"),
            (user_ids["student2_fr12"], math_id, "2026-10-15", "Present"),
            (user_ids["student3_fr12"], physics_id, "2026-10-10", "Present"),
            (user_ids["student3_fr12"], physics_id, "2026-10-30", "Present"),
        ]
        for sid, subjid, adate, status in records:
            db.execute(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
                (sid, subjid, adate, status),
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
# 1. Authentication & Security (401 / 403)
# =====================================================================

def test_export_requires_authentication(client):
    """Unauthenticated users cannot access export endpoints (401 Unauthorized)."""
    assert client.get("/api/reports/attendance/export").status_code == 401
    assert client.get("/api/reports/attendance/export/csv").status_code == 401
    assert client.get("/api/reports/attendance/export/pdf").status_code == 401
    assert client.get("/api/reports/export").status_code == 401
    assert client.get("/api/reports/attendance?format=csv").status_code == 401


def test_admin_can_export_any_report(client, fr12_setup):
    """Administrator can export attendance reports for any scope."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export")
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("Content-Type", "")


def test_teacher_can_export_assigned_subject_report(client, fr12_setup):
    """Teacher can export reports for subjects assigned to them."""
    login(client, "teacher1_fr12")
    math_id = fr12_setup["subjects"]["math"]

    res = client.get(f"/api/reports/attendance/export?subject_id={math_id}&format=csv")
    assert res.status_code == 200
    csv_text = res.get_data(as_text=True)
    assert "Mathematics" in csv_text


def test_teacher_cannot_export_unassigned_subject_report(client, fr12_setup):
    """Teacher cannot export reports for subjects assigned to other teachers (403 Forbidden)."""
    login(client, "teacher1_fr12")
    physics_id = fr12_setup["subjects"]["physics"]  # assigned to teacher2

    res = client.get(f"/api/reports/attendance/export?subject_id={physics_id}")
    assert res.status_code == 403
    assert "Access denied" in res.get_json()["error"]


def test_student_can_export_own_report(client, fr12_setup):
    """Student can export their own attendance report."""
    login(client, "student1_fr12")
    res = client.get("/api/reports/attendance/export?format=csv")
    assert res.status_code == 200

    csv_text = res.get_data(as_text=True)
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    assert len(rows) == 5  # student1 has 5 records
    for row in rows:
        assert row["Student Name"] == "student1_fr12"


def test_student_cannot_export_other_student_report(client, fr12_setup):
    """Student cannot export another student's report (403 Forbidden)."""
    login(client, "student1_fr12")
    student2_id = fr12_setup["users"]["student2_fr12"]

    res = client.get(f"/api/reports/attendance/export?student_id={student2_id}")
    assert res.status_code == 403
    assert "Access denied" in res.get_json()["error"]


# =====================================================================
# 2. Supported Formats: CSV, PDF, JSON & Unsupported Formats
# =====================================================================

def test_export_csv_headers_and_content(client, fr12_setup):
    """CSV export returns proper Content-Type, Content-Disposition, and accurate CSV data."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?format=csv")
    assert res.status_code == 200

    # Headers
    assert "text/csv" in res.headers.get("Content-Type", "")
    disp = res.headers.get("Content-Disposition", "")
    assert "attachment" in disp
    assert "attendance_report" in disp
    assert disp.endswith('.csv"') or disp.endswith('.csv')

    # Parse and verify CSV data
    csv_text = res.get_data(as_text=True)
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    assert len(rows) == 9  # 9 total records seeded
    expected_headers = {
        "Attendance ID",
        "Date",
        "Student ID",
        "Student Name",
        "Class ID",
        "Class Name",
        "Subject ID",
        "Subject Name",
        "Status",
    }
    assert expected_headers.issubset(set(reader.fieldnames))


def test_export_pdf_headers_and_content(client, fr12_setup):
    """PDF export returns application/pdf, Content-Disposition, and a valid PDF document."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?format=pdf")
    assert res.status_code == 200

    assert "application/pdf" in res.headers.get("Content-Type", "")
    disp = res.headers.get("Content-Disposition", "")
    assert "attachment" in disp
    assert disp.endswith('.pdf"') or disp.endswith('.pdf')

    pdf_bytes = res.data
    # Valid PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF-1.")
    assert b"%%EOF" in pdf_bytes

    if pypdf is not None:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 1
        page_text = reader.pages[0].extract_text()
        assert "Attendance Report" in page_text
        assert "student1_fr12" in page_text


def test_export_json_format(client, fr12_setup):
    """JSON export returns application/json with attachment header and report payload."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?format=json")
    assert res.status_code == 200

    assert "application/json" in res.headers.get("Content-Type", "")
    disp = res.headers.get("Content-Disposition", "")
    assert "attachment" in disp
    assert "attendance_report" in disp

    data = res.get_json()
    assert data["report_type"] == "attendance_report"
    assert data["total_records"] == 9
    assert len(data["records"]) == 9


def test_unsupported_export_format_returns_400(client, fr12_setup):
    """Requesting an unsupported export format returns 400 Bad Request."""
    login(client, "admin_fr12")
    for bad_fmt in ["xlsx", "xml", "docx", "tar", "html"]:
        res = client.get(f"/api/reports/attendance/export?format={bad_fmt}")
        assert res.status_code == 400
        data = res.get_json()
        assert "Unsupported export format" in data["error"]
        assert "csv" in data["error"]
        assert "pdf" in data["error"]


# =====================================================================
# 3. Filter Scoping: Student, Class, Subject, Dates, Status
# =====================================================================

def test_export_by_student_scope(client, fr12_setup):
    """Export scoped to a specific student exports only their records."""
    login(client, "admin_fr12")
    student1_id = fr12_setup["users"]["student1_fr12"]

    res = client.get(f"/api/reports/attendance/export?student_id={student1_id}&format=csv")
    assert res.status_code == 200

    # Filename reflects student
    disp = res.headers.get("Content-Disposition", "")
    assert "student1_fr12" in disp

    rows = list(csv.DictReader(io.StringIO(res.get_data(as_text=True))))
    assert len(rows) == 5
    for r in rows:
        assert r["Student ID"] == str(student1_id)
        assert r["Student Name"] == "student1_fr12"


def test_export_by_class_scope(client, fr12_setup):
    """Export scoped to a specific class exports only students in that class."""
    login(client, "admin_fr12")
    class_10a_id = fr12_setup["classes"]["10A"]

    res = client.get(f"/api/reports/attendance/export?class_id={class_10a_id}&format=csv")
    assert res.status_code == 200

    # Filename reflects class
    disp = res.headers.get("Content-Disposition", "")
    assert "Class_10-A" in disp

    rows = list(csv.DictReader(io.StringIO(res.get_data(as_text=True))))
    # Class 10-A has student1 (5) + student2 (2) = 7 records
    assert len(rows) == 7
    for r in rows:
        assert r["Class Name"] == "Class 10-A"


def test_export_by_subject_scope(client, fr12_setup):
    """Export scoped to a specific subject exports only that subject."""
    login(client, "admin_fr12")
    physics_id = fr12_setup["subjects"]["physics"]

    res = client.get(f"/api/reports/attendance/export?subject_id={physics_id}&format=csv")
    assert res.status_code == 200

    disp = res.headers.get("Content-Disposition", "")
    assert "Physics" in disp

    rows = list(csv.DictReader(io.StringIO(res.get_data(as_text=True))))
    assert len(rows) == 2
    for r in rows:
        assert r["Subject Name"] == "Physics"


def test_export_by_date_range_scope(client, fr12_setup):
    """Export scoped to a date range includes only records within that range."""
    login(client, "admin_fr12")
    res = client.get(
        "/api/reports/attendance/export?start_date=2026-10-12&end_date=2026-10-20&format=csv"
    )
    assert res.status_code == 200

    rows = list(csv.DictReader(io.StringIO(res.get_data(as_text=True))))
    # Records between 2026-10-12 and 2026-10-20:
    # 2026-10-12 (student1 Chem)
    # 2026-10-15 (student1 Math)
    # 2026-10-15 (student2 Math)
    # 2026-10-20 (student1 Math)
    assert len(rows) == 4
    for r in rows:
        assert "2026-10-12" <= r["Date"] <= "2026-10-20"


def test_export_by_status_filter(client, fr12_setup):
    """Export filtered by status exports only matching status rows."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?status=Absent&format=csv")
    assert res.status_code == 200

    rows = list(csv.DictReader(io.StringIO(res.get_data(as_text=True))))
    assert len(rows) == 2
    for r in rows:
        assert r["Status"] == "Absent"


def test_export_combined_filters(client, fr12_setup):
    """Export with combined student, class, subject, date, and status filters."""
    login(client, "admin_fr12")
    s1_id = fr12_setup["users"]["student1_fr12"]
    c_id = fr12_setup["classes"]["10A"]
    m_id = fr12_setup["subjects"]["math"]

    url = (
        f"/api/reports/attendance/export"
        f"?student_id={s1_id}&class_id={c_id}&subject_id={m_id}"
        f"&start_date=2026-10-10&end_date=2026-10-25&status=Present&format=csv"
    )
    res = client.get(url)
    assert res.status_code == 200

    rows = list(csv.DictReader(io.StringIO(res.get_data(as_text=True))))
    # student1 math presents: 2026-10-10 and 2026-10-25
    assert len(rows) == 2
    for r in rows:
        assert r["Student Name"] == "student1_fr12"
        assert r["Subject Name"] == "Mathematics"
        assert r["Status"] == "Present"


# =====================================================================
# 4. Input Validation & Error Handling
# =====================================================================

def test_export_invalid_date_format(client, fr12_setup):
    """Invalid date format in export request returns 400 Bad Request."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?start_date=not-a-date")
    assert res.status_code == 400
    assert "Invalid start_date format" in res.get_json()["error"]


def test_export_start_date_later_than_end_date(client, fr12_setup):
    """start_date later than end_date returns 400 Bad Request."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?start_date=2026-10-25&end_date=2026-10-10")
    assert res.status_code == 400
    assert "start_date cannot be later than end_date" in res.get_json()["error"]


def test_export_invalid_identifiers(client, fr12_setup):
    """Invalid ID types or values return 400 Bad Request."""
    login(client, "admin_fr12")
    assert client.get("/api/reports/attendance/export?student_id=-1").status_code == 400
    assert client.get("/api/reports/attendance/export?student_id=abc").status_code == 400
    assert client.get("/api/reports/attendance/export?class_id=zero").status_code == 400
    assert client.get("/api/reports/attendance/export?subject_id=-5").status_code == 400


def test_export_nonexistent_records_return_404(client, fr12_setup):
    """Non-existent student, class, or subject returns 404 Not Found."""
    login(client, "admin_fr12")
    assert client.get("/api/reports/attendance/export?student_id=999999").status_code == 404
    assert client.get("/api/reports/attendance/export?class_id=999999").status_code == 404
    assert client.get("/api/reports/attendance/export?subject_id=999999").status_code == 404


def test_export_invalid_status_filter(client, fr12_setup):
    """Invalid status value returns 400 Bad Request."""
    login(client, "admin_fr12")
    res = client.get("/api/reports/attendance/export?status=Excused")
    assert res.status_code == 400
    assert "Invalid status filter" in res.get_json()["error"]


def test_export_empty_results(client, fr12_setup):
    """Valid filter with no matching records returns valid 200 OK export."""
    login(client, "admin_fr12")
    empty_class_id = fr12_setup["classes"]["empty"]

    # CSV with 0 records
    res_csv = client.get(f"/api/reports/attendance/export?class_id={empty_class_id}&format=csv")
    assert res_csv.status_code == 200
    rows = list(csv.DictReader(io.StringIO(res_csv.get_data(as_text=True))))
    assert len(rows) == 0

    # PDF with 0 records
    res_pdf = client.get(f"/api/reports/attendance/export?class_id={empty_class_id}&format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.data.startswith(b"%PDF-1.")
    if pypdf is not None:
        reader = pypdf.PdfReader(io.BytesIO(res_pdf.data))
        assert "No attendance records found" in reader.pages[0].extract_text()


# =====================================================================
# 5. Route Aliases & Alternative Endpoints
# =====================================================================

def test_export_route_aliases(client, fr12_setup):
    """All documented export endpoint aliases function correctly."""
    login(client, "admin_fr12")
    s1_id = fr12_setup["users"]["student1_fr12"]
    c_id = fr12_setup["classes"]["10A"]
    m_id = fr12_setup["subjects"]["math"]

    # 1. Path format alias
    res1 = client.get("/api/reports/attendance/export/csv")
    assert res1.status_code == 200
    assert "text/csv" in res1.headers["Content-Type"]

    res2 = client.get("/api/reports/attendance/export/pdf")
    assert res2.status_code == 200
    assert "application/pdf" in res2.headers["Content-Type"]

    # 2. Student path param export
    res3 = client.get(f"/api/reports/attendance/student/{s1_id}/export?format=csv")
    assert res3.status_code == 200
    assert len(list(csv.DictReader(io.StringIO(res3.get_data(as_text=True))))) == 5

    # 3. Class path param export
    res4 = client.get(f"/api/reports/attendance/class/{c_id}/export?format=csv")
    assert res4.status_code == 200
    assert len(list(csv.DictReader(io.StringIO(res4.get_data(as_text=True))))) == 7

    # 4. Subject path param export
    res5 = client.get(f"/api/reports/attendance/subject/{m_id}/export?format=csv")
    assert res5.status_code == 200
    assert len(list(csv.DictReader(io.StringIO(res5.get_data(as_text=True))))) == 6

    # 5. Query param on base report route
    res6 = client.get("/api/reports/attendance?format=csv")
    assert res6.status_code == 200
    assert "text/csv" in res6.headers["Content-Type"]

    res7 = client.get("/api/attendance/report/export?format=csv")
    assert res7.status_code == 200
    assert "text/csv" in res7.headers["Content-Type"]

    res8 = client.get("/api/reports/export?format=csv")
    assert res8.status_code == 200
    assert "text/csv" in res8.headers["Content-Type"]


# =====================================================================
# 6. Pagination & Data Integrity
# =====================================================================

def test_export_multipage_pdf(client, fr12_setup):
    """Large datasets generate multi-page PDF documents properly."""
    login(client, "admin_fr12")
    app = client.application
    db_path = app.config["DATABASE"]

    # Seed 50 records
    with sqlite3.connect(db_path) as db:
        cur = db.execute("INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
                         ("large_student", generate_password_hash("pass")))
        large_student_id = cur.lastrowid
        cur = db.execute("INSERT INTO subjects (name) VALUES ('BigSubject')")
        large_subject_id = cur.lastrowid

        for day in range(1, 51):
            db.execute(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
                (large_student_id, large_subject_id, f"2026-01-{day:02d}", "Present" if day % 2 == 0 else "Absent"),
            )
        db.commit()

    res = client.get(f"/api/reports/attendance/export?student_id={large_student_id}&format=pdf")
    assert res.status_code == 200
    assert res.data.startswith(b"%PDF-1.")

    if pypdf is not None:
        reader = pypdf.PdfReader(io.BytesIO(res.data))
        assert len(reader.pages) >= 2


def test_export_reflects_updated_records(client, fr12_setup):
    """Updating an attendance record is immediately reflected in subsequent exports."""
    login(client, "admin_fr12")
    student1_id = fr12_setup["users"]["student1_fr12"]
    math_id = fr12_setup["subjects"]["math"]
    app = client.application

    # Verify initial state: 2026-10-15 was Absent
    res1 = client.get(f"/api/reports/attendance/export?student_id={student1_id}&subject_id={math_id}&format=csv")
    rows1 = {r["Date"]: r["Status"] for r in csv.DictReader(io.StringIO(res1.get_data(as_text=True)))}
    assert rows1["2026-10-15"] == "Absent"

    # Update record in DB to Present
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute(
            "UPDATE attendance SET status = 'Present' WHERE student_id = ? AND subject_id = ? AND attendance_date = '2026-10-15'",
            (student1_id, math_id),
        )
        db.commit()

    # Export again and verify status changed
    res2 = client.get(f"/api/reports/attendance/export?student_id={student1_id}&subject_id={math_id}&format=csv")
    rows2 = {r["Date"]: r["Status"] for r in csv.DictReader(io.StringIO(res2.get_data(as_text=True)))}
    assert rows2["2026-10-15"] == "Present"


# =====================================================================
# 7. Additional Hardening: CSV Security, JSON Consistency & PDF Formatting
# =====================================================================

def test_csv_formula_injection_prevention(client, fr12_setup):
    """Names or text starting with '=', '+', '-', '@', '\\t', or '\\r' are sanitized to prevent CSV injection (CWE-1236)."""
    login(client, "admin_fr12")
    app = client.application

    with sqlite3.connect(app.config["DATABASE"]) as db:
        # Create users with formula characters in username
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
            ("=1+2_calc", generate_password_hash("pass")),
        )
        s_calc_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
            ("+plus_user", generate_password_hash("pass")),
        )
        s_plus_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
            ("@at_user", generate_password_hash("pass")),
        )
        s_at_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
            ("-minus_user", generate_password_hash("pass")),
        )
        s_minus_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
            ("  =tab_user", generate_password_hash("pass")),
        )
        s_tab_id = cur.lastrowid

        # Create subject with leading formula trigger
        cur = db.execute("INSERT INTO subjects (name) VALUES ('=HYPERLINK(\"http://evil.com\")')")
        formula_subj_id = cur.lastrowid

        # Insert attendance records
        for sid in [s_calc_id, s_plus_id, s_at_id, s_minus_id, s_tab_id]:
            db.execute(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, '2026-10-31', 'Present')",
                (sid, formula_subj_id),
            )
        db.commit()

    res = client.get(f"/api/reports/attendance/export?subject_id={formula_subj_id}&format=csv")
    assert res.status_code == 200
    csv_raw = res.get_data(as_text=True)

    # Check raw CSV output: formula triggers MUST be prefixed with single quote (')
    assert "'=1+2_calc" in csv_raw
    assert "'+plus_user" in csv_raw
    assert "'@at_user" in csv_raw
    assert "'-minus_user" in csv_raw
    assert "'  =tab_user" in csv_raw
    assert "'=HYPERLINK" in csv_raw

    # Verify parsed CSV rows using csv.reader have the sanitized formula strings
    rows = list(csv.reader(io.StringIO(csv_raw)))
    subject_names = [r[7] for r in rows[1:]]
    assert all(s == '\'=HYPERLINK("http://evil.com")' for s in subject_names)

    # Verify standard names do NOT get prepended with single quotes
    res_normal = client.get("/api/reports/attendance/export?format=csv")
    csv_normal = res_normal.get_data(as_text=True)
    assert ",student1_fr12," in csv_normal
    assert ",'student1_fr12," not in csv_normal


def test_json_export_consistency_and_download_headers(client, fr12_setup):
    """JSON exports work consistently with documented endpoints and download headers."""
    login(client, "admin_fr12")
    s1_id = fr12_setup["users"]["student1_fr12"]
    c1_id = fr12_setup["classes"]["10A"]
    m1_id = fr12_setup["subjects"]["math"]

    endpoints_to_test = [
        # (URL, expected_filename_part)
        ("/api/reports/attendance/export?format=json", "attendance_report.json"),
        ("/api/reports/attendance/export/json", "attendance_report.json"),
        (f"/api/reports/attendance/student/{s1_id}/export?format=json", "attendance_report_student_student1_fr12.json"),
        (f"/api/reports/attendance/student/{s1_id}/export/json", "attendance_report_student_student1_fr12.json"),
        (f"/api/reports/attendance/class/{c1_id}/export?format=json", "attendance_report_class_Class_10-A.json"),
        (f"/api/reports/attendance/class/{c1_id}/export/json", "attendance_report_class_Class_10-A.json"),
        (f"/api/reports/attendance/subject/{m1_id}/export?format=json", "attendance_report_subject_Mathematics.json"),
        (f"/api/reports/attendance/subject/{m1_id}/export/json", "attendance_report_subject_Mathematics.json"),
        ("/api/reports/attendance?format=json", "attendance_report.json"),
        ("/api/reports/attendance?export=json", "attendance_report.json"),
        ("/api/attendance/report/export?format=json", "attendance_report.json"),
        ("/api/attendance/report/export/json", "attendance_report.json"),
        ("/api/reports/export?format=json", "attendance_report.json"),
        ("/api/reports/export/json", "attendance_report.json"),
    ]

    for url, exp_filename in endpoints_to_test:
        res = client.get(url)
        assert res.status_code == 200, f"Failed for {url}"
        assert "application/json" in res.headers.get("Content-Type", "")
        disp = res.headers.get("Content-Disposition", "")
        assert "attachment" in disp, f"Missing attachment disposition for {url}"
        assert exp_filename in disp, f"Filename '{exp_filename}' not in '{disp}' for {url}"

        data = res.get_json()
        assert data is not None
        assert data.get("report_type") == "attendance_report"
        assert "summary" in data
        assert "records" in data
        assert isinstance(data["records"], list)

    # Base report without format/export should return 200 JSON WITHOUT Content-Disposition attachment (FR-06 UI)
    res_base = client.get("/api/reports/attendance")
    assert res_base.status_code == 200
    assert "application/json" in res_base.headers.get("Content-Type", "")
    assert "Content-Disposition" not in res_base.headers


def test_pdf_long_text_no_cutoff_or_overlap(client, fr12_setup):
    """Long student names, subject names, and class names do not get cut off or overlap in PDF export."""
    login(client, "admin_fr12")
    app = client.application

    long_student_name = "Alexander Bartholomew Montgomery-Cunningham"
    long_subject_name = "Advanced Microprocessors and System Architecture"
    long_class_name = "Class 10-A Special Advanced Honours"

    with sqlite3.connect(app.config["DATABASE"]) as db:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'student', 1)",
            (long_student_name, generate_password_hash("pass")),
        )
        long_stu_id = cur.lastrowid

        cur = db.execute("INSERT INTO classes (name) VALUES (?)", (long_class_name,))
        long_cls_id = cur.lastrowid

        cur = db.execute("INSERT INTO subjects (name) VALUES (?)", (long_subject_name,))
        long_sub_id = cur.lastrowid

        db.execute(
            "INSERT INTO enrollments (student_id, class_id, subject_id) VALUES (?, ?, ?)",
            (long_stu_id, long_cls_id, long_sub_id),
        )

        db.execute(
            "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, '2026-10-31', 'Present')",
            (long_stu_id, long_sub_id),
        )
        db.commit()

    res = client.get(f"/api/reports/attendance/export?student_id={long_stu_id}&format=pdf")
    assert res.status_code == 200
    assert "application/pdf" in res.headers.get("Content-Type", "")
    pdf_bytes = res.data
    assert pdf_bytes.startswith(b"%PDF-1.")
    assert b"%%EOF" in pdf_bytes

    if pypdf is not None:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        full_text = "\n".join(page.extract_text() for page in reader.pages)

        # Verify that long student name was NOT bluntly cut off
        assert "Alexander" in full_text
        assert "Montgomery-" in full_text
        assert "Cunningham" in full_text

        # Verify that long subject name was NOT bluntly cut off
        assert "Advanced" in full_text
        assert "Microprocessors" in full_text
        assert "System Architecture" in full_text

        # Verify that long class name was NOT bluntly cut off
        assert "Class 10-A" in full_text
        assert "Special" in full_text


def test_pdf_large_report_pagination_and_repeated_headers(client, fr12_setup):
    """Large reports spanning multiple pages include repeated headers and format cleanly."""
    login(client, "admin_fr12")
    app = client.application

    with sqlite3.connect(app.config["DATABASE"]) as db:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, active) VALUES ('bulk_stu', ?, 'student', 1)",
            (generate_password_hash("pass"),),
        )
        bulk_stu_id = cur.lastrowid

        cur = db.execute("INSERT INTO subjects (name) VALUES ('BulkSubject')")
        bulk_sub_id = cur.lastrowid

        for d in range(1, 90):
            month = (d // 28) + 1
            day = (d % 28) + 1
            db.execute(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, 'Present')",
                (bulk_stu_id, bulk_sub_id, f"2026-{month:02d}-{day:02d}"),
            )
        db.commit()

    res = client.get(f"/api/reports/attendance/export?student_id={bulk_stu_id}&format=pdf")
    assert res.status_code == 200
    pdf_bytes = res.data

    if pypdf is not None:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 3

        # Every page should have column headers
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            assert "Date" in page_text
            assert "Student" in page_text
            assert "Subject" in page_text
            assert "Status" in page_text
            assert f"Page {i+1} of {len(reader.pages)}" in page_text

        # Final page must have End of Attendance Report
        last_page_text = reader.pages[-1].extract_text()
        assert "End of Attendance Report" in last_page_text

