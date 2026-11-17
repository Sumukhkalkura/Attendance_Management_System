"""Test case catalogue for the updated Test Case Document (Deliverable Part-3).

Single source of truth for docs/Test_Case_Document.md and
docs/Test_Case_Document.xlsx (built by scripts/build_test_case_document.py).

Traceability
------------
* The 75 test cases of the original Test Plan (Documents/Test_Plan.pdf,
  sections FR-01..FR-06, NFR-01..NFR-03) keep their original IDs.
* New test cases continue the same ID convention:
  ``<UT|IT|SYS>_<REQ>_<NN>`` (UT = unit, IT = integration, SYS = system).

Execution fields (actual result, status, date, evidence) start as NOT RUN.
They are only filled in from real execution evidence in later phases.

Method codes
------------
A = automated pytest (Flask test client / unit level)
B = automated real-browser test (Playwright)
M = manual / human confirmation required
"""

MODULES = {
    "FR-01": "Authentication & Role Management",
    "FR-02": "Attendance Marking",
    "FR-03": "Attendance Record Management",
    "FR-04": "Attendance Percentage Calculation",
    "FR-05": "Attendance Viewing",
    "FR-06": "Attendance Reporting",
    "FR-07": "User Management",
    "FR-08": "Class & Subject Management",
    "FR-09": "Student Enrollment",
    "FR-10": "Attendance Search & Filter",
    "FR-11": "Attendance Alert",
    "FR-12": "Report Export",
    "FR-13": "Password Management",
    "FR-14": "Dashboard Summary",
    "FR-15": "Logout",
    "NFR-01": "Security",
    "NFR-02": "Performance",
    "NFR-03": "Reliability",
    "NFR-04": "Usability",
    "NFR-05": "Compatibility",
    "NFR-06": "Maintainability",
}

# Requirement text, quoted from Documents/SRS.pdf.
SRS_TEXT = {
    "FR-01": "The system shall allow authorized users (Administrator, Teacher, and Student) to log in according to their assigned role.",
    "FR-02": "The system shall allow teachers to select a class/subject and mark each student as Present, Absent, or Late for a specific date.",
    "FR-03": "The system shall save and allow authorized teachers to update attendance records while preventing duplicate attendance for the same student, subject, and date.",
    "FR-04": "The system shall automatically calculate and display each student's attendance percentage based on recorded attendance.",
    "FR-05": "The system shall allow students and teachers to view attendance records, including attendance by subject and date.",
    "FR-06": "The system shall generate attendance reports based on student, class, subject, or selected date range.",
    "FR-07": "The system shall allow administrators to add, update, and deactivate student and teacher accounts.",
    "FR-08": "The system shall allow administrators to create and manage classes and subjects and assign teachers to them.",
    "FR-09": "The system shall allow administrators to assign students to their respective classes and subjects.",
    "FR-10": "The system shall allow authorized users to search and filter attendance records by student, subject, class, or date.",
    "FR-11": "The system shall identify students whose attendance percentage falls below a specified attendance threshold.",
    "FR-12": "The system shall allow authorized users to export generated attendance reports in a supported file format.",
    "FR-13": "The system shall allow authenticated users to change their account password.",
    "FR-14": "The system shall display a dashboard summary containing relevant attendance information based on the user's role.",
    "FR-15": "The system shall allow authenticated users to securely log out of the system and terminate their active session.",
    "NFR-01": "The system shall ensure that users can access only the functions and attendance information permitted by their role, and sensitive data shall be protected during transmission.",
    "NFR-02": "The system shall load major pages and attendance information within 3 seconds under normal operating conditions.",
    "NFR-03": "The system shall preserve saved attendance records without data loss and shall perform regular backups of attendance data.",
    "NFR-04": "The system shall provide a clear and consistent user interface that allows users to navigate major functions easily.",
    "NFR-05": "The system shall function correctly on commonly used modern web browsers.",
    "NFR-06": "The system shall be designed in modular components so that individual features can be updated and maintained with minimal impact on other components.",
}

ORIGINAL = "Original (unchanged)"
UPDATED = "Original (updated)"
NEW = "New"

CASES = []


def tc(case_id, req, scenario, pre, data, steps, expected, method, refs=(),
       change=ORIGINAL, remarks=""):
    CASES.append({
        "id": case_id,
        "req": req,
        "type": case_id.split("_")[0],
        "module": MODULES[req],
        "scenario": scenario,
        "pre": pre,
        "data": data,
        "steps": steps,
        "expected": expected,
        "method": method,
        "refs": list(refs),
        "change": change,
        "remarks": remarks,
        # Execution fields -- filled only from real evidence in later phases.
        "actual": "Not yet executed",
        "status": "NOT RUN",
        "date": "",
        "evidence": "",
    })


# ---------------------------------------------------------------- FR-01
tc("UT_FR-01_01", "FR-01", "Valid login", "Valid active account exists",
   "Teacher01 / valid password", "Open /login; enter credentials; submit",
   "POST /api/login returns 200 with the user's role; browser is redirected to the role dashboard (/teacher).",
   "A+B", ["test_fr01_authentication::test_successful_login",
           "test_frontend_pages::test_page_login_flow_uses_real_authentication",
           "test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect"],
   UPDATED, "Expected result made specific to the implemented API (HTTP 200) and redirect.")
tc("UT_FR-01_02", "FR-01", "Invalid password", "Login page available",
   "Teacher01 / Wrong@123", "Enter wrong password; submit",
   "HTTP 401 'Invalid username or password'; error shown on login page; no session created.",
   "A", ["test_fr01_authentication::test_wrong_password",
         "test_fr01_authentication::test_unknown_username",
         "test_foundation::test_login_rejects_unknown_user"],
   UPDATED, "Exact message from app/api/auth_routes.py added.")
tc("UT_FR-01_03", "FR-01", "Blank credentials", "Login page available",
   "Blank username / password", "Submit empty fields",
   "UI shows 'Please enter both your username and password.'; API returns 400 'Username and password are required'.",
   "A+B", ["test_fr01_authentication::test_missing_credentials",
           "test_foundation::test_login_rejects_empty_credentials",
           "test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect"],
   UPDATED, "Exact UI and API messages added.")
tc("IT_FR-01_04", "FR-01", "Administrator role mapping", "Admin account exists",
   "Admin account", "Login as administrator",
   "Admin dashboard (/admin) opens; admin-only API (/api/admin/check) returns 200.",
   "A", ["test_fr01_authentication::test_correct_role_access",
         "test_frontend_pages::test_role_page_renders_for_its_role"])
tc("IT_FR-01_05", "FR-01", "Teacher role mapping", "Teacher account exists",
   "Teacher account", "Login as teacher",
   "Teacher dashboard (/teacher) opens; teacher functions available.",
   "A", ["test_fr01_authentication::test_correct_role_access",
         "test_frontend_pages::test_role_page_renders_for_its_role"])
tc("IT_FR-01_06", "FR-01", "Student role mapping", "Student account exists",
   "Student account", "Login as student",
   "Student dashboard (/student) opens; student functions available.",
   "A", ["test_fr01_authentication::test_correct_role_access",
         "test_frontend_pages::test_role_page_renders_for_its_role"])
tc("IT_FR-01_07", "FR-01", "Unauthorized page access", "Student logged in",
   "Student session", "Open /teacher and /admin pages; call admin/teacher APIs",
   "Pages redirect the student to their own dashboard; restricted APIs return 403.",
   "A", ["test_fr01_authentication::test_wrong_role_denied",
         "test_frontend_pages::test_role_page_redirects_other_roles",
         "test_fr14_dashboard_summary::test_fr14_users_cannot_open_another_roles_dashboard"],
   UPDATED, "Clarified that pages redirect and APIs return 403 (implemented behaviour).")
tc("SYS_FR-01_08", "FR-01", "Logout", "User logged in",
   "Teacher account", "Click logout; press browser Back; reload protected page",
   "Protected pages cannot be reopened: page requests redirect to /login, API requests return 401. Responses carry Cache-Control: no-store.",
   "A+B", ["test_fr15_logout::test_protected_route_after_logout",
           "test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out"],
   UPDATED, "Back-button behaviour needs a real-browser check in System Validation.")
tc("SYS_FR-01_09", "FR-01", "Session timeout", "Timeout configured (PERMANENT_SESSION_LIFETIME = 30 minutes)",
   "Idle session", "Remain inactive past the lifetime; open protected page",
   "Login is required again after 30 minutes of inactivity.",
   "A+M", ["test_nfr01_security::test_session_expiration_configured"],
   UPDATED, "Timeout value made explicit. The existing test only checks the configuration, not actual expiry; see gap G-10.")
tc("SYS_FR-01_10", "FR-01", "Authentication failure handling", "Application available; database made unavailable",
   "Valid credentials", "Attempt login while the user database cannot be read",
   "HTTP 503 'Authentication temporarily unavailable'; no stack trace or technical detail shown.",
   "A", [],
   UPDATED, "'Auth service' replaced by the database (the app checks credentials locally). No automated test exists yet; see gap G-10.")
tc("UT_FR-01_11", "FR-01", "Inactive (deactivated) account login", "Account deactivated by admin",
   "Deactivated student account", "Attempt login",
   "Login rejected; any existing session for that user loses access.",
   "A", ["test_fr01_authentication::test_inactive_account_cannot_login",
         "test_fr01_authentication::test_inactive_user_loses_existing_access",
         "test_frontend_pages::test_inactive_user_is_sent_to_login"],
   NEW, "Covers backlog US-02 (locked/inactive accounts).")
tc("UT_FR-01_12", "FR-01", "Malformed login request", "Login API available",
   "Non-JSON body", "POST /api/login with an invalid body",
   "HTTP 400 'JSON request body required'.",
   "A", ["test_fr01_authentication::test_invalid_json_body"], NEW)
tc("IT_FR-01_13", "FR-01", "Session replaced on new login", "User A logged in",
   "Two accounts", "Log in as user B in the same browser session",
   "Session now belongs only to user B; no data from user A remains accessible.",
   "A", ["test_fr01_authentication::test_session_replaced_when_different_user_logs_in",
         "test_fr01_authentication::test_session_created_after_login"], NEW)

# ---------------------------------------------------------------- FR-02
tc("UT_FR-02_01", "FR-02", "Mark Present", "Teacher logged in; class exists; student enrolled",
   "S01, DBMS, 2026-09-01, Present", "Select class/subject/date; mark Present; save",
   "HTTP 201; record saved with status Present.", "A",
   ["test_fr02_attendance_marking::test_ut_fr_02_01_mark_present"])
tc("UT_FR-02_02", "FR-02", "Mark Absent", "Roster loaded", "S01, Absent", "Mark Absent; save",
   "HTTP 201; record saved with status Absent.", "A",
   ["test_fr02_attendance_marking::test_ut_fr_02_02_mark_absent"])
tc("UT_FR-02_03", "FR-02", "Mark Late", "Roster loaded", "S01, Late", "Mark Late; save",
   "HTTP 201; record saved with status Late.", "A",
   ["test_fr02_attendance_marking::test_ut_fr_02_03_mark_late"])
tc("UT_FR-02_04", "FR-02", "Missing date validation", "Teacher logged in", "Date blank",
   "Leave date empty; save",
   "API returns 400 with a validation error; UI date field is required and blocks submission.", "A",
   ["test_fr02_attendance_marking::test_ut_fr_02_04_missing_date_validation"])
tc("UT_FR-02_05", "FR-02", "Missing status validation", "Roster loaded", "Status blank",
   "Leave status unselected; save", "API returns 400 with a validation error.", "A",
   ["test_fr02_attendance_marking::test_ut_fr_02_05_missing_status_validation"])
tc("IT_FR-02_06", "FR-02", "Load class roster", "Class and subject data exist", "CSE-A, DBMS",
   "Select class and subject", "GET /api/roster returns exactly the students enrolled in that class and subject.", "A",
   ["test_fr02_attendance_marking::test_it_fr_02_06_load_class_roster"])
tc("IT_FR-02_07", "FR-02", "Save complete roster", "Roster loaded", "S01 Present; S02 Absent; S03 Late",
   "Mark statuses for all students; save", "All entries are processed and stored.", "A",
   ["test_fr02_attendance_marking::test_it_fr_02_07_save_complete_roster"])
tc("IT_FR-02_08", "FR-02", "Unauthorized subject", "Teacher logged in", "Unassigned subject",
   "Attempt to mark an unassigned subject", "Request denied with HTTP 403.", "A",
   ["test_fr02_attendance_marking::test_it_fr_02_08_unauthorized_subject"])
tc("SYS_FR-02_09", "FR-02", "Change attendance date", "Roster loaded", "2026-09-02",
   "Select another date; mark; save", "Records are stored against the selected date only.", "A",
   ["test_fr02_attendance_marking::test_sys_fr_02_09_change_attendance_date"])
tc("SYS_FR-02_10", "FR-02", "Invalid attendance status", "Roster loaded", "Excused",
   "Submit unsupported status", "Invalid status rejected with HTTP 400.", "A",
   ["test_fr02_attendance_marking::test_sys_fr_02_10_invalid_attendance_status"])
tc("IT_FR-02_11", "FR-02", "Unenrolled student rejected", "Student not enrolled in subject",
   "Unenrolled student id", "Mark attendance (single and batch)",
   "Request rejected; no record written.", "A",
   ["test_fr02_attendance_marking::test_unenrolled_student_rejected_single",
    "test_fr02_attendance_marking::test_unenrolled_student_rejected_batch",
    "test_fr02_attendance_marking::test_zero_enrollments_rejected_single"], NEW)
tc("IT_FR-02_12", "FR-02", "Batch save is all-or-nothing", "Roster loaded",
   "Batch with one invalid/unenrolled entry", "Submit the batch",
   "Whole batch rejected; no partial records saved.", "A",
   ["test_fr02_attendance_marking::test_batch_mixture_enrolled_unenrolled_rejected_without_partial_writes",
    "test_fr02_attendance_marking::test_batch_rollback_on_failure"], NEW)
tc("SYS_FR-02_13", "FR-02", "Mark attendance through teacher dashboard", "Teacher logged in to browser",
   "Seeded class/subject/students", "Open Teacher > Mark attendance; choose class, subject, date; set statuses; save",
   "Success message shown; saved statuses visible in Records.", "B",
   ["test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out"],
   NEW, "Frontend scenario.")

# ---------------------------------------------------------------- FR-03
tc("UT_FR-03_01", "FR-03", "Save new record", "Valid attendance form", "S01, DBMS, 2026-09-01, Present",
   "Enter data; save", "Record saved (HTTP 201).", "A",
   ["test_fr03_record_management::test_ut_fr_03_01_save_new_record"])
tc("UT_FR-03_02", "FR-03", "Update existing record", "Record exists", "Existing S01 record",
   "Change Present to Late; save", "Record updated to Late.", "A",
   ["test_fr03_record_management::test_ut_fr_03_02_update_existing_record_by_id"])
tc("UT_FR-03_03", "FR-03", "Prevent duplicate record", "Record exists", "Same key values",
   "Submit same student/subject/date", "Duplicate prevented; only one record exists for the key.", "A",
   ["test_fr03_record_management::test_ut_fr_03_03_prevent_duplicate_record",
    "test_foundation::test_duplicate_attendance_prevented"])
tc("UT_FR-03_04", "FR-03", "Missing student validation", "Form available", "Student blank",
   "Submit without student", "HTTP 400 validation error.", "A",
   ["test_fr03_record_management::test_ut_fr_03_04_missing_student_validation"])
tc("UT_FR-03_05", "FR-03", "Missing subject validation", "Form available", "Subject blank",
   "Submit without subject", "HTTP 400 validation error.", "A",
   ["test_fr03_record_management::test_ut_fr_03_05_missing_subject_validation"])
tc("IT_FR-03_06", "FR-03", "Database persistence", "Database connected", "Valid record",
   "Save; reload record list from a new connection", "Record remains available.", "A",
   ["test_fr03_record_management::test_it_fr_03_06_database_persistence_across_connection_reload"])
tc("IT_FR-03_07", "FR-03", "Student update restriction", "Student account exists", "Student session",
   "Login as student; attempt update", "Update denied (HTTP 403).", "A",
   ["test_fr03_record_management::test_it_fr_03_07_student_update_restriction"])
