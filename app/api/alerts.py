"""FR-11 attendance alerts and the persisted low-attendance threshold.
"""

import math
import sqlite3

from flask import current_app, g, jsonify, request

from ..auth import login_required
from ..db import get_db
from .blueprint import api

# =====================================================================
# FR-11: Attendance Alert
# =====================================================================

DEFAULT_ATTENDANCE_THRESHOLD = 75.0
SETTING_KEY_THRESHOLD = "attendance_threshold"


def get_persisted_threshold(db=None):
    """
    Retrieve the persisted global attendance threshold from the database.
    Falls back to current_app.config["DEFAULT_ATTENDANCE_THRESHOLD"] or
    DEFAULT_ATTENDANCE_THRESHOLD if not found.
    """
    if db is None:
        try:
            db = get_db()
        except RuntimeError:
            db = None

    default_val = current_app.config.get(
        "DEFAULT_ATTENDANCE_THRESHOLD", DEFAULT_ATTENDANCE_THRESHOLD
    )

    if db is None:
        return default_val

    try:
        row = db.execute(
            "SELECT value FROM settings WHERE key = ?",
            (SETTING_KEY_THRESHOLD,),
        ).fetchone()
        if row is not None:
            val, err = validate_threshold(row["value"])
            if not err and val is not None:
                return val
    except sqlite3.Error:
        pass

    return default_val


def set_persisted_threshold(val, db=None):
    """
    Persist the global attendance threshold in the database and update app.config.
    """
    if db is None:
        db = get_db()

    db.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (SETTING_KEY_THRESHOLD, str(val)),
    )
    db.commit()
    current_app.config["DEFAULT_ATTENDANCE_THRESHOLD"] = val


def validate_threshold(raw_value, default=None):
    """
    Validate that threshold is a numeric percentage between 0.0 and 100.0 inclusive.
    Returns (float_value, error_message). On success, error_message is None.
    Rejects booleans, negative values, values > 100, empty/invalid strings, and malformed inputs.
    """
    if raw_value is None:
        if default is not None:
            return float(default), None
        return None, "threshold is required"

    if isinstance(raw_value, bool):
        return None, "threshold must be a valid number between 0 and 100"

    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return None, "threshold cannot be empty"
        try:
            val = float(stripped)
        except (ValueError, TypeError):
            return None, "threshold must be a valid number between 0 and 100"
    elif isinstance(raw_value, (int, float)):
        val = float(raw_value)
    else:
        return None, "threshold must be a valid number between 0 and 100"

    if math.isnan(val) or math.isinf(val):
        return None, "threshold must be a finite number between 0 and 100"

    if val < 0.0 or val > 100.0:
        return None, "threshold must be between 0 and 100"

    return round(val, 2), None


