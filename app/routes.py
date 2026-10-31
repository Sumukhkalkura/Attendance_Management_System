"""Attendance Management System API routes: FR-01 authentication, FR-07 user management, FR-02/03 attendance records, FR-04 percentages, FR-05 viewing, FR-06 reporting, FR-08 classes/subjects, FR-09 enrollments, FR-12 report export, and FR-15 logout."""

import sqlite3
from datetime import datetime
from functools import wraps

import csv
import io
import textwrap
from flask import Blueprint, jsonify, request, session, g, Response
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

# =====================================================================
# FR-03: Attendance Record Management & Teacher Helpers
# =====================================================================



# =====================================================================
# FR-08: Class and Subject Management
# =====================================================================

@api.get("/classes")
@login_required(["admin"])
def list_classes():
    """Return all classes with teacher assignment information."""
    try:
        rows = get_db().execute(
            """
            SELECT
                c.id,
                c.name,
                c.teacher_id,
                u.username AS teacher_username
            FROM classes AS c
            LEFT JOIN users AS u ON c.teacher_id = u.id
            ORDER BY c.name
            """
        ).fetchall()

        return jsonify(
            classes=[
                {
                    "id": row["id"],
                    "name": row["name"],
                    "teacher_id": row["teacher_id"],
                    "teacher_username": row["teacher_username"],
                }
                for row in rows
            ]
        ), 200

    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503