tc("IT_FR-03_08", "FR-03", "Teacher authorization", "Teacher assigned to class", "Authorized teacher",
   "Update assigned record", "Update succeeds.", "A",
   ["test_fr03_record_management::test_it_fr_03_08_teacher_authorization"])
tc("SYS_FR-03_09", "FR-03", "Refresh after save", "Record saved", "Saved record",
   "Refresh page / re-query", "Record is retained exactly once.", "A",
   ["test_fr03_record_management::test_sys_fr_03_09_refresh_after_save"])
tc("SYS_FR-03_10", "FR-03", "Database failure handling", "Database error during save", "Valid attendance data",
   "Attempt save while a write fails", "Safe error returned; no partial record (transaction rolled back).", "A",
   ["test_fr03_record_management::test_sys_fr_03_10_database_atomic_rollback"],
   UPDATED, "Verified as transaction rollback; confirm in Phase 2 how the failure is simulated.")
tc("IT_FR-03_11", "FR-03", "Delete attendance record", "Record exists",
   "Own record; another teacher's record; missing id", "DELETE /api/attendance/<id>",
   "Assigned teacher/admin can delete (record gone); other teacher gets 403; unknown id gets 404.", "A",
   ["test_fr03_record_management::test_fr03_record_deletion"], NEW,
   "Deletion is implemented (not in original plan).")
tc("IT_FR-03_12", "FR-03", "Idempotent upsert by key", "Record exists", "Same student/subject/date, new status",
   "PUT /api/attendance with the same key", "Existing record updated in place; no duplicate.", "A",
   ["test_fr03_record_management::test_fr03_idempotent_upsert_by_key"], NEW)
tc("SYS_FR-03_13", "FR-03", "Edit and delete through teacher dashboard", "Teacher logged in to browser; records exist",
   "Seeded records", "Teacher > Records: edit a status; delete a record and confirm the dialog",
   "Edited status shown; deleted record removed from the table after confirmation.", "B",
   ["test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out"],
   NEW, "Existing browser test covers correction; the delete UI needs checking in System Validation.")

# ---------------------------------------------------------------- FR-04
tc("UT_FR-04_01", "FR-04", "All present calculation", "10 records exist", "10 Present / 10 classes",
   "Open percentage", "100% displayed.", "A",
   ["test_fr04_percentages::test_fr04_percentages_calculate_correctly"])
tc("UT_FR-04_02", "FR-04", "Half attendance calculation", "10 records exist", "5 Present / 10 classes",
   "Open percentage", "50% displayed.", "A",
   ["test_fr04_percentages::test_fr04_percentages_calculate_correctly"],
   remarks="Mapping to be confirmed against test data in Phase 2.")
tc("UT_FR-04_03", "FR-04", "Absent calculation", "Records exist", "6 Present / 4 Absent",
   "Open percentage", "60% displayed.", "A",
   ["test_fr04_percentages::test_fr04_percentages_calculate_correctly"],
   remarks="Mapping to be confirmed against test data in Phase 2.")
tc("UT_FR-04_04", "FR-04", "Late policy calculation", "Late rule: Late counts as a held class but not as attended",
   "8 Present / 2 Late", "Open percentage", "80.00% displayed (Late not counted as attended).", "A",
   ["test_fr04_percentages::test_fr04_late_is_not_counted_as_attended"],
   UPDATED, "Implemented late policy written into the expected result.")
tc("UT_FR-04_05", "FR-04", "No records calculation", "No records exist", "0 records",
   "Open percentage", "0% or a no-records indication shown; no division-by-zero error.", "A",
   ["test_fr11_attendance_alert::test_zero_eligible_attendance",
    "test_fr11_attendance_alert::test_empty_database_and_no_attendance_records"])
tc("IT_FR-04_06", "FR-04", "Recalculate after update", "Existing records exist", "Present changed to Absent",
   "Change status; refresh", "Percentage updates correctly.", "A",
   ["test_fr11_attendance_alert::test_reactivity_on_attendance_updates"],
   remarks="Covered via the alerts percentage; no test on /api/attendance/percentages itself (gap G-10).")
tc("IT_FR-04_07", "FR-04", "Subject filter calculation", "Multiple subjects exist", "DBMS only",
   "Select one subject", "Only the selected subject is included.", "A",
   ["test_fr04_percentages::test_fr04_subject_filter"])
tc("IT_FR-04_08", "FR-04", "Date range calculation", "Records across dates", "2026-09-01 to 2026-09-10",
   "Request a report for the date range", "Only the selected range is included in the percentage.", "A",
   ["test_fr06_attendance_reporting::test_date_range_filtering_inclusive"],
   UPDATED, "/api/attendance/percentages has no date-range filter; the range percentage comes from the FR-06 report summary (gap G-06).")
tc("SYS_FR-04_09", "FR-04", "Rounding calculation", "Repeating decimal possible", "2 Present / 3 classes",
   "Open percentage", "66.67% shown (rounded to 2 decimal places, consistently on server and student UI).", "A",
   [], UPDATED, "Rounding rule (2 decimals) made explicit. No automated test yet (gap G-10).")
tc("SYS_FR-04_10", "FR-04", "Large dataset calculation", "Large dataset exists", "1,500 records",
   "Open percentage", "Correct result within the 3-second target.", "A",
   ["test_nfr02_performance::test_nfr02_attendance_percentages_within_threshold"])

# ---------------------------------------------------------------- FR-05
tc("UT_FR-05_01", "FR-05", "View own records", "Student logged in; records exist", "Student S01",
   "Open attendance page", "Only the student's own records displayed.", "A+B",
   ["test_fr05_attendance_viewing::test_fr05_student_only_sees_own_records",
    "test_nfr05_browser_compatibility::test_student_views_own_attendance"])
tc("UT_FR-05_02", "FR-05", "View by subject", "Records exist", "DBMS", "Apply subject filter",
   "Only DBMS records displayed.", "A", ["test_fr05_attendance_viewing::test_fr05_filter_by_subject"])
tc("UT_FR-05_03", "FR-05", "View by date", "Records exist", "2026-09-01", "Apply date filter",
   "Only matching-date records displayed.", "A", ["test_fr05_attendance_viewing::test_fr05_filter_by_date"])
tc("UT_FR-05_04", "FR-05", "Empty result handling", "No matching records", "Nonexistent date",
   "Apply filter", "API returns an empty list; UI shows a clear empty-state message.", "A+B",
   ["test_fr05_attendance_viewing::test_fr05_empty_results"],
   remarks="UI empty-state message to be checked in System Validation.")
tc("IT_FR-05_05", "FR-05", "Teacher views assigned class", "Teacher assigned to class", "CSE-A",
   "Open class records", "Only records of the teacher's assigned subjects displayed.", "A",
   ["test_fr05_attendance_viewing::test_fr05_teacher_only_sees_assigned_subjects"])
tc("IT_FR-05_06", "FR-05", "Student data restriction", "Two student accounts exist", "S02 while logged in as S01",
   "Attempt to view another student", "Access denied.", "A",
   ["test_fr05_attendance_viewing::test_fr05_student_cannot_view_another_students_records"])
tc("IT_FR-05_07", "FR-05", "Updated record visibility", "Record updated", "S01 Late",
   "Open record", "Latest value displayed.", "A",
   ["test_fr03_record_management::test_sys_fr_03_09_refresh_after_save"],
   remarks="Mapping to be confirmed in Phase 2.")
tc("SYS_FR-05_08", "FR-05", "Sort records", "Records exist", "Multiple records",
   "View records", "Records listed newest date first, then by student.", "A",
   ["test_fr10_attendance_search_filter::test_fr10_results_keep_date_then_student_order"],
   UPDATED, "No user-selectable sort exists; expected result changed to the fixed order the system uses (gap G-05).")
tc("SYS_FR-05_09", "FR-05", "Pagination", "Many records exist", "100+ records",
   "Move between pages", "Correct records shown per page.", "B", [],
   remarks="Pagination is not implemented in API or UI (gap G-05). Not an SRS requirement; kept because it was in the original plan.")
tc("SYS_FR-05_10", "FR-05", "Responsive viewing", "Supported browser/device", "Desktop/mobile widths",
   "Open at different widths", "Content remains readable with no horizontal overflow.", "B+M",
   ["test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow",
    "test_nfr04_usability::test_nfr04_interface_supports_responsive_layout"],
   remarks="Readability itself needs human confirmation.")

# ---------------------------------------------------------------- FR-06
_R = "Executed through the REST API: the UI has no reporting screen (gap G-01)."
tc("UT_FR-06_01", "FR-06", "Report by student", "Records exist", "S01", "Request student report",
   "Only S01 data included; summary totals correct.", "A",
   ["test_fr06_attendance_reporting::test_student_wise_report_admin",
    "test_fr06_attendance_reporting::test_student_wise_report_via_path_param"], UPDATED, _R)
tc("UT_FR-06_02", "FR-06", "Report by class", "Records exist", "CSE-A", "Request class report",
   "Selected class data included.", "A", ["test_fr06_attendance_reporting::test_class_wise_report"], UPDATED, _R)
tc("UT_FR-06_03", "FR-06", "Report by subject", "Records exist", "DBMS", "Request subject report",
   "Selected subject data included.", "A", ["test_fr06_attendance_reporting::test_subject_wise_report"], UPDATED, _R)
tc("UT_FR-06_04", "FR-06", "Report by date range", "Records exist", "2026-09-01 to 2026-09-10",
   "Request report with start/end dates", "Only the inclusive range is included.", "A",
   ["test_fr06_attendance_reporting::test_date_range_filtering_inclusive",
    "test_fr06_attendance_reporting::test_date_range_single_day"], UPDATED, _R)
tc("IT_FR-06_05", "FR-06", "Combined filters", "Records exist", "CSE-A, DBMS, date range",
   "Request report with class, subject and range", "All filters applied together.", "A",
   ["test_fr06_attendance_reporting::test_combined_student_class_subject_date_filters"], UPDATED, _R)
tc("IT_FR-06_06", "FR-06", "Current saved data", "Records saved", "Updated S01 record",
   "Update record; generate report", "Report uses the latest data.", "A",
   ["test_fr12_implementation::test_export_reflects_updated_records"], UPDATED,
   _R + " Covered through the export of the same report; confirm in Phase 2.")
tc("IT_FR-06_07", "FR-06", "Report access control", "Role accounts exist", "Student account",
   "Student requests class-wide or another student's report", "Only the permitted scope is available (403 otherwise).", "A",
   ["test_fr06_attendance_reporting::test_student_cannot_view_other_student_report",
    "test_fr06_attendance_reporting::test_teacher_subject_restriction",
    "test_fr06_attendance_reporting::test_student_can_generate_own_report"], UPDATED, _R)
tc("SYS_FR-06_08", "FR-06", "Empty report", "No matching data", "No matching filter",
   "Generate report", "API returns zero records with zero totals; empty-report message shown in UI.", "A+B",
   ["test_fr06_attendance_reporting::test_valid_filter_empty_results",
    "test_fr06_attendance_reporting::test_date_range_empty_results"], UPDATED,
   "API part automated; the UI message cannot be checked because no reporting screen exists (gap G-01).")
tc("SYS_FR-06_09", "FR-06", "Report accuracy", "Known dataset exists", "Known totals",
   "Generate and compare totals", "Totals and percentages match the stored records.", "A",
   ["test_fr06_attendance_reporting::test_records_outside_filters_are_strictly_excluded",
    "test_fr06_attendance_reporting::test_no_duplicate_records_on_multiple_enrollments"], UPDATED, _R)
tc("SYS_FR-06_10", "FR-06", "Report performance", "Large dataset exists", "Large class/date range",
   "Generate report", "Report generated within 3 seconds.", "A",
   ["test_nfr02_performance::test_nfr02_attendance_report_generation_within_threshold"])
tc("UT_FR-06_11", "FR-06", "Invalid report parameters", "Reporting API available",
   "Bad date format; start > end; status 'Excused'; non-numeric ids", "Request report",
   "HTTP 400 with a clear error for each invalid input.", "A",
   ["test_fr06_attendance_reporting::test_invalid_start_date_format",
    "test_fr06_attendance_reporting::test_start_date_later_than_end_date",
    "test_fr06_attendance_reporting::test_invalid_status_filter",
    "test_fr06_attendance_reporting::test_invalid_identifiers"], NEW)
tc("UT_FR-06_12", "FR-06", "Nonexistent report target", "Reporting API available",
   "Unknown student/class/subject id", "Request report", "HTTP 404 'not found'.", "A",
   ["test_fr06_attendance_reporting::test_nonexistent_student_returns_404",
    "test_fr06_attendance_reporting::test_nonexistent_class_returns_404",
    "test_fr06_attendance_reporting::test_nonexistent_subject_returns_404"], NEW)

# ---------------------------------------------------------------- FR-07
tc("UT_FR-07_01", "FR-07", "Create student and teacher accounts", "Admin logged in",
   "New usernames, valid password (>= 8 chars), roles student/teacher", "POST /api/users for each role",
   "HTTP 201; accounts created and active.", "A",
   ["test_fr07_user_management::test_admin_can_create_all_roles"], NEW)
tc("UT_FR-07_02", "FR-07", "Invalid user input", "Admin logged in",
   "Blank username; short password; role 'superuser'; missing body", "POST /api/users",
   "HTTP 400 for each invalid input; no account created.", "A",
   ["test_fr07_user_management::test_create_user_invalid_inputs",
    "test_fr07_user_management::test_create_user_missing_body",
    "test_fr07_user_management::test_create_user_invalid_active_flag"], NEW)
tc("UT_FR-07_03", "FR-07", "Duplicate username", "User 'teacher01' exists", "teacher01",
   "Create another user named teacher01", "HTTP 409; duplicate rejected.", "A",
   ["test_fr07_user_management::test_create_duplicate_username"], NEW)
tc("UT_FR-07_04", "FR-07", "Password stored as hash", "Admin creates a user", "Any password",
   "Inspect the users table", "Only a salted hash is stored; plaintext never stored or returned.", "A",
   ["test_fr07_user_management::test_password_is_securely_hashed"], NEW)
tc("IT_FR-07_05", "FR-07", "Update account", "User exists", "New username, role, password",
   "PUT /api/users/<id>", "Changes saved; user can log in with the new password.", "A",
   ["test_fr07_user_management::test_admin_can_update_username",
    "test_fr07_user_management::test_admin_can_update_user_role",
    "test_fr07_user_management::test_admin_can_update_user_password"], NEW)
tc("IT_FR-07_06", "FR-07", "Update conflicts and missing user", "Users exist",
   "Taken username; nonexistent id", "PUT /api/users/<id>", "HTTP 409 for taken username; 404 for unknown id.", "A",
   ["test_fr07_user_management::test_update_user_duplicate_username_returns_409",
    "test_fr07_user_management::test_update_user_nonexistent_returns_404",
    "test_fr07_user_management::test_update_user_invalid_inputs"], NEW)
tc("IT_FR-07_07", "FR-07", "Deactivate and reactivate account", "Active user exists", "Student account",
   "Deactivate; attempt login; reactivate; login", "Deactivated user cannot log in; reactivated user can.", "A",
   ["test_fr07_user_management::test_admin_can_deactivate_and_activate_user",
    "test_fr07_user_management::test_deactivate_and_activate_nonexistent_user"], NEW)
tc("IT_FR-07_08", "FR-07", "Deactivation ends active session", "User logged in elsewhere", "Student session",
   "Admin deactivates the user; user makes a request", "Existing session is rejected.", "A",
   ["test_fr07_user_management::test_active_session_revoked_on_deactivation"], NEW)
tc("IT_FR-07_09", "FR-07", "Non-admin cannot manage users", "Teacher/student logged in; or logged out",
   "Teacher, student, anonymous", "Call create/list/update/deactivate user APIs",
   "HTTP 403 for teacher/student; 401 when logged out.", "A",
   ["test_fr07_user_management::test_create_user_forbidden_for_non_admins",
    "test_fr07_user_management::test_view_users_forbidden_for_non_admins",
    "test_fr07_user_management::test_update_user_forbidden_for_non_admins",
    "test_fr07_user_management::test_deactivate_and_activate_forbidden_for_non_admins",
    "test_fr07_user_management::test_create_user_unauthenticated"], NEW)
