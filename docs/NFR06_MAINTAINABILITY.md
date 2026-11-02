# NFR-06: Maintainability and Modular Backend Architecture

## Overview

Before NFR-06, every REST endpoint, helper and constant lived in a single
4,365-line `app/routes.py`. NFR-06 split that file into small modules with
one responsibility each, without changing behaviour:

- All 74 URL rules keep the same endpoint names, HTTP methods, URL patterns
  and registration order.
- Response bodies, status codes, authentication, authorization, SQL queries,
  the database schema, the frontend and the NFR-02 performance optimizations
  are unchanged. The view code was moved verbatim, not rewritten.
- Existing imports from `app.routes` keep working.

The refactor was done in three stages, each verified by the full test suite:

| Stage | Change |
|---|---|
| 0 | Froze the URL map in `tests/test_nfr06_maintainability.py` |
| 1 | Extracted shared helpers into `app/auth.py` and `app/validation.py` |
| 2 | Moved feature routes into modules under `app/api/` |
| 3 | Architecture tests and this document |

## Backend layout

```
app/
├── __init__.py          Application factory (create_app)
├── db.py                SQLite connection, schema, indexes
├── auth.py              Shared session and access-control helpers
├── validation.py        Shared validation constants and helpers
├── pages.py             HTML page blueprint ("pages")
├── routes.py            Backward-compatible re-exports only (no code)
└── api/
    ├── __init__.py              Imports route modules in registration order
    ├── blueprint.py             The shared "api" blueprint + GET /api/health
    ├── auth_routes.py           Login, current user, password change, role checks
    ├── users.py                 User management
    ├── attendance_view.py       Attendance viewing
    ├── academics.py             Classes, subjects, teacher assignments
    ├── attendance_records.py    Class roster and attendance marking
    ├── percentages.py           Attendance percentages
    ├── attendance_management.py Attendance record retrieval, update, deletion
    ├── enrollments.py           Student enrollment
    ├── session_routes.py        Logout
    ├── exports.py               CSV/PDF export helpers (no routes)
    ├── reports.py               Attendance reports and report export routes
    └── alerts.py                Attendance alerts and the threshold setting
```

### Module responsibilities

| Module | Requirement | Endpoints / contents |
|---|---|---|
| `api/blueprint.py` | — | `api` blueprint; `GET /api/health` |
| `api/auth_routes.py` | FR-01, FR-13 | `POST /api/login`, `GET /api/me`, `POST /api/me/password`, `GET /api/{admin,teacher,student}/check` |
| `api/users.py` | FR-07 | `/api/users`, `/api/users/<id>`, `/api/users/<id>/{deactivate,activate}` |
| `api/attendance_view.py` | FR-05 | `GET /api/attendance` (`view_attendance`) |
| `api/academics.py` | FR-08 | `/api/classes…`, `/api/subjects…`, `/api/teacher/{classes,subjects}` |
| `api/attendance_records.py` | FR-02/FR-03 | `GET /api/roster`, `POST /api/attendance` |
| `api/percentages.py` | FR-04 | `GET /api/attendance/percentages` |
| `api/attendance_management.py` | FR-03 | `GET /api/attendance` (`get_attendance`, shadowed), `/api/attendance/<id>`, `PUT /api/attendance` |
| `api/enrollments.py` | FR-09 | `/api/enrollments` (POST, GET, DELETE) |
| `api/session_routes.py` | FR-15 | `POST /api/logout` |
| `api/exports.py` | FR-06, FR-12 | CSV/PDF builders, CSV injection protection, `_format_export_response` |
| `api/reports.py` | FR-06, FR-12 | `/api/reports/attendance…` and `/…/export…` aliases, `_build_attendance_report_data` |
| `api/alerts.py` | FR-11 | `/api/attendance/threshold`, `/api/attendance/alerts…` aliases, threshold persistence |
| `pages.py` | Frontend | `/login`, `/dashboard`, `/admin`, `/teacher`, `/student` |

Two modules exist only because of registration order (see below):
`attendance_management.py` is separate from `attendance_records.py`, and
`session_routes.py` is separate from `auth_routes.py`.

### Dependency rules

```
         app/__init__.py (create_app)
           │            │
           ▼            ▼
       app/api/      app/pages.py
           │            │
           ▼            ▼
   app/auth.py   app/validation.py   app/db.py
```

- Feature modules depend only on `app.api.blueprint`, `app.auth`,
  `app.validation` and `app.db`. The only feature-to-feature import is
  `reports` → `exports`.
