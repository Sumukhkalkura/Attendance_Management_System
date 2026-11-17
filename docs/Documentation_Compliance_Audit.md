# Documentation Compliance Audit

**Project:** Attendance Management System (Software Engineering)
**Team:** Sumukh, Jagadeesh, Tharith
**Audit date:** 2026-11-17
**Scope:** `Documents/SRS.pdf`, `Documents/SAD.pdf`, `Documents/Test_Plan.pdf` (and the supporting `Use_Case_Flows.pdf`, `UML_Diagram.pdf`, `attendance_justification.pdf`) compared with the source code in `app/`, the tests in `tests/`, the scripts in `scripts/`, the CI workflow `.github/workflows/tests.yml` and the Deliverable 3 evidence in `docs/`.
**Optional Sprint 3:** skipped; nothing in this audit proposes Sprint 3 work.

## 1. Method

1. Read every document in `Documents/` and `docs/`, and the README.
2. Read the application code: app factory (`app/__init__.py`), authentication and sessions (`app/auth.py`, `app/api/auth_routes.py`, `app/api/session_routes.py`), schema (`app/db.py`), page routes (`app/pages.py`), validation (`app/validation.py`), all feature modules in `app/api/`, templates and JavaScript in `app/templates/` and `app/static/js/`.
3. Listed the real route table from Flask (`app.url_map`, 74 rules: 67 under `/api` plus `/`, `/login`, `/dashboard`, `/admin`, `/teacher`, `/student` and `/static`) and the role list of every `login_required` decorator.
4. Recomputed every test figure from the recorded evidence, not from earlier reports: `docs/evidence/final/junit.xml` (final suite run 2026-11-11: 856 results - 836 passed, 1 failed, 12 errors, 7 skipped; the failure and errors are the Edge/Firefox environment issues), the browser runs in `docs/evidence/final/browsers/`, the coverage JSON in `docs/evidence/coverage/`, and `docs/evidence/manual_validation_automation/results.json`.
5. Evaluated the 197-case catalogue (`scripts/case_catalog.py`) against that evidence exactly as `scripts/build_test_case_document.py` does: **182 PASS, 6 FAIL, 4 BLOCKED, 4 NOT RUN, 1 NOT APPLICABLE**.
6. Coverage recomputed from `docs/evidence/coverage/*/coverage_app.json`: statement 1765/2136 = **82.63%**, branch 653/828 = **78.86%** (application package `app/`).

Status meanings used below:

| Status | Meaning |
|---|---|
| IMPLEMENTED | Required behaviour exists in the code and is verified by passing tests (open Low defects are listed). |
| PARTIAL | Part of the requirement is implemented or verified; the missing part is named. |
| NOT IMPLEMENTED | No code implements the requirement. |
| NOT VERIFIED | Code exists but no evidence verifies it. |

No requirement is NOT IMPLEMENTED. No requirement is wholly NOT VERIFIED; the unverified parts of PARTIAL requirements are named.

## 2. Actual architecture (summary)

