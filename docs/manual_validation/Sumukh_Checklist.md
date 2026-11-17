# Manual Validation Checklist - Sumukh

| Item | Details |
|---|---|
| Assigned team member | Sumukh |
| Scope | Admin dashboard, user management, class and subject management, enrollment, password management, overall integration. |
| Test cases | 5 (5 PASS) |
| Execution date | 2026-11-17 |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Execution method | Manual validation procedure executed by Playwright browser automation (instructor-approved) |
| Source | Generated from `scripts/case_catalog.py` and the recorded results; the same records appear in `docs/Test_Case_Document.md` / `.xlsx` |

## Test environment and procedure

| Item | Details |
|---|---|
| Application | Attendance Management System, Flask application on `http://127.0.0.1:5001` |
| Test database | Isolated `validation_demo.db`, seeded with `scripts/seed_demo_data.py` (never the real `attendance.db`) |
| Test accounts | `demo.admin` (administrator), `prof.mehta` and `prof.iyer` (teachers), seeded student accounts; password in the git-ignored `demo_credentials.txt` |
| Execution | The checklist steps were executed by Playwright browser automation (`scripts/run_manual_validation_automation.py`); the instructor approved this as manual validation evidence |
| Evidence | Screenshots and browser logs in `docs/evidence/manual_validation_automation/`; per-step results in `docs/Manual_Validation_Automation_Report.md` |

Commands used:

```bash
python scripts/seed_demo_data.py --database validation_demo.db
python -c "from app import create_app; create_app({'DATABASE': 'validation_demo.db'}).run(port=5001)"
python scripts/run_manual_validation_automation.py   # requires validation_demo.db to be absent first
```

Status values: `PASS` = every check of the expected result was met; `FAIL` = the observed result differed (see the defect ID);
`BLOCKED` = the test could not be executed (reason given); `NOT RUN` = not executed (reason given).

## Summary of results

| # | Test Case ID | Requirement | Test scenario | Status | Defect / gap ID |
|---|---|---|---|---|---|
| 1 | SYS_FR-07_10 | FR-07 | Manage users through admin dashboard | PASS | - |
| 2 | SYS_FR-08_10 | FR-08 | Manage classes and subjects through admin dashboard | PASS | - |
| 3 | IT_FR-09_09 | FR-09 | Enrolled student appears in roster | PASS | - |
| 4 | SYS_FR-09_10 | FR-09 | Enroll through admin dashboard | PASS | - |
| 5 | SYS_FR-13_10 | FR-13 | Change password through the dashboard | PASS | - |

## Test case records

