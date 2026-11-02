"""FR-05 attendance record viewing: ``GET /api/attendance`` scoped by role.

``view_attendance`` must register before ``attendance_management.get_attendance``,
which shares the same rule; the first registration handles the request.
"""

import sqlite3

from flask import g, jsonify, request

from ..auth import login_required
from ..db import get_db
from ..validation import parse_date
from .blueprint import api

# =====================================================================
# FR-05: Attendance Record Viewing
# =====================================================================

@api.get("/attendance")
@login_required(["admin", "teacher", "student"])
def view_attendance():
    """View attendance records according to the user's role.

    Optional query parameters:
        subject_id: Filter records by subject.
        attendance_date: Filter records by YYYY-MM-DD date.
        student_id: Filter records by student.
        status: Filter records by attendance status.
        class_id: Filter records by the student's enrollment in a class
            for the record's subject.
    """
    db = get_db()
    current_user = g.current_user

    subject_id_arg = request.args.get("subject_id")
    student_id_arg = request.args.get("student_id")
    class_id_arg = request.args.get("class_id")
    date_arg = request.args.get("attendance_date")
    status_arg = request.args.get("status")

    # ---------------------------------------------------------------
    # Validate subject_id.
    # ---------------------------------------------------------------
    subject_id = None

    if subject_id_arg is not None:
        try:
            subject_id = int(subject_id_arg)
        except (TypeError, ValueError):
            return jsonify(
                error="subject_id must be a positive integer"
            ), 400

        if subject_id <= 0:
            return jsonify(
                error="subject_id must be a positive integer"
            ), 400

    # ---------------------------------------------------------------
    # Validate student_id.
    # ---------------------------------------------------------------
    student_id = None

    if student_id_arg is not None:
        try:
            student_id = int(student_id_arg)
        except (TypeError, ValueError):
            return jsonify(
                error="student_id must be a positive integer"
            ), 400

        if student_id <= 0:
            return jsonify(
                error="student_id must be a positive integer"
            ), 400

    # ---------------------------------------------------------------
    # Validate class_id.
    # ---------------------------------------------------------------
    class_id = None

    if class_id_arg is not None:
        try:
            class_id = int(class_id_arg)
        except (TypeError, ValueError):
            return jsonify(
                error="class_id must be a positive integer"
            ), 400

        # SQLite integers are 64-bit; larger values cannot be bound.
        if class_id <= 0 or class_id >= 2 ** 63:
            return jsonify(
                error="class_id must be a positive integer"
            ), 400

    # ---------------------------------------------------------------
    # Validate attendance_date and date range.
    # ---------------------------------------------------------------
    attendance_date = None

    if date_arg is not None:
        attendance_date = parse_date(date_arg)

        if attendance_date is None:
            return jsonify(
                error="Invalid date format, expected YYYY-MM-DD"
            ), 400

    start_date_arg = request.args.get("start_date") or request.args.get("from_date")
    end_date_arg = request.args.get("end_date") or request.args.get("to_date")
    start_date = None
    end_date = None

    if start_date_arg is not None:
        start_date = parse_date(start_date_arg)
        if start_date is None:
            return jsonify(
                error="Invalid start_date format. Must be YYYY-MM-DD"
            ), 400

    if end_date_arg is not None:
        end_date = parse_date(end_date_arg)
        if end_date is None:
            return jsonify(
                error="Invalid end_date format. Must be YYYY-MM-DD"
            ), 400

    if start_date is not None and end_date is not None and start_date > end_date:
        return jsonify(
            error="start_date cannot be later than end_date"
        ), 400

    # ---------------------------------------------------------------
    # Validate status.
    # ---------------------------------------------------------------
    if status_arg is not None:
        status_arg = status_arg.strip()

        if not status_arg:
            return jsonify(
                error="status must not be empty"
            ), 400

    role = current_user["role"]
    current_user_id = current_user["id"]

    # ---------------------------------------------------------------
    # Students may view only their own attendance.
    # ---------------------------------------------------------------
    if role == "student":
        if (
            student_id is not None
            and student_id != current_user_id
        ):
            return jsonify(
                error=(
                    "Access denied: "
                    "students can only view their own attendance"
                )
            ), 403

        student_id = current_user_id

    try:
        # -----------------------------------------------------------
        # Validate subject and check teacher ownership.
        # -----------------------------------------------------------
        if subject_id is not None:
            subject = db.execute(
                """
                SELECT id, teacher_id
                FROM subjects
                WHERE id = ?
                """,
                (subject_id,)
            ).fetchone()

            if subject is None:
                return jsonify(
                    error="Subject not found"
                ), 404

            if (
                role == "teacher"
                and subject["teacher_id"] != current_user_id
            ):
                return jsonify(
                    error=(
                        "Access denied: "
                        "teacher not assigned to this subject"
                    )
                ), 403

        # -----------------------------------------------------------
        # Validate the requested student.
        # -----------------------------------------------------------
        if student_id is not None:
            student = db.execute(
                """
                SELECT id
                FROM users
                WHERE id = ? AND role = 'student'
                """,
                (student_id,)
            ).fetchone()

            if student is None:
                return jsonify(
                    error="Student not found"
                ), 404

        # -----------------------------------------------------------
        # Validate the requested class.
        # -----------------------------------------------------------
        if class_id is not None:
            cls = db.execute(
                """
                SELECT id
                FROM classes
                WHERE id = ?
                """,
                (class_id,)
            ).fetchone()

            if cls is None:
                return jsonify(
                    error="Class not found"
                ), 404

        # -----------------------------------------------------------
        # Build the attendance query.
        # -----------------------------------------------------------
        query = """
            SELECT
                a.id AS attendance_id,
                a.student_id,
                u.username AS student_name,
                a.subject_id,
                s.name AS subject_name,
                a.attendance_date,
                a.status
            FROM attendance AS a
            JOIN users AS u
                ON u.id = a.student_id
            JOIN subjects AS s
                ON s.id = a.subject_id
            WHERE 1 = 1
        """

        params = []

        # Teachers can view only records for their assigned subjects.
        if role == "teacher":
            query += " AND s.teacher_id = ?"
            params.append(current_user_id)

        # Students can view only their own records.
        if role == "student":
            query += " AND a.student_id = ?"
            params.append(current_user_id)

        # Filter by subject.
        if subject_id is not None:
            query += " AND a.subject_id = ?"
            params.append(subject_id)

        # Filter by date.
        if attendance_date is not None:
            query += " AND a.attendance_date = ?"
            params.append(attendance_date)

        if start_date is not None:
            query += " AND a.attendance_date >= ?"
            params.append(start_date)

        if end_date is not None:
            query += " AND a.attendance_date <= ?"
            params.append(end_date)

        # Filter by student.
        if student_id is not None:
            query += " AND a.student_id = ?"
            params.append(student_id)

        # Filter by attendance status.
        if status_arg is not None:
            query += " AND a.status = ?"
            params.append(status_arg)

        # Filter by class. Attendance has no class_id column, so match
        # enrollments. EXISTS keeps one row per attendance record even
        # if a student is enrolled in several classes for the subject.
        if class_id is not None:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM enrollments AS e
                    WHERE e.student_id = a.student_id
                      AND e.subject_id = a.subject_id
                      AND e.class_id = ?
                )
            """
            params.append(class_id)

        query += """
            ORDER BY
                a.attendance_date DESC,
                u.username ASC
        """

        rows = db.execute(query, params).fetchall()

    except sqlite3.Error:
        return jsonify(
            error="Unable to retrieve attendance records"
        ), 503

    # ---------------------------------------------------------------
    # Format response.
    # Include both ID keys for backward compatibility.
    # ---------------------------------------------------------------
    records = [
        {
            "id": row["attendance_id"],
            "attendance_id": row["attendance_id"],
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "attendance_date": row["attendance_date"],
            "status": row["status"]
        }
        for row in rows
    ]

    return jsonify(
        count=len(records),
        records=records
    ), 200