@api.post("/classes")
@login_required(["admin"])
def create_class():
    """Create a new class, optionally assigning a teacher."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    name = data.get("name")
    teacher_id = data.get("teacher_id")

    if not isinstance(name, str) or not name.strip():
        return jsonify(error="Class name is required"), 400

    if teacher_id is not None and (
        isinstance(teacher_id, bool) or not isinstance(teacher_id, int)
    ):
        return jsonify(error="teacher_id must be an integer"), 400

    name = name.strip()

    try:
        db = get_db()

        if teacher_id is not None:
            teacher = db.execute(
                """
                SELECT id
                FROM users
                WHERE id = ? AND role = 'teacher' AND active = 1
                """,
                (teacher_id,)
            ).fetchone()

            if teacher is None:
                return jsonify(error="Active teacher account not found"), 400

        cursor = db.execute(
            "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
            (name, teacher_id)
        )
        db.commit()

        class_dict = {
            "id": cursor.lastrowid,
            "name": name,
            "teacher_id": teacher_id,
        }

        return jsonify({
            "message": "Class created successfully",
            "class_info": class_dict,
            "class": class_dict,
        }), 201

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify(error="Class name already exists"), 409

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.get("/classes/<int:class_id>")
@login_required(["admin"])
def get_class(class_id):
    """Retrieve details for a specific class."""
    try:
        row = get_db().execute(
            """
            SELECT
                c.id,
                c.name,
                c.teacher_id,
                u.username AS teacher_username
            FROM classes AS c
            LEFT JOIN users AS u ON c.teacher_id = u.id
            WHERE c.id = ?
            """,
            (class_id,)
        ).fetchone()

        if row is None:
            return jsonify(error="Class not found"), 404

        class_dict = {
            "id": row["id"],
            "name": row["name"],
            "teacher_id": row["teacher_id"],
            "teacher_username": row["teacher_username"],
        }

        return jsonify({
            "class_info": class_dict,
            "class": class_dict,
        }), 200

    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503


@api.route("/classes/<int:class_id>", methods=["PUT", "PATCH"])
@login_required(["admin"])
def update_class(class_id):
    """Update an existing class name or teacher assignment."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    allowed_fields = {"name", "teacher_id"}
    if not set(data).issubset(allowed_fields) or not data:
        return jsonify(error="Valid class update fields required"), 400

    name = data.get("name")
    teacher_id = data.get("teacher_id")

    if "name" in data and (not isinstance(name, str) or not name.strip()):
        return jsonify(error="Class name is required"), 400

    if "teacher_id" in data and teacher_id is not None and (
        isinstance(teacher_id, bool) or not isinstance(teacher_id, int)
    ):
        return jsonify(error="teacher_id must be an integer"), 400

    try:
        db = get_db()

        existing = db.execute(
            "SELECT id, name, teacher_id FROM classes WHERE id = ?",
            (class_id,)
        ).fetchone()

        if existing is None:
            return jsonify(error="Class not found"), 404

        new_name = name.strip() if "name" in data else existing["name"]
        new_teacher_id = existing["teacher_id"]

        if "teacher_id" in data:
            if teacher_id is not None:
                teacher = db.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE id = ? AND role = 'teacher' AND active = 1
                    """,
                    (teacher_id,)
                ).fetchone()

                if teacher is None:
                    return jsonify(error="Active teacher account not found"), 400
                new_teacher_id = teacher_id
            else:
                new_teacher_id = None

        db.execute(
            "UPDATE classes SET name = ?, teacher_id = ? WHERE id = ?",
            (new_name, new_teacher_id, class_id)
        )
        db.commit()

        class_dict = {
            "id": class_id,
            "name": new_name,
            "teacher_id": new_teacher_id,
        }

        return jsonify({
            "message": "Class updated successfully",
            "class_info": class_dict,
            "class": class_dict,
        }), 200

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify(error="Class name already exists"), 409

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.route("/classes/<int:class_id>/teacher", methods=["PUT", "PATCH"])
@login_required(["admin"])
def assign_class_teacher(class_id):
    """Assign or reassign an active teacher to a class."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    teacher_id = data.get("teacher_id")

    if isinstance(teacher_id, bool) or not isinstance(teacher_id, int):
        return jsonify(error="teacher_id must be an integer"), 400

    try:
        db = get_db()

        cls = db.execute("SELECT id FROM classes WHERE id = ?", (class_id,)).fetchone()
        if cls is None:
            return jsonify(error="Class not found"), 404

        teacher = db.execute(
            """
            SELECT id
            FROM users
            WHERE id = ? AND role = 'teacher' AND active = 1
            """,
            (teacher_id,)
        ).fetchone()

        if teacher is None:
            return jsonify(error="Active teacher account not found"), 400

        db.execute("UPDATE classes SET teacher_id = ? WHERE id = ?", (teacher_id, class_id))
        db.commit()

        return jsonify(
            message="Teacher assigned to class successfully",
            class_id=class_id,
            teacher_id=teacher_id,
        ), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.post("/classes/<int:class_id>/subjects")
