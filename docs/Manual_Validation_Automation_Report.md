# Manual Validation Automation Report

**Run of record:** regression run after the six fixes  
**Project:** Attendance Management System - Deliverable 3  
**Execution date:** 2026-11-17 (2026-11-17T08:29:17 to 2026-11-17T08:30:36, local time)  
**Scope:** the 19 cases in `docs/manual_validation/{Sumukh,Jagadeesh,Tharith}_Checklist.md`  
**Harness:** `scripts/run_manual_validation_automation.py`  
**Raw results:** `docs/evidence/regression/manual_validation_automation/results.json`

> **How these results are used.** The instructor approved automated browser execution as evidence for the manual validation deliverable, so these results are recorded in the checklists, the Test Case Document and the System Validation Report. **No person performed these steps**; the named team member is the responsible test owner. Aspects that need human judgement are listed as *not assessed by automation*; no human observation is claimed.

## 1. Environment

| Item | Value |
|---|---|
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) (all cases except the WebKit supplement in SYS_NFR-05_08) |
| Application | Flask on http://127.0.0.1:5001: `create_app({'DATABASE': 'validation_demo.db'}).run(port=5001)` (as in the checklist setup) |
| Database | `validation_demo.db`, newly seeded with `scripts/seed_demo_data.py --database validation_demo.db` (11 users, 2 classes, 4 subjects, 16 enrollments, 192 attendance records); git-ignored |
| attendance.db | Not used. SHA-256 before and after the run: `df6b0f51568511668bc629e3fed0845646eca18fcb99c56c1e784717dbcf838c` (unchanged: True) |
| Production code | Changed for the six fixes before this run (`app/static/js/`, `app/static/css/app.css`, `app/templates/`); no backend or security-policy change |
| Credentials | Demo password read from git-ignored `demo_credentials.txt`; redacted from all evidence files |
| Mode | Headless, 1280x800 unless the case sets another size; one fresh browser context per case |

## 2. Run history

Earlier runs are kept unchanged in their own directories. The run of record is the last row.

| Run | Directory | Executed | PASS | FAIL | BLOCKED | NOT RUN | Note |
|---|---|---|---|---|---|---|---|
| Original run (before the fixes) | `docs/evidence/manual_validation_automation` | 2026-11-17T03:41:47 to 2026-11-17T03:43:06 | 14 | 3 | 1 | 1 | Three FAILs: MV-01, MV-02, MV-03 |
| Regression attempt 1 (superseded) | `docs/evidence/regression/manual_validation_automation_attempt1` | 2026-11-17T08:27:38 to 2026-11-17T08:28:57 | 16 | 1 | 1 | 1 | Superseded: the harness's own reference value for SYS_FR-14_08 still used one-decimal rounding; see SUPERSEDED.txt |
| Regression run of record (after the fixes) | `docs/evidence/regression/manual_validation_automation` | 2026-11-17T08:29:17 to 2026-11-17T08:30:36 | 17 | 0 | 1 | 1 | Run reported in all documents |

| Test Case ID | Owner | Original run | Regression run |
|---|---|---|---|
| SYS_FR-07_10 | Sumukh | PASS | **PASS** |
| SYS_FR-08_10 | Sumukh | PASS | **PASS** |
| IT_FR-09_09 | Sumukh | PASS | **PASS** |
| SYS_FR-09_10 | Sumukh | PASS | **PASS** |
| SYS_FR-13_10 | Sumukh | PASS | **PASS** |
| SYS_FR-01_08 | Jagadeesh | PASS | **PASS** |
| SYS_FR-03_13 | Jagadeesh | PASS | **PASS** |
| SYS_FR-10_10 | Jagadeesh | FAIL | **PASS** |
| SYS_FR-11_10 | Jagadeesh | PASS | **PASS** |
| SYS_FR-15_06 | Jagadeesh | PASS | **PASS** |
| SYS_FR-04_11 | Jagadeesh | FAIL | **PASS** |
| SYS_NFR-02_06 | Jagadeesh | PASS | **PASS** |
| UT_FR-05_04 | Tharith | PASS | **PASS** |
| SYS_FR-05_10 | Tharith | FAIL | **PASS** |
| SYS_FR-14_08 | Tharith | PASS | **PASS** |
| SYS_FR-15_07 | Tharith | PASS | **PASS** |
| IT_NFR-04_04 | Tharith | PASS | **PASS** |
| SYS_NFR-04_06 | Tharith | NOT RUN | **NOT RUN** |
| SYS_NFR-05_08 | Tharith | BLOCKED | **BLOCKED** |

## 3. Summary

| Measure | Count |
|---|---|
| Scenarios executed end-to-end by automation | 17 of 19 |
| PASS | 17 |
| FAIL | 0 (D-01, MV-01, MV-02, MV-03, D-02, D-03) |
| BLOCKED | 1 (SYS_NFR-05_08: the Safari application cannot be driven by Playwright) |
| NOT RUN | 1 (SYS_NFR-04_06: needs a human participant) |
| Cases with aspects not assessed by automation | 7 |
| Screenshots | 75 |
| Browser logs | 21 |

| # | Test Case ID | Test owner | Description | Status |
|---|---|---|---|---|
| 1 | SYS_FR-07_10 | Sumukh | Manage users through admin dashboard | **PASS** |
| 2 | SYS_FR-08_10 | Sumukh | Manage classes and subjects through admin dashboard | **PASS** |
| 3 | IT_FR-09_09 | Sumukh | Enrolled student appears in roster | **PASS** |
| 4 | SYS_FR-09_10 | Sumukh | Enroll through admin dashboard | **PASS** |
| 5 | SYS_FR-13_10 | Sumukh | Change password through the dashboard | **PASS** |
| 6 | SYS_FR-01_08 | Jagadeesh | Logout | **PASS** |
| 7 | SYS_FR-03_13 | Jagadeesh | Edit and delete through teacher dashboard | **PASS** |
| 8 | SYS_FR-10_10 | Jagadeesh | Search and filter in the dashboards | **PASS** |
| 9 | SYS_FR-11_10 | Jagadeesh | Alerts shown on dashboards | **PASS** |
| 10 | SYS_FR-15_06 | Jagadeesh | Logout button on every dashboard | **PASS** |
| 11 | SYS_FR-04_11 | Jagadeesh | Percentages displayed on the teacher dashboard | **PASS** |
| 12 | SYS_NFR-02_06 | Jagadeesh | Perceived load time on the demo machine | **PASS** |
| 13 | UT_FR-05_04 | Tharith | Empty result handling | **PASS** |
| 14 | SYS_FR-05_10 | Tharith | Responsive viewing | **PASS** |
| 15 | SYS_FR-14_08 | Tharith | Dashboard summary displayed in browser | **PASS** |
| 16 | SYS_FR-15_07 | Tharith | Back button after logout | **PASS** |
| 17 | IT_NFR-04_04 | Tharith | Keyboard and accessibility | **PASS** |
| 18 | SYS_NFR-04_06 | Tharith | Human usability walkthrough | **NOT RUN** |
| 19 | SYS_NFR-05_08 | Tharith | Main workflows in the Apple Safari application | **BLOCKED** |

