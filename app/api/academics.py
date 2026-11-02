"""FR-08 class and subject management: classes, subjects, class-subject links,
teacher assignments, and the teacher's own class/subject listings.
"""

import sqlite3

from flask import g, jsonify, request

from ..auth import login_required
from ..db import get_db
from .blueprint import api

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
