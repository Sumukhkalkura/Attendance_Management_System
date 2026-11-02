"""NFR-06 Maintainability: baseline regression tests for the public routing contract.

These tests freeze the application's URL map exactly as it exists before the
NFR-06 modular refactor (Stage 0). Splitting app/routes.py into feature modules
must leave every URL rule, HTTP method, endpoint name, and registration order
unchanged, so the frontend JavaScript and API clients keep working.

If one of these tests fails after a refactor, the public API contract changed.
Only update EXPECTED_URL_MAP when a route change is intentional and reviewed.

Stage 3 adds architecture tests for the modular layout under app/api/:
module isolation, blueprint wiring, legacy app.routes imports, import-cycle
safety of the application factory, dependency direction between modules,
and representative API contracts per feature module.
See docs/NFR06_MAINTAINABILITY.md.
"""

import ast
import importlib
import subprocess
import sys
import types
from pathlib import Path
import sqlite3

import pytest
from flask import Blueprint
from werkzeug.security import generate_password_hash

from app import create_app


# Every rule in app.url_map, in registration order, as
# (endpoint, sorted HTTP methods, rule). Flask adds HEAD and OPTIONS
# automatically. Stacked route decorators register bottom-up, which is why
# the alias rules of a single view appear in reverse source order.
EXPECTED_URL_MAP = [
    ('static', ('GET', 'HEAD', 'OPTIONS'), '/static/<path:filename>'),
    ('api.health', ('GET', 'HEAD', 'OPTIONS'), '/api/health'),
    ('api.login', ('OPTIONS', 'POST'), '/api/login'),
    ('api.current_user', ('GET', 'HEAD', 'OPTIONS'), '/api/me'),
    ('api.change_password', ('OPTIONS', 'POST'), '/api/me/password'),
    ('api.admin_check', ('GET', 'HEAD', 'OPTIONS'), '/api/admin/check'),
    ('api.teacher_check', ('GET', 'HEAD', 'OPTIONS'), '/api/teacher/check'),
    ('api.student_check', ('GET', 'HEAD', 'OPTIONS'), '/api/student/check'),
    ('api.create_user', ('OPTIONS', 'POST'), '/api/users'),
    ('api.list_users', ('GET', 'HEAD', 'OPTIONS'), '/api/users'),
    ('api.get_user', ('GET', 'HEAD', 'OPTIONS'), '/api/users/<int:user_id>'),
    ('api.update_user', ('OPTIONS', 'PATCH', 'PUT'), '/api/users/<int:user_id>'),
    ('api.deactivate_user', ('OPTIONS', 'PATCH', 'POST'), '/api/users/<int:user_id>/deactivate'),
    ('api.activate_user', ('OPTIONS', 'PATCH', 'POST'), '/api/users/<int:user_id>/activate'),
    ('api.view_attendance', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance'),
    ('api.list_classes', ('GET', 'HEAD', 'OPTIONS'), '/api/classes'),
    ('api.create_class', ('OPTIONS', 'POST'), '/api/classes'),
    ('api.get_class', ('GET', 'HEAD', 'OPTIONS'), '/api/classes/<int:class_id>'),
    ('api.update_class', ('OPTIONS', 'PATCH', 'PUT'), '/api/classes/<int:class_id>'),
    ('api.assign_class_teacher', ('OPTIONS', 'PATCH', 'PUT'), '/api/classes/<int:class_id>/teacher'),
    ('api.associate_subject_with_class', ('OPTIONS', 'POST'), '/api/classes/<int:class_id>/subjects'),
    ('api.get_class_subjects', ('GET', 'HEAD', 'OPTIONS'), '/api/classes/<int:class_id>/subjects'),
    ('api.remove_subject_from_class', ('DELETE', 'OPTIONS'), '/api/classes/<int:class_id>/subjects/<int:subject_id>'),
    ('api.list_subjects', ('GET', 'HEAD', 'OPTIONS'), '/api/subjects'),
    ('api.create_subject', ('OPTIONS', 'POST'), '/api/subjects'),
    ('api.get_subject', ('GET', 'HEAD', 'OPTIONS'), '/api/subjects/<int:subject_id>'),
    ('api.update_subject', ('OPTIONS', 'PATCH', 'PUT'), '/api/subjects/<int:subject_id>'),
    ('api.assign_teacher', ('OPTIONS', 'PATCH', 'PUT'), '/api/subjects/<int:subject_id>/teacher'),
    ('api.teacher_classes', ('GET', 'HEAD', 'OPTIONS'), '/api/teacher/classes'),
    ('api.teacher_subjects', ('GET', 'HEAD', 'OPTIONS'), '/api/teacher/subjects'),
    ('api.class_roster', ('GET', 'HEAD', 'OPTIONS'), '/api/roster'),
    ('api.mark_attendance', ('OPTIONS', 'POST'), '/api/attendance'),
    ('api.attendance_percentages', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/percentages'),
    ('api.get_attendance', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance'),
    ('api.get_attendance_record', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/<int:record_id>'),
    ('api.update_attendance_record', ('OPTIONS', 'PATCH', 'PUT'), '/api/attendance/<int:record_id>'),
    ('api.update_attendance_by_key', ('OPTIONS', 'PUT'), '/api/attendance'),
    ('api.delete_attendance_record', ('DELETE', 'OPTIONS'), '/api/attendance/<int:record_id>'),
    ('api.create_enrollment', ('OPTIONS', 'POST'), '/api/enrollments'),
    ('api.list_enrollments', ('GET', 'HEAD', 'OPTIONS'), '/api/enrollments'),
    ('api.delete_enrollment', ('DELETE', 'OPTIONS'), '/api/enrollments'),
    ('api.logout', ('OPTIONS', 'POST'), '/api/logout'),
    ('api.generate_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/subject/<int:subject_id>'),
    ('api.generate_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/class/<int:class_id>'),
    ('api.generate_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/student/<int:student_id>'),
    ('api.generate_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/reports'),
    ('api.generate_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/report'),
    ('api.generate_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/subject/<int:subject_id>/export/<string:format_name>'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/class/<int:class_id>/export/<string:format_name>'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/student/<int:student_id>/export/<string:format_name>'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/export/<string:format_name>'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/report/export/<string:format_name>'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/subject/<int:subject_id>/export'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/class/<int:class_id>/export'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/student/<int:student_id>/export'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/export/<string:format_name>'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/export'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/report/export'),
    ('api.export_attendance_report', ('GET', 'HEAD', 'OPTIONS'), '/api/reports/attendance/export'),
    ('api.get_attendance_threshold', ('GET', 'HEAD', 'OPTIONS'), '/api/attendance/threshold'),
    ('api.set_attendance_threshold', ('OPTIONS', 'POST', 'PUT'), '/api/attendance/threshold'),
    ('api.attendance_alerts', ('GET', 'HEAD', 'OPTIONS', 'POST'), '/api/attendance/alerts/subject/<int:subject_id>'),
    ('api.attendance_alerts', ('GET', 'HEAD', 'OPTIONS', 'POST'), '/api/attendance/alerts/class/<int:class_id>'),
    ('api.attendance_alerts', ('GET', 'HEAD', 'OPTIONS', 'POST'), '/api/attendance/alerts/student/<int:student_id>'),
    ('api.attendance_alerts', ('GET', 'HEAD', 'OPTIONS', 'POST'), '/api/alerts/attendance'),
    ('api.attendance_alerts', ('GET', 'HEAD', 'OPTIONS', 'POST'), '/api/attendance/alert'),
    ('api.attendance_alerts', ('GET', 'HEAD', 'OPTIONS', 'POST'), '/api/attendance/alerts'),
    ('pages.login_page', ('GET', 'HEAD', 'OPTIONS'), '/login'),
    ('pages.dashboard', ('GET', 'HEAD', 'OPTIONS'), '/dashboard'),
    ('pages.admin_dashboard', ('GET', 'HEAD', 'OPTIONS'), '/admin'),
    ('pages.teacher_dashboard', ('GET', 'HEAD', 'OPTIONS'), '/teacher'),
    ('pages.student_dashboard', ('GET', 'HEAD', 'OPTIONS'), '/student'),
    ('home', ('GET', 'HEAD', 'OPTIONS'), '/'),
]


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "nfr06.db"),
        "SECRET_KEY": "test-only",
    })


def current_url_map(app):
    return [
        (rule.endpoint, tuple(sorted(rule.methods)), rule.rule)
        for rule in app.url_map.iter_rules()
    ]


# ---------------------------------------------------------------------
# URL map baseline
# ---------------------------------------------------------------------

def test_url_map_matches_baseline_exactly_and_in_order(app):
    """Endpoints, methods, rules, and registration order are unchanged."""
    assert current_url_map(app) == EXPECTED_URL_MAP


def test_url_map_has_no_missing_or_unexpected_rules(app):
    """Set comparison gives a readable diff if a rule is added or lost."""
    actual = set(current_url_map(app))
    expected = set(EXPECTED_URL_MAP)

    assert sorted(expected - actual) == [], "routes missing after change"
    assert sorted(actual - expected) == [], "unexpected new routes"


def test_url_map_rule_count_baseline(app):
    assert len(EXPECTED_URL_MAP) == 74
    assert len(list(app.url_map.iter_rules())) == 74


def test_endpoint_names_match_view_function_names(app):
    """Endpoint names derive from blueprint name + function name.

    Moving a view into another module must not rename it.
    """
    for endpoint, view_function in app.view_functions.items():
        if endpoint == "static":
            continue  # Flask's built-in static view is a lambda.
        expected_name = endpoint.rsplit(".", 1)[-1]
        assert view_function.__name__ == expected_name, endpoint


def test_blueprints_registered_with_expected_names(app):
    assert set(app.blueprints) == {"api", "pages"}


def test_every_api_rule_is_under_api_prefix(app):
    for endpoint, _methods, rule in EXPECTED_URL_MAP:
        if endpoint.startswith("api."):
            assert rule.startswith("/api/"), (endpoint, rule)


# ---------------------------------------------------------------------
# Duplicate GET /api/attendance: registration order decides the handler
# ---------------------------------------------------------------------

def test_both_attendance_implementations_remain_registered(app):
    """view_attendance (FR-05) and get_attendance (FR-03) both stay registered."""
    get_rules = [
        endpoint
        for endpoint, methods, rule in current_url_map(app)
        if rule == "/api/attendance" and "GET" in methods
    ]

    assert get_rules == ["api.view_attendance", "api.get_attendance"]
    assert "api.view_attendance" in app.view_functions
    assert "api.get_attendance" in app.view_functions


def test_view_attendance_is_registered_before_get_attendance(app):
    endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]

    assert endpoints.index("api.view_attendance") < endpoints.index(
        "api.get_attendance"
    )