- `app.auth` depends only on `app.db`. `app.validation` depends on nothing
  but the standard library.
- No module inside `app/` imports `app.routes`. It exists for external
  callers only, so it can never create an import cycle.

These rules are enforced by `tests/test_nfr06_maintainability.py`.

## Application factory and the API blueprint

`app/__init__.py` defines `create_app(test_config=None)`, which:

1. Creates the Flask app and applies the session/cookie configuration
   (FR-01), then any `test_config` overrides.
2. Initializes the database (`init_db`) and loads the persisted attendance
   threshold (FR-11).
3. Registers the `api` blueprint under `/api` and the `pages` blueprint at
   the root.
4. Installs the NFR-01 cross-site request check and security headers, and
   the `/` home route.

The factory imports the blueprint with `from .api import api as api_blueprint`.
The alias is deliberate: binding the name `api` inside the `app` package
would replace the `app.api` package attribute with the blueprint object, and
`import app.api.reports`-style access or `monkeypatch` paths would break.

There is exactly one API blueprint. It is defined in `app/api/blueprint.py`,
and every feature module attaches its routes to it:

```python
from .blueprint import api

@api.get("/example")
@login_required(["admin"])
def example():
    ...
```

Endpoint names are therefore still `api.<view function name>`, exactly as
before the split, so `url_for("api.login")`-style references and the frontend
JavaScript are unaffected.

## How routes are registered, and why import order matters

Flask records a URL rule when a `@api.get(...)`/`@api.route(...)` decorator
runs, which happens when the module is imported. When the blueprint is later
registered on the app, the rules are added to `app.url_map` in that order.
`app/api/__init__.py` imports the route modules in a fixed sequence, so
**the import order in `app/api/__init__.py` is the URL registration order**:

```
blueprint → auth_routes → users → attendance_view → academics →
attendance_records → percentages → attendance_management → enrollments →
session_routes → reports → alerts
```

(`exports` has no routes and is imported by `reports`.)

Order matters for one real behaviour: two views share `GET /api/attendance`.

- `attendance_view.view_attendance` (FR-05) is registered first, so it
  handles every `GET /api/attendance` request.
- `attendance_management.get_attendance` (FR-03) is registered second and is
  never reached. It is kept on purpose so the URL map is unchanged; removing
  or consolidating it is a separate, reviewed change.

Swapping those two imports would silently switch the handler (for example,
`?subject_id=abc` would stop returning HTTP 400). For other rules Werkzeug
picks the most specific match regardless of order, but the order is still
frozen so the URL map stays reproducible.

The original `routes.py` order interleaved features. To keep it exactly:

- `percentages` sits between attendance marking and record management, so
  record management lives in its own `attendance_management.py`.
- `logout` was registered after the enrollment routes, so it lives in
  `session_routes.py` instead of `auth_routes.py`.

Stacked decorators register bottom-up, which is why alias URLs for one view
(reports, exports, alerts) appear in reverse source order in the URL map.
Keep stacked decorators in their existing order.

## Adding a new feature

1. **Pick the module.** Add the route to the module that owns that
   responsibility (see the table above). Create a new module in `app/api/`
   only for a new responsibility.
2. **Use the shared blueprint and helpers.**

   ```python
   """FR-XX short description of the module's responsibility."""

   import sqlite3

   from flask import g, jsonify, request

   from ..auth import login_required
   from ..db import get_db
   from ..validation import parse_date
   from .blueprint import api
   ```

   Guard every non-public endpoint with `@login_required()` or
   `@login_required([...roles])`, placed **below** the route decorator, and
   read the authenticated user from `g.current_user`.
3. **Register a new module.** Add `from . import <module>  # noqa: F401` to
   `app/api/__init__.py`. Append new modules **at the end** so existing
   rules keep their positions. Do not reorder existing imports.
4. **Shared code goes to the shared layer.** A helper needed by more than one
   feature belongs in `app/auth.py`, `app/validation.py` or a new helper
   module, not in another feature module.
5. **Do not add code to `app/routes.py`.** It only re-exports old names.
6. **Update the tests.** New routes are a deliberate URL map change: add
   them to `EXPECTED_URL_MAP` and `ENDPOINT_MODULES` (and `API_MODULES` /
   `API_ROUTE_MODULE_ORDER` for a new module) in
   `tests/test_nfr06_maintainability.py`, and add feature tests in a new
   `tests/test_frXX_*.py` file.

## Shared helpers

### `app/auth.py` — sessions and access control

