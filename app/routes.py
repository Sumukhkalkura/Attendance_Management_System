"""FR-01: Authentication and FR-03: Attendance Record Management."""

import sqlite3
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request, session, g
from werkzeug.security import check_password_hash

from .db import get_db

VALID_STATUSES = {"Present", "Absent", "Late"}


def normalize_status(status):
    """Normalize and validate attendance status."""
    if not isinstance(status, str):
        return None
    cleaned = status.strip().capitalize()
    if cleaned in VALID_STATUSES:
        return cleaned
    return None


def parse_date(date_str):
    """Parse and validate date string formatted as YYYY-MM-DD."""
    if not isinstance(date_str, str):
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify(status="ok"), 200


# FR-01: Role-Based Access Control

def login_required(allowed_roles=None):
    """Allow access only to authenticated, authorized users."""

    def decorator(view_function):

        @wraps(view_function)
        def wrapped(*args, **kwargs):

            user_id = session.get("user_id")

            if user_id is None:
                return jsonify(
                    error="Authentication required"
                ), 401

            try:
                user = get_db().execute(
                    """
                    SELECT id, username, role, active
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()

            except sqlite3.Error:
                return jsonify(
                    error="Database temporarily unavailable"
                ), 503

            if user is None or not user["active"]:
                session.clear()
                return jsonify(
                    error="Authentication required"
                ), 401

            if (
                allowed_roles is not None
                and user["role"] not in allowed_roles
            ):
                return jsonify(
                    error="Access denied"
                ), 403

            g.current_user = user

            return view_function(*args, **kwargs)

        return wrapped

    return decorator


# FR-01: User Login

@api.post("/login")
def login():
    """Authenticate an administrator, teacher, or student."""

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="JSON request body required"
        ), 400

    username = data.get("username")
    password = data.get("password")

    if (
        not isinstance(username, str)
        or not username.strip()
        or not isinstance(password, str)
        or not password
    ):
        return jsonify(
            error="Username and password are required"
        ), 400

    try:
        user = get_db().execute(
            """
            SELECT id, username, password_hash, role, active
            FROM users
            WHERE username = ?
            """,
            (username.strip(),)
        ).fetchone()

        if (
            user is None
            or not user["active"]
            or not check_password_hash(
                user["password_hash"], password
            )
        ):
            return jsonify(
                error="Invalid username or password"
            ), 401

    except (sqlite3.Error, ValueError):
        return jsonify(
            error="Authentication temporarily unavailable"
        ), 503

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]

    return jsonify(
        message="Login successful",
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    ), 200


# FR-01: Get Current User

@api.get("/me")
@login_required()
def current_user():
    """Return the logged-in user's details."""

    user = g.current_user

    return jsonify(
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    ), 200


# FR-01: Admin Authorization

@api.get("/admin/check")
@login_required(["admin"])
def admin_check():
    return jsonify(
        message="Administrator access granted"
    ), 200


# FR-01: Teacher Authorization

@api.get("/teacher/check")
@login_required(["teacher"])
def teacher_check():
    return jsonify(
        message="Teacher access granted"
    ), 200


# FR-01: Student Authorization

@api.get("/student/check")
@login_required(["student"])
def student_check():
    return jsonify(
        message="Student access granted"
    ), 200

    
# FR-04: Attendance Percentage Calculation

@api.get("/attendance/percentages")
@login_required(["admin", "teacher"])
def attendance_percentages():
    """
    Calculate and return attendance percentages for students.

    Optional query parameter:
        subject_id: Calculate attendance for a specific subject.
    """

    subject_id = request.args.get("subject_id", type=int)

    if request.args.get("subject_id") is not None:
        if subject_id is None or subject_id <= 0:
            return jsonify(
                error="subject_id must be a positive integer"
            ), 400

    try:
        rows = get_db().execute(
            """
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
                ON a.student_id = u.id
                AND (
                    ? IS NULL
                    OR a.subject_id = ?
                )
            WHERE u.role = 'student'
            GROUP BY u.id, u.username
            ORDER BY u.username
            """,
            (subject_id, subject_id)
        ).fetchall()

    except sqlite3.Error:
        return jsonify(
            error="Unable to retrieve attendance records"
        ), 503

    results = []

    for row in rows:
        total_classes = row["total_classes"]
        classes_attended = row["classes_attended"]

        if total_classes == 0:
            percentage = 0.0
        else:
            percentage = round(
                (classes_attended / total_classes) * 100,
                2
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

# =====================================================================
# FR-03: Attendance Record Management & Teacher Helpers
# =====================================================================

@api.get("/teacher/classes")
@login_required(["teacher", "admin"])
def teacher_classes():
    """Return classes assigned to the logged-in teacher."""
    db = get_db()
    current_user = g.current_user
    try:
        if current_user["role"] == "admin":
            rows = db.execute(
                "SELECT id, name FROM classes ORDER BY name"
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT DISTINCT c.id, c.name
                FROM classes c
                JOIN enrollments e ON c.id = e.class_id
                JOIN subjects s ON e.subject_id = s.id
                WHERE s.teacher_id = ?
                ORDER BY c.name
                """,
                (current_user["id"],)
            ).fetchall()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    classes = [{"id": r["id"], "name": r["name"]} for r in rows]
    if not classes:
        return jsonify(message="No classes assigned", classes=[]), 200
    return jsonify(classes=classes), 200


@api.get("/teacher/subjects")
@login_required(["teacher", "admin"])
def teacher_subjects():
    """Return subjects assigned to the logged-in teacher."""
    db = get_db()
    current_user = g.current_user
    try:
        if current_user["role"] == "admin":
            rows = db.execute(
                "SELECT id, name, teacher_id FROM subjects ORDER BY name"
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, name, teacher_id
                FROM subjects
                WHERE teacher_id = ?
                ORDER BY name
                """,
                (current_user["id"],)
            ).fetchall()
    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    subjects = [
        {"id": r["id"], "name": r["name"], "teacher_id": r["teacher_id"]}
        for r in rows
    ]
    if not subjects:
        return jsonify(message="No subjects assigned", subjects=[]), 200
    return jsonify(subjects=subjects), 200


@api.get("/roster")
@login_required(["teacher", "admin"])
def class_roster():
    """Load the student roster for a chosen class, subject, and optional date."""
    db = get_db()
    current_user = g.current_user

    class_id = request.args.get("class_id", type=int)
    subject_id = request.args.get("subject_id", type=int)
    date_arg = request.args.get("attendance_date")
    if date_arg is None:
        date_arg = request.args.get("date")

    if not class_id or not subject_id:
        return jsonify(
            error="class_id and subject_id query parameters are required"
        ), 400

    attendance_date = None
    if date_arg:
        attendance_date = parse_date(date_arg)
        if not attendance_date:
            return jsonify(
                error="Invalid date format, expected YYYY-MM-DD"
            ), 400

    try:
        cls = db.execute(
            "SELECT id, name FROM classes WHERE id = ?", (class_id,)
        ).fetchone()
        if cls is None:
            return jsonify(error="Class not found"), 404

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

        query = """
            SELECT u.id AS student_id, u.username,
                   a.id AS attendance_id, a.status, a.attendance_date
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            LEFT JOIN attendance a ON a.student_id = u.id
                                  AND a.subject_id = e.subject_id
                                  AND a.attendance_date = ?
            WHERE e.class_id = ? AND e.subject_id = ?
              AND u.role = 'student' AND u.active = 1
            ORDER BY u.username
        """
        rows = db.execute(
            query, (attendance_date, class_id, subject_id)
        ).fetchall()

    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503

    students = [
        {
            "student_id": r["student_id"],
            "username": r["username"],
            "status": r["status"],
            "attendance_id": r["attendance_id"],
            "attendance_date": r["attendance_date"],
        }
        for r in rows
    ]

    return jsonify(
        class_id=class_id,
        class_name=cls["name"],
        subject_id=subject_id,
        subject_name=sub["name"],
        attendance_date=attendance_date,
        students=students,
        count=len(students)
    ), 200


# =====================================================================
# FR-03: Attendance Record Creation & Bulk Submission
# =====================================================================

@api.post("/attendance")
@login_required(["teacher", "admin"])
def mark_attendance():
    """Create or update attendance records for student(s) for a session."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="JSON request body required"), 400

    db = get_db()
    current_user = g.current_user

    # Handle batch submission (either {"records": [...]} or raw list)
    if isinstance(data, list) or (isinstance(data, dict) and "records" in data):
        if isinstance(data, list):
            items = data
            batch_subject_id = None
            batch_date_str = None
            class_id = None
            allow_update = False
        else:
            items = data.get("records")
            batch_subject_id = data.get("subject_id")
            batch_date_str = data.get("attendance_date")
            if batch_date_str is None:
                batch_date_str = data.get("date")
            class_id = data.get("class_id")
            allow_update = bool(
                data.get("update_existing") or data.get("allow_update") or data.get("update")
            )

        if not isinstance(items, list) or len(items) == 0:
            return jsonify(error="records must be a non-empty list"), 400

        # Validate batch-level subject_id and date if provided
        if batch_subject_id is not None:
            try:
                sub = db.execute(
                    "SELECT id, name, teacher_id FROM subjects WHERE id = ?",
                    (batch_subject_id,)
                ).fetchone()
            except sqlite3.Error:
                return jsonify(error="Database temporarily unavailable"), 503

            if sub is None:
                return jsonify(error="Subject not found"), 404
            if (
                current_user["role"] == "teacher"
                and sub["teacher_id"] != current_user["id"]
            ):
                return jsonify(
                    error="Access denied: teacher not assigned to this subject"
                ), 403

        if batch_date_str is not None:
            parsed_batch_date = parse_date(batch_date_str)
            if not parsed_batch_date:
                return jsonify(
                    error="Invalid attendance_date format. Must be YYYY-MM-DD"
                ), 400
        else:
            parsed_batch_date = None

        if class_id is not None:
            try:
                cls = db.execute(
                    "SELECT id, name FROM classes WHERE id = ?", (class_id,)
                ).fetchone()
            except sqlite3.Error:
                return jsonify(error="Database temporarily unavailable"), 503

            if cls is None:
                return jsonify(error="Class not found"), 404

            # Verify roster completeness if class_id and subject_id both present
            if batch_subject_id is not None:
                try:
                    enrolled_rows = db.execute(
                        """
                        SELECT student_id FROM enrollments
                        WHERE class_id = ? AND subject_id = ?
                        """,
                        (class_id, batch_subject_id)
                    ).fetchall()
                    if not enrolled_rows:
                        return jsonify(
                            error="No students enrolled in this class and subject"
                        ), 400
                    enrolled_ids = {r["student_id"] for r in enrolled_rows}
                    submitted_ids = {
                        it.get("student_id")
                        for it in items
                        if isinstance(it, dict)
                    }
                    unenrolled = submitted_ids - enrolled_ids
                    if unenrolled:
                        unenrolled_ids = sorted(list(unenrolled))
                        return jsonify(
                            error=(
                                f"Student IDs are not enrolled in class {class_id} "
                                f"for subject {batch_subject_id}: {unenrolled_ids}"
                            )
                        ), 400
                    missing = enrolled_ids - submitted_ids
                    if missing:
                        missing_ids = sorted(list(missing))
                        return jsonify(
                            error=f"All enrolled students must be marked. Missing student IDs: {missing_ids}"
                        ), 400
                except sqlite3.Error:
                    return jsonify(error="Database temporarily unavailable"), 503

        records_to_process = []
        seen_keys = set()

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                return jsonify(
                    error=f"Item at index {idx} must be a JSON object"
                ), 400

            sid = item.get("student_id")
            sub_id = item.get("subject_id") or batch_subject_id
            d_str = item.get("attendance_date")
            if d_str is None:
                d_str = item.get("date")
            if d_str is None:
                d_str = batch_date_str
            st = item.get("status")

            if sid is None or sub_id is None or d_str is None or st is None:
                return jsonify(
                    error="Each record requires student_id, subject_id, attendance_date, and status"
                ), 400

            norm_status = normalize_status(st)
            if norm_status is None:
                return jsonify(
                    error=f"Invalid attendance status '{st}'. Must be Present, Absent, or Late"
                ), 400

            att_date = parse_date(d_str)
            if not att_date:
                return jsonify(
                    error=f"Invalid attendance_date format for student {sid}. Must be YYYY-MM-DD"
                ), 400

            key = (sid, sub_id, att_date)
            if key in seen_keys:
                return jsonify(
                    error=f"Duplicate attendance entry for student {sid} in submission"
                ), 400
            seen_keys.add(key)

            try:
                if sub_id != batch_subject_id:
                    sub = db.execute(
                        "SELECT id, name, teacher_id FROM subjects WHERE id = ?",
                        (sub_id,)
                    ).fetchone()
                    if sub is None:
                        return jsonify(error=f"Subject {sub_id} not found"), 404
                    if (
                        current_user["role"] == "teacher"
                        and sub["teacher_id"] != current_user["id"]
                    ):
                        return jsonify(
                            error=f"Access denied: teacher not assigned to subject {sub_id}"
                        ), 403

                student = db.execute(
                    "SELECT id, username, role, active FROM users WHERE id = ?",
                    (sid,)
                ).fetchone()
                if student is None:
                    return jsonify(
                        error=f"Student with ID {sid} not found"
                    ), 404
                if student["role"] != "student":
                    return jsonify(error=f"User {sid} is not a student"), 400

                # Validate enrollment if class_id provided
                if class_id is not None:
                    enrollment = db.execute(
                        """
                        SELECT 1 FROM enrollments
                        WHERE student_id = ? AND class_id = ? AND subject_id = ?
                        """,
                        (sid, class_id, sub_id)
                    ).fetchone()
                    if enrollment is None:
                        return jsonify(
                            error=f"Student {sid} is not enrolled in class {class_id} for subject {sub_id}"
                        ), 400

                existing = db.execute(
                    """
                    SELECT id FROM attendance
                    WHERE student_id = ? AND subject_id = ? AND attendance_date = ?
                    """,
                    (sid, sub_id, att_date)
                ).fetchone()

                if existing is not None and not allow_update:
                    return jsonify(
                        error=f"Attendance record already exists for student ID {sid} on {att_date}"
                    ), 409

                records_to_process.append((sid, sub_id, att_date, norm_status, existing["id"] if existing else None))

            except sqlite3.Error:
                return jsonify(error="Database temporarily unavailable"), 503

        try:
            processed_results = []
            for sid, sub_id, att_date, norm_status, existing_id in records_to_process:
                if existing_id is not None:
                    db.execute(
                        "UPDATE attendance SET status = ? WHERE id = ?",
                        (norm_status, existing_id)
                    )
                    record_id = existing_id
                else:
                    cur = db.execute(
                        """
                        INSERT INTO attendance (student_id, subject_id, attendance_date, status)
                        VALUES (?, ?, ?, ?)
                        """,
                        (sid, sub_id, att_date, norm_status)
                    )
                    record_id = cur.lastrowid

                processed_results.append({
                    "id": record_id,
                    "student_id": sid,
                    "subject_id": sub_id,
                    "attendance_date": att_date,
                    "date": att_date,
                    "status": norm_status
                })
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            return jsonify(
                error="Duplicate attendance record or integrity violation"
            ), 409
        except sqlite3.Error:
            db.rollback()
            return jsonify(error="Database temporarily unavailable"), 503

        return jsonify(
            message="Attendance recorded successfully",
            records=processed_results,
            count=len(processed_results)
        ), 201

    # Single record submission
    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    student_id = data.get("student_id")
    subject_id = data.get("subject_id")
    class_id = data.get("class_id")
    date_str = data.get("attendance_date")
    if date_str is None:
        date_str = data.get("date")
    status = data.get("status")
    allow_update = bool(
        data.get("update_existing") or data.get("allow_update") or data.get("update")
    )

    if (
        student_id is None
        or subject_id is None
        or date_str is None
        or status is None
    ):
        return jsonify(
            error="student_id, subject_id, attendance_date, and status are required"
        ), 400

    norm_status = normalize_status(status)
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

        existing = db.execute(
            """
            SELECT id FROM attendance
            WHERE student_id = ? AND subject_id = ? AND attendance_date = ?
            """,
            (student_id, subject_id, attendance_date)
        ).fetchone()

        if existing is not None:
            if not allow_update:
                return jsonify(
                    error="Attendance record already exists for this student, subject, and date"
                ), 409

            # Update existing record
            db.execute(
                "UPDATE attendance SET status = ? WHERE id = ?",
                (norm_status, existing["id"])
            )
            db.commit()
            record_id = existing["id"]
            message_text = "Attendance record updated successfully"
            status_code = 200
        else:
            cur = db.execute(
                """
                INSERT INTO attendance (student_id, subject_id, attendance_date, status)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, subject_id, attendance_date, norm_status)
            )
            db.commit()
            record_id = cur.lastrowid
            message_text = "Attendance recorded successfully"
            status_code = 201

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify(
            error="Attendance record already exists for this student, subject, and date"
        ), 409
    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503

    return jsonify(
        message=message_text,
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