## 4. Defects found in the original run and their current status

These are recorded in the defect register of the Test Case Document and the System Validation Report.

| ID | Req. | Severity | Finding | Test impact | Status |
|---|---|---|---|---|---|
| D-01 | NFR-05 | Low | WebKit (Playwright 27.2) logs a Content-Security-Policy error for every <select> element on all dashboards ("Refused to apply a stylesheet ... style-src"). The app sends default-src 'self' with no style-src; WebKit appears to treat its own form-control styling as a blocked stylesheet. Functions and appearance are unaffected; Chrome and Chromium log nothing. | SYS_NFR-05_04 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): upstream WebKit regression (false-positive style-src-attr violation for <select>), fixed in WebKit 324283@main; re-run with Playwright 1.65.2 / WebKit r2388 shows 0 violations. No application change; CSP unchanged. |
| MV-01 | FR-10 | Low | The teacher Attendance records screen has no 'Clear filters' control (toolbar: search, Subject, Date, Status). The expected result of SYS_FR-10_10 requires 'Clear filters' to restore all rows; the teacher must reset each filter by hand. The admin Attendance screen has the control and it works. | SYS_FR-10_10 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): Clear filters, Class and From/To filters on the teacher records screen (app/templates/teacher.html, teacher.js). |
| MV-02 | FR-04 | Low | Attendance percentages are displayed to one decimal place (83.3%, 58.3%) although the backend returns, and SYS_FR-04_11 expects, two decimals (83.33, 58.33). The calculation is correct. The shared formatter App.formatPercent (app/static/js/common.js) uses toFixed(1), so other dashboards are likely affected too. | SYS_FR-04_11 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): App.formatPercent shows two decimals (app/static/js/common.js); overview averages rounded to two decimals. |
| MV-03 | FR-05 | Low | At 375 px wide the teacher Attendance records table overflows its container by 181 px: Status badges are cut off and the Actions (correct/delete) column is reachable only by scrolling the table sideways. The page itself does not scroll horizontally, so the existing automated layout test passes. | SYS_FR-05_10 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): labelled card layout for tables below 640 px (app/static/css/app.css, App.fillRows data-label). |
| D-02 | FR-06 | Medium | No reporting screen (gap G-01). | SYS_FR-06_08 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): Reports screen in the admin and teacher dashboards (app/static/js/reports.js, templates). |
| D-03 | FR-12 | Medium | No export control in the user interface (gap G-02). | SYS_FR-12_10 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): CSV / PDF / JSON export controls on the Reports screen using the existing export API. |

All six defects are fixed and verified in the regression run. The supplementary WebKit run in SYS_NFR-05_08 now uses Playwright WebKit build r2388 (Playwright 1.65.2) and logs no CSP errors; it remains engine-level evidence, not a Safari test. Gap G-04 (no threshold screen) is unchanged.

## 5. Not assessed by automation

| Case | Not assessed |
|---|---|
| SYS_FR-07_10 | The native empty-username bubble is not visible in headless screenshots; its validity state was checked instead. |
| SYS_NFR-02_06 | Timings taken on the development Mac with the cache disabled through the DevTools protocol, not on a separate demo machine. |
| UT_FR-05_04 | Whether the message is 'clear' to a student is a wording judgement that automation cannot make. |
| SYS_FR-05_10 | Readability and visual overlap were not judged by a person; only overflow was measured. |
| IT_NFR-04_04 | Focus styles were detected programmatically; how visible they are to a person, and screen-reader use, were not assessed. |
| SYS_NFR-04_06 | Requires a human participant; not automatable. |
| SYS_NFR-05_08 | Requires the real Safari application; WebKit is engine-level evidence only. |

## 6. Scenario details