tc("SYS_FR-07_10", "FR-07", "Manage users through admin dashboard", "Admin logged in to browser",
   "Synthetic users", "Admin > Users: create user via dialog; search/filter by role and status; edit; deactivate",
   "Each action succeeds and the table updates; validation errors shown for bad input.", "B",
   ["test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog"], NEW,
   "Existing browser test covers creation only; the rest is checked in System Validation.")

# ---------------------------------------------------------------- FR-08
tc("UT_FR-08_01", "FR-08", "Create class", "Admin logged in", "Class 'CSE-A' (optionally with teacher)",
   "POST /api/classes", "HTTP 201; class created (teacher assigned when given).", "A",
   ["test_fr08_class_subject_management::test_admin_can_create_class",
    "test_fr08_class_subject_management::test_admin_can_create_class_with_assigned_teacher"], NEW)
tc("UT_FR-08_02", "FR-08", "Invalid or duplicate class name", "Class 'CSE-A' exists", "Blank name; 'CSE-A'",
   "Create/update class", "HTTP 400 for blank; 409 for duplicate.", "A",
   ["test_fr08_class_subject_management::test_blank_class_name_rejected",
    "test_fr08_class_subject_management::test_duplicate_class_name_rejected",
    "test_fr08_class_subject_management::test_update_class_duplicate_name_rejected",
    "test_fr08_class_subject_management::test_update_class_invalid_payloads"], NEW)
tc("UT_FR-08_03", "FR-08", "Create subject", "Admin logged in", "Subject 'DBMS' (optionally with teacher/class)",
   "POST /api/subjects", "HTTP 201; subject created and linked.", "A",
   ["test_fr08_class_subject_management::test_admin_can_create_subject",
    "test_fr08_class_subject_management::test_admin_can_create_subject_with_assigned_teacher",
    "test_fr08_class_subject_management::test_create_subject_with_class_id_associates_automatically"], NEW)
tc("UT_FR-08_04", "FR-08", "Invalid or duplicate subject", "Subject 'DBMS' exists", "Blank name; 'DBMS'; bad payloads",
   "Create/update subject", "HTTP 400 for invalid; 409 for duplicate.", "A",
   ["test_fr08_class_subject_management::test_blank_subject_name_rejected",
    "test_fr08_class_subject_management::test_duplicate_subject_name_rejected",
    "test_fr08_class_subject_management::test_subject_creation_invalid_payloads",
    "test_fr08_class_subject_management::test_update_subject_invalid_payloads"], NEW)
tc("IT_FR-08_05", "FR-08", "Assign teacher to class and subject", "Class, subject, teacher exist", "Teacher01",
   "PUT /api/classes/<id>/teacher and /api/subjects/<id>/teacher", "Teacher assigned; visible in teacher's own routes.", "A",
   ["test_fr08_class_subject_management::test_admin_can_assign_teacher_to_class",
    "test_fr08_class_subject_management::test_admin_can_assign_teacher",
    "test_fr08_class_subject_management::test_assigned_teacher_visibility_in_teacher_routes"], NEW)
tc("IT_FR-08_06", "FR-08", "Invalid teacher assignment", "Users exist",
   "Student id; inactive teacher; nonexistent id; non-integer id", "Assign as teacher",
   "Assignment rejected with 400/404.", "A",
   ["test_fr08_class_subject_management::test_student_cannot_be_assigned_as_teacher",
    "test_fr08_class_subject_management::test_inactive_teacher_cannot_be_assigned",
    "test_fr08_class_subject_management::test_nonexistent_teacher_id_rejected",
    "test_fr08_class_subject_management::test_invalid_teacher_id_type_rejected"], NEW)
tc("IT_FR-08_07", "FR-08", "Link and unlink subject and class", "Class and subject exist", "CSE-A + DBMS",
   "POST/DELETE /api/classes/<id>/subjects", "Subject linked then unlinked; invalid ids rejected.", "A",
   ["test_fr08_class_subject_management::test_admin_can_associate_subject_with_class",
    "test_fr08_class_subject_management::test_associate_subject_invalid_ids",
    "test_fr08_class_subject_management::test_dissociate_subject_invalid_ids"], NEW)
tc("IT_FR-08_08", "FR-08", "Update and unassign", "Class/subject with teacher", "New name; teacher_id null",
   "PUT class/subject", "Name updated; teacher unassigned.", "A",
   ["test_fr08_class_subject_management::test_admin_can_update_class",
    "test_fr08_class_subject_management::test_admin_can_update_class_unassign_teacher",
    "test_fr08_class_subject_management::test_admin_can_update_subject_unassign_teacher"], NEW)
tc("IT_FR-08_09", "FR-08", "Non-admin cannot manage classes/subjects", "Teacher/student/anonymous",
   "Each role", "Call class/subject management APIs", "HTTP 403 (teacher/student) or 401 (anonymous).", "A",
   ["test_fr08_class_subject_management::test_teacher_access_is_denied",
    "test_fr08_class_subject_management::test_student_access_is_denied",
    "test_fr08_class_subject_management::test_unauthenticated_access_is_denied"], NEW)
tc("SYS_FR-08_10", "FR-08", "Manage classes and subjects through admin dashboard", "Admin logged in to browser",
   "Synthetic class/subject", "Admin > Classes and Subjects: create, edit, assign teacher, link subject, search",
   "Each action succeeds and the lists update.", "B", [], NEW,
   "No existing browser test; checked in System Validation.")

# ---------------------------------------------------------------- FR-09
tc("UT_FR-09_01", "FR-09", "Enroll student", "Admin logged in; student, class, subject exist", "S01 -> CSE-A / DBMS",
   "POST /api/enrollments", "HTTP 201; enrollment saved.", "A",
   ["test_fr09_student_enrollment::test_admin_can_enroll_student"], NEW)
tc("UT_FR-09_02", "FR-09", "Duplicate enrollment", "S01 already enrolled", "Same triple",
   "Enroll again", "Duplicate rejected.", "A",
   ["test_fr09_student_enrollment::test_duplicate_enrollment_is_rejected"], NEW)
tc("UT_FR-09_03", "FR-09", "Missing fields", "Admin logged in", "Missing student/class/subject",
   "POST /api/enrollments", "HTTP 400.", "A",
   ["test_fr09_student_enrollment::test_missing_fields_are_rejected"], NEW)
tc("UT_FR-09_04", "FR-09", "Nonexistent class", "Admin logged in", "class_id 9999",
   "POST /api/enrollments", "Rejected (not found).", "A",
   ["test_fr09_student_enrollment::test_nonexistent_class_is_rejected"], NEW)
tc("UT_FR-09_05", "FR-09", "Non-student or unknown ids", "Admin logged in",
   "Teacher id as student; unknown student/subject id", "POST /api/enrollments",
   "Rejected; no enrollment created.", "A", [], NEW,
   "No automated test found yet (gap G-10).")
tc("IT_FR-09_06", "FR-09", "Non-admin cannot enroll", "Teacher/student logged in", "Each role",
   "POST /api/enrollments", "HTTP 403.", "A",
   ["test_fr09_student_enrollment::test_non_admin_cannot_enroll_student",
    "test_frontend_pages::test_list_enrollments_requires_admin"], NEW)
tc("IT_FR-09_07", "FR-09", "List and filter enrollments", "Enrollments exist", "class filter",
   "GET /api/enrollments?class_id=", "List includes names; filters applied.", "A",
   ["test_frontend_pages::test_list_enrollments_returns_names",
    "test_frontend_pages::test_list_enrollments_filters"], NEW)
tc("IT_FR-09_08", "FR-09", "Remove enrollment", "Enrollment exists", "S01 / CSE-A / DBMS",
   "DELETE /api/enrollments", "Enrollment removed; invalid/unauthorized requests rejected.", "A",
   ["test_frontend_pages::test_delete_enrollment",
    "test_frontend_pages::test_delete_enrollment_validation_and_auth"], NEW)
tc("IT_FR-09_09", "FR-09", "Enrolled student appears in roster", "S01 enrolled", "CSE-A, DBMS",
   "Teacher loads roster", "S01 listed; unenrolled students not listed.", "A",
   ["test_fr02_attendance_marking::test_it_fr_02_06_load_class_roster"], NEW)
tc("SYS_FR-09_10", "FR-09", "Enroll through admin dashboard", "Admin logged in to browser", "Synthetic data",
   "Admin > Enrollments: pick student, class, subject; enroll; search; filter by class; remove",
   "Enrollment appears in the list and can be removed.", "B", [], NEW,
   "No existing browser test; checked in System Validation.")

# ---------------------------------------------------------------- FR-10
tc("UT_FR-10_01", "FR-10", "Filter by class", "Records in several classes", "class_id of CSE-A",
   "GET /api/attendance?class_id=", "Only records of students/subjects in that class.", "A",
   ["test_fr10_attendance_search_filter::test_fr10_filter_by_class_matches_student_and_subject",
    "test_fr10_attendance_search_filter::test_fr10_class_filter_excludes_subject_student_is_not_enrolled_for"], NEW)
tc("UT_FR-10_02", "FR-10", "Filter by student", "Records for several students", "student_id S01",
   "GET /api/attendance?student_id=", "Only S01 records.", "A",
   ["test_fr05_attendance_viewing_extra::test_fr05_admin_can_filter_by_student",
    "test_fr10_attendance_search_filter::test_fr10_class_and_student"], NEW)
tc("UT_FR-10_03", "FR-10", "Filter by subject", "Records for several subjects", "DBMS",
   "GET /api/attendance?subject_id=", "Only DBMS records.", "A",
   ["test_fr05_attendance_viewing_extra::test_fr05_admin_can_filter_by_subject",
    "test_fr10_attendance_search_filter::test_fr10_class_and_subject"], NEW)
tc("UT_FR-10_04", "FR-10", "Filter by date and date range", "Records on several dates",
   "2026-09-01; 2026-09-01..2026-09-10", "GET with attendance_date / start_date & end_date",
   "Only matching dates (range inclusive).", "A",
   ["test_fr10_attendance_search_filter::test_fr10_class_and_date",
    "test_fr10_attendance_search_filter::test_fr10_class_and_date_range",
    "test_fr06_attendance_reporting::test_api_attendance_date_range_regression"], NEW)
tc("UT_FR-10_05", "FR-10", "Filter by status", "Mixed statuses", "Late", "GET with status=Late",
   "Only Late records.", "A", ["test_fr10_attendance_search_filter::test_fr10_class_and_status"], NEW)
tc("IT_FR-10_06", "FR-10", "Combined filters and empty result", "Records exist", "All filters together",
   "GET with class, student, subject, date, status", "Intersection returned; empty list when nothing matches.", "A",
   ["test_fr10_attendance_search_filter::test_fr10_all_filters_combined",
    "test_fr10_attendance_search_filter::test_fr10_filters_excluding_all_class_records_return_empty"], NEW)
tc("IT_FR-10_07", "FR-10", "Invalid filter values", "API available", "class_id=abc; bad date; start > end",
   "GET with invalid filters", "HTTP 400.", "A",
   ["test_fr10_attendance_search_filter::test_fr10_invalid_class_id_returns_400",
    "test_fr10_attendance_search_filter::test_fr10_invalid_filter_alongside_class_returns_400",
    "test_fr06_attendance_reporting::test_api_attendance_invalid_date_range_regression"], NEW)
tc("IT_FR-10_08", "FR-10", "Nonexistent filter target", "API available",
   "class_id 9999; largest SQLite integer", "GET with nonexistent ids", "HTTP 404; no server error.", "A",
   ["test_fr10_attendance_search_filter::test_fr10_nonexistent_class_returns_404",
    "test_fr10_attendance_search_filter::test_fr10_largest_sqlite_integer_is_handled_as_missing_class"], NEW)
tc("IT_FR-10_09", "FR-10", "Filters respect role scope", "Teacher and students exist",
   "Teacher filters by another subject; student filters by class to see others", "GET with filters",
   "Teacher stays within assigned subjects; student only sees own records.", "A",
   ["test_fr10_attendance_search_filter::test_fr10_teacher_cannot_use_class_to_reach_other_subject",
    "test_fr10_attendance_search_filter::test_fr10_student_cannot_use_class_to_view_other_student",
    "test_fr10_attendance_search_filter::test_fr10_access_denial_precedes_class_lookup"], NEW)
tc("SYS_FR-10_10", "FR-10", "Search and filter in the dashboards", "Teacher/admin/student logged in to browser",
   "Seeded records", "Use search box and subject/date/status filters on Records/History; clear filters",
   "Table updates to matching rows; 'Clear filters' restores all rows.", "B", [], NEW,
   "UI has no class filter and no date-range filter (gap G-03); checked in System Validation.")

# ---------------------------------------------------------------- FR-11
tc("UT_FR-11_01", "FR-11", "Default threshold", "No threshold saved", "-", "GET /api/attendance/alerts",
   "Threshold is 75.0%.", "A", ["test_fr11_attendance_alert::test_default_threshold_behavior"], NEW)
tc("UT_FR-11_02", "FR-11", "Student below threshold flagged", "Student at 50%", "Threshold 75",
   "GET alerts", "Student listed with below_threshold=true, alert_status BELOW_THRESHOLD.", "A",
   ["test_fr11_attendance_alert::test_student_below_threshold_identified",
    "test_fr11_attendance_alert::test_clear_indication_of_low_attendance"], NEW)
tc("UT_FR-11_03", "FR-11", "Boundary: exactly at threshold", "Students at 75.00% and 74.99%", "Threshold 75",
   "GET alerts", "75.00% not flagged; 74.99% flagged (strictly below).", "A",
   ["test_fr11_attendance_alert::test_student_exactly_at_threshold_not_identified",
    "test_fr11_attendance_alert::test_boundary_strict_inequality",
    "test_fr11_attendance_alert::test_student_above_threshold_not_identified"], NEW)
tc("UT_FR-11_04", "FR-11", "Student with no records", "Enrolled student with 0 records", "include_zero false/true",
   "GET alerts", "Not flagged by default (NO_RECORDS); flagged when include_zero=true.", "A",
   ["test_fr11_attendance_alert::test_zero_eligible_attendance",
    "test_fr11_attendance_alert::test_zero_eligible_attendance_with_include_zero_flag"], NEW)
tc("UT_FR-11_05", "FR-11", "Invalid threshold", "Admin logged in", "-1; 101; 'abc'; true; null",
   "Set or query threshold", "HTTP 400 for each invalid value.", "A",
   ["test_fr11_attendance_alert::test_reject_negative_threshold",
    "test_fr11_attendance_alert::test_reject_threshold_above_100",
    "test_fr11_attendance_alert::test_reject_malformed_threshold_values"], NEW)
tc("IT_FR-11_06", "FR-11", "Admin sets threshold; persists", "Admin logged in", "80",
   "POST /api/attendance/threshold; restart app; GET threshold", "Threshold 80 saved and still 80 after restart.", "A",
   ["test_fr11_attendance_alert::test_successful_threshold_configuration",
    "test_fr11_attendance_alert::test_threshold_persisted_in_database",
    "test_fr11_attendance_alert::test_threshold_persists_across_application_restart"], NEW)
tc("IT_FR-11_07", "FR-11", "Only admin may change threshold", "Teacher/student logged in", "80",
   "POST /api/attendance/threshold", "HTTP 403 (401 when logged out).", "A",
   ["test_fr11_attendance_alert::test_threshold_modification_is_admin_only",
    "test_fr11_attendance_alert::test_unauthenticated_rejected"], NEW)
tc("IT_FR-11_08", "FR-11", "Alerts respect role scope", "Teacher/student logged in", "Other subject/student",
   "GET alerts", "Teacher sees only assigned subjects; student only self.", "A",
   ["test_fr11_attendance_alert::test_teacher_role_isolation",
    "test_fr11_attendance_alert::test_student_role_isolation"], NEW)
tc("IT_FR-11_09", "FR-11", "Alerts react to attendance changes", "Student near threshold", "Change Present to Absent",
   "Update record; GET alerts", "Alert status updates; changing threshold does not alter records.", "A",
   ["test_fr11_attendance_alert::test_reactivity_on_attendance_updates",
    "test_fr11_attendance_alert::test_threshold_change_updates_alerts_without_touching_records"], NEW)