| Name | Purpose |
|---|---|
| `_password_fingerprint(password_hash)` | HMAC-SHA256 of the stored password hash, keyed by `SECRET_KEY`. Stored in the session instead of the hash. |
| `start_user_session(user_id, password_hash)` | Clears the session and starts a permanent one bound to the current password (FR-13). |
| `session_matches_password(password_hash)` | True only if the session was issued for the current password, so a password change ends other sessions. |
| `login_required(allowed_roles=None)` | Decorator: 401 `{"error": "Authentication required"}` when unauthenticated, inactive or stale; 403 `{"error": "Access denied"}` for the wrong role; 503 if the database is unavailable. Sets `g.current_user`. |

`app/pages.py` uses `session_matches_password` for its HTML pages, so pages
and API share one session-validity rule.

### `app/validation.py` — input validation

| Name | Purpose |
|---|---|
| `VALID_STATUSES` | `{"Present", "Absent", "Late"}` |
| `VALID_ROLES` | `{"admin", "teacher", "student"}` |
| `MIN_PASSWORD_LENGTH` | `8` |
| `normalize_status(status)` | Trims and capitalizes a status; `None` if invalid. |
| `parse_date(date_str)` | Validates `YYYY-MM-DD`; returns the normalized string or `None`. |
| `_is_encodable(text)` | Rejects strings the password hasher cannot encode (lone surrogates). |

These are pure functions with no Flask, request or database dependency.

Feature-specific helpers stay with their feature: threshold validation in
`api/alerts.py`, export formatting in `api/exports.py`, report data in
`api/reports.py`.

## Backward compatibility through `app/routes.py`

`app/routes.py` now contains no logic. It re-exports every name it used to
define — the `api` blueprint, all view functions, the helpers and the
constants — from their new homes. The re-exported objects are the same
objects, not copies:

```python
from app.routes import api, _password_fingerprint   # still works
from app.routes import login_required, parse_date   # still works
```

`tests/session_helpers.py` relies on `from app.routes import _password_fingerprint`.
New code should import from the real module (`app.auth`, `app.validation`,
`app.api.<module>`) instead. Because nothing inside `app/` imports
`app.routes`, the shim can be retired later without touching the application.

## Running the automated tests

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium        # once, for browser tests

# NFR-06 baseline and architecture tests
python -m pytest tests/test_nfr06_maintainability.py -v

# NFR-02 browser performance tests (Playwright)
python -m pytest tests/test_nfr02_browser_performance.py -v

# Complete suite, as run in CI (.github/workflows/tests.yml)
python -m pytest
```

`tests/test_nfr06_maintainability.py` checks:

- **URL map baseline** — every rule, method, endpoint and its order, the
  rule count (74), and both `GET /api/attendance` registrations, including
  that a real request is still handled by `view_attendance`.
- **Module isolation** — each `app.api.*` module, `app.auth`,
  `app.validation`, `app.routes` and `app.pages` imports on its own in a
  fresh interpreter, and `create_app()` works in a fresh interpreter, which
  catches circular imports that an already-warm test process would hide.
- **Blueprint wiring** — one shared `api` blueprint registered under `/api`,
  `app.api` still resolves to the package, route modules imported in the
  documented order, and every view in its documented module.
- **Dependency direction** — no internal imports of `app.routes`; feature
  modules depend only on the shared layers.
- **Legacy imports** — every old `app.routes` name is still exported and is
  the same object as in its new module.
- **API contracts** — health check, 401 for unauthenticated requests across
  every feature module, 403 role restrictions, and a login → protected
  request → logout flow spanning modules.

If one of these tests fails after a change, the architecture or the public
API contract changed. Update the expected values only when the change is
intentional and reviewed.

## Known limitations

- **Import order is load-bearing.** Reordering `app/api/__init__.py` changes
  the URL map, and for `GET /api/attendance` the handler. The tests catch
  this, but contributors must know about it.
- **`get_attendance` is unreachable.** It is kept to preserve the URL map;
  consolidating the two `GET /api/attendance` implementations should be its
  own change with updated tests.
- **`app.pages` resolves to the blueprint, not the module**, because
  `app/__init__.py` binds `pages` by name. Use `sys.modules["app.pages"]`
  to reach the module. This predates NFR-06.
- **Module sizes vary.** `academics.py` (~800 lines) and
  `attendance_management.py` / `attendance_records.py` (~500 lines each) are
  still large; the views were moved
  verbatim, and repeated query/permission code inside them could be
  factored out in a later change.
