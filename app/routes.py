"""Attendance Management System API routes: FR-01 authentication, FR-07 user management, FR-02/03 attendance records, FR-04 percentages, and FR-15 logout."""

import sqlite3
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request, session, g
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

VALID_STATUSES = {"Present", "Absent", "Late"}
VALID_ROLES = {"admin", "teacher", "student"}


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
    """Check whether the API is running."""
    return jsonify(status="ok"), 200


# =====================================================================
# FR-01: Role-Based Access Control
# =====================================================================

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


# =====================================================================
# FR-07: User Management
# =====================================================================

@api.post("/users")
@login_required(["admin"])
def create_user():
    """
    Create an admin, teacher, or student account.

    Expected JSON:
    {
        "username": "student01",
        "password": "StrongPassword123",
        "role": "student"
    }
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="JSON request body required"
        ), 400

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if (
        not isinstance(username, str)
        or not username.strip()
        or not isinstance(password, str)
        or not password
        or role not in VALID_ROLES
    ):
        return jsonify(
            error="Username, password, and valid role are required"
        ), 400

    active = 1
    if "active" in data:
        raw_active = data["active"]
        if isinstance(raw_active, bool):
            active = 1 if raw_active else 0
        elif isinstance(raw_active, int) and raw_active in (0, 1):
            active = raw_active
        else:
            return jsonify(error="Active status must be a boolean or 0/1"), 400

    try:
        db = get_db()
        password_hash = generate_password_hash(password)

        cursor = db.execute(
            """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (?, ?, ?, ?)
            """,
            (username.strip(), password_hash, role, active),
        )
        db.commit()

        return jsonify(
            message="User created successfully",
            user={
                "id": cursor.lastrowid,
                "username": username.strip(),
                "role": role,
                "active": active,
            },
        ), 201

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify(
            error="Username already exists"
        ), 409

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.get("/users")
@login_required(["admin"])
def list_users():
    """List user accounts with optional role and active filtering."""
    db = get_db()
    role = request.args.get("role")
    active = request.args.get("active")

    query = "SELECT id, username, role, active FROM users"
    conditions = []
    params = []

    if role:
        cleaned_role = role.strip().lower()
        if cleaned_role not in VALID_ROLES:
            return jsonify(error="Invalid role filter"), 400
        conditions.append("role = ?")
        params.append(cleaned_role)

    if active is not None:
        if active.lower() in ("true", "1"):
            conditions.append("active = 1")
        elif active.lower() in ("false", "0"):
            conditions.append("active = 0")
        else:
            return jsonify(error="Invalid active filter"), 400

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id"

    try:
        users = db.execute(query, params).fetchall()
        return jsonify(
            users=[
                {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "active": user["active"],
                }
                for user in users
            ]
        ), 200

    except sqlite3.Error:
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.get("/users/<int:user_id>")
@login_required(["admin"])
def get_user(user_id):
    """Retrieve details for a specific user."""
    try:
        user = get_db().execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            return jsonify(error="User not found"), 404

        return jsonify(
            user={
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "active": user["active"],
            }
        ), 200

    except sqlite3.Error:
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.route("/users/<int:user_id>", methods=["PUT", "PATCH"])
@login_required(["admin"])
def update_user(user_id):
    """
    Update a user's information (username, role, password, active).
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify(
            error="JSON request body required"
        ), 400

    allowed_fields = {"username", "role", "password", "active"}

    if not set(data).issubset(allowed_fields):
        return jsonify(
            error="Only valid user fields can be updated"
        ), 400

    username = data.get("username")
    role = data.get("role")
    password = data.get("password")
    active = data.get("active")

    if "username" in data and (
        not isinstance(username, str)
        or not username.strip()
    ):
        return jsonify(
            error="Username cannot be empty"
        ), 400

    if "role" in data and role not in VALID_ROLES:
        return jsonify(
            error="Role must be admin, teacher, or student"
        ), 400

    if "password" in data and (
        not isinstance(password, str)
        or not password
    ):
        return jsonify(
            error="Password cannot be empty"
        ), 400

    if "active" in data:
        if isinstance(active, bool):
            active = 1 if active else 0
        elif isinstance(active, int) and active in (0, 1):
            pass
        else:
            return jsonify(error="Active status must be a boolean or 0/1"), 400

    try:
        db = get_db()

        user = db.execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify(
                error="User not found"
            ), 404

        new_username = (
            username.strip()
            if "username" in data
            else user["username"]
        )

        new_role = (
            role
            if "role" in data
            else user["role"]
        )

        new_active = (
            active
            if "active" in data
            else user["active"]
        )

        if "password" in data:
            new_password_hash = generate_password_hash(password)
            db.execute(
                """
                UPDATE users
                SET username = ?, role = ?, active = ?, password_hash = ?
                WHERE id = ?
                """,
                (new_username, new_role, new_active, new_password_hash, user_id),
            )
        else:
            db.execute(
                """
                UPDATE users
                SET username = ?, role = ?, active = ?
                WHERE id = ?
                """,
                (new_username, new_role, new_active, user_id),
            )

        db.commit()

        return jsonify(
            message="User updated successfully",
            user={
                "id": user_id,
                "username": new_username,
                "role": new_role,
                "active": new_active,
            }
        ), 200

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify(
            error="Username already exists"
        ), 409

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.route("/users/<int:user_id>/deactivate", methods=["POST", "PATCH"])
@login_required(["admin"])
def deactivate_user(user_id):
    """
    Deactivate a user account without deleting records.
    """
    try:
        db = get_db()

        user = db.execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify(
                error="User not found"
            ), 404

        if not user["active"]:
            return jsonify(
                error="User is already inactive"
            ), 409

        db.execute(
            """
            UPDATE users
            SET active = 0
            WHERE id = ?
            """,
            (user_id,)
        )
        db.commit()

        return jsonify(
            message="User deactivated successfully",
            user={
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "active": 0,
            }
        ), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