tc("SYS_FR-11_10", "FR-11", "Alerts shown on dashboards", "Teacher/admin logged in to browser",
   "Student below 75%", "Open dashboard overview", "Low-attendance students listed; 'Everyone is on track' when none.", "B",
   [], NEW, "Display only; no UI to change the threshold (gap G-04). Checked in System Validation.")

# ---------------------------------------------------------------- FR-12
tc("UT_FR-12_01", "FR-12", "Export CSV", "Report data exists", "format=csv",
   "GET /api/reports/attendance/export?format=csv", "text/csv download with header row and correct rows.", "A",
   ["test_fr12_implementation::test_export_csv_headers_and_content"], NEW)
tc("UT_FR-12_02", "FR-12", "Export PDF", "Report data exists", "format=pdf",
   "GET export as PDF", "application/pdf download with report content.", "A",
   ["test_fr12_implementation::test_export_pdf_headers_and_content"], NEW)
tc("UT_FR-12_03", "FR-12", "Export JSON", "Report data exists", "format=json",
   "GET export as JSON", "JSON download consistent with the report.", "A",
   ["test_fr12_implementation::test_export_json_format",
    "test_fr12_implementation::test_json_export_consistency_and_download_headers"], NEW)
tc("UT_FR-12_04", "FR-12", "Unsupported format", "Export API available", "format=xml",
   "GET export", "HTTP 400; supported formats are csv, pdf, json.", "A",
   ["test_fr12_implementation::test_unsupported_export_format_returns_400"], NEW)
tc("UT_FR-12_05", "FR-12", "CSV formula injection", "Name starting with '=' exists", "=HYPERLINK(...)",
   "Export CSV", "Dangerous leading characters neutralised.", "A",
   ["test_fr12_implementation::test_csv_formula_injection_prevention"], NEW)
tc("IT_FR-12_06", "FR-12", "Export by scope", "Records exist", "student/class/subject/date range/status",
   "Export with each scope", "Exported rows match the scope.", "A",
   ["test_fr12_implementation::test_export_by_student_scope",
    "test_fr12_implementation::test_export_by_class_scope",
    "test_fr12_implementation::test_export_by_subject_scope",
    "test_fr12_implementation::test_export_by_date_range_scope",
    "test_fr12_implementation::test_export_combined_filters"], NEW)
tc("IT_FR-12_07", "FR-12", "Export access control", "Role accounts exist", "Unassigned subject; other student",
   "Export as teacher/student", "HTTP 403 outside the user's scope; 401 when logged out.", "A",
   ["test_fr12_implementation::test_teacher_cannot_export_unassigned_subject_report",
    "test_fr12_implementation::test_student_cannot_export_other_student_report",
    "test_fr12_implementation::test_export_requires_authentication"], NEW)
tc("IT_FR-12_08", "FR-12", "Invalid export parameters", "Export API available", "Bad date; start > end; bad ids",
   "Export", "HTTP 400/404 with clear error.", "A",
   ["test_fr12_implementation::test_export_invalid_date_format",
    "test_fr12_implementation::test_export_start_date_later_than_end_date",
    "test_fr12_implementation::test_export_invalid_identifiers",
    "test_fr12_implementation::test_export_nonexistent_records_return_404"], NEW)
tc("SYS_FR-12_09", "FR-12", "Large PDF export", "Large dataset", "Multi-page report",
   "Export PDF", "Multiple pages with repeated headers; no text cut off.", "A",
   ["test_fr12_implementation::test_export_multipage_pdf",
    "test_fr12_implementation::test_pdf_large_report_pagination_and_repeated_headers",
    "test_fr12_implementation::test_pdf_long_text_no_cutoff_or_overlap"], NEW)
tc("SYS_FR-12_10", "FR-12", "Export from the user interface", "User logged in to browser", "Any report",
   "Find and use an export control; open the downloaded file", "File downloads and opens correctly.", "B",
   [], NEW, "No export control exists in any dashboard (gap G-02). Expected to be BLOCKED until a UI is built.")

# ---------------------------------------------------------------- FR-13
tc("UT_FR-13_01", "FR-13", "Change own password", "Admin/teacher/student logged in",
   "Current password; new password 'NewPass#2026'", "POST /api/me/password", "HTTP 200 for each role.", "A",
   ["test_fr13_password_management::test_every_role_can_change_own_password"], NEW)
tc("UT_FR-13_02", "FR-13", "Wrong current password", "User logged in", "Wrong current password",
   "POST /api/me/password", "Rejected 'Current password is incorrect'; session stays valid.", "A",
   ["test_fr13_password_management::test_incorrect_current_password_rejected",
    "test_fr13_password_management::test_incorrect_current_password_keeps_session"], NEW)
tc("UT_FR-13_03", "FR-13", "Password length boundary", "User logged in", "7 chars (reject); exactly 8 chars (accept)",
   "POST /api/me/password", "7-character password rejected; 8-character password accepted.", "A",
   ["test_fr13_password_management::test_weak_new_password_rejected",
    "test_fr13_password_management::test_password_of_exactly_minimum_length_is_accepted"], NEW)
tc("UT_FR-13_04", "FR-13", "New password same as current", "User logged in", "new == current",
   "POST /api/me/password", "Rejected 'New password must be different from the current password'.", "A",
   ["test_fr13_password_management::test_new_password_must_differ_from_current"], NEW)
tc("UT_FR-13_05", "FR-13", "Malformed request", "User logged in", "Missing fields; non-object body; unencodable text",
   "POST /api/me/password", "HTTP 400 for each.", "A",
   ["test_fr13_password_management::test_missing_or_invalid_new_password_rejected",
    "test_fr13_password_management::test_missing_or_invalid_current_password_rejected",
    "test_fr13_password_management::test_non_object_body_rejected",
    "test_fr13_password_management::test_new_password_that_cannot_be_encoded_rejected"], NEW)
tc("IT_FR-13_06", "FR-13", "Login after change", "Password changed", "Old and new passwords",
   "Log out; log in with old then new password", "Old password rejected; new accepted.", "A",
   ["test_fr13_password_management::test_old_password_rejected_after_change",
    "test_fr13_password_management::test_new_password_accepted_after_change"], NEW)
tc("IT_FR-13_07", "FR-13", "Other sessions ended on change", "Same user logged in on two clients", "-",
   "Change password on client A; use client B", "Client A stays signed in; client B and replayed old cookies rejected.", "A",
   ["test_fr13_password_management::test_current_session_survives_change",
    "test_fr13_password_management::test_other_sessions_invalidated_by_change",
    "test_fr13_password_management::test_replayed_old_cookie_rejected_after_change"], NEW)
tc("IT_FR-13_08", "FR-13", "Cannot change another user's password", "Two users", "target user id in body",
   "POST /api/me/password targeting another user", "Request rejected; other account unchanged.", "A",
   ["test_fr13_password_management::test_cannot_target_another_account_through_request_body",
    "test_fr13_password_management::test_other_users_current_password_does_not_authorize_change"], NEW)
tc("IT_FR-13_09", "FR-13", "Unauthenticated / cross-site change", "Logged out; or foreign Origin", "-",
   "POST /api/me/password", "HTTP 401 when logged out; 403 cross-site.", "A",
   ["test_fr13_password_management::test_unauthenticated_request_rejected",
    "test_fr13_password_management::test_request_after_logout_rejected",
    "test_fr13_password_management::test_cross_site_request_rejected"], NEW)
tc("SYS_FR-13_10", "FR-13", "Change password through the dashboard", "User logged in to browser",
   "Current and new password", "Click 'Change password'; fill dialog; submit; log out; log in with new password",
   "Success message; new password works.", "B",
   ["test_fr13_password_management::test_dashboards_offer_change_password"], NEW,
   "Existing test checks the control is present; the full flow is checked in System Validation.")

# ---------------------------------------------------------------- FR-14
tc("UT_FR-14_01", "FR-14", "Dashboard requires login", "Logged out", "-", "Open /dashboard",
   "Redirected to /login.", "A", ["test_fr14_dashboard_summary::test_fr14_dashboard_requires_authentication"], NEW)
tc("IT_FR-14_02", "FR-14", "Dashboard routed by role", "Each role logged in", "Admin/teacher/student",
   "Open /dashboard", "Redirected to /admin, /teacher or /student.", "A",
   ["test_fr14_dashboard_summary::test_fr14_dashboard_redirects_by_role",
    "test_frontend_pages::test_dashboard_redirects_to_role_page"], NEW)
tc("IT_FR-14_03", "FR-14", "Admin summary matches data", "Seeded data", "Known counts",
   "Load admin dashboard data", "Totals equal database counts.", "A",
   ["test_fr14_dashboard_summary::test_fr14_admin_dashboard_summary_matches_database_records"], NEW)
tc("IT_FR-14_04", "FR-14", "Teacher summary limited to assigned subjects", "Seeded data", "Teacher01",
   "Load teacher dashboard data", "Only assigned subjects' figures.", "A",
   ["test_fr14_dashboard_summary::test_fr14_teacher_dashboard_summary_matches_assigned_records"], NEW)
tc("IT_FR-14_05", "FR-14", "Student summary shows own attendance", "Seeded data", "S01",
   "Load student dashboard data", "Only S01's figures.", "A",
   ["test_fr14_dashboard_summary::test_fr14_student_dashboard_summary_matches_own_records"], NEW)
tc("IT_FR-14_06", "FR-14", "Cross-role dashboard access", "Each role logged in", "Other role pages",
   "Open another role's dashboard", "Redirected to own dashboard.", "A",
   ["test_fr14_dashboard_summary::test_fr14_users_cannot_open_another_roles_dashboard"], NEW)
tc("IT_FR-14_07", "FR-14", "Summary data isolation", "Two teachers / two students", "-",
   "Request another user's summary data", "Denied or excluded.", "A",
   ["test_fr14_dashboard_summary::test_fr14_teacher_cannot_view_another_teachers_subject",
    "test_fr14_dashboard_summary::test_fr14_student_cannot_view_another_students_attendance"], NEW)
tc("SYS_FR-14_08", "FR-14", "Dashboard summary displayed in browser", "Each role logged in to browser",
   "Seeded data", "Open overview section", "Summary cards show figures matching the data; no errors.", "B",
   ["test_nfr02_browser_performance::test_browser_main_dashboard_overview_renders_within_threshold"], NEW,
   "Existing browser test checks rendering time, not the figures; checked in System Validation.")

# ---------------------------------------------------------------- FR-15
tc("UT_FR-15_01", "FR-15", "Logout", "User logged in", "-", "POST /api/logout", "HTTP 200; session cleared.", "A",
   ["test_fr15_logout::test_logout_success"], NEW)
tc("UT_FR-15_02", "FR-15", "Logout when not logged in", "Logged out", "-", "POST /api/logout", "HTTP 401.", "A",
   ["test_fr15_logout::test_logout_without_login"], NEW)
tc("IT_FR-15_03", "FR-15", "Protected API after logout", "User logged out", "Old session cookie",
   "Call protected API", "HTTP 401.", "A", ["test_fr15_logout::test_protected_route_after_logout"], NEW)
tc("IT_FR-15_04", "FR-15", "Logout after password change", "Password changed", "-", "Log out",
   "Logout works normally.", "A", ["test_fr13_password_management::test_logout_still_works_after_change"], NEW)
tc("IT_FR-15_05", "FR-15", "Login/logout across modules", "App running", "-",
   "Log in, use APIs in several modules, log out, retry", "All modules reject the ended session.", "A",
   ["test_nfr06_maintainability::test_login_session_and_logout_flow_spans_modules"], NEW)
tc("SYS_FR-15_06", "FR-15", "Logout button on every dashboard", "Each role logged in to browser", "-",
   "Click logout", "Returned to /login with a signed-out state.", "B",
   ["test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out"], NEW,
   "Existing browser test covers the teacher; admin and student checked in System Validation.")
tc("SYS_FR-15_07", "FR-15", "Back button after logout", "User logged out in browser", "-",
   "Press Back", "Protected content is not shown again (no-store caching; redirect to login).", "B", [], NEW,
   "Checked in System Validation; overlaps SYS_FR-01_08.")
tc("SYS_FR-15_08", "FR-15", "Logout cannot be forged cross-site", "User logged in", "Foreign Origin header",
   "POST /api/logout from another origin", "HTTP 403; session not ended.", "A",
   ["test_frontend_pages::test_cross_site_post_is_rejected"], NEW,
   "Mapping is generic CSRF protection; confirm it covers /api/logout in Phase 2.")

# ---------------------------------------------------------------- NFR-01
tc("UT_NFR-01_01", "NFR-01", "Password field masking", "Login page available", "Password value",
   "Type password", "Password is masked by default (input type=password); the show/hide toggle reveals it only on request.", "B",
   ["test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect"],
   UPDATED, "Show-password toggle exists; expected result updated. Default masked state to be confirmed in Phase 2.")
tc("IT_NFR-01_02", "NFR-01", "Role permission enforcement", "Role accounts exist", "Admin/Teacher/Student",
   "Access functions for each role", "Only permitted functions are accessible.", "A",
   ["test_nfr06_maintainability::test_role_restrictions_unchanged_after_modularization",
    "test_fr01_authentication::test_wrong_role_denied"])
tc("IT_NFR-01_03", "NFR-01", "Record scope protection", "Records exist", "Unauthorized student ID",
   "Request another user's record", "Request denied.", "A",
   ["test_fr05_attendance_viewing::test_fr05_student_cannot_view_another_students_records",
    "test_fr10_attendance_search_filter::test_fr10_student_cannot_use_class_to_view_other_student"])
tc("SYS_NFR-01_04", "NFR-01", "Secure transmission", "HTTPS deployment available", "Credentials over HTTPS",
   "Login and inspect connection", "Sensitive data transmitted securely.", "M",
   ["test_nfr01_security::test_session_cookie_security"],
   remarks="No HTTPS deployment exists; only a Secure-cookie switch (FLASK_COOKIE_SECURE=1). Expected BLOCKED (gap G-08).")
tc("SYS_NFR-01_05", "NFR-01", "Session protection", "User logged in", "Protected URL",
   "Copy protected URL to a logged-out browser", "Login required.", "A+B",
   ["test_frontend_pages::test_pages_redirect_to_login_when_signed_out",
    "test_nfr01_security::test_unauthenticated_admin_access_denied"])
tc("IT_NFR-01_06", "NFR-01", "Cross-site request forgery blocked", "User logged in",
   "Foreign Origin / Referer; look-alike origin", "Send state-changing request", "HTTP 403; same-origin requests allowed.", "A",
   ["test_frontend_pages::test_cross_site_post_is_rejected",
    "test_frontend_pages::test_cross_site_referer_is_rejected",
    "test_frontend_pages::test_lookalike_origin_is_rejected",
    "test_frontend_pages::test_same_origin_post_is_allowed"], NEW)
tc("IT_NFR-01_07", "NFR-01", "Security headers and cookie flags", "App running", "Any page",
   "Inspect response headers and cookie", "CSP, X-Frame-Options DENY, nosniff, no-store present; cookie HttpOnly, SameSite=Lax.", "A",
   ["test_nfr01_security::test_security_headers",
    "test_frontend_pages::test_pages_keep_security_headers",
    "test_frontend_pages::test_templates_have_no_inline_code_blocked_by_csp"], NEW)
tc("UT_NFR-01_08", "NFR-01", "Passwords never exposed", "Users exist", "-",
   "Inspect DB, API responses and session cookie", "Only hashes stored; no password or hash in responses or cookie.", "A",
   ["test_fr13_password_management::test_password_stored_as_hash",
    "test_fr13_password_management::test_responses_do_not_contain_passwords_or_hashes",
    "test_fr13_password_management::test_session_cookie_does_not_contain_password_hash",
    "test_fr01_authentication::test_no_plaintext_password_returned"], NEW)

# ---------------------------------------------------------------- NFR-02
_P = "Measured time must be recorded (Test Plan section 3)."
tc("SYS_NFR-02_01", "NFR-02", "Login response time", "Application available", "Valid account",
   "Login and measure response", "Login completes within 3 seconds.", "A+B",
   ["test_nfr02_performance::test_nfr02_major_page_login_loads_within_threshold",
    "test_nfr02_browser_performance::test_browser_login_page_renders_within_threshold"], remarks=_P)