- **Style:** layered web application in one Flask process. Browser pages (Jinja2 templates + vanilla JavaScript) call a JSON REST API under `/api`; the API modules call SQLite through `app/db.py`.
- **Authentication:** inside the Flask app. `POST /api/login` checks a Werkzeug password hash (`check_password_hash`) in the `users` table. There is **no external Security / Auth Service** (the original SAD showed one).
- **Sessions:** Flask signed-cookie session; `PERMANENT_SESSION_LIFETIME` 30 minutes, `HttpOnly`, `SameSite=Lax`, `Secure` only when `FLASK_COOKIE_SECURE=1`. The session stores `user_id` and an HMAC fingerprint of the password hash, so a password change ends every other session.
- **Authorization:** `login_required(roles)` decorator on every API view except `/api/login` and `/api/health`; it reloads the user on every request (active flag, fingerprint, role). Page routes redirect by role. Data scoping inside views: teachers only their subjects, students only their own records.
- **CSRF:** global `before_request` hook rejects POST/PUT/PATCH/DELETE whose `Origin`/`Referer` is another site (403).
- **Headers:** `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Cache-Control: no-store`.
- **Database:** SQLite with 7 tables (`users`, `classes`, `subjects`, `class_subjects`, `enrollments`, `attendance`, `settings`), foreign keys enabled per connection, `UNIQUE(student_id, subject_id, attendance_date)` on `attendance`, CHECK constraints on role and status, 10 indexes.
- **Percentages:** server-side SQL (`COUNT`, `SUM(CASE status='Present')`), `round(present/total*100, 2)`, Late counts as not attended (`GET /api/attendance/percentages`, admin and teacher only). The student dashboard computes the same formula in the browser from its own records.
- **Reports/exports:** `GET /api/reports/attendance[...]` and `.../export[/csv|pdf|json]`; CSV with formula-injection protection; PDF generated in-process. There is **no external Report Engine** and **no reporting or export screen** in any dashboard.
- **Reliability:** transactions with rollback in the write paths; `scripts/backup_db.py` (SQLite backup API + `PRAGMA integrity_check`) and `scripts/schedule_daily_backup.py` (cron). No restore script.
- **CI:** `.github/workflows/tests.yml` runs `pytest` on Ubuntu with Python 3.11 and Playwright Chromium/Firefox plus Chrome/Edge.

## 3. Requirement-by-requirement audit

### Functional requirements