@login_required(["admin"])
def associate_subject_with_class(class_id):
    """Associate a subject with a class."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    subject_id = data.get("subject_id")
    if isinstance(subject_id, bool) or not isinstance(subject_id, int):
        return jsonify(error="subject_id must be an integer"), 400

    try:
        db = get_db()

        cls = db.execute("SELECT id FROM classes WHERE id = ?", (class_id,)).fetchone()
        if cls is None:
            return jsonify(error="Class not found"), 404

        subj = db.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if subj is None:
            return jsonify(error="Subject not found"), 404

        exists = db.execute(
            "SELECT 1 FROM class_subjects WHERE class_id = ? AND subject_id = ?",
            (class_id, subject_id)
        ).fetchone()

        if exists is not None:
            return jsonify(error="Subject already associated with this class"), 409

        db.execute(
            "INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
            (class_id, subject_id)
        )
        db.commit()

        return jsonify(
            message="Subject associated with class successfully",
            class_id=class_id,
            subject_id=subject_id,
        ), 201

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.get("/classes/<int:class_id>/subjects")
@login_required(["admin"])
def get_class_subjects(class_id):
    """List all subjects associated with a specific class."""
    try:
        db = get_db()

        cls = db.execute("SELECT id, name FROM classes WHERE id = ?", (class_id,)).fetchone()
        if cls is None:
            return jsonify(error="Class not found"), 404

        rows = db.execute(
            """
            SELECT DISTINCT
                s.id,
                s.name,
                s.teacher_id,
                u.username AS teacher_username
            FROM subjects AS s
            JOIN class_subjects AS cs ON s.id = cs.subject_id
            LEFT JOIN users AS u ON s.teacher_id = u.id
            WHERE cs.class_id = ?
            ORDER BY s.name
            """,
            (class_id,)
        ).fetchall()

        return jsonify(
            class_id=class_id,
            subjects=[
                {
                    "id": row["id"],
                    "name": row["name"],
                    "teacher_id": row["teacher_id"],
                    "teacher_username": row["teacher_username"],
                }
                for row in rows
            ]
        ), 200

    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503


@api.delete("/classes/<int:class_id>/subjects/<int:subject_id>")
@login_required(["admin"])
def remove_subject_from_class(class_id, subject_id):
    """Dissociate a subject from a class."""
    try:
        db = get_db()

        cls = db.execute("SELECT id FROM classes WHERE id = ?", (class_id,)).fetchone()
        if cls is None:
            return jsonify(error="Class not found"), 404

        subj = db.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if subj is None:
            return jsonify(error="Subject not found"), 404

        cursor = db.execute(
            "DELETE FROM class_subjects WHERE class_id = ? AND subject_id = ?",
            (class_id, subject_id)
        )
        db.commit()

        return jsonify(message="Subject dissociated from class successfully"), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.get("/subjects")
@login_required(["admin"])
def list_subjects():
    """Return all subjects and their assigned teachers, with optional class_id filter."""
    class_id = request.args.get("class_id", type=int)

    try:
        db = get_db()

        if class_id is not None:
            rows = db.execute(
                """
                SELECT DISTINCT
                    s.id,
                    s.name,
                    s.teacher_id,
                    u.username AS teacher_username
                FROM subjects AS s
                LEFT JOIN class_subjects AS cs ON s.id = cs.subject_id
                LEFT JOIN users AS u ON s.teacher_id = u.id
                WHERE cs.class_id = ?
                ORDER BY s.name
                """,
                (class_id,)
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.teacher_id,
                    u.username AS teacher_username
                FROM subjects AS s
                LEFT JOIN users AS u ON s.teacher_id = u.id
                ORDER BY s.name
                """
            ).fetchall()

        return jsonify(
            subjects=[
                {
                    "id": row["id"],
                    "name": row["name"],
                    "teacher_id": row["teacher_id"],
                    "teacher_username": row["teacher_username"],
                }
                for row in rows
            ]
        ), 200

    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503


