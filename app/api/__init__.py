"""REST API package: the shared ``api`` blueprint and its feature route modules.

Importing this package attaches every API route to ``api`` (defined in
``blueprint``). Flask records rules in the order the route decorators run,
so the import order below *is* the URL registration order. It reproduces the
pre-NFR-06 order of app/routes.py exactly, which matters because two views
share ``GET /api/attendance``: ``attendance_view.view_attendance`` must be
imported before ``attendance_management.get_attendance`` so it keeps
handling that request.

Do not reorder these imports; tests/test_nfr06_maintainability.py freezes
the resulting URL map.

Module responsibilities:

- blueprint             -- the ``api`` blueprint and ``GET /api/health``
- auth_routes           -- FR-01/FR-13 login, current user, password, role checks
- users                 -- FR-07 user management
- attendance_view       -- FR-05 attendance viewing
- academics             -- FR-08 classes, subjects, teacher assignments
- attendance_records    -- FR-03 roster and attendance marking
- percentages           -- FR-04 attendance percentages
- attendance_management -- FR-03 record retrieval, update, deletion
- enrollments           -- FR-09 student enrollment
- session_routes        -- FR-15 logout
- exports               -- FR-06/FR-12 CSV/PDF export helpers (no routes)
- reports               -- FR-06 reporting and FR-12 export routes
- alerts                -- FR-11 attendance alerts and threshold
"""

from .blueprint import api

# Registration order -- do not reorder (see module docstring).
from . import auth_routes  # noqa: F401
from . import users  # noqa: F401
from . import attendance_view  # noqa: F401
from . import academics  # noqa: F401
from . import attendance_records  # noqa: F401
from . import percentages  # noqa: F401
from . import attendance_management  # noqa: F401
from . import enrollments  # noqa: F401
from . import session_routes  # noqa: F401
from . import reports  # noqa: F401
from . import alerts  # noqa: F401

__all__ = ["api"]