| ID | Requirement (SRS v1.0) | Status | Code evidence | Test evidence | Documentation gaps | Recommended correction |
|---|---|---|---|---|---|---|
| FR-01 | Role-based login for Administrator, Teacher, Student | IMPLEMENTED | `app/api/auth_routes.py::login`, `app/auth.py::login_required`, `start_user_session`; `app/pages.py` role redirects; 30-minute session in `app/__init__.py` | 13 cases, 13 PASS (`test_fr01_authentication.py`, `test_fr01_session_expiry_and_auth_failure.py`, `test_foundation.py`, browser `test_nfr05_browser_compatibility.py`) | SRS has a one-line requirement only; UC-01 and the SAD describe an external Security/Auth Service that does not exist | Describe in-app Werkzeug hash check, sessions and role redirects; mark the external service as an original design element not implemented |
| FR-02 | Teacher selects class/subject and marks Present/Absent/Late for a date | IMPLEMENTED | `api/attendance_records.py::class_roster`, `mark_attendance`; `teacher.js` Mark attendance | 13 cases, 13 PASS (`test_fr02_attendance_marking.py`) | No detailed behaviour, preconditions or acceptance criteria | Add full requirement detail; note that every enrolled student must be submitted in a class batch |
| FR-03 | Save/update records; prevent duplicates | IMPLEMENTED | `UNIQUE(student_id, subject_id, attendance_date)` in `app/db.py`; 409 on duplicates; `attendance_management.py` update/delete | 13 cases, 13 PASS (`test_fr03_record_management.py`) | Deletion and the update path are not described | Document update via `update_existing`, PATCH/PUT and DELETE, and the database constraint |
| FR-04 | Calculate and display attendance percentage | IMPLEMENTED (open defect MV-02) | `api/percentages.py` SQL aggregate, `round(..., 2)`; `student.js percentOf()`; `common.js formatPercent` displays 1 decimal | 11 cases: 10 PASS, 1 FAIL (SYS_FR-04_11, MV-02 display precision) | Formula, Late handling and rounding not specified in SRS | State formula Present / (Present+Absent+Late) x 100, Late not attended, 2-decimal rounding; record MV-02 |
| FR-05 | Students and teachers view records by subject and date | IMPLEMENTED (open defect MV-03) | `api/attendance_view.py::view_attendance` with role scoping; History and Records screens | 10 cases: 8 PASS, 1 FAIL (SYS_FR-05_10, MV-03 at 375 px), 1 NOT APPLICABLE (SYS_FR-05_09 pagination, outside SRS) | No role scoping rules in SRS | Document own-records rule for students and own-subjects rule for teachers |
| FR-06 | Reports by student, class, subject or date range | PARTIAL | `api/reports.py` (`/api/reports/attendance`, `/student/<id>`, `/class/<id>`, `/subject/<id>`, date range) | 12 cases: 11 PASS, 1 FAIL (SYS_FR-06_08, no UI) | Original SAD shows external Report Engine; no statement that the UI is missing | Mark as API-only (gap G-01, defect D-02); remove Report Engine from implemented architecture |
| FR-07 | Admin adds, updates, deactivates accounts | IMPLEMENTED | `api/users.py` create/list/get/update/activate/deactivate; admin Users screen | 10 cases, 10 PASS (`test_fr07_user_management.py`); manual-validation run SYS_FR-07_10 PASS | Validation rules undocumented. Audit findings AF-01 (the API accepts any non-empty password for new/edited accounts; the 8-character minimum is enforced only by the admin form's `minlength`) and AF-02 (the API lets an admin deactivate their own account; only the UI disables that button) | Document actual rules (unique username, valid role, non-empty password); record AF-01 and AF-02 as open issues |
| FR-08 | Admin manages classes/subjects and assigns teachers | IMPLEMENTED | `api/academics.py` (classes, subjects, class-subject links, teacher assignment) | 10 cases, 10 PASS (`test_fr08_class_subject_management.py`); SYS_FR-08_10 PASS | Class-subject link not described | Document `class_subjects` and assignment endpoints |
| FR-09 | Admin assigns students to classes and subjects | IMPLEMENTED (observation O-01) | `api/enrollments.py` create/list/delete; admin Enrollments screen | 10 cases, 10 PASS (`test_fr09_student_enrollment.py`, `test_fr09_enrollment_validation.py`); IT_FR-09_09 and SYS_FR-09_10 PASS | API accepts a subject not linked to the class (O-01) | Record O-01 as an open low-severity validation gap |
| FR-10 | Search/filter by student, subject, class or date | PARTIAL | API filters `student_id`, `subject_id`, `class_id`, `attendance_date`, `start_date`/`end_date`, `status`; UI has search, subject, date, status only | 10 cases: 9 PASS, 1 FAIL (SYS_FR-10_10, MV-01 no teacher Clear filters) | UI lacks class and date-range filters (G-03) | State that class/date-range filtering is API-only; record MV-01 |
| FR-11 | Identify students below a threshold | IMPLEMENTED | `api/alerts.py` (strictly below threshold, default 75%, persisted in `settings`); overview tables | 10 cases, 10 PASS (`test_fr11_attendance_alert.py`); SYS_FR-11_10 PASS | Threshold changeable only by admin API (G-04) | Document threshold API and default |
| FR-12 | Export reports in a supported format | PARTIAL | `api/exports.py` CSV (formula-injection safe), PDF, JSON; `api/reports.py` export routes | 10 cases: 9 PASS, 1 FAIL (SYS_FR-12_10, no UI export) | No UI control (G-02) | Mark export as API-only (defect D-03) |
| FR-13 | Users change their own password | IMPLEMENTED | `api/auth_routes.py::change_password` (current password, 8-char minimum, must differ, other sessions invalidated) | 10 cases, 10 PASS (`test_fr13_password_management.py`); SYS_FR-13_10 PASS | Policy not documented | Add policy and session-invalidation behaviour |
| FR-14 | Role-based dashboard summary | IMPLEMENTED | Overview sections in `admin.js`, `teacher.js`, `student.js` using existing APIs | 8 cases, 8 PASS (`test_fr14_dashboard_summary.py`); SYS_FR-14_08 PASS | Contents per role not specified | List the figures shown to each role |
| FR-15 | Secure logout ending the session | IMPLEMENTED | `api/session_routes.py::logout` (`session.clear()`); confirmation dialog; `Cache-Control: no-store` | 8 cases: 7 PASS, 1 NOT RUN (SYS_FR-15_08 cross-site logout forgery not tested) | - | Record SYS_FR-15_08 as an untested security check |

### Non-functional requirements

| ID | Requirement (SRS v1.0) | Status | Code evidence | Test evidence | Documentation gaps | Recommended correction |
|---|---|---|---|---|---|---|
| NFR-01 | Role-limited access; sensitive data protected in transmission | PARTIAL | RBAC, data scoping, CSRF origin check, security headers, hashed passwords, HttpOnly/SameSite cookies; **no HTTPS deployment** (Secure cookie switch only) | 8 cases: 7 PASS, 1 BLOCKED (SYS_NFR-01_04 secure transmission) | Original justification claims all traffic uses HTTPS | Do not claim HTTPS; record G-08 and SYS_NFR-01_04 BLOCKED |
| NFR-02 | Pages and attendance information within 3 s | IMPLEMENTED | Indexes in `app/db.py`; aggregate SQL | 6 cases, 6 PASS (`test_nfr02_performance.py`, `test_nfr02_browser_performance.py`, SYS_NFR-02_06 measured 28-235 ms) | Target and measured results not separated | Report the 3 s target and measured values separately |
| NFR-03 | No data loss; regular backups | PARTIAL | Transactions/rollback; `scripts/backup_db.py`, `scripts/schedule_daily_backup.py`; **no restore script** | 6 cases: 4 PASS, 2 NOT RUN (IT_NFR-03_03 restore, SYS_NFR-03_05 retry after failure) | Restore procedure missing (G-07) | Record restore as not implemented/not verified |
| NFR-04 | Clear, consistent, easy-to-navigate UI | PARTIAL | Shared layout, focus-visible styles, ARIA labels, keyboard support, responsive CSS | 6 cases: 5 PASS, 1 NOT RUN (SYS_NFR-04_06 human usability walkthrough) | "Easily" not measurable; MV-03 at 375 px | Separate automated accessibility evidence from the unperformed human walkthrough |
| NFR-05 | Works on common modern browsers | PARTIAL | Standards mode, polyfills, fixed MIME types | 8 cases: 4 PASS (Chrome, Chromium), 1 FAIL (SYS_NFR-05_04 WebKit console CSP errors, D-01), 3 BLOCKED (Firefox cannot start, Edge not installed, Safari not automatable) | Browser list not defined in SRS | Define target browsers and report per-browser results honestly |
| NFR-06 | Modular, maintainable components | IMPLEMENTED | `app/api/` feature modules on one blueprint; helpers in `app/auth.py`, `app/validation.py`; frozen URL map | 5 cases, 5 PASS (`test_nfr06_maintainability.py`) | Module map not documented | Document module responsibilities (SAD section 4) |

## 4. Document-level findings

| Document | Template sections missing in the baseline | Factual problems found |
|---|---|---|
| `SRS.pdf` (3 pages) | Document control, introduction, overall description, detailed FRs (actors, flows, acceptance criteria), security requirements, use cases and diagrams, traceability, appendices | None in the requirement text; IDs FR-01..FR-15 and NFR-01..NFR-06 are kept unchanged |
| `SAD.pdf` (3 pages) | Everything except one component diagram; the diagram is cut across three pages | Shows an external Security/Auth Service and Report Engine that do not exist; "HTTPS/token API" not implemented |
| `Use_Case_Flows.pdf` | No UML use-case diagrams; UC-01..UC-07 cover only FR-01..FR-06 | UC-01 step 3 uses the external Auth Service; UC-07 uses the Report Engine |
| `attendance_justification.pdf` | - | States that all traffic uses HTTPS and that credentials are checked by an external service; neither is true |
| `Test_Plan.pdf` (7 pages) | Strategy, environment, entry/exit criteria, roles, risks, coverage, results, defects | 75 cases for FR-01..FR-06 and NFR-01..NFR-03, all "Pending"; superseded by the 197-case Test Case Document v2.4 (all 75 IDs preserved) |
| Professor templates | Not present in the repository | Template compliance is checked against the section list given by the team, not the official template files |

## 5. New audit findings (not in the defect register)

Found while reading the code for this audit. They are not test results and are not added to the Test Case Document's defect register (which is generated from `scripts/case_catalog.py`); the team should decide whether to register them.

| ID | Requirement | Finding | Evidence | Severity (proposed) |
|---|---|---|---|---|
| AF-01 | FR-07, NFR-01 | `POST /api/users` and `PATCH /api/users/<id>` accept any non-empty password; the 8-character minimum (`MIN_PASSWORD_LENGTH`) is applied only by `POST /api/me/password`. The admin form's `minlength="8"` is a browser-side check only. | `app/api/users.py` lines 43-50 and 222-227; `app/templates/admin.html` line 312 | Low |
| AF-02 | FR-07 | The API does not stop an administrator from deactivating their own account; only `admin.js` disables the button for the signed-in user. | `app/api/users.py::deactivate_user`; `app/static/js/admin.js::renderUsers` | Low |

## 6. Corrections applied in the final documents

1. `Documents/SRS_Final.*` keeps every requirement ID and original requirement text, and adds the implementation status separately (section 3 and 4), security requirements, 17 use cases with two UML use-case diagrams, and a traceability matrix generated from the test catalogue.
2. `Documents/SAD_Final.*` replaces the cropped component diagram, removes the non-existent external services from the implemented architecture (kept as documented deviations), and adds component design, two sequence diagrams, the API table generated from Flask's route map, the ER diagram, security, error handling, UI and decisions.
3. `Documents/Test_Plan_Final.*` reconciles the original 75-case plan with the 197-case catalogue and reports only recorded results.
4. The original PDFs in `Documents/` are not modified or overwritten.

## 7. Update after the six fixes (2026-11-17)

The six test cases that failed in the original runs were fixed and re-verified in a regression run
(`docs/evidence/regression/`). The tables above record the audit as it stood before the fixes; the changes are:

| Requirement | Status before | Status now | Change | Evidence |
|---|---|---|---|---|
| FR-04 | IMPLEMENTED (MV-02 open) | IMPLEMENTED | `App.formatPercent` shows two decimals (`app/static/js/common.js`); overview averages rounded to two decimals | SYS_FR-04_11 PASS |
| FR-05 | IMPLEMENTED (MV-03 open) | IMPLEMENTED | Tables become labelled cards below 640 px (`app/static/css/app.css`, `App.fillRows` sets `data-label`) | SYS_FR-05_10 PASS |
| FR-06 | PARTIAL | IMPLEMENTED | Reports screen in the admin and teacher dashboards (`app/static/js/reports.js`, `admin.html`, `teacher.html`) using the existing `/api/reports/attendance` | SYS_FR-06_08 PASS |
| FR-10 | PARTIAL | IMPLEMENTED | Class filter, From/To date range and Clear filters on the teacher and admin records screens; student search on the admin screen | SYS_FR-10_10 PASS |
| FR-12 | PARTIAL | IMPLEMENTED | CSV / PDF / JSON export buttons on the Reports screen using the existing export API | SYS_FR-12_10 PASS |
| NFR-05 | PARTIAL (D-01 open) | PARTIAL | D-01 was an upstream WebKit 27.2 (r2370) regression; Playwright upgraded to 1.65.2 (WebKit r2388, approved), no violations; CSP unchanged. Firefox, Edge and Safari remain untested | SYS_NFR-05_04 PASS |

No backend endpoint, database schema or security header was changed. Audit findings AF-01 and AF-02 are unchanged and still open.