tc("SYS_NFR-02_02", "NFR-02", "Dashboard load time", "User logged in", "Teacher account",
   "Open dashboard and measure", "Dashboard loads within 3 seconds.", "A+B",
   ["test_nfr02_performance::test_nfr02_major_page_teacher_dashboard_loads_within_threshold",
    "test_nfr02_browser_performance::test_browser_main_dashboard_overview_renders_within_threshold"], remarks=_P)
tc("SYS_NFR-02_03", "NFR-02", "Attendance page load", "Records exist", "Normal dataset (1,500 records)",
   "Open attendance page", "Page loads within 3 seconds.", "A+B",
   ["test_nfr02_performance::test_nfr02_attendance_records_retrieval_within_threshold",
    "test_nfr02_browser_performance::test_browser_student_attendance_view_renders_within_threshold"], remarks=_P)
tc("SYS_NFR-02_04", "NFR-02", "Percentage calculation time", "Records exist", "Normal dataset",
   "Open summary and measure", "Percentage appears within 3 seconds.", "A+B",
   ["test_nfr02_performance::test_nfr02_attendance_percentages_within_threshold",
    "test_nfr02_browser_performance::test_browser_subject_attendance_view_renders_within_threshold"], remarks=_P)
tc("SYS_NFR-02_05", "NFR-02", "Report generation time", "Large dataset exists", "Large date range",
   "Generate report and measure", "Report generated within 3 seconds.", "A",
   ["test_nfr02_performance::test_nfr02_attendance_report_generation_within_threshold",
    "test_nfr02_performance::test_nfr02_attendance_export_generation_within_threshold"],
   remarks=_P + " Browser 'reporting page' test measures /admin#attendance, not a report screen (gap G-01).")

# ---------------------------------------------------------------- NFR-03
tc("UT_NFR-03_01", "NFR-03", "Record persistence", "Database available", "Valid record",
   "Save record; retrieve it", "Record remains unchanged.", "A",
   ["test_fr03_record_management::test_it_fr_03_06_database_persistence_across_connection_reload"])
tc("IT_NFR-03_02", "NFR-03", "Backup creation", "Backup process configured", "Attendance database",
   "Run backup (scripts/backup_db.py)", "Backup is created successfully with a valid schema.", "A",
   ["test_nfr03_reliability::test_nfr03_backup_is_created",
    "test_nfr03_reliability::test_nfr03_backup_contains_valid_database_schema"])
tc("IT_NFR-03_03", "NFR-03", "Restore backup", "Valid backup exists", "Backup file",
   "Restore backup to a test database", "Records are restored correctly.", "A+M",
   ["test_nfr03_reliability::test_nfr03_backup_preserves_attendance_records",
    "test_nfr03_reliability::test_nfr03_backup_survives_original_data_changes"],
   UPDATED, "No restore script exists; restore means copying the backup file into place (gap G-07). Tests check backup contents only.")
tc("SYS_NFR-03_04", "NFR-03", "Refresh reliability", "Record saved", "Saved record",
   "Refresh and reopen record", "No data loss or duplicate.", "A",
   ["test_fr03_record_management::test_sys_fr_03_09_refresh_after_save"])
tc("SYS_NFR-03_05", "NFR-03", "Failure recovery", "Temporary failure simulated", "Valid attendance data",
   "Retry after failure", "System recovers without corrupting records.", "A",
   ["test_fr02_attendance_marking::test_batch_rollback_on_failure",
    "test_fr03_record_management::test_sys_fr_03_10_database_atomic_rollback",
    "test_nfr03_reliability::test_nfr03_missing_database_fails_safely"])
tc("IT_NFR-03_06", "NFR-03", "Regular (daily) backup schedule", "Scheduler script available",
   "Default and '04:30' times; invalid times", "Build the cron entry",
   "Daily entry at 02:00 by default (or requested time); invalid times rejected; other cron jobs kept.", "A",
   ["test_nfr03_scheduling::test_schedule_defaults_to_two_am",
    "test_nfr03_scheduling::test_schedule_uses_requested_time",
    "test_nfr03_scheduling::test_invalid_schedule_time_is_rejected",
    "test_nfr03_scheduling::test_replacing_schedule_preserves_unrelated_jobs"], NEW,
   "Tests use pure functions only; they never modify the real crontab.")

# ---------------------------------------------------------------- NFR-04
tc("UT_NFR-04_01", "NFR-04", "Consistent layout", "Templates available", "admin/teacher/student pages",
   "Render each dashboard", "Shared layout, header, sidebar and resources on all dashboards.", "A",
   ["test_nfr04_usability::test_nfr04_all_dashboards_use_consistent_layout",
    "test_nfr04_usability::test_nfr04_all_dashboards_load_shared_resources"], NEW)
tc("UT_NFR-04_02", "NFR-04", "Clear navigation labels", "Dashboards render", "-",
   "Inspect navigation", "Each section has a clear text label.", "A",
   ["test_nfr04_usability::test_nfr04_navigation_labels_are_clear"], NEW)
tc("IT_NFR-04_03", "NFR-04", "Section navigation works", "User logged in", "-",
   "Switch between sidebar sections", "Selected section shown; others hidden.", "A+B",
   ["test_nfr04_usability::test_nfr04_dashboard_navigation_supports_section_switching"], NEW)
tc("IT_NFR-04_04", "NFR-04", "Keyboard and accessibility", "Dashboards render", "Keyboard only",
   "Tab through controls", "Visible focus; controls reachable and labelled.", "A+M",
   ["test_nfr04_usability::test_nfr04_navigation_controls_are_accessible",
    "test_nfr04_usability::test_nfr04_interface_supports_keyboard_focus"], NEW)
tc("IT_NFR-04_05", "NFR-04", "Responsive and reduced motion", "Dashboards render", "Narrow width; reduced-motion setting",
   "Inspect styles / view at narrow width", "Layout adapts; animations reduced.", "A",
   ["test_nfr04_usability::test_nfr04_interface_supports_responsive_layout",
    "test_nfr04_usability::test_nfr04_reduced_motion_is_supported"], NEW)
tc("SYS_NFR-04_06", "NFR-04", "Human usability walkthrough", "Seeded demo data", "One user per role",
   "A person performs each role's main tasks without help", "Tasks completed easily; observations recorded.", "M",
   [], NEW, "Requires human judgement; cannot be automated.")

# ---------------------------------------------------------------- NFR-05
tc("SYS_NFR-05_01", "NFR-05", "Main workflows in Google Chrome", "Chrome installed", "Seeded data",
   "Run browser workflow suite with NFR05_BROWSERS=chrome", "Login, marking, viewing, user creation and layout checks pass.", "B",
   ["test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect",
    "test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out",
    "test_nfr05_browser_compatibility::test_student_views_own_attendance",
    "test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog",
    "test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow"], NEW)
tc("SYS_NFR-05_02", "NFR-05", "Main workflows in Mozilla Firefox", "Playwright Firefox installed", "Seeded data",
   "Run browser workflow suite with NFR05_BROWSERS=firefox", "Same workflows pass.", "B",
   ["test_nfr05_browser_compatibility (firefox parameter)"], NEW, "Firefox install approved for Phase 2.")
tc("SYS_NFR-05_03", "NFR-05", "Main workflows in Microsoft Edge", "Edge installed", "Seeded data",
   "Run browser workflow suite with NFR05_BROWSERS=edge", "Same workflows pass.", "B",
   ["test_nfr05_browser_compatibility (edge parameter)"], NEW,
   "Edge not installed and installation not approved; expected BLOCKED locally (gap G-09).")
tc("SYS_NFR-05_04", "NFR-05", "Main workflows in Safari (WebKit)", "WebKit available", "Seeded data",
   "Run main workflows in WebKit", "Same workflows pass.", "B", [], NEW,
   "Not part of the existing browser suite (gap G-09).")
tc("IT_NFR-05_05", "NFR-05", "Browser-neutral server responses", "App running", "Chrome/Edge/Firefox/Safari User-Agent strings",
   "Request pages and assets with each User-Agent", "Same headers, correct JS/CSS MIME types, standards mode.", "A",
   ["test_nfr05_implementation::test_nfr05_static_assets_serve_correct_mime_types",
    "test_nfr05_implementation::test_nfr05_static_types_do_not_depend_on_host_mime_table",
    "test_nfr05_implementation::test_nfr05_x_ua_compatible_header_present_for_all_browsers",
    "test_nfr05_implementation::test_nfr05_security_headers_consistent_across_browsers"], NEW,
   "These tests only fake the User-Agent header; they do not run a real browser.")
tc("SYS_NFR-05_06", "NFR-05", "No horizontal overflow", "Browser available", "Desktop and narrow widths",
   "Open each dashboard", "No horizontal scrolling.", "B",
   ["test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow"], NEW)

# ---------------------------------------------------------------- NFR-06
tc("UT_NFR-06_01", "NFR-06", "Modules import independently", "Source available", "Each app/api module",
   "Import each module in a fresh interpreter", "Each imports without the others.", "A",
   ["test_nfr06_maintainability::test_module_is_independently_importable",
    "test_nfr06_maintainability::test_application_factory_builds_app_in_fresh_interpreter"], NEW)
tc("IT_NFR-06_02", "NFR-06", "URL map unchanged", "App built", "Frozen baseline",
   "Compare URL map", "Rules, order and endpoint names match the baseline.", "A",
   ["test_nfr06_maintainability::test_url_map_matches_baseline_exactly_and_in_order",
    "test_nfr06_maintainability::test_url_map_has_no_missing_or_unexpected_rules"], NEW)
tc("IT_NFR-06_03", "NFR-06", "Layer dependency rules", "Source available", "-",
   "Inspect imports", "Feature modules depend only on shared layers; helpers do not depend on the API layer.", "A",
   ["test_nfr06_maintainability::test_feature_modules_only_depend_on_shared_layers",
    "test_nfr06_maintainability::test_shared_helper_modules_do_not_depend_on_api_layer",
    "test_nfr06_maintainability::test_validation_helpers_have_no_framework_dependencies"], NEW)
tc("IT_NFR-06_04", "NFR-06", "Backward-compatible imports", "Source available", "app.routes",
   "Import legacy names", "Legacy imports still resolve to the same objects.", "A",
   ["test_nfr06_maintainability::test_legacy_routes_import_returns_same_object",
    "test_nfr06_maintainability::test_legacy_style_imports_used_by_existing_code_still_work"], NEW)
tc("SYS_NFR-06_05", "NFR-06", "Whole-suite regression after modularisation", "Full test suite", "-",
   "Run the full suite", "No regressions in other features.", "A", ["(entire test suite)"], NEW)


# ===================================================================
# Phase 2 additions (Deliverable 3): new browser/manual cases
# ===================================================================
tc("SYS_FR-04_11", "FR-04", "Percentages displayed on the teacher dashboard", "Teacher logged in to browser; records exist",
   "Seeded demo data", "Teacher > Percentages: compare each student's shown percentage with the records (Present / total)",
   "Displayed percentages equal Present / total x 100 rounded to 2 decimals; Late is not counted as attended.", "M",
   [], NEW, "Added in Phase 2: on-screen display is not covered by any automated test.")
tc("SYS_NFR-02_06", "NFR-02", "Perceived load time on the demo machine", "Demo data seeded (scripts/seed_demo_data.py)",
   "Teacher account", "Open each teacher section; note load time in browser DevTools (Network > Load)",
   "Every section loads within 3 seconds.", "M", [], NEW, "Added in Phase 2 for the demo environment.")
tc("SYS_NFR-05_07", "NFR-05", "Main workflows in Playwright Chromium", "Playwright Chromium installed", "Seeded data",
   "Run browser workflow suite with NFR05_BROWSERS=chromium", "Login, marking, viewing, user creation and layout checks pass.", "B",
   ["test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chromium]@chromium",
    "test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chromium]@chromium",
    "test_nfr05_browser_compatibility::test_student_views_own_attendance[chromium]@chromium",
    "test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[chromium]@chromium",
    "test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chromium]@chromium"],
   NEW, "Added in Phase 2 (opt-in browser name 'chromium').")
tc("SYS_NFR-05_08", "NFR-05", "Main workflows in the Apple Safari application", "Safari on macOS; app running locally (python run.py)",
   "Seeded demo data", "Repeat the admin, teacher and student main tasks in Safari",
   "All tasks work as in other browsers; no layout or script errors.", "M", [], NEW,
   "Added in Phase 2. Playwright cannot drive the Safari application; WebKit results (SYS_NFR-05_04) do not count as Safari.")


# ===================================================================
# Phase 2 traceability review (Deliverable 3)
# Every linked test was read. Where a link did not prove the expected
# result, the case was corrected here (the Phase 1 entry above is kept
# for history). ``exec`` decides how the status is derived:
#   "auto"  -> PASS only if every linked test passed in the recorded run
#              (FAIL if any failed; NOT RUN if a linked test did not run)
#   dict    -> fixed status/actual text, used when automated evidence is
#              partial or the case needs a person, an environment or a
#              missing feature
# ``tester`` assigns a NOT RUN case to a manual checklist.
# ===================================================================

_BY_ID = {c["id"]: c for c in CASES}
for _c in CASES:
    _c.setdefault("exec", "auto")
    _c.setdefault("tester", "")
    _c.setdefault("review", "Linked test(s) read; they verify the expected result.")


def amend(case_id, review=None, exec=None, tester=None, add_refs=(), set_refs=None, **fields):
    case = _BY_ID[case_id]
    if set_refs is not None:
        case["refs"] = list(set_refs)
    case["refs"].extend(add_refs)
    for key, value in fields.items():
        case[key] = value
    if review is not None:
        case["review"] = review
    if exec is not None:
        case["exec"] = exec
    if tester is not None:
        case["tester"] = tester


def partial(verified, missing):
    return {"status": "NOT RUN",
            "actual": f"Partially verified by automated tests: {verified} Not yet verified: {missing}"}


B = "test_nfr05_browser_compatibility::"
CHROME = "[chrome]"

# ---- FR-01
amend("UT_FR-01_01", set_refs=["test_fr01_authentication::test_successful_login",
                                "test_frontend_pages::test_page_login_flow_uses_real_authentication",
                                B + "test_login_page_validation_and_role_redirect" + CHROME])
amend("UT_FR-01_02", expected="HTTP 401 'Invalid username or password'; error shown on the login page and the user stays on /login.",
      add_refs=[B + "test_login_page_validation_and_role_redirect" + CHROME],
      review="Corrected: 'no session created' was not asserted by any test; replaced with the browser check that the user stays on /login.")
amend("UT_FR-01_03", set_refs=["test_fr01_authentication::test_missing_credentials",
                                "test_foundation::test_login_rejects_empty_credentials",
                                B + "test_login_page_validation_and_role_redirect" + CHROME])
amend("UT_FR-01_12", expected="HTTP 400; request rejected.",
      review="Corrected: the test checks the status code only, not the message text.")
amend("SYS_FR-01_08", set_refs=["test_fr15_logout::test_protected_route_after_logout",
                                 "test_nfr01_security::test_security_headers",
                                 B + "test_teacher_marks_corrects_attendance_and_logs_out" + CHROME],
      exec=partial("after logout the protected API returns 401, reopening /teacher redirects to /login (Chrome), "
                   "responses carry Cache-Control: no-store.", "pressing the browser Back button."),
      tester="Jagadeesh", review="Back-button step is not automated.")
amend("SYS_FR-01_09", set_refs=["test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_session_lifetime_is_thirty_minutes",
                                 "test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_idle_session_expires_after_thirty_minutes",
                                 "test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_session_still_valid_just_before_timeout",
                                 "test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_activity_renews_the_inactivity_window"],
      method="A", remarks="New Phase 2 tests check real server-side expiry by advancing the session signer's clock (31 idle minutes -> 401; 29 -> 200).",
      review="Previously only the configuration value was checked; new tests added (gap G-10 closed).")
amend("SYS_FR-01_10", set_refs=["test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_10_login_with_unavailable_database_fails_safely",
                                 "test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_10_valid_login_works_when_database_is_available"],
      remarks="New Phase 2 test: database file replaced by a directory so it cannot be opened.",
      review="No test existed; new test added (gap G-10 closed).")