@api.post("/subjects")
@login_required(["admin"])
def create_subject():
    """Create a subject, optionally assigning a teacher and associating with a class."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    name = data.get("name")
    teacher_id = data.get("teacher_id")
    class_id = data.get("class_id")

    if not isinstance(name, str) or not name.strip():
        return jsonify(error="Subject name is required"), 400

    if teacher_id is not None and (
        isinstance(teacher_id, bool) or not isinstance(teacher_id, int)
    ):
        return jsonify(error="teacher_id must be an integer"), 400

    if class_id is not None and (
        isinstance(class_id, bool) or not isinstance(class_id, int)
    ):
        return jsonify(error="class_id must be an integer"), 400

    try:
        db = get_db()

        if teacher_id is not None:
            teacher = db.execute(
                """
                SELECT id
                FROM users
                WHERE id = ? AND role = 'teacher' AND active = 1
                """,
                (teacher_id,)
            ).fetchone()

            if teacher is None:
                return jsonify(error="Active teacher account not found"), 400

        if class_id is not None:
            cls = db.execute("SELECT id FROM classes WHERE id = ?", (class_id,)).fetchone()
            if cls is None:
                return jsonify(error="Class not found"), 404

        name = name.strip()

        cursor = db.execute(
            "INSERT INTO subjects (name, teacher_id) VALUES (?, ?)",
            (name, teacher_id)
        )
        subject_id = cursor.lastrowid

        if class_id is not None:
            db.execute(
                "INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
                (class_id, subject_id)
            )

        db.commit()

        resp_dict = {
            "id": subject_id,
            "name": name,
            "teacher_id": teacher_id,
        }
        if class_id is not None:
            resp_dict["class_id"] = class_id

        return jsonify(
            message="Subject created successfully",
            subject=resp_dict,
        ), 201

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify(error="Subject name already exists"), 409

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.get("/subjects/<int:subject_id>")
@login_required(["admin"])
def get_subject(subject_id):
    """Retrieve details for a specific subject."""
    try:
        row = get_db().execute(
            """
            SELECT
                s.id,
                s.name,
                s.teacher_id,
                u.username AS teacher_username
            FROM subjects AS s
            LEFT JOIN users AS u ON s.teacher_id = u.id
            WHERE s.id = ?
            """,
            (subject_id,)
        ).fetchone()

        if row is None:
            return jsonify(error="Subject not found"), 404

        return jsonify(
            subject={
                "id": row["id"],
                "name": row["name"],
                "teacher_id": row["teacher_id"],
                "teacher_username": row["teacher_username"],
            }
        ), 200

    except sqlite3.Error:
        return jsonify(error="Database temporarily unavailable"), 503


@api.route("/subjects/<int:subject_id>", methods=["PUT", "PATCH"])
@login_required(["admin"])
def update_subject(subject_id):
    """Update a subject name or teacher assignment."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    allowed_fields = {"name", "teacher_id", "class_id"}
    if not set(data).issubset(allowed_fields) or not data:
        return jsonify(error="Valid subject update fields required"), 400

    name = data.get("name")
    teacher_id = data.get("teacher_id")
    class_id = data.get("class_id")

    if "name" in data and (not isinstance(name, str) or not name.strip()):
        return jsonify(error="Subject name is required"), 400

    if "teacher_id" in data and teacher_id is not None and (
        isinstance(teacher_id, bool) or not isinstance(teacher_id, int)
    ):
        return jsonify(error="teacher_id must be an integer"), 400

    if "class_id" in data and class_id is not None and (
        isinstance(class_id, bool) or not isinstance(class_id, int)
    ):
        return jsonify(error="class_id must be an integer"), 400

    try:
        db = get_db()

        existing = db.execute(
            "SELECT id, name, teacher_id FROM subjects WHERE id = ?",
            (subject_id,)
        ).fetchone()

        if existing is None:
            return jsonify(error="Subject not found"), 404

        new_name = name.strip() if "name" in data else existing["name"]
        new_teacher_id = existing["teacher_id"]

        if "teacher_id" in data:
            if teacher_id is not None:
                teacher = db.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE id = ? AND role = 'teacher' AND active = 1
                    """,
                    (teacher_id,)
                ).fetchone()

                if teacher is None:
                    return jsonify(error="Active teacher account not found"), 400
                new_teacher_id = teacher_id
            else:
                new_teacher_id = None

        if "class_id" in data and class_id is not None:
            cls = db.execute("SELECT id FROM classes WHERE id = ?", (class_id,)).fetchone()
            if cls is None:
                return jsonify(error="Class not found"), 404
            db.execute(
                "INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
                (class_id, subject_id)
            )

        db.execute(
            "UPDATE subjects SET name = ?, teacher_id = ? WHERE id = ?",
            (new_name, new_teacher_id, subject_id)
        )
        db.commit()

        return jsonify(
            message="Subject updated successfully",
            subject={
                "id": subject_id,
                "name": new_name,
                "teacher_id": new_teacher_id,
            }
        ), 200

    except sqlite3.IntegrityError:
        get_db().rollback()
        return jsonify(error="Subject name already exists"), 409

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


@api.route("/subjects/<int:subject_id>/teacher", methods=["PUT", "PATCH"])
@login_required(["admin"])
def assign_teacher(subject_id):
    """Assign or reassign an active teacher to a subject."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="JSON request body required"), 400

    teacher_id = data.get("teacher_id")

    if isinstance(teacher_id, bool) or not isinstance(teacher_id, int):
        return jsonify(error="teacher_id must be an integer"), 400

    try:
        db = get_db()

        subject = db.execute(
            "SELECT id FROM subjects WHERE id = ?",
            (subject_id,)
        ).fetchone()

        if subject is None:
            return jsonify(error="Subject not found"), 404

        teacher = db.execute(
            """
            SELECT id
            FROM users
            WHERE id = ? AND role = 'teacher' AND active = 1
            """,
            (teacher_id,)
        ).fetchone()

        if teacher is None:
            return jsonify(error="Active teacher account not found"), 400

        db.execute(
            "UPDATE subjects SET teacher_id = ? WHERE id = ?",
            (teacher_id, subject_id)
        )
        db.commit()

        return jsonify(
            message="Teacher assigned successfully",
            subject_id=subject_id,
            teacher_id=teacher_id,
        ), 200

    except sqlite3.Error:
        get_db().rollback()
        return jsonify(error="Database temporarily unavailable"), 503


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


