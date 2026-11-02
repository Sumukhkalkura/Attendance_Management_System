"""Backward-compatible re-exports of the API routes and shared helpers.

Before NFR-06 every API route lived in this module. Routes now live in
feature modules under ``app.api`` (see app/api/__init__.py for the module
map and registration order), authentication helpers in ``app.auth`` and
validation helpers in ``app.validation``.

This module defines nothing new. It re-exports every name it used to define
so existing imports such as ``from app.routes import api`` and
``from app.routes import _password_fingerprint`` keep working.
"""

from .api import api  # noqa: F401  (registers every route in original order)
from .auth import (  # noqa: F401
    _password_fingerprint,
    login_required,
    session_matches_password,
    start_user_session,
)
from .validation import (  # noqa: F401
    MIN_PASSWORD_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
    _is_encodable,
    normalize_status,
    parse_date,
)

from .api.blueprint import (  # noqa: F401
    health,
)
from .api.auth_routes import (  # noqa: F401
    login,
    current_user,
    change_password,
    admin_check,
    teacher_check,
    student_check,
)
from .api.users import (  # noqa: F401
    create_user,
    list_users,
    get_user,
    update_user,
    deactivate_user,
    activate_user,
)
from .api.attendance_view import (  # noqa: F401
    view_attendance,
)
from .api.academics import (  # noqa: F401
    list_classes,
    create_class,
    get_class,
    update_class,
    assign_class_teacher,
    associate_subject_with_class,
    get_class_subjects,
    remove_subject_from_class,
    list_subjects,
    create_subject,
    get_subject,
    update_subject,
    assign_teacher,
    teacher_classes,
    teacher_subjects,
)
from .api.attendance_records import (  # noqa: F401
    class_roster,
    mark_attendance,
)
from .api.percentages import (  # noqa: F401
    attendance_percentages,
)
from .api.attendance_management import (  # noqa: F401
    get_attendance,
    get_attendance_record,
    update_attendance_record,
    update_attendance_by_key,
    delete_attendance_record,
)
from .api.enrollments import (  # noqa: F401
    create_enrollment,
    list_enrollments,
    delete_enrollment,
)
from .api.session_routes import (  # noqa: F401
    logout,
)
from .api.exports import (  # noqa: F401
    SUPPORTED_EXPORT_FORMATS,
    _get_export_filename,
    _sanitize_csv_cell,
    _generate_csv_report,
    _generate_pdf_report,
    _format_export_response,
)
from .api.reports import (  # noqa: F401
    _build_attendance_report_data,
    generate_attendance_report,
    export_attendance_report,
)
from .api.alerts import (  # noqa: F401
    DEFAULT_ATTENDANCE_THRESHOLD,
    SETTING_KEY_THRESHOLD,
    get_persisted_threshold,
    set_persisted_threshold,
    validate_threshold,
    _calculate_attendance_alerts,
    get_attendance_threshold,
    set_attendance_threshold,
    attendance_alerts,
)