@pytest.mark.parametrize("method, expected_endpoint", [
    ("GET", "api.view_attendance"),
    ("POST", "api.mark_attendance"),
    ("PUT", "api.update_attendance_by_key"),
])
def test_attendance_collection_url_dispatch(app, method, expected_endpoint):
    adapter = app.url_map.bind("localhost")

    endpoint, args = adapter.match("/api/attendance", method=method)

    assert endpoint == expected_endpoint
    assert args == {}


def test_get_api_attendance_request_is_handled_by_view_attendance(app):
    """Behavioural check: the request really runs view_attendance.

    view_attendance rejects a non-integer subject_id with 400; the shadowed
    get_attendance parses it with type=int and would silently ignore it.
    """
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute(
            "INSERT INTO users (username, password_hash, role, active) "
            "VALUES (?, ?, 'admin', 1)",
            ("nfr06_admin", generate_password_hash("Nfr06-Password")),
        )

    client = app.test_client()
    login = client.post(
        "/api/login",
        json={"username": "nfr06_admin", "password": "Nfr06-Password"},
    )
    assert login.status_code == 200

    response = client.get("/api/attendance?subject_id=abc")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "subject_id must be a positive integer"
    }

    ok = client.get("/api/attendance")
    assert ok.status_code == 200
    assert set(ok.get_json()) == {"count", "records"}


