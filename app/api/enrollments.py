"""FR-09 student enrollment in classes and subjects.
"""

import sqlite3

from flask import jsonify, request

from ..auth import login_required
from ..db import get_db
from .blueprint import api

# ============================================================
# FR-09: Student Enrollment in Classes and Subjects
# ============================================================

@api.post("/enrollments")
@login_required(["admin"])
def create_enrollment():
    """Enroll a student in a class and subject."""

    db = get_db()
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="A JSON request body is required"), 400

    student_id = data.get("student_id")
    class_id = data.get("class_id")
    subject_id = data.get("subject_id")

    if (
        not isinstance(student_id, int)
        or isinstance(student_id, bool)
        or not isinstance(class_id, int)
        or isinstance(class_id, bool)
        or not isinstance(subject_id, int)
        or isinstance(subject_id, bool)
        or student_id <= 0
        or class_id <= 0
        or subject_id <= 0
    ):
        return jsonify(
            error="student_id, class_id, and subject_id must be positive integers"
        ), 400

    try:
        student = db.execute(
            "SELECT id, role, active FROM users WHERE id = ?",
            (student_id,),
        ).fetchone()

        if student is None or student["role"] != "student":
            return jsonify(error="Student not found"), 404

        if not student["active"]:
            return jsonify(error="Student account is inactive"), 400

        class_row = db.execute(
            "SELECT id FROM classes WHERE id = ?",
            (class_id,),
        ).fetchone()

        if class_row is None:
            return jsonify(error="Class not found"), 404

        subject = db.execute(
            "SELECT id FROM subjects WHERE id = ?",
            (subject_id,),
        ).fetchone()

        if subject is None:
            return jsonify(error="Subject not found"), 404

        existing = db.execute(
            """
            SELECT 1
            FROM enrollments
            WHERE student_id = ?
              AND class_id = ?
              AND subject_id = ?
            """,
            (student_id, class_id, subject_id),
        ).fetchone()

        if existing is not None:
            return jsonify(error="Student is already enrolled"), 409

        db.execute(
            """
            INSERT INTO enrollments (student_id, class_id, subject_id)
            VALUES (?, ?, ?)
            """,
            (student_id, class_id, subject_id),
        )
        db.commit()

        return jsonify(
            message="Student enrolled successfully",
            enrollment={
                "student_id": student_id,
                "class_id": class_id,
                "subject_id": subject_id,
            },
        ), 201

    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.get("/enrollments")
@login_required(["admin"])
def list_enrollments():
    """List enrollments with student, class, and subject names.

    Optional query parameters: student_id, class_id, subject_id.
    """
    conditions = []
    params = []

    for field in ("student_id", "class_id", "subject_id"):
        raw_value = request.args.get(field)
        if raw_value is None:
            continue
        value = request.args.get(field, type=int)
        if value is None or value <= 0:
            return jsonify(error=f"{field} must be a positive integer"), 400
        conditions.append(f"e.{field} = ?")
        params.append(value)

    query = """
        SELECT
            e.student_id,
            u.username AS student_name,
            e.class_id,
            c.name AS class_name,
            e.subject_id,
            s.name AS subject_name
        FROM enrollments AS e
        JOIN users AS u ON u.id = e.student_id
        JOIN classes AS c ON c.id = e.class_id
        JOIN subjects AS s ON s.id = e.subject_id
    """

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.name, s.name, u.username"

    try:
        rows = get_db().execute(query, params).fetchall()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    enrollments = [
        {
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "class_id": row["class_id"],
            "class_name": row["class_name"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
        }
        for row in rows
    ]

    return jsonify(count=len(enrollments), enrollments=enrollments), 200


@api.delete("/enrollments")
@login_required(["admin"])
def delete_enrollment():
    """Remove a student's enrollment; attendance records are kept."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="A JSON request body is required"), 400

    values = [data.get(f) for f in ("student_id", "class_id", "subject_id")]

    if any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in values
    ):
        return jsonify(
            error="student_id, class_id, and subject_id must be positive integers"
        ), 400

    db = get_db()

    try:
        cursor = db.execute(
            """
            DELETE FROM enrollments
            WHERE student_id = ? AND class_id = ? AND subject_id = ?
            """,
            values,
        )
        db.commit()
    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503

    if cursor.rowcount == 0:
        return jsonify(error="Enrollment not found"), 404

    return jsonify(message="Enrollment removed successfully"), 200
