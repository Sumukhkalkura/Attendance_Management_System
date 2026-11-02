"""FR-06 attendance reporting and FR-12 report export routes, plus the
shared report data builder. File formatting comes from ``exports``.
"""

import sqlite3

from flask import g, jsonify, request

from ..auth import login_required
from ..db import get_db
from ..validation import normalize_status, parse_date
from .blueprint import api
from .exports import _format_export_response

def _build_attendance_report_data(student_id=None, class_id=None, subject_id=None):
    """Compile and return attendance report data dictionary or error response."""
    db = get_db()
    current_user = g.current_user
    role = current_user["role"]
    current_user_id = current_user["id"]

    # ---------------------------------------------------------------
    # 1. Resolve and validate student_id
    # ---------------------------------------------------------------
    if student_id is None:
        student_id_arg = request.args.get("student_id")
        if student_id_arg is not None:
            try:
                student_id = int(student_id_arg)
            except (TypeError, ValueError):
                return None, jsonify(error="student_id must be a positive integer"), 400
            if student_id <= 0:
                return None, jsonify(error="student_id must be a positive integer"), 400

    # Role enforcement for students:
    if role == "student":
        if student_id is not None and student_id != current_user_id:
            return None, jsonify(
                error="Access denied: students can only view their own attendance"
            ), 403
        student_id = current_user_id

    student_entity = None
    if student_id is not None:
        try:
            student_row = db.execute(
                "SELECT id, username FROM users WHERE id = ? AND role = 'student'",
                (student_id,)
            ).fetchone()
        except sqlite3.Error:
            return None, jsonify(error="Database temporarily unavailable"), 503

        if student_row is None:
            return None, jsonify(error="Student not found"), 404
        student_entity = {
            "id": student_row["id"],
            "username": student_row["username"],
            "name": student_row["username"]
        }

    # ---------------------------------------------------------------
    # 2. Resolve and validate class_id
    # ---------------------------------------------------------------
    if class_id is None:
        class_id_arg = request.args.get("class_id")
        if class_id_arg is not None:
            try:
                class_id = int(class_id_arg)
            except (TypeError, ValueError):
                return None, jsonify(error="class_id must be a positive integer"), 400
            if class_id <= 0:
                return None, jsonify(error="class_id must be a positive integer"), 400

    class_entity = None
    if class_id is not None:
        try:
            class_row = db.execute(
                "SELECT id, name, teacher_id FROM classes WHERE id = ?",
                (class_id,)
            ).fetchone()
        except sqlite3.Error:
            return None, jsonify(error="Database temporarily unavailable"), 503

        if class_row is None:
            return None, jsonify(error="Class not found"), 404
        class_entity = {"id": class_row["id"], "name": class_row["name"]}

    # ---------------------------------------------------------------
    # 3. Resolve and validate subject_id
    # ---------------------------------------------------------------
    if subject_id is None:
        subject_id_arg = request.args.get("subject_id")
        if subject_id_arg is not None:
            try:
                subject_id = int(subject_id_arg)
            except (TypeError, ValueError):
                return None, jsonify(error="subject_id must be a positive integer"), 400
            if subject_id <= 0:
                return None, jsonify(error="subject_id must be a positive integer"), 400

    subject_entity = None
    if subject_id is not None:
        try:
            subject_row = db.execute(
                "SELECT id, name, teacher_id FROM subjects WHERE id = ?",
                (subject_id,)
            ).fetchone()
        except sqlite3.Error:
            return None, jsonify(error="Database temporarily unavailable"), 503

        if subject_row is None:
            return None, jsonify(error="Subject not found"), 404

        if role == "teacher" and subject_row["teacher_id"] != current_user_id:
            return None, jsonify(
                error="Access denied: teacher not assigned to this subject"
            ), 403

        subject_entity = {"id": subject_row["id"], "name": subject_row["name"]}

    # ---------------------------------------------------------------
    # 4. Resolve and validate date range
    # ---------------------------------------------------------------
    start_date_arg = request.args.get("start_date") or request.args.get("from_date") or request.args.get("start")
    end_date_arg = request.args.get("end_date") or request.args.get("to_date") or request.args.get("end")

    parsed_start = None
    if start_date_arg is not None:
        start_date_clean = start_date_arg.strip() if isinstance(start_date_arg, str) else ""
        parsed_start = parse_date(start_date_clean)
        if parsed_start is None:
            return None, jsonify(error="Invalid start_date format. Must be YYYY-MM-DD"), 400

    parsed_end = None
    if end_date_arg is not None:
        end_date_clean = end_date_arg.strip() if isinstance(end_date_arg, str) else ""
        parsed_end = parse_date(end_date_clean)
        if parsed_end is None:
            return None, jsonify(error="Invalid end_date format. Must be YYYY-MM-DD"), 400

    if parsed_start is not None and parsed_end is not None:
        if parsed_start > parsed_end:
            return None, jsonify(error="start_date cannot be later than end_date"), 400

    # ---------------------------------------------------------------
    # 5. Resolve and validate status
    # ---------------------------------------------------------------
    status_arg = request.args.get("status")
    norm_status = None
    if status_arg is not None:
        status_clean = status_arg.strip() if isinstance(status_arg, str) else ""
        norm_status = normalize_status(status_clean)
        if norm_status is None:
            return None, jsonify(error="Invalid status filter. Must be Present, Absent, or Late"), 400

    # ---------------------------------------------------------------
    # 6. Build and execute SQL query
    # ---------------------------------------------------------------
    query = """
        SELECT
            a.id,
            a.student_id,
            u.username AS student_name,
            MIN(e.class_id) AS class_id,
            MIN(c.name) AS class_name,
            a.subject_id,
            s.name AS subject_name,
            a.attendance_date,
            a.status
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        JOIN subjects s ON a.subject_id = s.id
    """
    conditions = []
    params = []

    if class_id is not None:
        query += " JOIN enrollments e ON a.student_id = e.student_id AND a.subject_id = e.subject_id JOIN classes c ON e.class_id = c.id "
        conditions.append("e.class_id = ?")
        params.append(class_id)
    else:
        query += " LEFT JOIN enrollments e ON a.student_id = e.student_id AND a.subject_id = e.subject_id LEFT JOIN classes c ON e.class_id = c.id "

    if student_id is not None:
        conditions.append("a.student_id = ?")
        params.append(student_id)

    if subject_id is not None:
        conditions.append("a.subject_id = ?")
        params.append(subject_id)
    elif role == "teacher":
        conditions.append("s.teacher_id = ?")
        params.append(current_user_id)

    if parsed_start is not None:
        conditions.append("a.attendance_date >= ?")
        params.append(parsed_start)

    if parsed_end is not None:
        conditions.append("a.attendance_date <= ?")
        params.append(parsed_end)

    if norm_status is not None:
        conditions.append("a.status = ?")
        params.append(norm_status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if class_id is not None:
        query += " GROUP BY a.id, a.student_id, u.username, e.class_id, c.name, a.subject_id, s.name, a.attendance_date, a.status "
    else:
        query += " GROUP BY a.id, a.student_id, u.username, a.subject_id, s.name, a.attendance_date, a.status "

    query += " ORDER BY a.attendance_date DESC, u.username ASC, a.id ASC"

    try:
        rows = db.execute(query, params).fetchall()
    except sqlite3.Error:
        return None, jsonify(error="Unable to generate attendance report"), 503

    records = [
        {
            "id": r["id"],
            "attendance_id": r["id"],
            "student_id": r["student_id"],
            "student_name": r["student_name"],
            "student_username": r["student_name"],
            "class_id": r["class_id"],
            "class_name": r["class_name"],
            "subject_id": r["subject_id"],
            "subject_name": r["subject_name"],
            "attendance_date": r["attendance_date"],
            "date": r["attendance_date"],
            "status": r["status"]
        }
        for r in rows
    ]

    total_records = len(records)
    present_count = sum(1 for r in records if r["status"] == "Present")
    absent_count = sum(1 for r in records if r["status"] == "Absent")
    late_count = sum(1 for r in records if r["status"] == "Late")
    attendance_percentage = (
        0.0 if total_records == 0 else round((present_count / total_records) * 100, 2)
    )

    summary = {
        "total_records": total_records,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "attendance_percentage": attendance_percentage,
    }

    response_payload = {
        "report_type": "attendance_report",
        "filters": {
            "student_id": student_id,
            "class_id": class_id,
            "subject_id": subject_id,
            "start_date": parsed_start,
            "end_date": parsed_end,
            "status": norm_status,
        },
        "summary": summary,
        "count": total_records,
        "total_records": total_records,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "attendance_percentage": attendance_percentage,
        "records": records,
    }

    if student_entity is not None:
        response_payload["student"] = student_entity
    if class_entity is not None:
        response_payload["class"] = class_entity
    if subject_entity is not None:
        response_payload["subject"] = subject_entity

    return response_payload, None, 200


# =====================================================================
# FR-06: Attendance Reporting
# =====================================================================

@api.get("/reports/attendance")
@api.get("/reports/attendance/student/<int:student_id>")
@api.get("/reports/attendance/class/<int:class_id>")
@api.get("/reports/attendance/subject/<int:subject_id>")
@api.get("/attendance/report")
@api.get("/attendance/reports")
@login_required()
def generate_attendance_report(student_id=None, class_id=None, subject_id=None):
    """Generate attendance reports based on student, class, subject, or date range.

    Acceptance criteria:
    - Users can generate attendance reports for a student.
    - Reports can be generated by class or subject.
    - Users can select a date range for reporting.
    - Generated reports contain matching attendance information.

    Supported query parameters:
        student_id: Filter by student ID.
        class_id: Filter by class ID.
        subject_id: Filter by subject ID.
        start_date (or from_date): Start date (YYYY-MM-DD), inclusive.
        end_date (or to_date): End date (YYYY-MM-DD), inclusive.
        status: Filter by status (Present, Absent, Late).
        format (or export): Export format (csv, pdf, json).
    """
    payload, error_resp, status_code = _build_attendance_report_data(
        student_id=student_id,
        class_id=class_id,
        subject_id=subject_id,
    )
    if error_resp is not None:
        return error_resp, status_code

    export_fmt = request.args.get("export") or request.args.get("format")
    if export_fmt:
        return _format_export_response(payload, export_fmt)

    return jsonify(payload), 200


# =====================================================================
# FR-12: Report Export
# =====================================================================

@api.get("/reports/attendance/export")
@api.get("/reports/attendance/export/<string:format_name>")
@api.get("/reports/attendance/student/<int:student_id>/export")
@api.get("/reports/attendance/student/<int:student_id>/export/<string:format_name>")
@api.get("/reports/attendance/class/<int:class_id>/export")
@api.get("/reports/attendance/class/<int:class_id>/export/<string:format_name>")
@api.get("/reports/attendance/subject/<int:subject_id>/export")
@api.get("/reports/attendance/subject/<int:subject_id>/export/<string:format_name>")
@api.get("/attendance/report/export")
@api.get("/attendance/report/export/<string:format_name>")
@api.get("/reports/export")
@api.get("/reports/export/<string:format_name>")
@login_required()
def export_attendance_report(student_id=None, class_id=None, subject_id=None, format_name=None):
    """Export attendance reports in a supported file format (CSV, PDF, JSON).

    FR-12 Acceptance Criteria:
    - Authorized users can export a generated attendance report.
    - The exported file uses a supported format (CSV, PDF, JSON).
    - The exported report contains the correct attendance data.
    """
    payload, error_resp, status_code = _build_attendance_report_data(
        student_id=student_id,
        class_id=class_id,
        subject_id=subject_id,
    )
    if error_resp is not None:
        return error_resp, status_code

    req_format = (
        format_name
        or request.args.get("format")
        or request.args.get("export")
        or "csv"
    )
    return _format_export_response(payload, req_format)