@api.route("/users/<int:user_id>/activate", methods=["POST", "PATCH"])
@login_required(["admin"])
def activate_user(user_id):
    """
    Activate a user account.
    """
    try:
        db = get_db()

        user = db.execute(
            """
            SELECT id, username, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify(
                error="User not found"
            ), 404

        if user["active"]:
            return jsonify(
                error="User is already active"
            ), 409

        db.execute(
            """
            UPDATE users
            SET active = 1
            WHERE id = ?
            """,
            (user_id,)
        )
        db.commit()

        return jsonify(
            message="User activated successfully",
            user={
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "active": 1,
            }
        ), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(
            error="Database temporarily unavailable"
        ), 503


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
        class_id: Accepted for backward compatibility.
    """
    db = get_db()
    current_user = g.current_user

    subject_id_arg = request.args.get("subject_id")
    student_id_arg = request.args.get("student_id")
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
    # Validate attendance_date.
    # ---------------------------------------------------------------
    attendance_date = None

    if date_arg is not None:
        attendance_date = parse_date(date_arg)

        if attendance_date is None:
            return jsonify(
                error="Invalid date format, expected YYYY-MM-DD"
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

        # Filter by student.
        if student_id is not None:
            query += " AND a.student_id = ?"
            params.append(student_id)

        # Filter by attendance status.
        if status_arg is not None:
            query += " AND a.status = ?"
            params.append(status_arg)

        # Preserve compatibility with callers passing class_id.
        # This schema does not have a class_id column in the
        # attendance table, so class_id is not used as a SQL filter.

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


# =====================================================================
# FR-15: User Logout
# =====================================================================

@api.post("/logout")
@login_required()
def logout():
    """
    Log out the currently authenticated user.

    Clears the Flask session so the user can no longer access
    protected endpoints without logging in again.
    """

    session.clear()

    return jsonify(
        message="Logged out successfully"
    ), 200