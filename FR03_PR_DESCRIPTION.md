# Pull Request Description: FR-03 Attendance Record Management

**Requirement**: FR-03 — Attendance Record Management  
**Assigned to**: Jagadeesh  
**Story Points**: 5  
**Local Feature Branch**: `feature/fr-03-attendance-record-management`  
**Base Branch**: `main` (`origin/main`)  

---

## 1. Overview & Objective

Sprint 1 assigned requirement **FR-03: Attendance Record Management** addresses the creation, retrieval, idempotent updating, duplicate prevention, and deletion of attendance records within the Attendance Management System.

This feature enables teachers and administrators to reliably record class session attendance, update records when attendance corrections are required, query attendance history with rich filters, and safeguard against duplicate record entry or unauthorized student tampering.

---

## 2. Requirements & Acceptance Criteria Checklist

| Requirement / Criterion | Description | Implementation Status |
| :--- | :--- | :---: |
| **Record Creation** | Save new attendance record with student, subject, date, and status (`Present`, `Absent`, `Late`). Returns `201 Created`. | Completed |
| **Idempotent Update** | Update existing record by ID (`PUT`/`PATCH /api/attendance/<id>`) or by composite key (`PUT /api/attendance`). Returns `200 OK`. | Completed |
| **Duplicate Protection** | Multiple attendance records for the same `(student_id, subject_id, attendance_date)` are prevented with `409 Conflict` unless explicit update intent (`update_existing=True`) is provided. | Completed |
| **Input Validation** | Calendar-aware `YYYY-MM-DD` validation (rejects invalid format and impossible dates like Feb 31) and status validation (`Present`, `Absent`, `Late`). Returns `400 Bad Request`. | Completed |
| **Referential Integrity** | Verifies student exists and has `role='student'`, subject exists, and optional class enrollment matches. Returns `404` or `400`. | Completed |
| **Teacher Authorization** | Teachers can only create, update, or delete records for subjects explicitly assigned to them (`teacher_id = current_user.id`). Unauthorized access returns `403 Forbidden`. | Completed |
| **Student Restrictions** | Students are strictly prohibited from creating, modifying, or deleting attendance records (`403 Forbidden`). | Completed |
| **Student Privacy** | When viewing attendance via `GET /api/attendance`, students can only view their own attendance records; attempting to query another student's records returns `403 Forbidden`. | Completed |
| **Record Deletion** | Authorized teachers and admins can delete records via `DELETE /api/attendance/<id>`. Returns `200 OK` or `404 Not Found`. | Completed |
| **Session & Batch Marking** | Supports batch submission of class roster attendance with atomic rollback on failure. | Completed |
| **Teacher Workflow Helpers** | Provides `/api/teacher/classes`, `/api/teacher/subjects`, and `/api/roster` for seamless UI/client integration. | Completed |

---

## 3. Architecture & Implementation Summary

### A. Helper Utilities (`app/routes.py`)
- `normalize_status(status_str)`: Case-insensitive normalization to canonical title-case (`Present`, `Absent`, `Late`). Rejects invalid statuses.
- `parse_date(date_str)`: Uses Python's `datetime.strptime(..., "%Y-%m-%d")` with full calendar validation to prevent database corruption from malformed or out-of-range dates.

### B. Endpoints Implemented

1. **`POST /api/attendance`** (`@login_required(["teacher", "admin"])`)
   - Handles single record creation or batch class session submissions.
   - Enforces teacher subject assignment and student role validation.
   - Detects existing records for the `(student, subject, date)` tuple. If already present, returns `409 Conflict` unless `update_existing=True`.
   - Wraps batch operations in atomic database transactions (`db.commit()` / `db.rollback()`).

2. **`PUT /api/attendance`** (`@login_required(["teacher", "admin"])`)
   - Idempotent upsert by composite key `(student_id, subject_id, attendance_date)`.
   - Returns `201 Created` if the record does not exist yet; returns `200 OK` if updating an existing record.

3. **`GET /api/attendance`** (`@login_required()`)
   - Query filters: `student_id`, `subject_id`, `class_id`, `attendance_date` / `date`, `status`.
   - Role enforcement: Students can only view their own records (`student_id = current_user.id`). Any attempt to query another student returns `403 Forbidden`.
   - Teachers automatically scope to their assigned subjects unless specific authorized parameters are passed.