# =====================================================================
# FR-06 & FR-12: Attendance Reporting & Export Helpers
# =====================================================================

SUPPORTED_EXPORT_FORMATS = {"csv", "pdf", "json"}


def _get_export_filename(report_payload, file_ext):
    """Determine a sensible download filename based on applied filters."""
    if report_payload.get("student"):
        username = report_payload["student"].get("username", "student")
        return f"attendance_report_student_{username}.{file_ext}"
    if report_payload.get("class"):
        cname = str(report_payload["class"].get("name", "class")).replace(" ", "_")
        return f"attendance_report_class_{cname}.{file_ext}"
    if report_payload.get("subject"):
        sname = str(report_payload["subject"].get("name", "subject")).replace(" ", "_")
        return f"attendance_report_subject_{sname}.{file_ext}"
    return f"attendance_report.{file_ext}"


def _sanitize_csv_cell(value):
    """Sanitize cell value to prevent CSV Formula Injection (CWE-1236).

    Prepend a single quote (') if the text begins with '=', '+', '-', '@', '\t', or '\r',
    or begins with whitespace followed by one of those formula triggers.
    """
    if value is None:
        return ""
    val_str = str(value)
    stripped = val_str.lstrip(" \t\r\n")
    if val_str and (val_str[0] in ("=", "+", "-", "@", "\t", "\r") or (stripped and stripped[0] in ("=", "+", "-", "@"))):
        return f"'{val_str}"
    return val_str


