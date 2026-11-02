"""FR-03 attendance record retrieval, updating and deletion.

``get_attendance`` shares ``GET /api/attendance`` with
``attendance_view.view_attendance``, which is registered first and therefore
handles that request. Both stay registered to preserve the URL map.
"""

import sqlite3

from flask import g, jsonify, request

from ..auth import login_required
from ..db import get_db
from ..validation import normalize_status, parse_date
from .blueprint import api

# =====================================================================
# FR-03: Attendance Record Retrieval, Updating, and Deletion
# =====================================================================

@api.get("/attendance")
@login_required()
def get_attendance():
    """Retrieve attendance records for supported students, classes, and dates."""
    db = get_db()
    current_user = g.current_user

    student_id = request.args.get("student_id", type=int)
    subject_id = request.args.get("subject_id", type=int)
    class_id = request.args.get("class_id", type=int)
    date_arg = request.args.get("attendance_date")
    if date_arg is None:
        date_arg = request.args.get("date")
    status_arg = request.args.get("status")

    if current_user["role"] == "student":
        if student_id is not None and student_id != current_user["id"]:
            return jsonify(
                error="Access denied: students can only view their own attendance"
            ), 403
        student_id = current_user["id"]

    elif current_user["role"] == "teacher":
        if subject_id is not None:
            try:
                sub = db.execute(
                    "SELECT teacher_id FROM subjects WHERE id = ?", (subject_id,)
                ).fetchone()
            except sqlite3.Error:
                return jsonify(error="Database temporarily unavailable"), 503
            if sub is None:
                return jsonify(error="Subject not found"), 404
            if sub["teacher_id"] != current_user["id"]:
                return jsonify(
                    error="Access denied: teacher not assigned to this subject"
                ), 403

    query = """
        SELECT DISTINCT
            a.id,
            a.student_id,
            u.username AS student_username,
            a.subject_id,
            s.name AS subject_name,
            s.teacher_id,
            a.attendance_date,
            a.status
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        JOIN subjects s ON a.subject_id = s.id
    """
    conditions = []
    params = []

    if class_id is not None:
        try:
            cls = db.execute(
                "SELECT id FROM classes WHERE id = ?", (class_id,)
            ).fetchone()
        except sqlite3.Error:
            return jsonify(error="Database temporarily unavailable"), 503
        if cls is None:
            return jsonify(error="Class not found"), 404
        query += " JOIN enrollments e ON a.student_id = e.student_id AND a.subject_id = e.subject_id "
        conditions.append("e.class_id = ?")
        params.append(class_id)

    if student_id is not None:
        conditions.append("a.student_id = ?")
        params.append(student_id)

    if subject_id is not None:
        conditions.append("a.subject_id = ?")
        params.append(subject_id)
    elif current_user["role"] == "teacher":
        conditions.append("s.teacher_id = ?")
        params.append(current_user["id"])

    if date_arg is not None:
        parsed_date = parse_date(date_arg)
        if not parsed_date:
            return jsonify(
                error="Invalid attendance_date format. Must be YYYY-MM-DD"
            ), 400
        conditions.append("a.attendance_date = ?")
        params.append(parsed_date)

    start_date_arg = request.args.get("start_date") or request.args.get("from_date")
    end_date_arg = request.args.get("end_date") or request.args.get("to_date")
    parsed_start_range = None
    parsed_end_range = None

    if start_date_arg is not None:
        parsed_start_range = parse_date(start_date_arg)
        if not parsed_start_range:
            return jsonify(
                error="Invalid start_date format. Must be YYYY-MM-DD"
            ), 400
        conditions.append("a.attendance_date >= ?")
        params.append(parsed_start_range)

    if end_date_arg is not None:
        parsed_end_range = parse_date(end_date_arg)
        if not parsed_end_range:
            return jsonify(
                error="Invalid end_date format. Must be YYYY-MM-DD"
            ), 400
        conditions.append("a.attendance_date <= ?")
        params.append(parsed_end_range)

    if parsed_start_range and parsed_end_range and parsed_start_range > parsed_end_range:
        return jsonify(
            error="start_date cannot be later than end_date"
        ), 400

    if status_arg is not None:
        norm_status = normalize_status(status_arg)
        if not norm_status:
            return jsonify(
                error="Invalid status filter. Must be Present, Absent, or Late"
            ), 400
        conditions.append("a.status = ?")
        params.append(norm_status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY a.attendance_date DESC, u.username ASC"

    try:
        rows = db.execute(query, tuple(params)).fetchall()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    records = [
        {
            "id": r["id"],
            "student_id": r["student_id"],
            "student_username": r["student_username"],
            "subject_id": r["subject_id"],
            "subject_name": r["subject_name"],
            "attendance_date": r["attendance_date"],
            "date": r["attendance_date"],
            "status": r["status"]
        }
        for r in rows
    ]

    return jsonify(records=records, count=len(records)), 200


@api.get("/attendance/<int:record_id>")
@login_required()
def get_attendance_record(record_id):
    """Retrieve a specific attendance record by ID."""
    db = get_db()
    current_user = g.current_user

    try:
        row = db.execute(
            """
            SELECT a.id, a.student_id, u.username AS student_username,
                   a.subject_id, s.name AS subject_name, s.teacher_id,
                   a.attendance_date, a.status
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.id = ?
            """,
            (record_id,)
        ).fetchone()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    if row is None:
        return jsonify(error="Attendance record not found"), 404

    if current_user["role"] == "student" and row["student_id"] != current_user["id"]:
        return jsonify(error="Access denied"), 403

    if (
        current_user["role"] == "teacher"
        and row["teacher_id"] != current_user["id"]
    ):
        return jsonify(
            error="Access denied: teacher not assigned to this subject"
        ), 403

    record = {
        "id": row["id"],
        "student_id": row["student_id"],
        "student_username": row["student_username"],
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"],
        "attendance_date": row["attendance_date"],
        "date": row["attendance_date"],
        "status": row["status"]
    }

    return jsonify(record=record), 200


@api.route("/attendance/<int:record_id>", methods=["PUT", "PATCH"])
@login_required(["teacher", "admin"])
def update_attendance_record(record_id):
    """Update an existing attendance record by ID."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    db = get_db()
    current_user = g.current_user

    try:
        row = db.execute(
            """
            SELECT a.id, a.student_id, a.subject_id, s.teacher_id,
                   a.attendance_date, a.status, s.name AS subject_name,
                   u.username AS student_username
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            JOIN users u ON a.student_id = u.id
            WHERE a.id = ?
            """,
            (record_id,)
        ).fetchone()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    if row is None:
        return jsonify(error="Attendance record not found"), 404

    if (
        current_user["role"] == "teacher"
        and row["teacher_id"] != current_user["id"]
    ):
        return jsonify(
            error="Access denied: teacher not assigned to this subject"
        ), 403

    class_id = data.get("class_id")
    if class_id is not None:
        try:
            cls = db.execute(
                "SELECT id, name FROM classes WHERE id = ?", (class_id,)
            ).fetchone()
            if cls is None:
                return jsonify(error="Class not found"), 404
            enrollment = db.execute(
                """
                SELECT 1 FROM enrollments
                WHERE student_id = ? AND class_id = ? AND subject_id = ?
                """,
                (row["student_id"], class_id, row["subject_id"])
            ).fetchone()
            if enrollment is None:
                return jsonify(
                    error="Student is not enrolled in this class and subject"
                ), 400
        except sqlite3.Error:
            return jsonify(error="Database temporarily unavailable"), 503

    new_status = data.get("status")
    new_date_str = data.get("attendance_date")
    if new_date_str is None:
        new_date_str = data.get("date")

    if new_status is None and new_date_str is None:
        return jsonify(
            error="At least one field (status or attendance_date) must be provided"
        ), 400

    update_status = row["status"]
    if new_status is not None:
        norm_status = normalize_status(new_status)
        if norm_status is None:
            return jsonify(
                error="Invalid attendance status. Must be Present, Absent, or Late"
            ), 400
        update_status = norm_status

    update_date = row["attendance_date"]
    if new_date_str is not None:
        parsed_date = parse_date(new_date_str)
        if not parsed_date:
            return jsonify(
                error="Invalid attendance_date format. Must be YYYY-MM-DD"
            ), 400
        update_date = parsed_date

    # Prevent duplicate records if date is changed
    if update_date != row["attendance_date"]:
        try:
            existing = db.execute(
                """
                SELECT id FROM attendance
                WHERE student_id = ? AND subject_id = ? AND attendance_date = ? AND id != ?
                """,
                (row["student_id"], row["subject_id"], update_date, record_id)
            ).fetchone()
            if existing is not None:
                return jsonify(
                    error="Attendance record already exists for this student, subject, and date"
                ), 409
        except sqlite3.Error:
            return jsonify(error="Database temporarily unavailable"), 503

    try:
        db.execute(
            """
            UPDATE attendance
            SET status = ?, attendance_date = ?
            WHERE id = ?
            """,
            (update_status, update_date, record_id)
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify(
            error="Attendance record already exists for this student, subject, and date"
        ), 409
    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503

    return jsonify(
        message="Attendance record updated successfully",
        record={
            "id": record_id,
            "student_id": row["student_id"],
            "student_username": row["student_username"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "attendance_date": update_date,
            "date": update_date,
            "status": update_status
        }
    ), 200


@api.put("/attendance")
@login_required(["teacher", "admin"])
def update_attendance_by_key():
    """Create or update attendance record identified by student_id, subject_id, and attendance_date."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    db = get_db()
    current_user = g.current_user

    student_id = data.get("student_id")
    subject_id = data.get("subject_id")
    class_id = data.get("class_id")
    date_str = data.get("attendance_date")
    if date_str is None:
        date_str = data.get("date")
    new_status = data.get("status")

    if (
        student_id is None
        or subject_id is None
        or date_str is None
        or new_status is None
    ):
        return jsonify(
            error="student_id, subject_id, attendance_date, and status are required"
        ), 400

    norm_status = normalize_status(new_status)
    if norm_status is None:
        return jsonify(
            error="Invalid attendance status. Must be Present, Absent, or Late"
        ), 400

    attendance_date = parse_date(date_str)
    if not attendance_date:
        return jsonify(
            error="Invalid attendance_date format. Must be YYYY-MM-DD"
        ), 400

    try:
        sub = db.execute(
            "SELECT id, name, teacher_id FROM subjects WHERE id = ?",
            (subject_id,)
        ).fetchone()
        if sub is None:
            return jsonify(error="Subject not found"), 404

        if (
            current_user["role"] == "teacher"
            and sub["teacher_id"] != current_user["id"]
        ):
            return jsonify(
                error="Access denied: teacher not assigned to this subject"
            ), 403

        student = db.execute(
            "SELECT id, username, role, active FROM users WHERE id = ?",
            (student_id,)
        ).fetchone()
        if student is None:
            return jsonify(error="Student not found"), 404
        if student["role"] != "student":
            return jsonify(error="Referenced user is not a student"), 400

        if class_id is not None:
            cls = db.execute(
                "SELECT id, name FROM classes WHERE id = ?", (class_id,)
            ).fetchone()
            if cls is None:
                return jsonify(error="Class not found"), 404
            enrollment = db.execute(
                """
                SELECT 1 FROM enrollments
                WHERE student_id = ? AND class_id = ? AND subject_id = ?
                """,
                (student_id, class_id, subject_id)
            ).fetchone()
            if enrollment is None:
                return jsonify(
                    error="Student is not enrolled in this class and subject"
                ), 400

        row = db.execute(
            """
            SELECT id FROM attendance
            WHERE student_id = ? AND subject_id = ? AND attendance_date = ?
            """,
            (student_id, subject_id, attendance_date)
        ).fetchone()

        if row is not None:
            db.execute(
                "UPDATE attendance SET status = ? WHERE id = ?",
                (norm_status, row["id"])
            )
            record_id = row["id"]
            status_code = 200
            msg = "Attendance record updated successfully"
        else:
            cur = db.execute(
                """
                INSERT INTO attendance (student_id, subject_id, attendance_date, status)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, subject_id, attendance_date, norm_status)
            )
            record_id = cur.lastrowid
            status_code = 201
            msg = "Attendance recorded successfully"

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify(
            error="Attendance record already exists for this student, subject, and date"
        ), 409
    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503

    return jsonify(
        message=msg,
        record={
            "id": record_id,
            "student_id": student_id,
            "student_username": student["username"],
            "subject_id": subject_id,
            "subject_name": sub["name"],
            "attendance_date": attendance_date,
            "date": attendance_date,
            "status": norm_status
        }
    ), status_code


@api.delete("/attendance/<int:record_id>")
@login_required(["teacher", "admin"])
def delete_attendance_record(record_id):
    """Delete an attendance record."""
    db = get_db()
    current_user = g.current_user

    try:
        row = db.execute(
            """
            SELECT a.id, s.teacher_id
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.id = ?
            """,
            (record_id,)
        ).fetchone()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    if row is None:
        return jsonify(error="Attendance record not found"), 404

    if (
        current_user["role"] == "teacher"
        and row["teacher_id"] != current_user["id"]
    ):
        return jsonify(
            error="Access denied: teacher not assigned to this subject"
        ), 403

    try:
        db.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
        db.commit()
    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503

    return jsonify(message="Attendance record deleted successfully"), 200