# ---- FR-02
amend("UT_FR-02_04", expected="API returns 400; the error names attendance_date.", change=UPDATED,
      remarks="The teacher form's date input has the HTML 'required' attribute; browser behaviour is in the manual checklist for SYS_FR-10_10 / SYS_FR-02_13 walkthroughs.",
      review="Corrected: the linked test is API-only, so the UI half of the expected result was moved to remarks.")
amend("SYS_FR-02_13", set_refs=[B + "test_teacher_marks_corrects_attendance_and_logs_out" + CHROME])

# ---- FR-03
amend("UT_FR-03_02", add_refs=["test_fr03_record_management::test_fr03_idempotent_upsert_by_key"],
      review="The linked test changes Present -> Absent (not Late) as teacher1; the change to Late is covered by the upsert test.")
amend("IT_FR-03_08", add_refs=["test_fr03_record_management::test_ut_fr_03_02_update_existing_record_by_id"],
      review="Added the test where the assigned teacher updates their own record; the original link proved denial and admin update only.")
amend("SYS_FR-03_10", remarks="Failure is simulated with a duplicate-key error part-way through a batch; the whole batch is rolled back. "
                              "A fully unavailable database during save is not simulated.",
      review="Verified: rollback with no partial record. Note the type of failure simulated.")
amend("IT_FR-03_11", add_refs=["test_fr03_record_management::test_it_fr_03_08_teacher_authorization"],
      review="Added the test where another teacher's delete is refused (403).")
amend("SYS_FR-03_13", set_refs=[B + "test_teacher_marks_corrects_attendance_and_logs_out" + CHROME],
      exec=partial("correcting a status through the Records dialog (Chrome).", "deleting a record through the confirmation dialog."),
      tester="Jagadeesh")

# ---- FR-04
_P = "test_fr04_percentage_test_plan_cases::"
for _id, _param in [("UT_FR-04_01", "UT_FR-04_01"), ("UT_FR-04_02", "UT_FR-04_02"),
                    ("UT_FR-04_03", "UT_FR-04_03"), ("UT_FR-04_04", "UT_FR-04_04"),
                    ("UT_FR-04_05", "UT_FR-04_05")]:
    amend(_id, set_refs=[f"{_P}test_test_plan_percentage_datasets[{_param}"],
          review="The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data.")
amend("UT_FR-04_02", add_refs=["test_fr04_percentages::test_fr04_percentages_calculate_correctly"])
amend("UT_FR-04_04", add_refs=["test_fr04_percentages::test_fr04_late_is_not_counted_as_attended"])
amend("UT_FR-04_05", add_refs=["test_fr04_percentages::test_fr04_percentages_calculate_correctly",
                               "test_fr11_attendance_alert::test_zero_eligible_attendance"])
amend("IT_FR-04_06", set_refs=[_P + "test_it_fr_04_06_percentage_recalculates_after_update",
                                "test_fr11_attendance_alert::test_reactivity_on_attendance_updates"],
      remarks="", review="New Phase 2 test on /api/attendance/percentages itself (gap G-10 closed).")
amend("IT_FR-04_08", set_refs=[_P + "test_it_fr_04_08_percentage_for_selected_date_range",
                                "test_fr06_attendance_reporting::test_date_range_filtering_inclusive"],
      review="The original link checked which records were included but not the percentage; new test checks 75% in range vs 50% overall.")
amend("SYS_FR-04_09", expected="66.67% (2 Present / 3) returned by both the percentage API and the alerts API (rounded to 2 decimal places).",
      set_refs=[f"{_P}test_test_plan_percentage_datasets[SYS_FR-04_09",
                _P + "test_sys_fr_04_09_rounding_is_consistent_between_percentage_and_alert_apis",
                "test_fr04_percentages::test_fr04_subject_filter"],
      remarks="On-screen display of the rounded value is checked manually under SYS_FR-04_11 and SYS_FR-14_08.",
      review="New Phase 2 tests (gap G-10 closed). Expected result limited to the APIs; display moved to manual cases.")
amend("SYS_FR-04_11", exec={"status": "NOT RUN", "actual": ""}, tester="Jagadeesh")

# ---- FR-05
amend("UT_FR-05_01", set_refs=["test_fr05_attendance_viewing::test_fr05_student_only_sees_own_records",
                                B + "test_student_views_own_attendance" + CHROME])
amend("UT_FR-05_04", exec=partial("the API returns {'count': 0, 'records': []} for a filter with no matches.",
                                  "the empty-state message on the student History screen."), tester="Tharith")
amend("IT_FR-05_07", set_refs=["test_fr03_record_management::test_ut_fr_03_02_update_existing_record_by_id"],
      review="Corrected: the Phase 1 link (refresh after save) did not update a record; the new link re-reads a record after updating it.")
amend("SYS_FR-05_09", exec={"status": "NOT APPLICABLE",
                            "actual": "Pagination is not implemented in the API or the UI."},
      remarks="SRS FR-05 requires viewing records by subject and date, which is implemented and passes. It does not require pagination. "
              "With 1,500 records the full list loads well within 3 s (NFR-02 tests), so the lack of pagination does not break any SRS requirement.",
      review="Classified NOT APPLICABLE: outside the SRS; kept for traceability to the original plan.")
amend("SYS_FR-05_10", set_refs=[B + "test_dashboard_layout_has_no_horizontal_overflow" + CHROME,
                                 "test_nfr04_usability::test_nfr04_interface_supports_responsive_layout"],
      exec=partial("no horizontal overflow at 1280x800 and 375x812 (Chrome); responsive CSS rules present.",
                   "that content is comfortably readable (human judgement)."), tester="Tharith")

# ---- FR-06
amend("SYS_FR-06_08", exec={"status": "FAIL",
      "actual": "API part verified: zero records and zero totals returned. UI part: no reporting screen exists, so no empty-report message can be shown."},
      review="Known gap G-01 (reporting screen missing). Not fixed: Sprint 3 skipped.")
amend("SYS_FR-06_09", add_refs=["test_fr06_attendance_reporting::test_student_wise_report_admin"],
      review="Added the test that compares totals and the percentage (3 Present of 5 = 60%) with the seeded records.")

# ---- FR-07 .. FR-10
amend("UT_FR-07_02", expected="HTTP 400 with an error message for each invalid input.",
      review="Corrected: 'no account created' was not asserted by the linked tests.")
amend("SYS_FR-07_10", set_refs=[B + "test_admin_creates_user_through_dialog" + CHROME],
      exec=partial("creating a user through the dialog (Chrome).", "search/filter, edit and deactivate through the UI."),
      tester="Sumukh")
amend("SYS_FR-08_10", exec={"status": "NOT RUN", "actual": ""}, tester="Sumukh")
amend("UT_FR-09_05", set_refs=["test_fr09_enrollment_validation::test_ut_fr_09_05_only_active_students_can_be_enrolled",
                                "test_fr09_enrollment_validation::test_ut_fr_09_05_unknown_student_or_subject_rejected",
                                "test_fr09_enrollment_validation::test_ut_fr_09_05_non_positive_or_non_integer_ids_rejected",
                                "test_fr09_enrollment_validation::test_ut_fr_09_05_control_valid_active_student_is_enrolled"],
      remarks="New Phase 2 tests: teacher/admin id -> 404, inactive student -> 400, unknown ids -> 404, bad ids -> 400; enrollment count stays 0.",
      review="No test existed; new tests added (gap G-10 closed).")
amend("IT_FR-09_09", exec=partial("all enrolled students appear in the roster.",
                                  "that a student who is not enrolled is left out (the test data has no unenrolled student)."),
      tester="Sumukh")
amend("SYS_FR-09_10", exec={"status": "NOT RUN", "actual": ""}, tester="Sumukh")
amend("SYS_FR-10_10", exec={"status": "NOT RUN", "actual": ""}, tester="Jagadeesh")

# ---- FR-11 .. FR-15
amend("UT_FR-11_03", expected="A student at exactly 75.00% is not flagged at thresholds 75.0 and 74.99, and is flagged at 75.01 (strictly below).",
      review="Corrected to the boundary values the test actually uses.")
amend("SYS_FR-11_10", exec={"status": "NOT RUN", "actual": ""}, tester="Jagadeesh")
amend("SYS_FR-12_10", exec={"status": "FAIL",
      "actual": "No export control exists in the admin, teacher or student dashboards. Export works only by calling /api/reports/.../export directly."},
      review="Known gap G-02 (export UI missing). Not fixed: Sprint 3 skipped.")
amend("UT_FR-13_04", expected="HTTP 400; the stored password is unchanged.",
      review="Corrected: the test checks status and stored hash, not the message text.")
amend("SYS_FR-13_10", exec=partial("the Change password button and dialog fields are present on every dashboard.",
                                   "completing the dialog and logging in with the new password."), tester="Sumukh")
amend("SYS_FR-14_08", set_refs=["test_nfr02_browser_performance::test_browser_main_dashboard_overview_renders_within_threshold"],
      exec=partial("the admin overview renders in a real browser within 3 s.", "that the summary figures shown match the data, for each role."),
      tester="Tharith")
amend("SYS_FR-15_06", set_refs=[B + "test_teacher_marks_corrects_attendance_and_logs_out" + CHROME],
      exec=partial("teacher logout through the confirmation dialog returns to /login (Chrome).", "admin and student logout."),
      tester="Jagadeesh")
amend("SYS_FR-15_07", exec={"status": "NOT RUN", "actual": ""}, tester="Tharith")
amend("SYS_FR-15_08", exec={"status": "NOT RUN",
      "actual": "Not verified: the linked CSRF test posts to /api/users, not /api/logout. The Origin check is global, but no test proves it for logout."},
      review="Mapping was inaccurate. Planned for System Validation (crafted cross-origin POST to /api/logout).")

# ---- NFR-01
amend("UT_NFR-01_01", set_refs=[B + "test_login_page_validation_and_role_redirect" + CHROME],
      review="The test toggles the field to type=text and back to type=password; a toggle can only reveal from the masked state, "
             "so the default is masked. The default state itself is not asserted separately.")
amend("IT_NFR-01_07", add_refs=["test_nfr01_security::test_session_cookie_security"],
      review="Added the test that checks the HttpOnly and SameSite cookie flags.")
amend("SYS_NFR-01_04", exec={"status": "BLOCKED",
      "actual": "No HTTPS deployment is available; the development server serves plain HTTP. Only the Secure-cookie switch exists."},
      review="Environmental limitation G-08.")

# ---- NFR-02
amend("SYS_NFR-02_01", add_refs=["test_nfr02_performance::test_nfr02_representative_teacher_workflow_scenario"],
      review="Added the workflow test that times the login request itself (the page tests time the login page).")
amend("SYS_NFR-02_06", exec={"status": "NOT RUN", "actual": ""}, tester="Jagadeesh")
for _id in ("SYS_NFR-02_01", "SYS_NFR-02_02", "SYS_NFR-02_03", "SYS_NFR-02_04", "SYS_NFR-02_05"):
    _BY_ID[_id]["remarks"] = ("The tests assert a time under 3 s but do not print it; exact timings are to be recorded in the "
                              "System Validation Report (Test Plan section 3).")

# ---- NFR-03
amend("IT_NFR-03_03", exec=partial("the backup contains exactly the saved attendance rows and is unaffected by later changes.",
                                   "restoring the backup into a database and using it through the application."),
      review="No restore step exists in code or tests (G-07). Planned for System Validation using a temporary copy.")
amend("SYS_NFR-03_05", exec=partial("a failed batch rolls back completely and a missing database fails safely.",
                                    "retrying the same save after the failure."),
      review="'Retry after failure' is not exercised. Planned for System Validation.")

# ---- NFR-04
amend("IT_NFR-04_03", add_refs=[B + "test_teacher_marks_corrects_attendance_and_logs_out" + CHROME],
      review="The usability test is a static check; added the browser test that shows the selected section and hides Overview.")
amend("IT_NFR-04_04", exec=partial("focus-visible styles and ARIA attributes are present in the CSS/HTML.",
                                   "keyboard-only navigation by a person."), tester="Tharith")
amend("IT_NFR-04_05", add_refs=[B + "test_dashboard_layout_has_no_horizontal_overflow" + CHROME],
      remarks="Reduced motion is verified at stylesheet level only (the @media rule exists).",
      review="Added the browser test that proves the layout adapts at 375 px.")
amend("SYS_NFR-04_06", exec={"status": "NOT RUN", "actual": ""}, tester="Tharith")

# ---- NFR-05
amend("SYS_NFR-05_01", scenario="Main workflows in Google Chrome (installed application)",
      set_refs=[B + n + CHROME for n in ("test_login_page_validation_and_role_redirect",
                                         "test_teacher_marks_corrects_attendance_and_logs_out",
                                         "test_student_views_own_attendance",
                                         "test_admin_creates_user_through_dialog",
                                         "test_dashboard_layout_has_no_horizontal_overflow")])
amend("SYS_NFR-05_02", set_refs=[B + n + "[firefox]" for n in ("test_login_page_validation_and_role_redirect",
                                                              "test_teacher_marks_corrects_attendance_and_logs_out",
                                                              "test_student_views_own_attendance",
                                                              "test_admin_creates_user_through_dialog",
                                                              "test_dashboard_layout_has_no_horizontal_overflow")])
amend("SYS_NFR-05_03", set_refs=[], exec={"status": "BLOCKED",
      "actual": "Microsoft Edge is not installed and installing it was not approved. The suite reports: "
                "\"Chromium distribution 'msedge' is not found at /Applications/Microsoft Edge.app\"."},
      review="Environmental limitation G-09.")
amend("SYS_NFR-05_04", scenario="Main workflows in the WebKit engine (Playwright build; not the Safari application)",
      steps="Run browser workflow suite with NFR05_BROWSERS=webkit",
      set_refs=[B + n + "[webkit]@webkit" for n in ("test_login_page_validation_and_role_redirect",
                                                   "test_teacher_marks_corrects_attendance_and_logs_out",
                                                   "test_student_views_own_attendance",
                                                   "test_admin_creates_user_through_dialog",
                                                   "test_dashboard_layout_has_no_horizontal_overflow")],
      remarks="Uses the opt-in 'webkit' browser name added in Phase 2. WebKit is Safari's engine; this is not a Safari test.")
amend("SYS_NFR-05_06", set_refs=[B + "test_dashboard_layout_has_no_horizontal_overflow" + CHROME,
                                  B + "test_dashboard_layout_has_no_horizontal_overflow[chromium]@chromium"])
amend("SYS_NFR-05_08", exec={"status": "NOT RUN", "actual": ""}, tester="Tharith")
amend("SYS_NFR-05_02", exec={"status": "BLOCKED",
      "actual": "Playwright Firefox 157.0 was installed but cannot start on this Mac (macOS 27.0): \"Could not find profile folder\", "
                "even when started directly without Playwright and outside the Claude Code sandbox. No Firefox result is claimed."},
      evidence_override="docs/evidence/final/browsers/firefox_blocked_diagnosis.txt; firefox_output.txt",
      review="Environmental limitation G-09.")
amend("SYS_NFR-05_04", exec={"status": "FAIL",
      "actual": "Every workflow step passed in WebKit 27.2 (7 test calls passed), but each test's teardown check failed: WebKit logged "
                "\"Refused to apply a stylesheet ... Content Security Policy\" once per <select> element on every dashboard "
                "(admin 15 errors / 14 selects, teacher 7/6, student 3/2). Screenshots show no visible difference from Chromium."},
      evidence_override="docs/evidence/final/browsers/webkit_output.txt; webkit_junit.xml; webkit_csp_investigation_output.txt; screenshots/",
      review="Defect D-01 (low severity). Not fixed: the fix needs a production CSP change, which needs approval.")

# ---- NFR-06
amend("SYS_NFR-06_05", set_refs=["(entire test suite)"],
      exec={"status": "PASS", "actual": "SUITE"},
      review="Status taken from the final full run: PASS only if no non-environmental test failed.")