### 1. SYS_FR-07_10 - Manage users through admin dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-07_10 |
| Requirement | FR-07 - User Management |
| Test level | System |
| Test scenario | Manage users through admin dashboard |
| Assigned team member | Sumukh |
| Preconditions | Admin logged in to browser |
| Test data | Synthetic users |
| Test steps | 1. Log in as demo.admin.<br>2. Open Users.<br>3. Click New user; submit with an empty username and note the error.<br>4. Create a student 'manual_s1' with a password of at least 8 characters.<br>5. Type 'manual' in the search box; check only matching users are listed.<br>6. Use the role and status filters; check the table follows them.<br>7. Edit 'manual_s1' (change the username to 'manual_s1b'); check the table updates.<br>8. Deactivate 'manual_s1b'; log out; try to log in as 'manual_s1b' (must fail).<br>9. Log in as demo.admin again and reactivate the account. |
| Expected result | Each action succeeds and the table updates; validation errors shown for bad input. |
| Actual observed result | All 13 checks met. Observed: Submit New user with an empty username -> validation error, dialog stays open (native validation message: 'Please fill out this field.'; dialog open=True; form-error box=''); Create student 'manual_s1' (8+ char password) (toast: 'Created student account "manual_s1".'); Search 'manual' lists only matching users (rows: ['manual_s1']); Role filter 'student' shows only Student rows (9 row(s)); Role filter 'teacher' shows only Teacher rows (2 row(s)); Role filter 'admin' shows only Admin rows (1 row(s)); Status filter 'Active' shows only Active rows (12 row(s)); Status filter 'Inactive' shows only Inactive rows (0 row(s); empty state: 'No users found\nTry a different search or filter.'); Edit 'manual_s1' -> 'manual_s1b'; table updates (dialog title 'Edit manual_s1'; toast 'Updated manual_s1b.'); Deactivate 'manual_s1b' (confirmation dialog) (confirm 'Deactivate manual_s1b?'; toast 'manual_s1b. |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_01_users_list.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_02_empty_username_validation.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_03_search_manual.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_04_filters_student_active.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_05_deactivated.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_06_deactivated_login_refused.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-07_10_07_reactivated.png` |
| Supporting evidence | Executed 2026-11-17 08:29:17 to 08:29:22 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 13 of 13 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-07_10_main.log`<br>Automated test reference: `test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

*Not assessed by the automated execution:* The native empty-username bubble is not visible in headless screenshots; its validity state was checked instead.

### 2. SYS_FR-08_10 - Manage classes and subjects through admin dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-08_10 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | System |
| Test scenario | Manage classes and subjects through admin dashboard |
| Assigned team member | Sumukh |
| Preconditions | Admin logged in to browser |
| Test data | Synthetic class/subject |
| Test steps | 1. Log in as demo.admin.<br>2. Open Classes; create class 'Manual Class'.<br>3. Edit it and assign teacher prof.mehta.<br>4. Open Subjects; create subject 'Manual Subject' and assign prof.mehta.<br>5. Link 'Manual Subject' to 'Manual Class'.<br>6. Try to create 'Manual Class' again (duplicate) and note the error.<br>7. Use the search boxes on both lists.<br>8. Log in as prof.mehta and check 'Manual Subject' appears in Overview. |
| Expected result | Each action succeeds and the lists update. |
| Actual observed result | All 11 checks met. Observed: Open Classes; create class 'Manual Class' (toast 'Created class "Manual Class".'); Edit it and assign teacher prof.mehta (row: ['Manual Class', 'prof.mehta', 'No subjects']); Open Subjects; create 'Manual Subject' assigned to prof.mehta (toast 'Created subject "Manual Subject".'); Link 'Manual Subject' to 'Manual Class' (chips ['Manual Subject']; toast 'Subject added to class.'); Create duplicate 'Manual Class' -> error shown (error: 'Class name already exists'); Duplicate was not created (1 'Manual Class' row(s)); Class search 'Manual' lists only matching classes (['Manual Class']); Class search 'Year 2' lists only matching classes (['BSc Computer Science - Year 2']); Subject search 'Manual' lists only matching subjects (['Manual Subject']); Log in as prof.mehta; 'Manual Subject' appears in Overview (['Database Systems\nAssigned', 'Manual Subject\nAssigned', 'Programming Fundamentals\nA. |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-08_10_01_class_created_edited.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-08_10_02_subject_created.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-08_10_03_link_subject_dialog.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-08_10_04_duplicate_class_error.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-08_10_05_subject_search.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-08_10_06_teacher_overview_manual_subject.png` |
| Supporting evidence | Executed 2026-11-17 08:29:22 to 08:29:27 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 11 of 11 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-08_10_main.log` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 3. IT_FR-09_09 - Enrolled student appears in roster

| Field | Details |
|---|---|
| Test Case ID | IT_FR-09_09 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Integration |
| Test scenario | Enrolled student appears in roster |
| Assigned team member | Sumukh |
| Preconditions | S01 enrolled |
| Test data | CSE-A, DBMS |
| Test steps | 1. Log in as demo.admin; open Enrollments.<br>2. Note which students are enrolled in 'Manual Class' / 'Manual Subject' (from SYS_FR-08_10).<br>3. Enroll exactly one student in it.<br>4. Log in as prof.mehta; open Mark attendance.<br>5. Select 'Manual Class', 'Manual Subject' and today's date; click Load roster.<br>6. Check only the enrolled student is listed and nobody else. |
| Expected result | S01 listed; unenrolled students not listed. |
| Actual observed result | All 4 checks met. Observed: Enroll exactly one student (aarav) (toast 'Student enrolled.'; Manual Class rows ['aarav']); Manual Class offered in Mark attendance (classes: ['Choose a class', 'BSc Computer Science - Year 1', 'BSc Computer Science - Year 2', 'Manual Class']); Only the enrolled student is listed and nobody else (roster: ['aarav']); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/IT_FR-09_09_01_one_student_enrolled.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/IT_FR-09_09_02_roster_only_enrolled.png` |
| Supporting evidence | Executed 2026-11-17 08:29:27 to 08:29:30 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 4 of 4 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/IT_FR-09_09_main.log`<br>Automated test reference: `test_fr02_attendance_marking::test_it_fr_02_06_load_class_roster` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 4. SYS_FR-09_10 - Enroll through admin dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-09_10 |
| Requirement | FR-09 - Student Enrollment |
| Test level | System |
| Test scenario | Enroll through admin dashboard |
| Assigned team member | Sumukh |
| Preconditions | Admin logged in to browser |
| Test data | Synthetic data |
| Test steps | 1. Log in as demo.admin; open Enrollments.<br>2. Pick a student, class and subject; click Enroll.<br>3. Check the enrollment appears in the list.<br>4. Enroll the same combination again; note the error.<br>5. Use the search box and the class filter.<br>6. Remove the enrollment; check it disappears. |
| Expected result | Enrollment appears in the list and can be removed. |
| Actual observed result | All 7 checks met. Observed: Enroll diya in Manual Class / Manual Subject; appears in list (toast 'Student enrolled.'; count '17 enrollment(s) in total.' -> '18 enrollment(s) in total.'); Enroll the same combination again -> error (error toast: 'Student is already enrolled'); Search 'diya' lists only diya's enrollments (3 row(s)); Class filter 'Year 2' lists only that class (8 row(s)); Class filter 'Manual Class' lists only that class (['aarav', 'diya']); Remove the enrollment; it disappears (confirm 'diya will be removed from Manual Subject in Manual Class. Past attendance records are kept.'; toast '); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-09_10_01_enrolled.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-09_10_02_duplicate_error.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-09_10_03_class_filter.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-09_10_04_removed.png` |
| Supporting evidence | Executed 2026-11-17 08:29:30 to 08:29:32 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 7 of 7 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-09_10_main.log` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 5. SYS_FR-13_10 - Change password through the dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-13_10 |
| Requirement | FR-13 - Password Management |
| Test level | System |
| Test scenario | Change password through the dashboard |
| Assigned team member | Sumukh |
| Preconditions | User logged in to browser |
| Test data | Current and new password |
| Test steps | 1. Log in as a demo student.<br>2. Click Change password.<br>3. Enter a wrong current password; submit; note the error.<br>4. Enter the correct current password and a new password of 7 characters; note the error.<br>5. Enter the correct current password and a new 8+ character password; submit; note the message.<br>6. Log out; log in with the old password (must fail), then with the new one (must work).<br>7. Change the password back so other testers are not affected. |
| Expected result | Success message; new password works. |
| Actual observed result | All 7 checks met. Observed: Wrong current password -> error (error: 'Current password is incorrect'); Correct current + 7-character new password -> error (form-error=''; native tooShort=True message='Please lengthen this text to 8 characters or more (you are curren); Correct current + new 8+ char password -> success message (toast 'Your password has been changed.'); Log in with the old password must fail (Invalid username or password); Log in with the new password must work (http://127.0.0.1:5001/student); Change the password back (original password works again) (toast 'Your password has been changed.'); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-13_10_01_wrong_current.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-13_10_02_seven_char_rejected.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-13_10_03_changed.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-13_10_04_new_password_login.png` |
| Supporting evidence | Executed 2026-11-17 08:29:32 to 08:29:38 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 7 of 7 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-13_10_main.log`<br>Automated test reference: `test_fr13_password_management::test_dashboards_offer_change_password` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