def test_get_api_attendance_requires_authentication(app):
    response = app.test_client().get("/api/attendance")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Authentication required"}


# =====================================================================
# Stage 3: modular architecture tests
# =====================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_DIR = PROJECT_ROOT / "app" / "api"

# Route modules in the order app/api/__init__.py must import them. This order
# is the URL registration order (see docs/NFR06_MAINTAINABILITY.md).
API_ROUTE_MODULE_ORDER = [
    "auth_routes",
    "users",
    "attendance_view",
    "academics",
    "attendance_records",
    "percentages",
    "attendance_management",
    "enrollments",
    "session_routes",
    "reports",
    "alerts",
]

# Every module in app/api/, including the ones without their own routes.
API_MODULES = ["blueprint", *API_ROUTE_MODULE_ORDER, "exports"]

# Which module owns each API view. Moving a view between modules is a
# deliberate architectural change and must update this table.
ENDPOINT_MODULES = {
    "health": "blueprint",
    "login": "auth_routes",
    "current_user": "auth_routes",
    "change_password": "auth_routes",
    "admin_check": "auth_routes",
    "teacher_check": "auth_routes",
    "student_check": "auth_routes",
    "create_user": "users",
    "list_users": "users",
    "get_user": "users",
    "update_user": "users",
    "deactivate_user": "users",
    "activate_user": "users",
    "view_attendance": "attendance_view",
    "list_classes": "academics",
    "create_class": "academics",
    "get_class": "academics",
    "update_class": "academics",
    "assign_class_teacher": "academics",
    "associate_subject_with_class": "academics",
    "get_class_subjects": "academics",
    "remove_subject_from_class": "academics",
    "list_subjects": "academics",
    "create_subject": "academics",
    "get_subject": "academics",
    "update_subject": "academics",
    "assign_teacher": "academics",
    "teacher_classes": "academics",
    "teacher_subjects": "academics",
    "class_roster": "attendance_records",
    "mark_attendance": "attendance_records",
    "attendance_percentages": "percentages",
    "get_attendance": "attendance_management",
    "get_attendance_record": "attendance_management",
    "update_attendance_record": "attendance_management",
    "update_attendance_by_key": "attendance_management",
    "delete_attendance_record": "attendance_management",
    "create_enrollment": "enrollments",
    "list_enrollments": "enrollments",
    "delete_enrollment": "enrollments",
    "logout": "session_routes",
    "generate_attendance_report": "reports",
    "export_attendance_report": "reports",
    "get_attendance_threshold": "alerts",
    "set_attendance_threshold": "alerts",
    "attendance_alerts": "alerts",
}