# ---- Step-by-step instructions for the manual checklists (Phase 2)
MANUAL_STEPS = {
    # Sumukh
    "SYS_FR-07_10": ["Log in as demo.admin.", "Open Users.", "Click New user; submit with an empty username and note the error.",
                     "Create a student 'manual_s1' with a password of at least 8 characters.",
                     "Type 'manual' in the search box; check only matching users are listed.",
                     "Use the role and status filters; check the table follows them.",
                     "Edit 'manual_s1' (change the username to 'manual_s1b'); check the table updates.",
                     "Deactivate 'manual_s1b'; log out; try to log in as 'manual_s1b' (must fail).",
                     "Log in as demo.admin again and reactivate the account."],
    "SYS_FR-08_10": ["Log in as demo.admin.", "Open Classes; create class 'Manual Class'.",
                     "Edit it and assign teacher prof.mehta.", "Open Subjects; create subject 'Manual Subject' and assign prof.mehta.",
                     "Link 'Manual Subject' to 'Manual Class'.", "Try to create 'Manual Class' again (duplicate) and note the error.",
                     "Use the search boxes on both lists.", "Log in as prof.mehta and check 'Manual Subject' appears in Overview."],
    "IT_FR-09_09": ["Log in as demo.admin; open Enrollments.", "Note which students are enrolled in 'Manual Class' / 'Manual Subject' (from SYS_FR-08_10).",
                    "Enroll exactly one student in it.", "Log in as prof.mehta; open Mark attendance.",
                    "Select 'Manual Class', 'Manual Subject' and today's date; click Load roster.",
                    "Check only the enrolled student is listed and nobody else."],
    "SYS_FR-09_10": ["Log in as demo.admin; open Enrollments.", "Pick a student, class and subject; click Enroll.",
                     "Check the enrollment appears in the list.", "Enroll the same combination again; note the error.",
                     "Use the search box and the class filter.", "Remove the enrollment; check it disappears."],
    "SYS_FR-13_10": ["Log in as a demo student.", "Click Change password.", "Enter a wrong current password; submit; note the error.",
                     "Enter the correct current password and a new password of 7 characters; note the error.",
                     "Enter the correct current password and a new 8+ character password; submit; note the message.",
                     "Log out; log in with the old password (must fail), then with the new one (must work).",
                     "Change the password back so other testers are not affected."],
    # Jagadeesh
    "SYS_FR-03_13": ["Log in as prof.mehta; open Attendance records.", "Pick a record; click Correct status; change it to Late; save.",
                     "Check the table shows Late.", "Click delete on the same record; check a confirmation dialog appears; click Cancel.",
                     "Check the record is still there.", "Delete again and confirm; check the record disappears and a message is shown."],
    "SYS_FR-10_10": ["Log in as prof.mehta; open Attendance records.", "Type a student name in the search box.",
                     "Choose a subject, then a date, then a status; check the table updates each time.",
                     "Click Clear filters; check every filter is reset and all rows return.",
                     "Choose a class in the Class filter, then a From and a To date; check the table updates each time.",
                     "Click Clear filters again; check all rows return.",
                     "Repeat the subject/date/status filters and Clear filters as demo.admin in Attendance."],
    "SYS_FR-11_10": ["Log in as prof.mehta; open Overview.", "Look at 'Students needing attention'.",
                     "Compare the listed students with Percentages: every student below 75% must be listed, none at or above 75%.",
                     "If nobody is below 75%, mark a student Absent on several dates in Mark attendance, then reload Overview.",
                     "Repeat as demo.admin on Overview.", "Record that there is no screen to change the 75% threshold (known gap G-04)."],
    "SYS_FR-04_11": ["Log in as prof.mehta; open Percentages.", "Pick one student and one subject.",
                     "In Attendance records filter by that student and subject; count Present, Absent and Late.",
                     "Calculate Present / (Present + Absent + Late) x 100, rounded to 2 decimals.",
                     "Check the Percentages screen shows the same value (Late does not count as attended).",
                     "Repeat for a second student."],
    "SYS_NFR-02_06": ["Open the browser DevTools (F12) and the Network tab; tick 'Disable cache'.",
                     "Log in as prof.mehta.", "Reload Overview; note the 'Load' time at the bottom of the Network tab.",
                     "Open Mark attendance, Attendance records and Percentages; note the time until data appears.",
                     "Record each time; all must be under 3 seconds."],
    "SYS_FR-01_08": ["Log in as prof.mehta (teacher).", "Open Attendance records.", "Click Log out and confirm.",
                     "Press the browser Back button twice.", "Check whether any attendance data is shown, then reload the page.",
                     "Type http://127.0.0.1:5001/teacher in the address bar and press Enter."],
    "SYS_FR-15_06": ["Log in as demo.admin; click Log out; confirm.", "Check you are on the login page.",
                     "Repeat as a demo student.", "Repeat as prof.mehta."],
    # Tharith
    "UT_FR-05_04": ["Log in as a demo student; open Attendance history.", "Choose a date on which you have no attendance (e.g. a Sunday far in the past).",
                    "Check that a clear message says there are no records (not an empty table without explanation).",
                    "Click Clear filters (if shown) and check records return."],
    "SYS_FR-05_10": ["Log in as a demo student.", "Open DevTools device toolbar (Ctrl/Cmd+Shift+M).",
                     "View My attendance and Attendance history at 375 px, 768 px and 1280 px wide.",
                     "At each width check that text is readable, nothing overlaps, and no sideways scrolling is needed.",
                     "Repeat for the teacher Attendance records screen."],
    "SYS_FR-14_08": ["Log in as a demo student; note the numbers on My attendance (overall %, present, absent, total).",
                     "Open Attendance history and count the records yourself; check the numbers match.",
                     "Log in as prof.mehta; check the Overview cards (subjects, classes, students, average) against the Percentages screen.",
                     "Log in as demo.admin; check the Overview counts against the Users, Classes and Subjects lists."],
    "IT_NFR-04_04": ["Log in as demo.admin using only the keyboard (Tab, Shift+Tab, Enter, Space).",
                     "Tab through the sidebar; check a visible focus outline on every item.",
                     "Open each section with Enter; open and close a dialog with the keyboard (Esc closes it).",
                     "Repeat on the teacher Mark attendance screen and select statuses with the keyboard."],
    "SYS_NFR-04_06": ["Ask a person who has not used the app (or a team member) to do these tasks without help:",
                      "As student: find your overall attendance and your attendance for one subject.",
                      "As teacher: mark attendance for one class today, then correct one status.",
                      "As admin: create a student and enroll them in a class and subject.",
                      "Record time taken, any hesitation or confusion, and their comments."],
    "SYS_NFR-05_08": ["Open the Safari application on a Mac.", "Go to http://127.0.0.1:5001/login.",
                      "Log in as demo.admin; create a user; log out.", "Log in as prof.mehta; mark attendance; correct one status; log out.",
                      "Log in as a demo student; view My attendance and Attendance history.",
                      "Open Safari's Web Inspector (Develop > Show Web Inspector; enable Develop menu in Safari Settings > Advanced) and note any console errors, "
                      "especially 'Refused to apply a stylesheet' (defect D-01)."],
    "SYS_FR-15_07": ["Log in as a demo student; open Attendance history.", "Log out and confirm.",
                     "Press Back.", "Check that attendance data is not shown and you are sent to the login page when you interact or reload."],
}
for _id in MANUAL_STEPS:
    assert _BY_ID[_id]["tester"], _id


# ---- Execution of the 19 manual validation cases (Phase 4)
# The checklist steps were executed by Playwright browser automation
# (scripts/run_manual_validation_automation.py), which the instructor approved
# as evidence for the manual validation deliverable. No person performed the
# steps; the assigned member is the responsible test owner. Statuses are read
# from the recorded results file, never typed in here.
import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_ROOT = _Path(__file__).resolve().parents[1]
ORIGINAL_MANUAL_RUN_DIR = "docs/evidence/manual_validation_automation"              # 2026-11-17, before the fixes
REGRESSION_MANUAL_RUN_DIR = "docs/evidence/regression/manual_validation_automation"  # 2026-11-17, after the fixes
# The current results come from the regression run once it exists; the original run is kept as history.
MANUAL_RUN_DIR = (REGRESSION_MANUAL_RUN_DIR if (_ROOT / REGRESSION_MANUAL_RUN_DIR / "results.json").exists()
                  else ORIGINAL_MANUAL_RUN_DIR)
MANUAL_RESULTS_PATH = _ROOT / MANUAL_RUN_DIR / "results.json"
IS_REGRESSION_RUN = MANUAL_RUN_DIR == REGRESSION_MANUAL_RUN_DIR
MANUAL_REPORT = "docs/Manual_Validation_Automation_Report.md"
MANUAL_EXEC_METHOD = ("Playwright automated browser execution of the checklist steps "
                      "(scripts/run_manual_validation_automation.py); instructor-approved as manual validation evidence. "
                      "No person performed these steps.")

# Actual results, written from the observations recorded in results.json.
MANUAL_ACTUAL = {
    "SYS_FR-07_10": "All actions worked. Empty username blocked by the browser's native 'Please fill out this field.' message (dialog stayed open); manual_s1 created; search and role/status filters filtered correctly; rename to manual_s1b updated the table; the deactivated account could not log in ('Invalid username or password'); reactivation worked.",
    "SYS_FR-08_10": "Manual Class created, prof.mehta assigned, Manual Subject created and linked; duplicate class rejected with 'Class name already exists' (no duplicate row); class and subject searches filtered correctly; Manual Subject appeared on prof.mehta's Overview.",
    "IT_FR-09_09": "Manual Class had 0 enrollments; aarav enrolled; prof.mehta's roster for Manual Class / Manual Subject listed exactly aarav and nobody else.",
    "SYS_FR-09_10": "diya enrolled (17 -> 18 enrollments); duplicate rejected with 'Student is already enrolled'; search and class filter correct; removal through the confirmation dialog removed the row.",
    "SYS_FR-13_10": "Wrong current password -> 'Current password is incorrect'; 7-character password blocked by native minlength validation; valid change -> 'Your password has been changed.'; old password refused, new password accepted; password restored afterwards.",
    "SYS_FR-01_08": "After logout, Back (twice) showed the login page with no attendance rows; reload and typing /teacher both redirected to /login; /api/attendance returned 401; /teacher and the API both sent Cache-Control: no-store.",
    "SYS_FR-03_13": "aarav / Programming Fundamentals / 16 Nov 2026 corrected Present -> Late; delete showed a confirmation dialog; Cancel kept the record; confirming deleted it (96 -> 95 rows) with 'Attendance record deleted.'",
    "SYS_FR-10_10": "Teacher search, subject, date and status filters all updated the table correctly, but the teacher Attendance records screen has no 'Clear filters' control, so 'Clear filters restores all rows' could not be performed there (defect MV-01). No class or date-range filter (gap G-03). On the admin Attendance screen all filters and 'Clear filters' worked (191 rows restored).",
    "SYS_FR-11_10": "Teacher Overview listed kabir and vikram (58.3% each), exactly the students below 75% on Percentages; admin Overview listed vikram (50%) and kabir (70.8%), exactly those below 75%. No threshold control (gap G-04). The 'Everyone is on track' state was not exercised: the seeded data always has students below 75%.",
    "SYS_FR-04_11": "Hand counts for rohan (10 Present / 2 Absent / 0 Late -> 83.33) and vikram (7 / 5 / 0 -> 58.33) equal the backend percentages, but the Percentages screen shows 83.3% and 58.3%: one decimal place instead of the two decimals in the expected result (defect MV-02).",
    "SYS_NFR-02_06": "Browser cache disabled. Overview Load event 28 ms, Overview data shown 202 ms, Mark attendance 74 ms, Attendance records 235 ms, Percentages 193 ms; all under 3 seconds (measured on the development Mac).",
    "UT_FR-05_04": "Date 2020-01-05 showed 'No matching records - Try different filters.' and '0 of 23 record(s) shown.'; the API returned {'count': 0, 'records': []}. No Clear filters button on the student History screen (the step says 'if shown'); clearing the date restored all 23 records.",
    "SYS_FR-05_10": "No page-level horizontal scrolling at 375, 768 or 1280 px on the checked screens; student tables fit at all widths. At 375 px the teacher Attendance records table overflows its container by 181 px: Status badges are cut off and the Actions column needs sideways scrolling inside the table (defect MV-03).",
    "SYS_FR-14_08": "Student cards (95.7%; 22 Present, 0 Absent, 1 Late, 23 total) match the History records; teacher cards (3 subjects, 3 classes, 8 students, 83.2% = 79/95) match the Percentages and Mark attendance screens; admin cards (9 students, 2 teachers, 3 classes, 5 subjects) match the Users, Classes and Subjects lists.",
    "SYS_FR-15_06": "Admin, student (aarav) and teacher each logged out through the confirmation dialog and landed on /login; afterwards /admin, /student and /teacher each redirected to /login.",
    "SYS_FR-15_07": "After logout, Back landed on /login#history with no attendance rows; reload stayed on /login.",
    "IT_NFR-04_04": "Keyboard-only login worked; all 8 sidebar items showed a :focus-visible style and had accessible names; Enter opened Users; the New user dialog opened with Enter and closed with Esc; class and subject chosen by typing; Tab reached Load students; ArrowRight moved a roster status from Present to Absent with a focus style.",
    "SYS_NFR-04_06": "Not executed: the case needs a person who has not used the app, and automation cannot observe usability. A scripted smoke only showed the three role tasks can be completed (student viewed 95.7% and Discrete Mathematics 11/12; teacher saved today's attendance and corrected a status; admin created usability_s1 and enrolled them).",
    "SYS_NFR-05_08": "Blocked: Playwright cannot drive the Safari application, and enabling safaridriver remote automation (a system setting change) was not approved. Supplementary Playwright WebKit 27.2 run (not Safari): admin, teacher and student tasks completed; 26 'Refused to apply a stylesheet' CSP console errors (consistent with D-01); no page errors.",
}

# What the automated run could not assess (no human judgement was made).
MANUAL_LIMITS = {
    "SYS_FR-07_10": "The native empty-username bubble is not visible in headless screenshots; its validity state was checked instead.",
    "SYS_NFR-02_06": "Timings taken on the development Mac with the cache disabled through the DevTools protocol, not on a separate demo machine.",
    "UT_FR-05_04": "Whether the message is 'clear' to a student is a wording judgement that automation cannot make.",
    "SYS_FR-05_10": "Readability and visual overlap were not judged by a person; only overflow was measured.",
    "IT_NFR-04_04": "Focus styles were detected programmatically; how visible they are to a person, and screen-reader use, were not assessed.",
    "SYS_NFR-04_06": "Requires a human participant; not automatable.",
    "SYS_NFR-05_08": "Requires the real Safari application; WebKit is engine-level evidence only.",
}


def load_manual_results(run_dir=None):
    path = _ROOT / run_dir / "results.json" if run_dir else MANUAL_RESULTS_PATH
    data = _json.loads(path.read_text())
    return data["meta"], {r["id"]: r for r in data["results"]}


def run_actual(result):
    """Actual observed result of a manual validation case, taken from the recorded run."""
    checks = [x for x in result["steps"] if x["ok"] is not None]
    failed = [x for x in checks if x["ok"] is False]
    short = lambda x: (x["step"] + (f" ({x['observed'][:110]})" if x["observed"] else "")).replace("\n", " ")  # noqa: E731
    if result["status"] in ("BLOCKED", "NOT RUN"):
        text = " ".join(short(x) + "." for x in result["steps"]) + (" " + " ".join(result["notes"]) if result["notes"] else "")
        return f"{result['status']}: {text}".strip()
    parts = []
    if failed:
        parts.append(f"{len(failed)} of {len(checks)} checks not met: " + "; ".join(short(x) for x in failed) + ".")
    else:
        parts.append(f"All {len(checks)} checks met.")
    parts.append("Observed: " + "; ".join(short(x) for x in checks if x["ok"] and x["observed"])[:900] + ".")
    return " ".join(parts)