def _generate_csv_report(report_payload):
    """Generate a clean, RFC 4180 compliant CSV string for the attendance report."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Attendance ID",
        "Date",
        "Student ID",
        "Student Name",
        "Class ID",
        "Class Name",
        "Subject ID",
        "Subject Name",
        "Status",
    ])

    for rec in report_payload.get("records", []):
        writer.writerow([
            _sanitize_csv_cell(rec.get("attendance_id") or rec.get("id")),
            _sanitize_csv_cell(rec.get("attendance_date") or rec.get("date")),
            _sanitize_csv_cell(rec.get("student_id")),
            _sanitize_csv_cell(rec.get("student_name") or rec.get("student_username")),
            _sanitize_csv_cell(rec.get("class_id") or ""),
            _sanitize_csv_cell(rec.get("class_name") or ""),
            _sanitize_csv_cell(rec.get("subject_id") or ""),
            _sanitize_csv_cell(rec.get("subject_name") or ""),
            _sanitize_csv_cell(rec.get("status")),
        ])

    return output.getvalue()


def _generate_pdf_report(report_payload, title="Attendance Report"):
    """Generate a clean, valid PDF 1.4 document for the attendance report.

    Formats text properly without truncating or overlapping long student names,
    subject names, or class names, and paginates large reports cleanly.
    """
    summary = report_payload.get("summary", {})
    filters = report_payload.get("filters", {})
    records = report_payload.get("records", [])

    w_date = 12
    w_student = 20
    w_class = 14
    w_subject = 22
    w_status = 10
    table_width = 82
    table_sep = "-" * table_width
    table_header = f"{'Date':<12} {'Student':<20} {'Class':<14} {'Subject':<22} {'Status':<10}"

    meta_lines = []
    meta_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    filter_parts = []
    if report_payload.get("student"):
        filter_parts.append(
            f"Student: {report_payload['student'].get('username', '')} (ID: {report_payload['student'].get('id', '')})"
        )
    elif filters.get("student_id"):
        filter_parts.append(f"Student ID: {filters['student_id']}")

    if report_payload.get("class"):
        filter_parts.append(
            f"Class: {report_payload['class'].get('name', '')} (ID: {report_payload['class'].get('id', '')})"
        )
    elif filters.get("class_id"):
        filter_parts.append(f"Class ID: {filters['class_id']}")

    if report_payload.get("subject"):
        filter_parts.append(
            f"Subject: {report_payload['subject'].get('name', '')} (ID: {report_payload['subject'].get('id', '')})"
        )
    elif filters.get("subject_id"):
        filter_parts.append(f"Subject ID: {filters['subject_id']}")

    if filters.get("start_date") or filters.get("end_date"):
        start = filters.get("start_date") or "Earliest"
        end = filters.get("end_date") or "Latest"
        filter_parts.append(f"Date Range: {start} to {end}")

    if filters.get("status"):
        filter_parts.append(f"Status Filter: {filters['status']}")

    filter_text = "Filters: " + (" | ".join(filter_parts) if filter_parts else "All Records")
    for f_line in textwrap.wrap(filter_text, width=table_width):
        meta_lines.append(f_line)

    summary_text = (
        f"Summary: Total: {summary.get('total_records', len(records))} | "
        f"Present: {summary.get('present_count', 0)} | "
        f"Absent: {summary.get('absent_count', 0)} | "
        f"Late: {summary.get('late_count', 0)} | "
        f"Attendance Rate: {summary.get('attendance_percentage', 0.0)}%"
    )
    for s_line in textwrap.wrap(summary_text, width=table_width):
        meta_lines.append(s_line)

    MAX_PAGE_LINES = 38
    pages = []
    current_page = list(meta_lines)
    current_page.append(table_sep)
    current_page.append(table_header)
    current_page.append(table_sep)

    def start_new_page():
        nonlocal current_page
        pages.append(current_page)
        current_page = [table_sep, table_header, table_sep]

    if not records:
        current_page.append("No attendance records found matching the specified criteria.")
        current_page.append(table_sep)
        current_page.append("End of Attendance Report")
        pages.append(current_page)
    else:
        for r in records:
            r_date = str(r.get("attendance_date") or r.get("date") or "")
            r_student = str(r.get("student_name") or r.get("student_username") or "")
            r_class = str(r.get("class_name") or "N/A")
            r_subject = str(r.get("subject_name") or "")
            r_status = str(r.get("status") or "")

            d_lines = textwrap.wrap(r_date, width=w_date, break_long_words=True) or [""]
            st_lines = textwrap.wrap(r_student, width=w_student, break_long_words=True) or [""]
            c_lines = textwrap.wrap(r_class, width=w_class, break_long_words=True) or [""]
            su_lines = textwrap.wrap(r_subject, width=w_subject, break_long_words=True) or [""]
            stat_lines = textwrap.wrap(r_status, width=w_status, break_long_words=True) or [""]

            row_height = max(len(d_lines), len(st_lines), len(c_lines), len(su_lines), len(stat_lines))
            row_lines = []
            for i in range(row_height):
                d = d_lines[i] if i < len(d_lines) else ""
                st = st_lines[i] if i < len(st_lines) else ""
                c = c_lines[i] if i < len(c_lines) else ""
                su = su_lines[i] if i < len(su_lines) else ""
                stat = stat_lines[i] if i < len(stat_lines) else ""
                row_lines.append(f"{d:<12} {st:<20} {c:<14} {su:<22} {stat:<10}".rstrip())

            if len(current_page) + row_height > MAX_PAGE_LINES and len(current_page) > 3:
                start_new_page()

            current_page.extend(row_lines)

        if len(current_page) + 2 > MAX_PAGE_LINES and len(current_page) > 3:
            start_new_page()
        current_page.append(table_sep)
        current_page.append("End of Attendance Report")
        pages.append(current_page)

    num_pages = len(pages)
    font_obj_num = 3
    page_obj_nums = [4 + 2 * i for i in range(num_pages)]
    content_obj_nums = [5 + 2 * i for i in range(num_pages)]
    total_objects = 3 + 2 * num_pages

    obj_dict = {}
    obj_dict[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids_str = " ".join(f"{num} 0 R" for num in page_obj_nums)
    obj_dict[2] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode("ascii")
    obj_dict[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"

    for i, p_lines in enumerate(pages):
        page_num = i + 1
        stream_cmds = ["BT", "/F1 12 Tf", "40 750 Td"]
        page_title = title if num_pages == 1 else f"{title} (Page {page_num} of {num_pages})"
        escaped_title = page_title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_cmds.append(f"({escaped_title}) Tj")
        stream_cmds.append("/F1 9 Tf")
        stream_cmds.append("0 -20 Td")

        for line_item in p_lines:
            escaped = line_item.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_cmds.append(f"({escaped}) Tj")
            stream_cmds.append("0 -14 Td")
        stream_cmds.append("ET")
        stream_bytes = "\n".join(stream_cmds).encode("latin1", errors="replace")

        p_obj = page_obj_nums[i]
        c_obj = content_obj_nums[i]
        obj_dict[p_obj] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {c_obj} 0 R /Resources << /Font << /F1 {font_obj_num} 0 R >> >> >>"
        ).encode("ascii")
        obj_dict[c_obj] = (
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream"
        )

    out = [b"%PDF-1.4\n"]
    offsets = {}
    for obj_num in range(1, total_objects + 1):
        offsets[obj_num] = sum(len(x) for x in out)
        out.append(f"{obj_num} 0 obj\n".encode("ascii") + obj_dict[obj_num] + b"\nendobj\n")

    xref_offset = sum(len(x) for x in out)
    out.append(f"xref\n0 {total_objects + 1}\n0000000000 65535 f \n".encode("ascii"))
    for obj_num in range(1, total_objects + 1):
        out.append(f"{offsets[obj_num]:010d} 00000 n \n".encode("ascii"))
    out.append(
        f"trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return b"".join(out)


def _format_export_response(report_payload, fmt):
    """Format and return the HTTP Response for the requested export format."""
    clean_fmt = fmt.lower().strip() if isinstance(fmt, str) else ""
    if clean_fmt not in SUPPORTED_EXPORT_FORMATS:
        return jsonify(
            error=f"Unsupported export format '{clean_fmt}'. Supported formats are: csv, pdf, json"
        ), 400

    if clean_fmt == "csv":
        csv_data = _generate_csv_report(report_payload)
        filename = _get_export_filename(report_payload, "csv")
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            status=200,
        )

    elif clean_fmt == "pdf":
        pdf_data = _generate_pdf_report(report_payload)
        filename = _get_export_filename(report_payload, "pdf")
        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            status=200,
        )

    elif clean_fmt == "json":
        filename = _get_export_filename(report_payload, "json")
        response = jsonify(report_payload)
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response, 200


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