# Every name app/routes.py exposed before NFR-06, and the module that now
# defines it. app.routes must keep re-exporting each one unchanged.
LEGACY_ROUTES_EXPORTS = {
    **{name: f"app.api.{module}" for name, module in ENDPOINT_MODULES.items()},
    "api": "app.api.blueprint",
    "_password_fingerprint": "app.auth",
    "start_user_session": "app.auth",
    "session_matches_password": "app.auth",
    "login_required": "app.auth",
    "VALID_STATUSES": "app.validation",
    "VALID_ROLES": "app.validation",
    "MIN_PASSWORD_LENGTH": "app.validation",
    "normalize_status": "app.validation",
    "parse_date": "app.validation",
    "_is_encodable": "app.validation",
    "SUPPORTED_EXPORT_FORMATS": "app.api.exports",
    "_get_export_filename": "app.api.exports",
    "_sanitize_csv_cell": "app.api.exports",
    "_generate_csv_report": "app.api.exports",
    "_generate_pdf_report": "app.api.exports",
    "_format_export_response": "app.api.exports",
    "_build_attendance_report_data": "app.api.reports",
    "DEFAULT_ATTENDANCE_THRESHOLD": "app.api.alerts",
    "SETTING_KEY_THRESHOLD": "app.api.alerts",
    "get_persisted_threshold": "app.api.alerts",
    "set_persisted_threshold": "app.api.alerts",
    "validate_threshold": "app.api.alerts",
    "_calculate_attendance_alerts": "app.api.alerts",
}