4. **`GET /api/attendance/<record_id>`** (`@login_required()`)
   - Retrieves single attendance record by ID.
   - Verifies ownership/assignment: students can only fetch their own; teachers can only fetch records for their assigned subjects.

5. **`PUT /api/attendance/<record_id>` & `PATCH /api/attendance/<record_id>`** (`@login_required(["teacher", "admin"])`)
   - Updates status and/or attendance date of an existing record.
   - Verifies teacher assignment (`403` if teacher is not assigned to the record's subject).
   - Validates status and date format.
   - Checks against duplicate collision if changing attendance date (`409`).

6. **`DELETE /api/attendance/<record_id>`** (`@login_required(["teacher", "admin"])`)
   - Deletes specified attendance record.
   - Enforces teacher subject assignment (`403` if not assigned).

7. **Teacher Workflow Helpers**:
   - `GET /api/teacher/classes`: Returns classes taught by the authenticated teacher.
   - `GET /api/teacher/subjects`: Returns subjects assigned to the authenticated teacher.
   - `GET /api/roster`: Returns student roster for a class and subject, including existing attendance status for a given date.

---

## 4. Test Coverage & Verification

### A. Dedicated Test Suite: `tests/test_fr03_record_management.py`
Contains 15 unit, integration, and system tests mapped directly to the Sprint 1 Test Plan:

1. `test_ut_fr_03_01_save_new_record`: Validates creation of a new attendance record (`POST /api/attendance` -> `201 Created`).
2. `test_ut_fr_03_02_update_existing_record_by_id`: Validates record update by ID (`PUT /api/attendance/<id>` -> `200 OK`).
3. `test_ut_fr_03_03_prevent_duplicate_record`: Validates duplicate conflict rejection (`POST /api/attendance` -> `409 Conflict`).
4. `test_ut_fr_03_04_missing_student_validation`: Validates 400 for missing student, 404 for nonexistent student, 400 for non-student user.
5. `test_ut_fr_03_05_missing_subject_validation`: Validates 400 for missing subject, 404 for nonexistent subject.
6. `test_it_fr_03_06_database_persistence_across_connection_reload`: Verifies SQLite disk persistence across direct SQLite reload and secondary test client.
7. `test_it_fr_03_07_student_update_restriction`: Verifies students cannot `POST`, `PUT`, `PATCH`, or `DELETE` attendance (`403 Forbidden`).
8. `test_it_fr_03_08_teacher_authorization`: Verifies unassigned teachers cannot touch subjects of other teachers (`403 Forbidden`).
9. `test_sys_fr_03_09_refresh_after_save`: Simulates UI page refresh; verifies exact record count = 1 with zero duplicate rows.
10. `test_sys_fr_03_10_database_atomic_rollback`: Verifies atomic rollback on batch failure; no partial writes exist.
11. `test_fr03_idempotent_upsert_by_key`: Verifies `PUT /api/attendance` key-based upsert (201 on insert, 200 on update).
12. `test_fr03_record_deletion`: Verifies `DELETE /api/attendance/<id>` (200 on success, subsequent 404 on re-fetch or re-delete).
13. `test_fr03_query_filters_and_student_privacy`: Verifies multi-parameter filters and student privacy protection (403 on privacy violation).
14. `test_fr03_status_and_date_validation`: Verifies rejection of invalid statuses and impossible calendar dates.
15. `test_fr03_teacher_helper_routes`: Verifies teacher classes, subjects, and roster lookup endpoints.

### B. Acceptance Test: `tests/test_sprint1_requirements.py`
- Removed skip marker from `test_fr03_record_management(client)`.
- Verified complete FR-03 lifecycle (creation, duplicate rejection, update, persistence, student permission rejection).

### C. Test Execution Output

```
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\Jagadeesh R\OneDrive\Desktop\se\Attendance_Management_System
plugins: anyio-4.14.1
collected 58 items

tests/test_foundation.py::test_home PASSED                               [  1%]
tests/test_foundation.py::test_health PASSED                             [  3%]
tests/test_foundation.py::test_database_schema PASSED                    [  5%]
tests/test_foundation.py::test_duplicate_attendance_prevented PASSED     [  6%]
tests/test_foundation.py::test_login_requires_credentials PASSED         [  8%]
tests/test_foundation.py::test_login_rejects_empty_credentials PASSED    [ 10%]
tests/test_foundation.py::test_login_rejects_unknown_user PASSED         [ 12%]
tests/test_foundation.py::test_protected_endpoint_requires_login PASSED  [ 13%]
tests/test_foundation.py::test_admin_endpoint_requires_login PASSED      [ 15%]
tests/test_foundation.py::test_teacher_endpoint_requires_login PASSED    [ 17%]
tests/test_foundation.py::test_student_endpoint_requires_login PASSED    [ 18%]
tests/test_fr01_authentication.py::test_successful_login[admin1-admin123-admin] PASSED [ 20%]
tests/test_fr01_authentication.py::test_successful_login[teacher1-teacher123-teacher] PASSED [ 22%]
tests/test_fr01_authentication.py::test_successful_login[student1-student123-student] PASSED [ 24%]
tests/test_fr01_authentication.py::test_wrong_password PASSED            [ 25%]
tests/test_fr01_authentication.py::test_unknown_username PASSED          [ 27%]
tests/test_fr01_authentication.py::test_inactive_account_cannot_login PASSED [ 29%]
tests/test_fr01_authentication.py::test_missing_credentials PASSED       [ 31%]
tests/test_fr01_authentication.py::test_invalid_json_body PASSED         [ 32%]
tests/test_fr01_authentication.py::test_authenticated_user_details PASSED [ 34%]
tests/test_fr01_authentication.py::test_unauthenticated_user_details PASSED [ 36%]
tests/test_fr01_authentication.py::test_correct_role_access[admin1-admin123-/api/admin/check] PASSED [ 37%]
tests/test_fr01_authentication.py::test_correct_role_access[teacher1-teacher123-/api/teacher/check] PASSED [ 39%]
tests/test_fr01_authentication.py::test_correct_role_access[student1-student123-/api/student/check] PASSED [ 41%]
tests/test_fr01_authentication.py::test_wrong_role_denied[admin1-admin123-/api/teacher/check] PASSED [ 43%]
tests/test_fr01_authentication.py::test_wrong_role_denied[admin1-admin123-/api/student/check] PASSED [ 44%]
tests/test_fr01_authentication.py::test_wrong_role_denied[teacher1-teacher123-/api/admin/check] PASSED [ 46%]
tests/test_fr01_authentication.py::test_wrong_role_denied[teacher1-teacher123-/api/student/check] PASSED [ 48%]
tests/test_fr01_authentication.py::test_wrong_role_denied[student1-student123-/api/admin/check] PASSED [ 50%]
tests/test_fr01_authentication.py::test_wrong_role_denied[student1-student123-/api/teacher/check] PASSED [ 51%]
tests/test_fr01_authentication.py::test_session_created_after_login PASSED [ 53%]
tests/test_fr01_authentication.py::test_session_replaced_when_different_user_logs_in PASSED [ 55%]
tests/test_fr01_authentication.py::test_inactive_user_loses_existing_access PASSED [ 56%]
tests/test_fr01_authentication.py::test_no_plaintext_password_returned PASSED [ 58%]
tests/test_fr03_record_management.py::test_ut_fr_03_01_save_new_record PASSED [ 60%]
tests/test_fr03_record_management.py::test_ut_fr_03_02_update_existing_record_by_id PASSED [ 62%]
tests/test_fr03_record_management.py::test_ut_fr_03_03_prevent_duplicate_record PASSED [ 63%]
tests/test_fr03_record_management.py::test_ut_fr_03_04_missing_student_validation PASSED [ 65%]
tests/test_fr03_record_management.py::test_ut_fr_03_05_missing_subject_validation PASSED [ 67%]
tests/test_fr03_record_management.py::test_it_fr_03_06_database_persistence_across_connection_reload PASSED [ 68%]
tests/test_fr03_record_management.py::test_it_fr_03_07_student_update_restriction PASSED [ 70%]
tests/test_fr03_record_management.py::test_it_fr_03_08_teacher_authorization PASSED [ 72%]
tests/test_fr03_record_management.py::test_sys_fr_03_09_refresh_after_save PASSED [ 74%]
tests/test_fr03_record_management.py::test_sys_fr_03_10_database_atomic_rollback PASSED [ 75%]
tests/test_fr03_record_management.py::test_fr03_idempotent_upsert_by_key PASSED [ 77%]
tests/test_fr03_record_management.py::test_fr03_record_deletion PASSED   [ 79%]
tests/test_fr03_record_management.py::test_fr03_query_filters_and_student_privacy PASSED [ 81%]
tests/test_fr03_record_management.py::test_fr03_status_and_date_validation PASSED [ 82%]
tests/test_fr03_record_management.py::test_fr03_teacher_helper_routes PASSED [ 84%]
tests/test_sprint1_requirements.py::test_fr01_authentication SKIPPED     [ 86%]
tests/test_sprint1_requirements.py::test_admin_management SKIPPED        [ 87%]
tests/test_sprint1_requirements.py::test_fr02_attendance_marking SKIPPED [ 89%]
tests/test_sprint1_requirements.py::test_fr03_record_management PASSED   [ 91%]
tests/test_sprint1_requirements.py::test_fr04_percentages SKIPPED        [ 93%]
tests/test_sprint1_requirements.py::test_fr05_viewing SKIPPED           [ 94%]
tests/test_sprint1_requirements.py::test_fr15_logout SKIPPED            [ 96%]
tests/test_sprint1_requirements.py::test_nfr01_security SKIPPED          [ 98%]
tests/test_sprint1_requirements.py::test_nfr03_reliability SKIPPED       [100%]

======================= 50 passed, 8 skipped in 30.80s ========================
```

- **Total Test Cases**: 58
- **Passed**: 50
- **Skipped**: 8 (intentional skip markers for other team members' pending Sprint 1 stories: FR-02, FR-04, FR-05, FR-07/08/09, FR-15, NFR-01, NFR-03)
- **Failed**: 0

---

## 5. Teammate Conflict Inspection

Inspection of remote branches and recent commits was performed prior to and during development:
- **`origin/main`**: Reset by team leader in commit `74fc391` to remove early PR #24 merge and align with commit `687ae4b` (FR-01 authentication).
- **`origin/progress`**: Contains commit `6a641d1` ("feat(FR-07): Implement user management APIs") by Kailash Murali.
- **Diff Analysis (`git diff origin/main..origin/progress`)**:
  - Kailash added user management endpoints under `/api/users` in `app/routes.py` and corresponding tests in `tests/test_fr07_user_management.py`.
  - No database schema alterations were made.
  - The attendance endpoints (`/api/attendance`, `/api/teacher/*`, `/api/roster`) and `tests/test_fr03_record_management.py` added in this feature do not overlap or conflict with `/api/users`.
  - Merging into `main` or integrating with `progress` will be clean and conflict-free.

---

## 6. Git Compliance & Instructions for Team Leader Review

Per strict collaboration rules:
- All changes are made on the local feature branch: `feature/fr-03-attendance-record-management`.
- **NO commits and NO remote pushes have been executed by Jagadeesh.** All modified and new files remain safely uncommitted in the local working tree.
- The team leader (**Sumukhkalkura**) will review, commit, push, and open the GitHub pull request.

### Instructions for Team Leader:

1. **Verify Current Branch & Status**:
   ```bash
   git status
   ```
   *Expected output*: On branch `feature/fr-03-attendance-record-management`, showing:
   - Modified: `app/routes.py`
   - Modified: `tests/test_sprint1_requirements.py`
   - Untracked: `tests/test_fr03_record_management.py`
   - Untracked: `FR03_PR_DESCRIPTION.md`

2. **Run Test Verification**:
   ```bash
   python -m pytest -v
   ```
   *Expected output*: 50 passed, 8 skipped, 0 failures.

3. **Stage Changes**:
   ```bash
   git add app/routes.py tests/test_fr03_record_management.py tests/test_sprint1_requirements.py FR03_PR_DESCRIPTION.md
   ```

4. **Commit with Descriptive Message**:
   ```bash
   git commit -m "feat(FR-03): implement attendance record management and test suite"
   ```

5. **Push Feature Branch to GitHub**:
   ```bash
   git push origin feature/fr-03-attendance-record-management
   ```

6. **Open Pull Request**:
   - Title: `feat(FR-03): Attendance Record Management`
   - Description: Copy contents from `FR03_PR_DESCRIPTION.md`