def _apply_manual_results():
    meta, results = load_manual_results()
    assert set(results) == set(MANUAL_STEPS) == set(MANUAL_ACTUAL), "manual results do not cover the 19 cases"
    for cid, r in results.items():
        case = _BY_ID[cid]
        assert case["tester"] == r["tester"], (cid, case["tester"], r["tester"])
        actual = run_actual(r) if IS_REGRESSION_RUN else MANUAL_ACTUAL[cid]
        case["exec"] = {"status": r["status"], "actual": actual, "date": r["started"][:10]}
        case["evidence_override"] = (f"{MANUAL_RUN_DIR}/screenshots/{cid}_*.png ({len(r['screenshots'])}); "
                                     f"{MANUAL_RUN_DIR}/logs/{cid}_*.log ({len(r['logs'])}); {MANUAL_REPORT}")
        case["manual_run"] = r
    return meta


# Missing only while the harness is producing a fresh results file; the
# document builders refuse to run without it.
MANUAL_META = _apply_manual_results() if MANUAL_RESULTS_PATH.exists() else None


# ------------------------------------------------------------------ registers

# Phase 2: each gap checked against the SRS text and classified.
# Columns: id, requirement, description, does the SRS require it?, classification,
#          impact on testing, affected test cases (status).
# Sprint 3 was skipped by decision; these gaps remain open and are documented only.
GAPS = [
    ("G-01", "FR-06", "No reporting screen in any dashboard; reports are generated only through /api/reports/*.",
     "Partly. FR-06 requires the system to generate reports by student, class, subject or date range; it does not name a screen. The API does this.",
     "Required behaviour implemented in the backend; user-facing screen missing",
     "API cases executed and passed; the UI part of one case cannot pass.",
     "SYS_FR-06_08 (FAIL); other FR-06 cases PASS via API"),
    ("G-02", "FR-12", "No export button or download control in any dashboard; export only by calling /api/reports/.../export.",
     "Yes in practice. FR-12 requires authorized users to export reports; without a control, users can only type an API URL.",
     "Required feature, only partly usable (backend only)",
     "API export cases pass; the UI export case fails.",
     "SYS_FR-12_10 (FAIL); UT/IT/SYS_FR-12_01..09 PASS via API"),
    ("G-03", "FR-10", "Dashboard filters have no class filter and no date-range filter (the API supports both).",
     "Class filter: yes (FR-10 names student, subject, class or date). Date range: not explicitly.",
     "Required control partly missing in the UI",
     "API filter cases pass; the UI case shows the missing class and date-range filters (and the missing teacher Clear filters control, MV-01).",
     "SYS_FR-10_10 (FAIL, MV-01)"),
    ("G-04", "FR-11", "No screen to view or change the alert threshold; changed only through the admin API (default 75%).",
     "No. FR-11 requires identifying students below a specified threshold, which works via configuration/API; alerts are shown on dashboards.",
     "Optional UI convenience",
     "None failing.",
     "SYS_FR-11_10 (PASS, dashboard display check)"),
    ("G-05", "FR-05", "No pagination and no user-selectable sort.",
     "No. FR-05 requires viewing by subject and date only.",
     "Outside the SRS (original Test Plan expectation)",
     "Pagination case excluded; sort case re-based on the fixed order.",
     "SYS_FR-05_09 (NOT APPLICABLE); SYS_FR-05_08 (PASS, fixed order)"),
    ("G-06", "FR-04", "/api/attendance/percentages has no date-range filter; the student dashboard calculates its percentage in the browser.",
     "No. FR-04 does not require date ranges.",
     "Design note",
     "Date-range percentage tested through the FR-06 report summary.",
     "IT_FR-04_08 (PASS via report)"),
    ("G-07", "NFR-03", "Backups exist and are scheduled, but there is no restore script or documented restore procedure.",
     "Not explicitly. NFR-03 requires preserving records and regular backups; the Test Plan adds a restore test.",
     "Test Plan expectation without tooling",
     "Restore must be checked manually in System Validation.",
     "IT_NFR-03_03 (NOT RUN)"),
    ("G-08", "NFR-01", "No HTTPS deployment; the development server is plain HTTP. Only a Secure-cookie switch exists.",
     "Yes. NFR-01 requires protecting sensitive data during transmission.",
     "Environmental limitation (deployment)",
     "Cannot be executed locally.",
     "SYS_NFR-01_04 (BLOCKED)"),
    ("G-09", "NFR-05", "Edge not installed (not approved); Playwright Firefox cannot start on this Mac; the Safari application cannot be automated; test_nfr05_implementation only fakes User-Agent headers.",
     "Yes. NFR-05 requires commonly used modern browsers.",
     "Environmental limitation",
     "Chrome and Chromium executed; WebKit executed (defect D-01); Edge and Firefox blocked; Safari application blocked (cannot be automated).",
     "SYS_NFR-05_02 (BLOCKED), SYS_NFR-05_03 (BLOCKED), SYS_NFR-05_04 (FAIL), SYS_NFR-05_08 (BLOCKED)"),
    ("G-10", "Several", "Missing automated tests for session expiry, login with database unavailable, Test Plan percentage datasets, recalculation after update, and enrolling a non-student.",
     "Yes (Test Plan cases).",
     "Test gap - CLOSED in Phase 2",
     "Three new test files added (26 test results in the first run; see final evidence).",
     "SYS_FR-01_09, SYS_FR-01_10, UT_FR-04_01..05, IT_FR-04_06, IT_FR-04_08, SYS_FR-04_09, UT_FR-09_05 (PASS)"),
]

# Defects and observations found during Phases 2-3 (none fixed: production code
# changes need approval).
DEFECTS = [
    ("D-01", "NFR-05", "Low", "WebKit (Playwright 27.2) logs a Content-Security-Policy error for every <select> element on all dashboards "
     "(\"Refused to apply a stylesheet ... style-src\"). The app sends default-src 'self' with no style-src; WebKit appears to treat its own "
     "form-control styling as a blocked stylesheet. Functions and appearance are unaffected; Chrome and Chromium log nothing.",
     "SYS_NFR-05_04 FAIL", "Open - fix needs a production CSP change (approval required). Re-observed in Playwright WebKit during the "
     "manual validation run (26 errors); the Safari application itself is untested (SYS_NFR-05_08 BLOCKED)."),
    ("MV-01", "FR-10", "Low", "The teacher Attendance records screen has no 'Clear filters' control (toolbar: search, Subject, Date, Status). "
     "The expected result of SYS_FR-10_10 requires 'Clear filters' to restore all rows; the teacher must reset each filter by hand. "
     "The admin Attendance screen has the control and it works.",
     "SYS_FR-10_10 FAIL", "Open - found by the manual validation run (2026-11-17); fix is a production change (approval required)."),
    ("MV-02", "FR-04", "Low", "Attendance percentages are displayed to one decimal place (83.3%, 58.3%) although the backend returns, and "
     "SYS_FR-04_11 expects, two decimals (83.33, 58.33). The calculation is correct. The shared formatter App.formatPercent "
     "(app/static/js/common.js) uses toFixed(1), so other dashboards are likely affected too.",
     "SYS_FR-04_11 FAIL", "Open - found by the manual validation run (2026-11-17); fix is a production change (approval required)."),
    ("MV-03", "FR-05", "Low", "At 375 px wide the teacher Attendance records table overflows its container by 181 px: Status badges are cut "
     "off and the Actions (correct/delete) column is reachable only by scrolling the table sideways. The page itself does not "
     "scroll horizontally, so the existing automated layout test passes.",
     "SYS_FR-05_10 FAIL", "Open - found by the manual validation run (2026-11-17); fix is a production change (approval required)."),
    ("D-02", "FR-06", "Medium", "No reporting screen (gap G-01).", "SYS_FR-06_08 FAIL", "Open - known gap; Sprint 3 skipped."),
    ("D-03", "FR-12", "Medium", "No export control in the user interface (gap G-02).", "SYS_FR-12_10 FAIL", "Open - known gap; Sprint 3 skipped."),
    ("D-04", "NFR-06", "Low", "app/api/exports.py:104 calls datetime.utcnow(), deprecated in Python 3.12+ (12 DeprecationWarnings per run). "
     "Works today; will break when Python removes it.", "Warnings only", "Open - production change needs approval."),
    ("O-01", "FR-09", "Low", "POST /api/enrollments accepts a subject that is not linked to the chosen class (no class_subjects check). "
     "Verified in Phase 3 on a temporary database (docs/evidence/phase3/o01_enrollment_probe_output.txt): enrolling a student in CSE-B / DBMS, "
     "where DBMS is linked only to CSE-A, returns 201, and the teacher roster for CSE-B / DBMS then lists the student although "
     "GET /api/classes/<CSE-B>/subjects is empty. The admin dashboard only offers the class's own subjects, so normal UI use cannot create "
     "this. Against the SRS: FR-09 says students are assigned to 'their respective classes and subjects', which implies the subject "
     "belongs to the class; the API does not enforce this. Assessment: genuine but minor validation gap (API only), not a missing feature.",
     "None (no test case expects this check)", "Open - documented only; a fix is a production change and needs approval."),
    ("O-02", "NFR-06", "Observation", "Two views are registered for GET /api/attendance; attendance_management.get_attendance never runs (documented in "
     "app/api/__init__.py and pinned by test_nfr06_maintainability). Phase 3 coverage confirms it: 84 statements and 44 branches of that function "
     "are never executed.", "None", "Documented; no change."),
    ("O-03", "-", "Observation", "GET / still returns a placeholder 'starter' JSON message.", "None", "Documented in README; no change."),
    ("O-04", "NFR-03", "Observation", "scripts/backup_db.py (lines 50-51) and many test helpers use 'with sqlite3.connect(...)', which commits "
     "but does not close the connection. Under coverage measurement pytest reports these as ResourceWarning: unclosed database "
     "(555 in each measured coverage run); without coverage they are not reported. Full-suite allocation trace: 547 opened in "
     "test files, 8 in scripts/backup_db.py, 0 in app/ (docs/evidence/coverage/resourcewarning_allocation_summary.txt).", "Warnings only (coverage runs)",
     "Documented; no change (backup script change needs approval; test helpers unchanged)."),
]

PLACEHOLDERS = [
    ("test_fr01_authentication", "FR-01", "tests/test_fr01_authentication.py; test_foundation.py (login tests); test_nfr01_security.py::test_session_expiration_configured"),
    ("test_admin_management", "FR-07, FR-08, FR-09", "tests/test_fr07_user_management.py; tests/test_fr08_class_subject_management.py; tests/test_fr09_student_enrollment.py"),
    ("test_fr04_percentages", "FR-04", "tests/test_fr04_percentages.py; tests/test_fr11_attendance_alert.py (zero-record cases)"),
    ("test_fr05_viewing", "FR-05", "tests/test_fr05_attendance_viewing.py; tests/test_fr05_attendance_viewing_extra.py"),
    ("test_fr15_logout", "FR-15", "tests/test_fr15_logout.py"),
    ("test_nfr01_security", "NFR-01", "tests/test_nfr01_security.py; tests/test_frontend_pages.py (CSRF/headers). HTTPS deployment still unverified (G-08)."),
    ("test_nfr03_reliability", "NFR-03", "tests/test_nfr03_reliability.py; tests/test_nfr03_scheduling.py. Restore still untested (G-07)."),
]


# =============================================================================
# Regression run after fixing the six failed cases (2026-11-17)
# =============================================================================
# Statuses before the fixes are frozen in docs/evidence/regression/original_statuses.json.
# The three automated cases below are evaluated again from the regression JUnit
# evidence (exec "auto"); the three manual cases come from the regression
# validation run (see MANUAL_RUN_DIR).
REGRESSION_DIR = "docs/evidence/regression"
ORIGINAL_STATUSES_PATH = _ROOT / REGRESSION_DIR / "original_statuses.json"
FIX = "Fixed and verified in the regression run (2026-11-17): "

amend("SYS_FR-06_08", exec="auto",
      add_refs=["test_six_failures_browser::test_empty_report_shows_message[chrome]",
                "test_six_failures_browser::test_admin_generates_report_matching_the_api[chrome]"],
      review="Reporting screen added to the admin and teacher dashboards (app/static/js/reports.js); the empty report shows "
             "'No attendance records match this report'. Was FAIL (gap G-01, defect D-02).")
amend("SYS_FR-12_10", exec="auto",
      set_refs=["test_six_failures_browser::test_export_downloads_match_the_report[chrome]",
                "test_six_failures_browser::test_export_of_empty_report_is_refused_with_message[chrome]",
                "test_six_failures_browser::test_teacher_reports_are_limited_to_own_subjects[chrome]",
                "test_fr12_implementation::test_teacher_cannot_export_unassigned_subject_report"],
      review="CSV, PDF and JSON export buttons added to the Reports screen; downloads use the existing export API with the "
             "report's filters. Was FAIL (gap G-02, defect D-03).")
amend("SYS_NFR-05_04", exec="auto", evidence_override=None,
      review="Was FAIL (defect D-01): WebKit 27.2 build r2370 logged a false-positive style-src-attr CSP violation for every "
             "<select>, also on a blank page (upstream WebKit regression, Playwright issue #43617, fixed in WebKit 324283@main). "
             "Re-run with Playwright 1.65.2 / WebKit build r2388; the application's CSP is unchanged.")
_BY_ID["SYS_NFR-05_04"].pop("evidence_override", None)
amend("SYS_FR-10_10", review="Teacher and admin records now have Class and From/To date filters and Clear filters "
                             "(was FAIL: MV-01, gap G-03).")
amend("SYS_FR-04_11", review="App.formatPercent now shows two decimals (was FAIL: MV-02).")
amend("SYS_FR-05_10", review="Tables use a labelled card layout below 640 px (was FAIL: MV-03).")
for _cid in ("SYS_FR-06_08", "SYS_FR-12_10"):
    _BY_ID[_cid]["method"] = "A+B"

_DEFECT_FIX = {
    "D-01": ("SYS_NFR-05_04 FAIL (original run); PASS in the regression run",
             FIX + "upstream WebKit regression (false-positive style-src-attr violation for <select>), fixed in WebKit "
             "324283@main; re-run with Playwright 1.65.2 / WebKit r2388 shows 0 violations. No application change; CSP unchanged."),
    "D-02": ("SYS_FR-06_08 FAIL (original run); PASS in the regression run",
             FIX + "Reports screen in the admin and teacher dashboards (app/static/js/reports.js, templates)."),
    "D-03": ("SYS_FR-12_10 FAIL (original run); PASS in the regression run",
             FIX + "CSV / PDF / JSON export controls on the Reports screen using the existing export API."),
    "MV-01": ("SYS_FR-10_10 FAIL (original run); PASS in the regression run",
              FIX + "Clear filters, Class and From/To filters on the teacher records screen (app/templates/teacher.html, teacher.js)."),
    "MV-02": ("SYS_FR-04_11 FAIL (original run); PASS in the regression run",
              FIX + "App.formatPercent shows two decimals (app/static/js/common.js); overview averages rounded to two decimals."),
    "MV-03": ("SYS_FR-05_10 FAIL (original run); PASS in the regression run",
              FIX + "labelled card layout for tables below 640 px (app/static/css/app.css, App.fillRows data-label)."),
}
DEFECTS[:] = [(d[0], d[1], d[2], d[3], *_DEFECT_FIX[d[0]]) if d[0] in _DEFECT_FIX else d for d in DEFECTS]

_GAP_FIX = {
    "G-01": ("Closed in the regression run: reporting screen added", "Reports can be generated in the dashboard.",
             "SYS_FR-06_08 (PASS); FR-06 API cases PASS"),
    "G-02": ("Closed in the regression run: export controls added", "Reports can be exported from the dashboard.",
             "SYS_FR-12_10 (PASS); UT/IT/SYS_FR-12_01..09 PASS via API"),
    "G-03": ("Closed in the regression run: class and date-range filters added", "All FR-10 filters are available in the dashboards.",
             "SYS_FR-10_10 (PASS)"),
}
_GAP_FIX["G-09"] = ("Environmental limitation",
                    "Chrome, Chromium and WebKit pass (WebKit r2388, defect D-01 closed); Edge not installed; Playwright Firefox "
                    "build 1572 still cannot start on this Mac; the Safari application cannot be automated.",
                    "SYS_NFR-05_02 (BLOCKED), SYS_NFR-05_03 (BLOCKED), SYS_NFR-05_04 (PASS), SYS_NFR-05_08 (BLOCKED)")
GAPS[:] = [(g[0], g[1], g[2], g[3], *_GAP_FIX[g[0]]) if g[0] in _GAP_FIX else g for g in GAPS]
