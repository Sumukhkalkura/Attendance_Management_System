"""FR-04 attendance percentage calculation (``GET /api/attendance/percentages``).
"""

import sqlite3

from flask import g, jsonify, request

from ..auth import login_required
from ..db import get_db
from .blueprint import api

# =====================================================================
# FR-04: Attendance Percentage Calculation
# =====================================================================

@api.get("/attendance/percentages")
@login_required(["admin", "teacher"])
def attendance_percentages():
    """Calculate attendance percentages with role-based subject access."""

    db = get_db()
    current_user = g.current_user
    subject_id = request.args.get("subject_id", type=int)
    role = current_user["role"]

    # Validate an explicitly supplied subject ID.
    if request.args.get("subject_id") is not None:
        if subject_id is None or subject_id <= 0:
            return jsonify(
                error="subject_id must be a positive integer"
            ), 400

        try:
            subject = db.execute(
                "SELECT id, teacher_id FROM subjects WHERE id = ?",
                (subject_id,)
            ).fetchone()
        except sqlite3.Error:
            return jsonify(
                error="Unable to retrieve attendance records"
            ), 503

        if subject is None:
            return jsonify(error="Subject not found"), 404

        # Teachers cannot access another teacher's subject.
        if (
            role == "teacher"
            and subject["teacher_id"] != current_user["id"]
        ):
            return jsonify(
                error="Access denied: teacher not assigned to this subject"
            ), 403

    # Scope attendance records to the requested subject or teacher.
    if role == "teacher":
        if subject_id is not None:
            join_condition = """
                a.student_id = u.id
                AND a.subject_id = ?
            """
            params = (subject_id,)
        else:
            join_condition = """
                a.student_id = u.id
                AND a.subject_id IN (
                    SELECT id
                    FROM subjects
                    WHERE teacher_id = ?
                )
            """
            params = (current_user["id"],)
    elif subject_id is not None:
        join_condition = """
            a.student_id = u.id
            AND a.subject_id = ?
        """
        params = (subject_id,)
    else:
        join_condition = "a.student_id = u.id"
        params = ()

    try:
        rows = db.execute(
            f"""
            SELECT
                u.id AS student_id,
                u.username AS student_name,
                COUNT(a.id) AS total_classes,
                COALESCE(
                    SUM(
                        CASE
                            WHEN a.status = 'Present' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS classes_attended
            FROM users AS u
            LEFT JOIN attendance AS a
                ON {join_condition}
            WHERE u.role = 'student'
            GROUP BY u.id, u.username
            ORDER BY u.username
            """,
            params
        ).fetchall()

    except sqlite3.Error:
        return jsonify(
            error="Unable to retrieve attendance records"
        ), 503

    results = []

    for row in rows:
        total_classes = row["total_classes"]
        classes_attended = row["classes_attended"]

        percentage = (
            0.0
            if total_classes == 0
            else round(
                (classes_attended / total_classes) * 100,
                2
            )
        )

        results.append({
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "classes_attended": classes_attended,
            "total_classes": total_classes,
            "attendance_percentage": percentage
        })

    return jsonify(
        count=len(results),
        students=results
    ), 200