def _calculate_attendance_alerts(
    student_id=None,
    class_id=None,
    subject_id=None,
    threshold=None,
    include_zero=False,
    only_alerts=False,
):
    """
    Core business logic for FR-11 attendance alerts.

    Accepts or retrieves the configured attendance threshold.
    Calculates attendance percentages using FR-04 rules.
    Identifies students strictly below the threshold (percentage < threshold).
    Returns relevant student info, calculated percentages, threshold, and alert indicators.
    """
    db = get_db()
    current_user = g.current_user
    role = current_user["role"]
    current_user_id = current_user["id"]

    # If POST request, check JSON body for optional filter fields
    if request.method == "POST":
        body = request.get_json(silent=True)
        if isinstance(body, dict):
            if threshold is None and "threshold" in body:
                threshold = body.get("threshold")
            if student_id is None and "student_id" in body:
                student_id = body.get("student_id")
            if class_id is None and "class_id" in body:
                class_id = body.get("class_id")
            if subject_id is None and "subject_id" in body:
                subject_id = body.get("subject_id")
            if "include_zero" in body:
                include_zero = bool(body.get("include_zero"))
            if "only_alerts" in body:
                only_alerts = bool(body.get("only_alerts"))

    # Resolve and validate threshold
    if threshold is None:
        raw_thresh = request.args.get("threshold")
        if raw_thresh is not None:
            threshold_val, err = validate_threshold(raw_thresh)
            if err:
                return None, jsonify(error=err), 400
            threshold = threshold_val
        else:
            threshold = get_persisted_threshold(db)
    else:
        threshold_val, err = validate_threshold(threshold)
        if err:
            return None, jsonify(error=err), 400
        threshold = threshold_val

    # Resolve and validate student_id
    if student_id is None:
        student_id_arg = request.args.get("student_id")
        if student_id_arg is not None:
            try:
                student_id = int(student_id_arg)
            except (TypeError, ValueError):
                return None, jsonify(error="student_id must be a positive integer"), 400
            if student_id <= 0:
                return None, jsonify(error="student_id must be a positive integer"), 400
    else:
        if not isinstance(student_id, int) or isinstance(student_id, bool) or student_id <= 0:
            return None, jsonify(error="student_id must be a positive integer"), 400

    # Role enforcement for students
    if role == "student":
        if student_id is not None and student_id != current_user_id:
            return None, jsonify(
                error="Access denied: students can only view their own attendance alerts"
            ), 403
        student_id = current_user_id

    student_entity = None
    if student_id is not None:
        try:
            student_row = db.execute(
                "SELECT id, username FROM users WHERE id = ? AND role = 'student'",
                (student_id,),
            ).fetchone()
        except sqlite3.Error:
            return None, jsonify(error="Database temporarily unavailable"), 503

        if student_row is None:
            return None, jsonify(error="Student not found"), 404
        student_entity = {
            "id": student_row["id"],
            "username": student_row["username"],
            "name": student_row["username"],
        }

    # Resolve and validate class_id
    if class_id is None:
        class_id_arg = request.args.get("class_id")
        if class_id_arg is not None:
            try:
                class_id = int(class_id_arg)
            except (TypeError, ValueError):
                return None, jsonify(error="class_id must be a positive integer"), 400
            if class_id <= 0:
                return None, jsonify(error="class_id must be a positive integer"), 400
    else:
        if not isinstance(class_id, int) or isinstance(class_id, bool) or class_id <= 0:
            return None, jsonify(error="class_id must be a positive integer"), 400

    class_entity = None
    if class_id is not None:
        try:
            class_row = db.execute(
                "SELECT id, name FROM classes WHERE id = ?",
                (class_id,),
            ).fetchone()
        except sqlite3.Error:
            return None, jsonify(error="Database temporarily unavailable"), 503

        if class_row is None:
            return None, jsonify(error="Class not found"), 404
        class_entity = {"id": class_row["id"], "name": class_row["name"]}

    # Resolve and validate subject_id
    if subject_id is None:
        subject_id_arg = request.args.get("subject_id")
        if subject_id_arg is not None:
            try:
                subject_id = int(subject_id_arg)
            except (TypeError, ValueError):
                return None, jsonify(error="subject_id must be a positive integer"), 400
            if subject_id <= 0:
                return None, jsonify(error="subject_id must be a positive integer"), 400
    else:
        if not isinstance(subject_id, int) or isinstance(subject_id, bool) or subject_id <= 0:
            return None, jsonify(error="subject_id must be a positive integer"), 400

    subject_entity = None
    if subject_id is not None:
        try:
            subject_row = db.execute(
                "SELECT id, name, teacher_id FROM subjects WHERE id = ?",
                (subject_id,),
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

    # Query flags
    raw_zero = request.args.get("include_zero") or request.args.get("include_zero_classes")
    if raw_zero is not None:
        include_zero = str(raw_zero).lower() in ("true", "1", "yes")

    raw_only = request.args.get("only_alerts") or request.args.get("below_threshold_only")
    if raw_only is not None:
        only_alerts = str(raw_only).lower() in ("true", "1", "yes")

    # Build SQL query
    user_conditions = ["u.role = 'student'"]
    user_params = []

    if student_id is not None:
        user_conditions.append("u.id = ?")
        user_params.append(student_id)

    if class_id is not None:
        user_conditions.append("u.id IN (SELECT student_id FROM enrollments WHERE class_id = ?)")
        user_params.append(class_id)

    attendance_join_conditions = ["a.student_id = u.id"]
    join_params = []

    if subject_id is not None:
        attendance_join_conditions.append("a.subject_id = ?")
        join_params.append(subject_id)
    elif role == "teacher":
        attendance_join_conditions.append(
            "a.subject_id IN (SELECT id FROM subjects WHERE teacher_id = ?)"
        )
        join_params.append(current_user_id)

    if class_id is not None:
        attendance_join_conditions.append("""
            EXISTS (
                SELECT 1 FROM enrollments e
                WHERE e.student_id = a.student_id
                  AND e.subject_id = a.subject_id
                  AND e.class_id = ?
            )
        """)
        join_params.append(class_id)

    join_sql = " AND ".join(attendance_join_conditions)
    where_sql = " AND ".join(user_conditions)

    sql = f"""
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
        FROM users u
        LEFT JOIN attendance a
            ON {join_sql}
        WHERE {where_sql}
        GROUP BY u.id, u.username
        ORDER BY u.username ASC
    """
    params = tuple(join_params + user_params)

    try:
        rows = db.execute(sql, params).fetchall()
    except sqlite3.Error:
        return None, jsonify(error="Unable to retrieve attendance alerts"), 503

    students_list = []
    alerts_list = []

    for row in rows:
        total = row["total_classes"]
        attended = row["classes_attended"]
        if total == 0:
            percentage = 0.0
            if include_zero:
                is_below = (0.0 < threshold)
                alert_status = "BELOW_THRESHOLD" if is_below else "NORMAL"
            else:
                is_below = False
                alert_status = "NO_RECORDS"
        else:
            percentage = round((attended / total) * 100, 2)
            is_below = (percentage < threshold)
            alert_status = "BELOW_THRESHOLD" if is_below else "NORMAL"

        student_info = {
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "username": row["student_name"],
            "classes_attended": attended,
            "total_classes": total,
            "attendance_percentage": percentage,
            "threshold": threshold,
            "is_alert": is_below,
            "below_threshold": is_below,
            "alert_status": alert_status,
        }
        students_list.append(student_info)
        if is_below:
            alerts_list.append(student_info)

    alerts_list.sort(key=lambda s: (s["attendance_percentage"], s["student_name"]))

    reported_students = alerts_list if only_alerts else students_list

    payload = {
        "threshold": threshold,
        "count": len(alerts_list),
        "alerts_count": len(alerts_list),
        "total_students": len(students_list),
        "alerts": alerts_list,
        "students": reported_students,
        "filters": {
            "threshold": threshold,
            "student_id": student_id,
            "class_id": class_id,
            "subject_id": subject_id,
            "include_zero": include_zero,
            "only_alerts": only_alerts,
        },
    }

    if student_entity is not None:
        payload["student"] = student_entity
    if class_entity is not None:
        payload["class"] = class_entity
    if subject_entity is not None:
        payload["subject"] = subject_entity

    return payload, None, 200


@api.get("/attendance/threshold")
@login_required()
def get_attendance_threshold():
    """Retrieve the current configured attendance alert threshold."""
    db = get_db()
    val = get_persisted_threshold(db)
    return jsonify(
        threshold=val,
        default_threshold=DEFAULT_ATTENDANCE_THRESHOLD,
    ), 200


@api.route("/attendance/threshold", methods=["POST", "PUT"])
@login_required(["admin"])
def set_attendance_threshold():
    """Configure the global attendance alert threshold (Admin only)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="A JSON request body is required"), 400

    if "threshold" not in data:
        return jsonify(error="threshold is required"), 400

    val, err = validate_threshold(data.get("threshold"))
    if err:
        return jsonify(error=err), 400

    db = get_db()
    try:
        set_persisted_threshold(val, db)
    except sqlite3.Error:
        db.rollback()
        return jsonify(error="Database temporarily unavailable"), 503

    return jsonify(
        message="Attendance threshold updated successfully",
        threshold=val,
    ), 200


@api.route("/attendance/alerts", methods=["GET", "POST"])
@api.route("/attendance/alert", methods=["GET", "POST"])
@api.route("/alerts/attendance", methods=["GET", "POST"])
@api.route("/attendance/alerts/student/<int:student_id>", methods=["GET", "POST"])
@api.route("/attendance/alerts/class/<int:class_id>", methods=["GET", "POST"])
@api.route("/attendance/alerts/subject/<int:subject_id>", methods=["GET", "POST"])
@login_required()
def attendance_alerts(student_id=None, class_id=None, subject_id=None):
    """
    Identify and return students whose attendance percentage falls below a threshold.

    Acceptance criteria:
    - An attendance threshold can be specified (via parameter, config, or API).
    - The system identifies students below the threshold (strictly below: percentage < threshold).
    - Students below the threshold are clearly indicated (with boolean flags and alert status).
    """
    payload, err_response, status_code = _calculate_attendance_alerts(
        student_id=student_id,
        class_id=class_id,
        subject_id=subject_id,
    )
    if err_response is not None:
        return err_response, status_code

    return jsonify(payload), status_code