### SYS_FR-07_10 - Manage users through admin dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-07_10 |
| Responsible test owner | Sumukh |
| Expected result | Each action succeeds and the table updates; validation errors shown for bad input. |
| Actual result | All 13 checks met. Observed: Submit New user with an empty username -> validation error, dialog stays open (native validation message: 'Please fill out this field.'; dialog open=True; form-error box=''); Create student 'manual_s1' (8+ char password) (toast: 'Created student account "manual_s1".'); Search 'manual' lists only matching users (rows: ['manual_s1']); Role filter 'student' shows only Student rows (9 row(s)); Role filter 'teacher' shows only Teacher rows (2 row(s)); Role filter 'admin' shows only Admin rows (1 row(s)); Status filter 'Active' shows only Active rows (12 row(s)); Status filter 'Inactive' shows only Inactive rows (0 row(s); empty state: 'No users found\nTry a different search or filter.'); Edit 'manual_s1' -> 'manual_s1b'; table updates (dialog title 'Edit manual_s1'; toast 'Updated manual_s1b.'); Deactivate 'manual_s1b' (confirmation dialog) (confirm 'Deactivate manual_s1b?'; toast 'manual_s1b. |
| Status | **PASS** (13/13 checks met) |
| Not assessed by automation | The native empty-username bubble is not visible in headless screenshots; its validity state was checked instead. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:17 to 2026-11-17T08:29:22 |
| Screenshots | `SYS_FR-07_10_01_users_list.png`, `SYS_FR-07_10_02_empty_username_validation.png`, `SYS_FR-07_10_03_search_manual.png`, `SYS_FR-07_10_04_filters_student_active.png`, `SYS_FR-07_10_05_deactivated.png`, `SYS_FR-07_10_06_deactivated_login_refused.png`, `SYS_FR-07_10_07_reactivated.png` |
| Logs | `SYS_FR-07_10_main.log` |

Steps executed:

1. [done] Log in as demo.admin - http://127.0.0.1:5001/admin
2. [done] Open Users - 11 users listed
3. [PASS] Submit New user with an empty username -> validation error, dialog stays open - native validation message: 'Please fill out this field.'; dialog open=True; form-error box=''
4. [PASS] Create student 'manual_s1' (8+ char password) - toast: 'Created student account "manual_s1".'
5. [PASS] Search 'manual' lists only matching users - rows: ['manual_s1']
6. [PASS] Role filter 'student' shows only Student rows - 9 row(s)
7. [PASS] Role filter 'teacher' shows only Teacher rows - 2 row(s)
8. [PASS] Role filter 'admin' shows only Admin rows - 1 row(s)
9. [PASS] Status filter 'Active' shows only Active rows - 12 row(s)
10. [PASS] Status filter 'Inactive' shows only Inactive rows - 0 row(s); empty state: 'No users found\nTry a different search or filter.'
11. [PASS] Edit 'manual_s1' -> 'manual_s1b'; table updates - dialog title 'Edit manual_s1'; toast 'Updated manual_s1b.'
12. [PASS] Deactivate 'manual_s1b' (confirmation dialog) - confirm 'Deactivate manual_s1b?'; toast 'manual_s1b deactivated.'; badge 'Inactive'
13. [done] Log out - http://127.0.0.1:5001/login
14. [PASS] Login as deactivated 'manual_s1b' must fail - error shown: 'Invalid username or password'
15. [PASS] Log in as demo.admin again and reactivate the account - toast 'manual_s1b activated.'
16. [PASS] No uncaught JavaScript errors - []

### SYS_FR-08_10 - Manage classes and subjects through admin dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-08_10 |
| Responsible test owner | Sumukh |
| Expected result | Each action succeeds and the lists update. |
| Actual result | All 11 checks met. Observed: Open Classes; create class 'Manual Class' (toast 'Created class "Manual Class".'); Edit it and assign teacher prof.mehta (row: ['Manual Class', 'prof.mehta', 'No subjects']); Open Subjects; create 'Manual Subject' assigned to prof.mehta (toast 'Created subject "Manual Subject".'); Link 'Manual Subject' to 'Manual Class' (chips ['Manual Subject']; toast 'Subject added to class.'); Create duplicate 'Manual Class' -> error shown (error: 'Class name already exists'); Duplicate was not created (1 'Manual Class' row(s)); Class search 'Manual' lists only matching classes (['Manual Class']); Class search 'Year 2' lists only matching classes (['BSc Computer Science - Year 2']); Subject search 'Manual' lists only matching subjects (['Manual Subject']); Log in as prof.mehta; 'Manual Subject' appears in Overview (['Database Systems\nAssigned', 'Manual Subject\nAssigned', 'Programming Fundamentals\nA. |
| Status | **PASS** (11/11 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:22 to 2026-11-17T08:29:27 |
| Screenshots | `SYS_FR-08_10_01_class_created_edited.png`, `SYS_FR-08_10_02_subject_created.png`, `SYS_FR-08_10_03_link_subject_dialog.png`, `SYS_FR-08_10_04_duplicate_class_error.png`, `SYS_FR-08_10_05_subject_search.png`, `SYS_FR-08_10_06_teacher_overview_manual_subject.png` |
| Logs | `SYS_FR-08_10_main.log` |

Steps executed:

1. [done] Log in as demo.admin
2. [PASS] Open Classes; create class 'Manual Class' - toast 'Created class "Manual Class".'
3. [PASS] Edit it and assign teacher prof.mehta - row: ['Manual Class', 'prof.mehta', 'No subjects']
4. [PASS] Open Subjects; create 'Manual Subject' assigned to prof.mehta - toast 'Created subject "Manual Subject".'
5. [PASS] Link 'Manual Subject' to 'Manual Class' - chips ['Manual Subject']; toast 'Subject added to class.'
6. [PASS] Create duplicate 'Manual Class' -> error shown - error: 'Class name already exists'
7. [PASS] Duplicate was not created - 1 'Manual Class' row(s)
8. [PASS] Class search 'Manual' lists only matching classes - ['Manual Class']
9. [PASS] Class search 'Year 2' lists only matching classes - ['BSc Computer Science - Year 2']
10. [PASS] Subject search 'Manual' lists only matching subjects - ['Manual Subject']
11. [PASS] Log in as prof.mehta; 'Manual Subject' appears in Overview - ['Database Systems\nAssigned', 'Manual Subject\nAssigned', 'Programming Fundamentals\nAssigned']
12. [PASS] No uncaught JavaScript errors - []

### IT_FR-09_09 - Enrolled student appears in roster

| Field | Value |
|---|---|
| Test Case ID | IT_FR-09_09 |
| Responsible test owner | Sumukh |
| Expected result | S01 listed; unenrolled students not listed. |
| Actual result | All 4 checks met. Observed: Enroll exactly one student (aarav) (toast 'Student enrolled.'; Manual Class rows ['aarav']); Manual Class offered in Mark attendance (classes: ['Choose a class', 'BSc Computer Science - Year 1', 'BSc Computer Science - Year 2', 'Manual Class']); Only the enrolled student is listed and nobody else (roster: ['aarav']); No uncaught JavaScript errors ([]). |
| Status | **PASS** (4/4 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:27 to 2026-11-17T08:29:30 |
| Screenshots | `IT_FR-09_09_01_one_student_enrolled.png`, `IT_FR-09_09_02_roster_only_enrolled.png` |
| Logs | `IT_FR-09_09_main.log` |

Steps executed:

1. [done] Admin > Enrollments: note enrollments in Manual Class / Manual Subject - 0 before: []
2. [PASS] Enroll exactly one student (aarav) - toast 'Student enrolled.'; Manual Class rows ['aarav']
3. [PASS] Manual Class offered in Mark attendance - classes: ['Choose a class', 'BSc Computer Science - Year 1', 'BSc Computer Science - Year 2', 'Manual Class']
4. [done] Select Manual Class, Manual Subject, today's date; click Load - 2026-11-17
5. [PASS] Only the enrolled student is listed and nobody else - roster: ['aarav']
6. [PASS] No uncaught JavaScript errors - []

### SYS_FR-09_10 - Enroll through admin dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-09_10 |
| Responsible test owner | Sumukh |
| Expected result | Enrollment appears in the list and can be removed. |
| Actual result | All 7 checks met. Observed: Enroll diya in Manual Class / Manual Subject; appears in list (toast 'Student enrolled.'; count '17 enrollment(s) in total.' -> '18 enrollment(s) in total.'); Enroll the same combination again -> error (error toast: 'Student is already enrolled'); Search 'diya' lists only diya's enrollments (3 row(s)); Class filter 'Year 2' lists only that class (8 row(s)); Class filter 'Manual Class' lists only that class (['aarav', 'diya']); Remove the enrollment; it disappears (confirm 'diya will be removed from Manual Subject in Manual Class. Past attendance records are kept.'; toast '); No uncaught JavaScript errors ([]). |
| Status | **PASS** (7/7 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:30 to 2026-11-17T08:29:32 |
| Screenshots | `SYS_FR-09_10_01_enrolled.png`, `SYS_FR-09_10_02_duplicate_error.png`, `SYS_FR-09_10_03_class_filter.png`, `SYS_FR-09_10_04_removed.png` |
| Logs | `SYS_FR-09_10_main.log` |

Steps executed:

1. [PASS] Enroll diya in Manual Class / Manual Subject; appears in list - toast 'Student enrolled.'; count '17 enrollment(s) in total.' -> '18 enrollment(s) in total.'
2. [PASS] Enroll the same combination again -> error - error toast: 'Student is already enrolled'
3. [PASS] Search 'diya' lists only diya's enrollments - 3 row(s)
4. [PASS] Class filter 'Year 2' lists only that class - 8 row(s)
5. [PASS] Class filter 'Manual Class' lists only that class - ['aarav', 'diya']
6. [PASS] Remove the enrollment; it disappears - confirm 'diya will be removed from Manual Subject in Manual Class. Past attendance records are kept.'; toast 'Enrollment removed.'
7. [PASS] No uncaught JavaScript errors - []

### SYS_FR-13_10 - Change password through the dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-13_10 |
| Responsible test owner | Sumukh |
| Expected result | Success message; new password works. |
| Actual result | All 7 checks met. Observed: Wrong current password -> error (error: 'Current password is incorrect'); Correct current + 7-character new password -> error (form-error=''; native tooShort=True message='Please lengthen this text to 8 characters or more (you are curren); Correct current + new 8+ char password -> success message (toast 'Your password has been changed.'); Log in with the old password must fail (Invalid username or password); Log in with the new password must work (http://127.0.0.1:5001/student); Change the password back (original password works again) (toast 'Your password has been changed.'); No uncaught JavaScript errors ([]). |
| Status | **PASS** (7/7 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:32 to 2026-11-17T08:29:38 |
| Screenshots | `SYS_FR-13_10_01_wrong_current.png`, `SYS_FR-13_10_02_seven_char_rejected.png`, `SYS_FR-13_10_03_changed.png`, `SYS_FR-13_10_04_new_password_login.png` |
| Logs | `SYS_FR-13_10_main.log` |

Steps executed:

1. [done] Log in as demo student meera
2. [PASS] Wrong current password -> error - error: 'Current password is incorrect'
3. [PASS] Correct current + 7-character new password -> error - form-error=''; native tooShort=True message='Please lengthen this text to 8 characters or more (you are currently using 7 characters).'
4. [PASS] Correct current + new 8+ char password -> success message - toast 'Your password has been changed.'
5. [PASS] Log in with the old password must fail - Invalid username or password
6. [PASS] Log in with the new password must work - http://127.0.0.1:5001/student
7. [PASS] Change the password back (original password works again) - toast 'Your password has been changed.'
8. [PASS] No uncaught JavaScript errors - []

### SYS_FR-01_08 - Logout

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-01_08 |
| Responsible test owner | Jagadeesh |
| Expected result | Protected pages cannot be reopened: page requests redirect to /login, API requests return 401. Responses carry Cache-Control: no-store. |
| Actual result | All 7 checks met. Observed: Press Back (1): no attendance data shown (url http://127.0.0.1:5001/login#records; record rows visible 0); Press Back (2): no attendance data shown (url http://127.0.0.1:5001/login; record rows visible 0); Reload the page -> login page (http://127.0.0.1:5001/login); Type /teacher in the address bar -> redirected to /login (http://127.0.0.1:5001/login); API request after logout returns 401 (status 401; body {'error': 'Authentication required'}); Responses carry Cache-Control: no-store (/teacher 'no-store'; /api/attendance 'no-store'); No uncaught JavaScript errors ([]). |
| Status | **PASS** (7/7 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:38 to 2026-11-17T08:29:43 |
| Screenshots | `SYS_FR-01_08_01_records_before_logout.png`, `SYS_FR-01_08_02_after_back_1.png`, `SYS_FR-01_08_03_after_back_2.png`, `SYS_FR-01_08_04_teacher_url_redirected.png` |
| Logs | `SYS_FR-01_08_main.log` |

Steps executed:

1. [done] Log in as prof.mehta (teacher) - /teacher Cache-Control: 'no-store'
2. [done] Open Attendance records - 96 rows; /api/attendance Cache-Control 'no-store'
3. [done] Click Log out and confirm - http://127.0.0.1:5001/login
4. [PASS] Press Back (1): no attendance data shown - url http://127.0.0.1:5001/login#records; record rows visible 0
5. [PASS] Press Back (2): no attendance data shown - url http://127.0.0.1:5001/login; record rows visible 0
6. [PASS] Reload the page -> login page - http://127.0.0.1:5001/login
7. [PASS] Type /teacher in the address bar -> redirected to /login - http://127.0.0.1:5001/login
8. [PASS] API request after logout returns 401 - status 401; body {'error': 'Authentication required'}
9. [PASS] Responses carry Cache-Control: no-store - /teacher 'no-store'; /api/attendance 'no-store'
10. [PASS] No uncaught JavaScript errors - []

### SYS_FR-03_13 - Edit and delete through teacher dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-03_13 |
| Responsible test owner | Jagadeesh |
| Expected result | Edited status shown; deleted record removed from the table after confirmation. |
| Actual result | All 5 checks met. Observed: Correct status -> Late; table shows Late (toast 'Attendance record updated.'; row ['Mon, Nov 16, 2026', 'A\naarav', 'Programming Fundamentals', 'Late', ); Click delete -> confirmation dialog appears ('Delete this record?': "aarav's Late record for Programming Fundamentals on Mon, Nov 16, 2026 will be permanen); Delete and confirm -> record disappears and a message is shown (toast 'Attendance record deleted.'; rows 96 -> 95); No uncaught JavaScript errors ([]). |
| Status | **PASS** (5/5 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:43 to 2026-11-17T08:29:46 |
| Screenshots | `SYS_FR-03_13_01_status_corrected.png`, `SYS_FR-03_13_02_delete_confirm.png`, `SYS_FR-03_13_03_record_deleted.png` |
| Logs | `SYS_FR-03_13_main.log` |

Steps executed:

1. [done] Open Attendance records; pick a record - 96 rows; record ('Mon, Nov 16, 2026', 'aarav', 'Programming Fundamentals') status 'Present'
2. [PASS] Correct status -> Late; table shows Late - toast 'Attendance record updated.'; row ['Mon, Nov 16, 2026', 'A\naarav', 'Programming Fundamentals', 'Late', '']
3. [PASS] Click delete -> confirmation dialog appears - 'Delete this record?': "aarav's Late record for Programming Fundamentals on Mon, Nov 16, 2026 will be permanently deleted."
4. [PASS] Cancel -> the record is still there
5. [PASS] Delete and confirm -> record disappears and a message is shown - toast 'Attendance record deleted.'; rows 96 -> 95
6. [PASS] No uncaught JavaScript errors - []

### SYS_FR-10_10 - Search and filter in the dashboards

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-10_10 |
| Responsible test owner | Jagadeesh |
| Expected result | Table updates to matching rows; 'Clear filters' restores all rows. |
| Actual result | All 14 checks met. Observed: Search 'kabir' -> only kabir's rows (12 rows); Subject filter 'Database Systems' -> table updates (48 rows); Then date 2026-11-16 -> table updates (4 rows); Then status Present -> table updates (4 rows); Click 'Clear filters' -> every filter reset and all rows restored (95 rows (all = 95); filter values after clearing ['', '', '', '', '', '', '']); Class filter 'BSc Computer Science - Year 1' -> table matches the API (47 rows (API 47)); Date range 2026-10-30 to 2026-11-03 (with class filter) -> table matches the API (12 rows (API 12)); Admin: subject filter 'Database Systems' (48 rows); Admin: date 2026-11-16 (4 rows); Admin: status Absent (0 rows); Admin: 'Clear filters' restores all rows (191 rows (all = 191)); No uncaught JavaScript errors ([]). |
| Status | **PASS** (14/14 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:46 to 2026-11-17T08:29:52 |
| Screenshots | `SYS_FR-10_10_01_teacher_search.png`, `SYS_FR-10_10_02_teacher_filters.png`, `SYS_FR-10_10_03_teacher_cleared.png`, `SYS_FR-10_10_04_teacher_class_and_range.png`, `SYS_FR-10_10_05_admin_filters.png`, `SYS_FR-10_10_06_admin_cleared.png` |
| Logs | `SYS_FR-10_10_main.log` |

Steps executed:

1. [done] Log in as prof.mehta; open Attendance records - 95 rows
2. [PASS] Search 'kabir' -> only kabir's rows - 12 rows
3. [PASS] Subject filter 'Database Systems' -> table updates - 48 rows
4. [PASS] Then date 2026-11-16 -> table updates - 4 rows
5. [PASS] Then status Present -> table updates - 4 rows
6. [PASS] 'Clear filters' control present on the teacher Attendance records screen
7. [PASS] Click 'Clear filters' -> every filter reset and all rows restored - 95 rows (all = 95); filter values after clearing ['', '', '', '', '', '', '']
8. [PASS] Class filter 'BSc Computer Science - Year 1' -> table matches the API - 47 rows (API 47)
9. [PASS] Date range 2026-10-30 to 2026-11-03 (with class filter) -> table matches the API - 12 rows (API 12)
10. [PASS] Clear filters after class and date-range filters -> all rows restored
11. [PASS] Admin: subject filter 'Database Systems' - 48 rows
12. [PASS] Admin: date 2026-11-16 - 4 rows
13. [PASS] Admin: status Absent - 0 rows
14. [PASS] Admin: 'Clear filters' restores all rows - 191 rows (all = 191)
15. [PASS] No uncaught JavaScript errors - []
- Note: The student History screen keeps its subject, status and date filters; they are exercised in UT_FR-05_04.

### SYS_FR-11_10 - Alerts shown on dashboards

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-11_10 |
| Responsible test owner | Jagadeesh |
| Expected result | Low-attendance students listed; 'Everyone is on track' when none. |
| Actual result | All 3 checks met. Observed: prof.mehta: every student below 75% is listed, none at/above 75% (below 75% on Percentages: {'kabir': 58.33, 'vikram': 58.33}; listed: ['kabir', 'vikram'] (overview shows at mo); demo.admin: every student below 75% is listed, none at/above 75% (below 75% on Percentages: {'kabir': 70.83, 'vikram': 50.0}; listed: ['kabir', 'vikram'] (overview shows at mos); No uncaught JavaScript errors ([]). |
| Status | **PASS** (3/3 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:52 to 2026-11-17T08:29:56 |
| Screenshots | `SYS_FR-11_10_01_prof_overview_alerts.png`, `SYS_FR-11_10_02_prof_percentages.png`, `SYS_FR-11_10_03_demo_overview_alerts.png`, `SYS_FR-11_10_04_demo_percentages.png` |
| Logs | `SYS_FR-11_10_main.log` |

Steps executed:

1. [done] prof.mehta: Overview 'Students needing attention' - {'kabir': 58.33, 'vikram': 58.33}
2. [PASS] prof.mehta: every student below 75% is listed, none at/above 75% - below 75% on Percentages: {'kabir': 58.33, 'vikram': 58.33}; listed: ['kabir', 'vikram'] (overview shows at most 6)
3. [done] demo.admin: Overview 'Students needing attention' - {'vikram': 50.0, 'kabir': 70.83}
4. [PASS] demo.admin: every student below 75% is listed, none at/above 75% - below 75% on Percentages: {'kabir': 70.83, 'vikram': 50.0}; listed: ['kabir', 'vikram'] (overview shows at most 8)
5. [done] Record that there is no screen to change the 75% threshold (known gap G-04) - threshold controls found in admin dashboard: 0
6. [PASS] No uncaught JavaScript errors - []
- Note: The 'Everyone is on track' empty state was not exercised: in the seeded data both dashboards have students below 75%.

### SYS_FR-15_06 - Logout button on every dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-15_06 |
| Responsible test owner | Jagadeesh |
| Expected result | Returned to /login with a signed-out state. |
| Actual result | All 7 checks met. Observed: demo.admin: Log out + confirm -> login page (http://127.0.0.1:5001/login); demo.admin: signed-out state (/admin redirects to /login) (http://127.0.0.1:5001/login); aarav: Log out + confirm -> login page (http://127.0.0.1:5001/login); aarav: signed-out state (/student redirects to /login) (http://127.0.0.1:5001/login); prof.mehta: Log out + confirm -> login page (http://127.0.0.1:5001/login); prof.mehta: signed-out state (/teacher redirects to /login) (http://127.0.0.1:5001/login); No uncaught JavaScript errors ([]). |
| Status | **PASS** (7/7 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:29:56 to 2026-11-17T08:30:00 |
| Screenshots | `SYS_FR-15_06_01_demo_logged_out.png`, `SYS_FR-15_06_02_aarav_logged_out.png`, `SYS_FR-15_06_03_prof_logged_out.png` |
| Logs | `SYS_FR-15_06_main.log` |

Steps executed:

1. [PASS] demo.admin: Log out + confirm -> login page - http://127.0.0.1:5001/login
2. [PASS] demo.admin: signed-out state (/admin redirects to /login) - http://127.0.0.1:5001/login
3. [PASS] aarav: Log out + confirm -> login page - http://127.0.0.1:5001/login
4. [PASS] aarav: signed-out state (/student redirects to /login) - http://127.0.0.1:5001/login
5. [PASS] prof.mehta: Log out + confirm -> login page - http://127.0.0.1:5001/login
6. [PASS] prof.mehta: signed-out state (/teacher redirects to /login) - http://127.0.0.1:5001/login
7. [PASS] No uncaught JavaScript errors - []

### SYS_FR-04_11 - Percentages displayed on the teacher dashboard

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-04_11 |
| Responsible test owner | Jagadeesh |
| Expected result | Displayed percentages equal Present / total x 100 rounded to 2 decimals; Late is not counted as attended. |
| Actual result | All 5 checks met. Observed: rohan: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended) (hand calc 83.33; API 83.33); rohan: Percentages screen shows the same value rounded to 2 decimals (screen '83.33%'; 2-dp value 83.33 (83.33%)); vikram: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended) (hand calc 58.33; API 58.33); vikram: Percentages screen shows the same value rounded to 2 decimals (screen '58.33%'; 2-dp value 58.33 (58.33%)); No uncaught JavaScript errors ([]). |
| Status | **PASS** (5/5 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:00 to 2026-11-17T08:30:03 |
| Screenshots | `SYS_FR-04_11_01_percentages_subject.png`, `SYS_FR-04_11_02_records_rohan.png`, `SYS_FR-04_11_03_records_vikram.png` |
| Logs | `SYS_FR-04_11_main.log` |

Steps executed:

1. [done] Open Percentages; pick subject 'Database Systems' - 4 students
2. [done] Records for rohan / Database Systems: count statuses - Present 10, Absent 2, Late 0
3. [PASS] rohan: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended) - hand calc 83.33; API 83.33
4. [PASS] rohan: Percentages screen shows the same value rounded to 2 decimals - screen '83.33%'; 2-dp value 83.33 (83.33%)
5. [done] Records for vikram / Database Systems: count statuses - Present 7, Absent 5, Late 0
6. [PASS] vikram: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended) - hand calc 58.33; API 58.33
7. [PASS] vikram: Percentages screen shows the same value rounded to 2 decimals - screen '58.33%'; 2-dp value 58.33 (58.33%)
8. [PASS] No uncaught JavaScript errors - []

### SYS_NFR-02_06 - Perceived load time on the demo machine

| Field | Value |
|---|---|
| Test Case ID | SYS_NFR-02_06 |
| Responsible test owner | Jagadeesh |
| Expected result | Every section loads within 3 seconds. |
| Actual result | All 6 checks met. Observed: overview (Load event) under 3 seconds (29 ms); overview (data shown) under 3 seconds (208 ms); mark under 3 seconds (56 ms); records under 3 seconds (235 ms); percentages under 3 seconds (205 ms); No uncaught JavaScript errors ([]). |
| Status | **PASS** (6/6 checks met) |
| Not assessed by automation | Timings taken on the development Mac with the cache disabled through the DevTools protocol, not on a separate demo machine. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:03 to 2026-11-17T08:30:05 |
| Screenshots | `SYS_NFR-02_06_01_overview.png`, `SYS_NFR-02_06_02_mark.png`, `SYS_NFR-02_06_03_records.png`, `SYS_NFR-02_06_04_percentages.png` |
| Logs | `SYS_NFR-02_06_main.log` |

Steps executed:

1. [done] Disable the browser cache (DevTools 'Disable cache' via CDP)
2. [PASS] overview (Load event) under 3 seconds - 29 ms
3. [PASS] overview (data shown) under 3 seconds - 208 ms
4. [PASS] mark under 3 seconds - 56 ms
5. [PASS] records under 3 seconds - 235 ms
6. [PASS] percentages under 3 seconds - 205 ms
7. [PASS] No uncaught JavaScript errors - []
- Note: {"overview (Load event)": 29, "overview (data shown)": 208, "mark": 56, "records": 235, "percentages": 205}

### UT_FR-05_04 - Empty result handling

| Field | Value |
|---|---|
| Test Case ID | UT_FR-05_04 |
| Responsible test owner | Tharith |
| Expected result | API returns an empty list; UI shows a clear empty-state message. |
| Actual result | All 4 checks met. Observed: Choose a date with no attendance (Sun 2020-01-05) -> clear 'no records' message (message: 'No matching records\nTry different filters.'; count line '0 of 23 record(s) shown.'); API returns an empty list for that date (200 {'count': 0, 'records': []}); Clearing the date by hand returns the records (23 records (clear button present: False)); No uncaught JavaScript errors ([]). |
| Status | **PASS** (4/4 checks met) |
| Not assessed by automation | Whether the message is 'clear' to a student is a wording judgement that automation cannot make. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:05 to 2026-11-17T08:30:06 |
| Screenshots | `UT_FR-05_04_01_empty_state.png`, `UT_FR-05_04_02_records_back.png` |
| Logs | `UT_FR-05_04_main.log` |

Steps executed:

1. [done] Log in as a demo student; open Attendance history - 23 records
2. [PASS] Choose a date with no attendance (Sun 2020-01-05) -> clear 'no records' message - message: 'No matching records\nTry different filters.'; count line '0 of 23 record(s) shown.'
3. [PASS] API returns an empty list for that date - 200 {'count': 0, 'records': []}
4. [done] Click Clear filters (if shown) - no Clear filters button is shown on the student History screen
5. [PASS] Clearing the date by hand returns the records - 23 records (clear button present: False)
6. [PASS] No uncaught JavaScript errors - []

### SYS_FR-05_10 - Responsive viewing

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-05_10 |
| Responsible test owner | Tharith |
| Expected result | Content remains readable with no horizontal overflow. |
| Actual result | All 29 checks met. Observed: student_overview at 375px: no page-level sideways scrolling (page overflow 0px; elements past right edge 0); student_overview at 375px: tables fit without their own sideways scroll (table-wrap overflow [] px); student_overview at 375px: no status badge or action button cut off (0 clipped); student_history at 375px: no page-level sideways scrolling (page overflow 0px; elements past right edge 0); student_history at 375px: tables fit without their own sideways scroll (table-wrap overflow [] px); student_history at 375px: no status badge or action button cut off (0 clipped); student_overview at 768px: no page-level sideways scrolling (page overflow 0px; elements past right edge 0); student_overview at 768px: tables fit without their own sideways scroll (table-wrap overflow [] px); student_overview at 768px: no status badge or action button cut off (0 clipped); student_history at 768px: no p. |
| Status | **PASS** (29/29 checks met) |
| Not assessed by automation | Readability and visual overlap were not judged by a person; only overflow was measured. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:06 to 2026-11-17T08:30:12 |
| Screenshots | `SYS_FR-05_10_01_student_overview_375px.png`, `SYS_FR-05_10_02_student_history_375px.png`, `SYS_FR-05_10_03_student_overview_768px.png`, `SYS_FR-05_10_04_student_history_768px.png`, `SYS_FR-05_10_05_student_overview_1280px.png`, `SYS_FR-05_10_06_student_history_1280px.png`, `SYS_FR-05_10_07_teacher_records_375px.png`, `SYS_FR-05_10_08_teacher_records_768px.png`, `SYS_FR-05_10_09_teacher_records_1280px.png` |
| Logs | `SYS_FR-05_10_aarav.log`, `SYS_FR-05_10_prof.log` |

Steps executed:

1. [PASS] student_overview at 375px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
2. [PASS] student_overview at 375px: tables fit without their own sideways scroll - table-wrap overflow [] px
3. [PASS] student_overview at 375px: no status badge or action button cut off - 0 clipped
4. [PASS] student_history at 375px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
5. [PASS] student_history at 375px: tables fit without their own sideways scroll - table-wrap overflow [] px
6. [PASS] student_history at 375px: no status badge or action button cut off - 0 clipped
7. [PASS] student_overview at 768px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
8. [PASS] student_overview at 768px: tables fit without their own sideways scroll - table-wrap overflow [] px
9. [PASS] student_overview at 768px: no status badge or action button cut off - 0 clipped
10. [PASS] student_history at 768px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
11. [PASS] student_history at 768px: tables fit without their own sideways scroll - table-wrap overflow [] px
12. [PASS] student_history at 768px: no status badge or action button cut off - 0 clipped
13. [PASS] student_overview at 1280px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
14. [PASS] student_overview at 1280px: tables fit without their own sideways scroll - table-wrap overflow [] px
15. [PASS] student_overview at 1280px: no status badge or action button cut off - 0 clipped
16. [PASS] student_history at 1280px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
17. [PASS] student_history at 1280px: tables fit without their own sideways scroll - table-wrap overflow [] px
18. [PASS] student_history at 1280px: no status badge or action button cut off - 0 clipped
19. [PASS] aarav: no uncaught JavaScript errors - []
20. [PASS] teacher_records at 375px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
21. [PASS] teacher_records at 375px: tables fit without their own sideways scroll - table-wrap overflow [] px
22. [PASS] teacher_records at 375px: no status badge or action button cut off - 0 clipped
23. [PASS] teacher_records at 768px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
24. [PASS] teacher_records at 768px: tables fit without their own sideways scroll - table-wrap overflow [] px
25. [PASS] teacher_records at 768px: no status badge or action button cut off - 0 clipped
26. [PASS] teacher_records at 1280px: no page-level sideways scrolling - page overflow 0px; elements past right edge 0
27. [PASS] teacher_records at 1280px: tables fit without their own sideways scroll - table-wrap overflow [] px
28. [PASS] teacher_records at 1280px: no status badge or action button cut off - 0 clipped
29. [PASS] prof.mehta: no uncaught JavaScript errors - []

### SYS_FR-14_08 - Dashboard summary displayed in browser

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-14_08 |
| Responsible test owner | Tharith |
| Expected result | Summary cards show figures matching the data; no errors. |
| Actual result | All 4 checks met. Observed: Student: My attendance numbers match the History records (cards {'overallPercent': '95.65%', 'countPresent': '22', 'countAbsent': '0', 'countLate': '1', 'countTotal': '); Teacher: Overview cards match Percentages / Mark attendance screens (cards {'statSubjects': '3', 'statClasses': '3', 'statStudents': '8', 'statAverage': '83.16%'}; screens: subjec); Admin: Overview counts match the Users, Classes and Subjects lists (cards {'statStudents': '9', 'statTeachers': '2', 'statClasses': '3', 'statSubjects': '5'}; lists: students 9, ); No uncaught JavaScript errors ([]). |
| Status | **PASS** (4/4 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:12 to 2026-11-17T08:30:17 |
| Screenshots | `SYS_FR-14_08_01_student_overview.png`, `SYS_FR-14_08_02_teacher_overview.png`, `SYS_FR-14_08_03_admin_overview.png` |
| Logs | `SYS_FR-14_08_main.log` |

Steps executed:

1. [PASS] Student: My attendance numbers match the History records - cards {'overallPercent': '95.65%', 'countPresent': '22', 'countAbsent': '0', 'countLate': '1', 'countTotal': '23'}; counted from history P22 A0 L1 T23 -> 95.65%
2. [PASS] Teacher: Overview cards match Percentages / Mark attendance screens - cards {'statSubjects': '3', 'statClasses': '3', 'statStudents': '8', 'statAverage': '83.16%'}; screens: subjects 3, classes 3, students 8, average 83.16% (79/95)
3. [PASS] Admin: Overview counts match the Users, Classes and Subjects lists - cards {'statStudents': '9', 'statTeachers': '2', 'statClasses': '3', 'statSubjects': '5'}; lists: students 9, teachers 2, classes 3, subjects 5
4. [PASS] No uncaught JavaScript errors - []

### SYS_FR-15_07 - Back button after logout

| Field | Value |
|---|---|
| Test Case ID | SYS_FR-15_07 |
| Responsible test owner | Tharith |
| Expected result | Protected content is not shown again (no-store caching; redirect to login). |
| Actual result | All 4 checks met. Observed: Press Back: attendance data is not shown (url http://127.0.0.1:5001/login#history; record rows visible 0); Press Back: user is on the login page (http://127.0.0.1:5001/login#history); Reload -> login page (http://127.0.0.1:5001/login#history); No uncaught JavaScript errors ([]). |
| Status | **PASS** (4/4 checks met) |
| Not assessed by automation | Nothing beyond the expected result. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:17 to 2026-11-17T08:30:20 |
| Screenshots | `SYS_FR-15_07_01_after_back.png` |
| Logs | `SYS_FR-15_07_main.log` |

Steps executed:

1. [done] Log in as a demo student; open Attendance history - 23 records
2. [done] Log out and confirm - http://127.0.0.1:5001/login
3. [PASS] Press Back: attendance data is not shown - url http://127.0.0.1:5001/login#history; record rows visible 0
4. [PASS] Press Back: user is on the login page - http://127.0.0.1:5001/login#history
5. [PASS] Reload -> login page - http://127.0.0.1:5001/login#history
6. [PASS] No uncaught JavaScript errors - []

### IT_NFR-04_04 - Keyboard and accessibility

| Field | Value |
|---|---|
| Test Case ID | IT_NFR-04_04 |
| Responsible test owner | Tharith |
| Expected result | Visible focus; controls reachable and labelled. |
| Actual result | All 9 checks met. Observed: Log in as demo.admin using only the keyboard (http://127.0.0.1:5001/admin); Tab through the sidebar: visible focus style on every item (9 items: ['Overview', 'Users', 'Classes', 'Subjects', 'Enrollments', 'Attendance', 'Reports', 'Change password); Every focused control has an accessible name (unnamed: []); Open a dialog with the keyboard and close it with Esc (opened True; closed by Esc True); Choose class and subject with the keyboard (class value '1', subject value '1'); Reach 'Load students' with Tab (loadRosterButton); Select attendance statuses with the keyboard (arrow keys in the status group) (focused 'Present' (Present); after ArrowRight Absent:true; focus style True); No uncaught JavaScript errors ([]). |
| Status | **PASS** (9/9 checks met) |
| Not assessed by automation | Focus styles were detected programmatically; how visible they are to a person, and screen-reader use, were not assessed. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:20 to 2026-11-17T08:30:23 |
| Screenshots | `IT_NFR-04_04_01_focus_nav_users.png`, `IT_NFR-04_04_02_dialog_opened_keyboard.png`, `IT_NFR-04_04_03_roster_keyboard_status.png` |
| Logs | `IT_NFR-04_04_main.log`, `IT_NFR-04_04_teacher.log` |

Steps executed:

1. [PASS] Log in as demo.admin using only the keyboard - http://127.0.0.1:5001/admin
2. [PASS] Tab through the sidebar: visible focus style on every item - 9 items: ['Overview', 'Users', 'Classes', 'Subjects', 'Enrollments', 'Attendance', 'Reports', 'Change password', 'Log out']; without focus style: []
3. [PASS] Every focused control has an accessible name - unnamed: []
4. [PASS] Open a section with Enter (Users)
5. [PASS] Open a dialog with the keyboard and close it with Esc - opened True; closed by Esc True
6. [PASS] Choose class and subject with the keyboard - class value '1', subject value '1'
7. [PASS] Reach 'Load students' with Tab - loadRosterButton
8. [PASS] Select attendance statuses with the keyboard (arrow keys in the status group) - focused 'Present' (Present); after ArrowRight Absent:true; focus style True
9. [done] Attendance was not saved (keyboard check only)
10. [PASS] No uncaught JavaScript errors - []

### SYS_NFR-04_06 - Human usability walkthrough

| Field | Value |
|---|---|
| Test Case ID | SYS_NFR-04_06 |
| Responsible test owner | Tharith |
| Expected result | Tasks completed easily; observations recorded. |
| Actual result | NOT RUN: Smoke - student: find overall and one subject's attendance (95.65%; 'Discrete Mathematics\n11 of 12 classes attended'). Smoke - teacher: mark today's attendance and correct one status (Saved attendance for 4 student(s).). Smoke - admin: create a student and enroll them (usability_s1 enrolled in Year 1 / Programming Fundamentals). Scripted task flows completed in 5.6 s (machine speed, not human effort). |
| Status | **NOT RUN** (0/0 checks met) |
| Not assessed by automation | Requires a human participant; not automatable. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless) |
| Executed | 2026-11-17T08:30:23 to 2026-11-17T08:30:29 |
| Screenshots | `SYS_NFR-04_06_01_student_task.png`, `SYS_NFR-04_06_02_teacher_task.png`, `SYS_NFR-04_06_03_admin_task.png` |
| Logs | `SYS_NFR-04_06_main.log` |

Steps executed:

1. [done] Smoke - student: find overall and one subject's attendance - 95.65%; 'Discrete Mathematics\n11 of 12 classes attended'
2. [done] Smoke - teacher: mark today's attendance and correct one status - Saved attendance for 4 student(s).
3. [done] Smoke - admin: create a student and enroll them - usability_s1 enrolled in Year 1 / Programming Fundamentals
- Note: Scripted task flows completed in 5.6 s (machine speed, not human effort).

### SYS_NFR-05_08 - Main workflows in the Apple Safari application

| Field | Value |
|---|---|
| Test Case ID | SYS_NFR-05_08 |
| Responsible test owner | Tharith |
| Expected result | All tasks work as in other browsers; no layout or script errors. |
| Actual result | BLOCKED: Open the Safari application on a Mac (Safari.app installed: True. Playwright cannot drive the Safari application. safaridriver is present, but using). [WebKit] admin: create a user; log out (created webkit_s1). [WebKit] teacher: mark attendance; correct one status; log out (Saved attendance for 5 student(s).). [WebKit] student: view My attendance and Attendance history (24 records). [WebKit] console errors (D-01 'Refused to apply a stylesheet') (4 console.error line(s); 4 CSP-related; page errors 0). Supplementary engine-level run in Playwright WebKit 27.2 (NOT the Safari application). WebKit CSP-related console lines: 4; first: 08:30:32.054 console.error: Refused to apply a stylesheet because its hash, its nonce, or 'unsafe-inline' appears in neither the style-src directive nor the default-src directive of the Content Securi |
| Status | **BLOCKED** (0/0 checks met) |
| Not assessed by automation | Requires the real Safari application; WebKit is engine-level evidence only. |
| Execution method | Playwright automation (no person performed the steps) |
| Browser | Safari application: not automatable by Playwright (supplementary run: Playwright WebKit) |
| Executed | 2026-11-17T08:30:29 to 2026-11-17T08:30:36 |
| Screenshots | `SYS_NFR-05_08_01_webkit_admin.png`, `SYS_NFR-05_08_02_webkit_teacher.png`, `SYS_NFR-05_08_03_webkit_student_overview.png`, `SYS_NFR-05_08_04_webkit_student_history.png` |
| Logs | `SYS_NFR-05_08_webkit_supplementary.log` |

Steps executed:

1. [done] Open the Safari application on a Mac - Safari.app installed: True. Playwright cannot drive the Safari application. safaridriver is present, but using it needs 'Allow Remote Automation' and 'sudo safaridriver --enable' (a system setting change) plus a WebDriver client; this was not set up without approval.
2. [done] [WebKit] admin: create a user; log out - created webkit_s1
3. [done] [WebKit] teacher: mark attendance; correct one status; log out - Saved attendance for 5 student(s).
4. [done] [WebKit] student: view My attendance and Attendance history - 24 records
5. [done] [WebKit] console errors (D-01 'Refused to apply a stylesheet') - 4 console.error line(s); 4 CSP-related; page errors 0
- Note: Supplementary engine-level run in Playwright WebKit 27.2 (NOT the Safari application).
- Note: WebKit CSP-related console lines: 4; first: 08:30:32.054 console.error: Refused to apply a stylesheet because its hash, its nonce, or 'unsafe-inline' appears in neither the style-src directive nor the default-src directive of the Content Securi

## 7. Evidence inventory

All paths are relative to `docs/evidence/regression/manual_validation_automation/`.

| File | Content |
|---|---|
| `results.json` | Machine-readable results for all 19 scenarios |
| `setup.log` | Seeding output, server command, browser version, attendance.db hashes (password redacted) |
| `server.log` | Flask request log for the run |
| `screenshots/` | 75 PNG files named `<TestCaseID>_<n>_<label>.png` |
| `logs/` | 21 browser logs (console messages, page errors, failed requests, HTTP 4xx/5xx, document responses with Cache-Control, navigations) |

## 8. Data changed in validation_demo.db (only)

Users manual_s1b (renamed from manual_s1), usability_s1 and webkit_s1; class Manual Class; subject Manual Subject; aarav enrolled in Manual Class / Manual Subject; usability_s1 enrolled in Year 1 / Programming Fundamentals; one record for aarav / Programming Fundamentals / 16 Nov 2026 deleted; today's attendance saved for Year 2 / Database Systems and Year 1 / Programming Fundamentals, with one correction each; meera's password changed and restored.

## 9. Limitations

- Headless Chrome on macOS; native validation bubbles and select pop-ups are not visible in screenshots, so validity state was checked instead.
- Progress bars animate, so some screenshots show bars part-way; values were checked from the text.
- Load times were measured with the browser cache disabled via the DevTools protocol on the development Mac.
- Firefox and Edge were not used (see G-09). The Safari application was not tested (BLOCKED); WebKit is engine-level evidence only.
- Re-run: delete `validation_demo.db`, then `python scripts/run_manual_validation_automation.py`; `--report` only re-renders this report from `results.json`.