def run_in_fresh_interpreter(code):
    """Run code in a new Python process so no module is already cached.

    This is the only reliable way to detect circular imports: inside the
    pytest process every app module has already been imported.
    """
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def imported_modules(path):
    """Return the absolute module names a source file imports from app."""
    tree = ast.parse(path.read_text())
    package = ".".join(path.relative_to(PROJECT_ROOT).with_suffix("").parts[:-1])
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[: len(package.split(".")) - node.level + 1]
                prefix = ".".join(base)
                module = f"{prefix}.{node.module}" if node.module else prefix
                if node.module is None:
                    names.update(f"{prefix}.{alias.name}" for alias in node.names)
                    continue
            else:
                module = node.module
            names.add(module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return {name for name in names if name == "app" or name.startswith("app.")}


def make_user(app, username, password, role):
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute(
            "INSERT INTO users (username, password_hash, role, active) "
            "VALUES (?, ?, ?, 1)",
            (username, generate_password_hash(password), role),
        )


# ---------------------------------------------------------------------
# Module isolation and circular-import safety
# ---------------------------------------------------------------------

def test_api_package_contains_exactly_the_documented_modules():
    actual = {path.stem for path in API_DIR.glob("*.py")} - {"__init__"}

    assert actual == set(API_MODULES)


@pytest.mark.parametrize(
    "module",
    [f"app.api.{name}" for name in API_MODULES]
    + ["app.api", "app.auth", "app.validation", "app.routes", "app.pages"],
)
def test_module_is_independently_importable(module):
    """Each module imports first, on its own, in a fresh interpreter."""
    result = run_in_fresh_interpreter(f"import {module}")

    assert result.returncode == 0, result.stderr


def test_application_factory_builds_app_in_fresh_interpreter(tmp_path):
    database = tmp_path / "fresh.db"
    result = run_in_fresh_interpreter(
        "from app import create_app\n"
        f"app = create_app({{'TESTING': True, 'DATABASE': {str(database)!r},"
        " 'SECRET_KEY': 'test-only'})\n"
        "print(len(list(app.url_map.iter_rules())))\n"
        "print(sorted(app.blueprints))\n"
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.split("\n")[:2] == ["74", "['api', 'pages']"]


def test_application_factory_can_build_multiple_independent_apps(tmp_path):
    """Route registration happens once at import, not per create_app call."""
    first = create_app({"TESTING": True, "DATABASE": str(tmp_path / "a.db"),
                        "SECRET_KEY": "test-only"})
    second = create_app({"TESTING": True, "DATABASE": str(tmp_path / "b.db"),
                         "SECRET_KEY": "test-only"})

    assert current_url_map(first) == EXPECTED_URL_MAP
    assert current_url_map(second) == EXPECTED_URL_MAP


# ---------------------------------------------------------------------
# Blueprint wiring and route ownership
# ---------------------------------------------------------------------

def test_app_api_name_resolves_to_package_not_blueprint():
    """app/__init__.py must not shadow the app.api package attribute."""
    import app as app_package

    assert isinstance(app_package.api, types.ModuleType)
    assert app_package.api is sys.modules["app.api"]


def test_single_shared_api_blueprint_is_registered_under_api_prefix(app):
    from app.api import api
    from app.api.blueprint import api as blueprint_api

    assert api is blueprint_api
    assert isinstance(api, Blueprint)
    assert api.name == "api"
    assert app.blueprints["api"] is api

    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith("api."):
            assert rule.rule.startswith("/api/"), rule


def test_api_init_imports_route_modules_in_registration_order():
    tree = ast.parse((API_DIR / "__init__.py").read_text())
    imported = [
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is None
        for alias in node.names
    ]

    assert imported == API_ROUTE_MODULE_ORDER


def test_every_api_view_lives_in_its_documented_module(app):
    actual = {
        endpoint.split(".", 1)[1]: view.__module__.removeprefix("app.api.")
        for endpoint, view in app.view_functions.items()
        if endpoint.startswith("api.")
    }

    assert actual == ENDPOINT_MODULES


def test_api_rules_register_in_module_order(app):
    """Rules appear grouped by module, following API_ROUTE_MODULE_ORDER."""
    order = ["blueprint", *API_ROUTE_MODULE_ORDER]
    positions = [
        order.index(ENDPOINT_MODULES[rule.endpoint.split(".", 1)[1]])
        for rule in app.url_map.iter_rules()
        if rule.endpoint.startswith("api.")
    ]

    assert positions == sorted(positions)


def test_helper_modules_register_no_routes(app):
    modules = {view.__module__ for view in app.view_functions.values()}

    for helper in ["app.api.exports", "app.routes", "app.auth", "app.validation"]:
        assert helper not in modules


def test_protected_views_keep_their_original_names_through_decorators(app):
    """login_required uses functools.wraps, so names and modules survive."""
    for endpoint, view in app.view_functions.items():
        if endpoint.startswith("api."):
            assert view.__qualname__ == endpoint.split(".", 1)[1]


# ---------------------------------------------------------------------
# Dependency direction
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    sorted(API_DIR.glob("*.py"))
    + [PROJECT_ROOT / "app" / name for name in ("auth.py", "validation.py", "pages.py")],
    ids=lambda path: path.relative_to(PROJECT_ROOT).as_posix(),
)
def test_modules_never_import_legacy_routes(path):
    """app.routes is a compatibility shim; importing it internally risks cycles."""
    assert "app.routes" not in imported_modules(path)


@pytest.mark.parametrize("module", API_MODULES)
def test_feature_modules_only_depend_on_shared_layers(module):
    """Feature modules share code via app.auth/app.validation/app.db, not each other.

    The single allowed cross-feature edge is reports -> exports.
    """
    allowed = {"app.auth", "app.validation", "app.db", "app.api.blueprint"}
    if module == "reports":
        allowed.add("app.api.exports")

    imports = imported_modules(API_DIR / f"{module}.py") - {f"app.api.{module}"}

    assert imports <= allowed, imports - allowed


def test_shared_helper_modules_do_not_depend_on_api_layer():
    assert imported_modules(PROJECT_ROOT / "app" / "auth.py") == {"app.db"}
    assert imported_modules(PROJECT_ROOT / "app" / "validation.py") == set()


def test_validation_helpers_have_no_framework_dependencies():
    tree = ast.parse((PROJECT_ROOT / "app" / "validation.py").read_text())
    top_level_imports = {
        alias.name.split(".")[0] if isinstance(node, ast.Import) else node.module
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert top_level_imports == {"datetime"}


def test_pages_use_shared_auth_helper():
    pages_module = sys.modules["app.pages"]
    from app.auth import session_matches_password

    assert pages_module.session_matches_password is session_matches_password


# ---------------------------------------------------------------------
# Legacy app.routes imports
# ---------------------------------------------------------------------

@pytest.mark.parametrize("name, home", sorted(LEGACY_ROUTES_EXPORTS.items()))
def test_legacy_routes_import_returns_same_object(name, home):
    routes = importlib.import_module("app.routes")
    defining_module = importlib.import_module(home)

    assert getattr(routes, name) is getattr(defining_module, name)


def test_legacy_routes_exposes_nothing_unexpected():
    routes = importlib.import_module("app.routes")
    public = {
        name for name, value in vars(routes).items()
        if not name.startswith("__") and not isinstance(value, types.ModuleType)
    }

    assert public == set(LEGACY_ROUTES_EXPORTS)


def test_legacy_style_imports_used_by_existing_code_still_work():
    from app.routes import _password_fingerprint, api, login_required  # noqa: F401
    from tests.session_helpers import _password_fingerprint as helper_fingerprint

    assert helper_fingerprint is _password_fingerprint
    assert api.name == "api"


# ---------------------------------------------------------------------
# Representative API contracts, one per feature module
# ---------------------------------------------------------------------

def test_health_contract(app):
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


@pytest.mark.parametrize("method, url, module", [
    ("GET", "/api/me", "auth_routes"),
    ("POST", "/api/me/password", "auth_routes"),
    ("GET", "/api/users", "users"),
    ("GET", "/api/attendance", "attendance_view"),
    ("GET", "/api/classes", "academics"),
    ("GET", "/api/subjects", "academics"),
    ("GET", "/api/roster", "attendance_records"),
    ("POST", "/api/attendance", "attendance_records"),
    ("GET", "/api/attendance/percentages", "percentages"),
    ("GET", "/api/attendance/1", "attendance_management"),
    ("PUT", "/api/attendance", "attendance_management"),
    ("GET", "/api/enrollments", "enrollments"),
    ("POST", "/api/logout", "session_routes"),
    ("GET", "/api/reports/attendance", "reports"),
    ("GET", "/api/reports/attendance/export", "reports"),
    ("GET", "/api/attendance/threshold", "alerts"),
    ("GET", "/api/attendance/alerts", "alerts"),
])
def test_unauthenticated_requests_rejected_in_every_module(app, method, url, module):
    response = app.test_client().open(url, method=method)

    assert response.status_code == 401, module
    assert response.get_json() == {"error": "Authentication required"}


@pytest.mark.parametrize("method, url", [
    ("GET", "/api/admin/check"),
    ("GET", "/api/users"),
    ("POST", "/api/classes"),
    ("POST", "/api/enrollments"),
    ("PUT", "/api/attendance/threshold"),
])
def test_role_restrictions_unchanged_after_modularization(app, method, url):
    make_user(app, "nfr06_student", "Nfr06-Password", "student")
    client = app.test_client()
    assert client.post(
        "/api/login",
        json={"username": "nfr06_student", "password": "Nfr06-Password"},
    ).status_code == 200

    response = client.open(url, method=method, json={})

    assert response.status_code == 403
    assert response.get_json() == {"error": "Access denied"}


def test_login_session_and_logout_flow_spans_modules(app):
    """auth_routes logs in, shared login_required guards, session_routes logs out."""
    make_user(app, "nfr06_teacher", "Nfr06-Password", "teacher")
    client = app.test_client()

    login = client.post(
        "/api/login",
        json={"username": "nfr06_teacher", "password": "Nfr06-Password"},
    )
    assert login.status_code == 200
    assert login.get_json()["message"] == "Login successful"
    assert login.get_json()["user"]["role"] == "teacher"

    assert client.get("/api/teacher/check").status_code == 200
    assert client.get("/api/me").get_json()["user"]["username"] == "nfr06_teacher"

    logout = client.post("/api/logout")
    assert logout.status_code == 200
    assert logout.get_json() == {"message": "Logged out successfully"}
    assert client.get("/api/me").status_code == 401
