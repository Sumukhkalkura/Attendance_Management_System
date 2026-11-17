# Manual Validation Checklist - Jagadeesh

| Item | Details |
|---|---|
| Assigned team member | Jagadeesh |
| Scope | Teacher dashboard, attendance marking, editing and deletion, percentage calculations, attendance filtering, low-attendance alerts, performance, teacher session logout. |
| Test cases | 7 (7 PASS) |
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
| 1 | SYS_FR-01_08 | FR-01 | Logout | PASS | - |
| 2 | SYS_FR-03_13 | FR-03 | Edit and delete through teacher dashboard | PASS | - |
| 3 | SYS_FR-10_10 | FR-10 | Search and filter in the dashboards | PASS | MV-01 |
| 4 | SYS_FR-11_10 | FR-11 | Alerts shown on dashboards | PASS | - |
| 5 | SYS_FR-15_06 | FR-15 | Logout button on every dashboard | PASS | - |
| 6 | SYS_FR-04_11 | FR-04 | Percentages displayed on the teacher dashboard | PASS | MV-02 |
| 7 | SYS_NFR-02_06 | NFR-02 | Perceived load time on the demo machine | PASS | - |

## Test case records

### 1. SYS_FR-01_08 - Logout

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-01_08 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | System |
| Test scenario | Logout |
| Assigned team member | Jagadeesh |
| Preconditions | User logged in |
| Test data | Teacher account |
| Test steps | 1. Log in as prof.mehta (teacher).<br>2. Open Attendance records.<br>3. Click Log out and confirm.<br>4. Press the browser Back button twice.<br>5. Check whether any attendance data is shown, then reload the page.<br>6. Type http://127.0.0.1:5001/teacher in the address bar and press Enter. |
| Expected result | Protected pages cannot be reopened: page requests redirect to /login, API requests return 401. Responses carry Cache-Control: no-store. |
| Actual observed result | All 7 checks met. Observed: Press Back (1): no attendance data shown (url http://127.0.0.1:5001/login#records; record rows visible 0); Press Back (2): no attendance data shown (url http://127.0.0.1:5001/login; record rows visible 0); Reload the page -> login page (http://127.0.0.1:5001/login); Type /teacher in the address bar -> redirected to /login (http://127.0.0.1:5001/login); API request after logout returns 401 (status 401; body {'error': 'Authentication required'}); Responses carry Cache-Control: no-store (/teacher 'no-store'; /api/attendance 'no-store'); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-01_08_01_records_before_logout.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-01_08_02_after_back_1.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-01_08_03_after_back_2.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-01_08_04_teacher_url_redirected.png` |
| Supporting evidence | Executed 2026-11-17 08:29:38 to 08:29:43 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 7 of 7 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-01_08_main.log`<br>Automated test reference: `test_fr15_logout::test_protected_route_after_logout`, `test_nfr01_security::test_security_headers`, `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 2. SYS_FR-03_13 - Edit and delete through teacher dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-03_13 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | System |
| Test scenario | Edit and delete through teacher dashboard |
| Assigned team member | Jagadeesh |
| Preconditions | Teacher logged in to browser; records exist |
| Test data | Seeded records |
| Test steps | 1. Log in as prof.mehta; open Attendance records.<br>2. Pick a record; click Correct status; change it to Late; save.<br>3. Check the table shows Late.<br>4. Click delete on the same record; check a confirmation dialog appears; click Cancel.<br>5. Check the record is still there.<br>6. Delete again and confirm; check the record disappears and a message is shown. |
| Expected result | Edited status shown; deleted record removed from the table after confirmation. |
| Actual observed result | All 5 checks met. Observed: Correct status -> Late; table shows Late (toast 'Attendance record updated.'; row ['Mon, Nov 16, 2026', 'A\naarav', 'Programming Fundamentals', 'Late', ); Click delete -> confirmation dialog appears ('Delete this record?': "aarav's Late record for Programming Fundamentals on Mon, Nov 16, 2026 will be permanen); Delete and confirm -> record disappears and a message is shown (toast 'Attendance record deleted.'; rows 96 -> 95); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-03_13_01_status_corrected.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-03_13_02_delete_confirm.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-03_13_03_record_deleted.png` |
| Supporting evidence | Executed 2026-11-17 08:29:43 to 08:29:46 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 5 of 5 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-03_13_main.log`<br>Automated test reference: `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 3. SYS_FR-10_10 - Search and filter in the dashboards

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-10_10 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | System |
| Test scenario | Search and filter in the dashboards |
| Assigned team member | Jagadeesh |
| Preconditions | Teacher/admin/student logged in to browser |
| Test data | Seeded records |
| Test steps | 1. Log in as prof.mehta; open Attendance records.<br>2. Type a student name in the search box.<br>3. Choose a subject, then a date, then a status; check the table updates each time.<br>4. Click Clear filters; check every filter is reset and all rows return.<br>5. Choose a class in the Class filter, then a From and a To date; check the table updates each time.<br>6. Click Clear filters again; check all rows return.<br>7. Repeat the subject/date/status filters and Clear filters as demo.admin in Attendance. |
| Expected result | Table updates to matching rows; 'Clear filters' restores all rows. |
| Actual observed result | All 14 checks met. Observed: Search 'kabir' -> only kabir's rows (12 rows); Subject filter 'Database Systems' -> table updates (48 rows); Then date 2026-11-16 -> table updates (4 rows); Then status Present -> table updates (4 rows); Click 'Clear filters' -> every filter reset and all rows restored (95 rows (all = 95); filter values after clearing ['', '', '', '', '', '', '']); Class filter 'BSc Computer Science - Year 1' -> table matches the API (47 rows (API 47)); Date range 2026-10-30 to 2026-11-03 (with class filter) -> table matches the API (12 rows (API 12)); Admin: subject filter 'Database Systems' (48 rows); Admin: date 2026-11-16 (4 rows); Admin: status Absent (0 rows); Admin: 'Clear filters' restores all rows (191 rows (all = 191)); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-10_10_01_teacher_search.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-10_10_02_teacher_filters.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-10_10_03_teacher_cleared.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-10_10_04_teacher_class_and_range.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-10_10_05_admin_filters.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-10_10_06_admin_cleared.png` |
| Supporting evidence | Executed 2026-11-17 08:29:46 to 08:29:52 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 14 of 14 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-10_10_main.log` |
| Defect / gap ID | MV-01 |
| Result history | 2026-11-17 manual validation run: FAIL; 2026-11-17 regression run: PASS (changed) |

### 4. SYS_FR-11_10 - Alerts shown on dashboards

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-11_10 |
| Requirement | FR-11 - Attendance Alert |
| Test level | System |
| Test scenario | Alerts shown on dashboards |
| Assigned team member | Jagadeesh |
| Preconditions | Teacher/admin logged in to browser |
| Test data | Student below 75% |
| Test steps | 1. Log in as prof.mehta; open Overview.<br>2. Look at 'Students needing attention'.<br>3. Compare the listed students with Percentages: every student below 75% must be listed, none at or above 75%.<br>4. If nobody is below 75%, mark a student Absent on several dates in Mark attendance, then reload Overview.<br>5. Repeat as demo.admin on Overview.<br>6. Record that there is no screen to change the 75% threshold (known gap G-04). |
| Expected result | Low-attendance students listed; 'Everyone is on track' when none. |
| Actual observed result | All 3 checks met. Observed: prof.mehta: every student below 75% is listed, none at/above 75% (below 75% on Percentages: {'kabir': 58.33, 'vikram': 58.33}; listed: ['kabir', 'vikram'] (overview shows at mo); demo.admin: every student below 75% is listed, none at/above 75% (below 75% on Percentages: {'kabir': 70.83, 'vikram': 50.0}; listed: ['kabir', 'vikram'] (overview shows at mos); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-11_10_01_prof_overview_alerts.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-11_10_02_prof_percentages.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-11_10_03_demo_overview_alerts.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-11_10_04_demo_percentages.png` |
| Supporting evidence | Executed 2026-11-17 08:29:52 to 08:29:56 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 3 of 3 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-11_10_main.log` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 5. SYS_FR-15_06 - Logout button on every dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-15_06 |
| Requirement | FR-15 - Logout |
| Test level | System |
| Test scenario | Logout button on every dashboard |
| Assigned team member | Jagadeesh |
| Preconditions | Each role logged in to browser |
| Test data | - |
| Test steps | 1. Log in as demo.admin; click Log out; confirm.<br>2. Check you are on the login page.<br>3. Repeat as a demo student.<br>4. Repeat as prof.mehta. |
| Expected result | Returned to /login with a signed-out state. |
| Actual observed result | All 7 checks met. Observed: demo.admin: Log out + confirm -> login page (http://127.0.0.1:5001/login); demo.admin: signed-out state (/admin redirects to /login) (http://127.0.0.1:5001/login); aarav: Log out + confirm -> login page (http://127.0.0.1:5001/login); aarav: signed-out state (/student redirects to /login) (http://127.0.0.1:5001/login); prof.mehta: Log out + confirm -> login page (http://127.0.0.1:5001/login); prof.mehta: signed-out state (/teacher redirects to /login) (http://127.0.0.1:5001/login); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-15_06_01_demo_logged_out.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-15_06_02_aarav_logged_out.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-15_06_03_prof_logged_out.png` |
| Supporting evidence | Executed 2026-11-17 08:29:56 to 08:30:00 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 7 of 7 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-15_06_main.log`<br>Automated test reference: `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 6. SYS_FR-04_11 - Percentages displayed on the teacher dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-04_11 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | System |
| Test scenario | Percentages displayed on the teacher dashboard |
| Assigned team member | Jagadeesh |
| Preconditions | Teacher logged in to browser; records exist |
| Test data | Seeded demo data |
| Test steps | 1. Log in as prof.mehta; open Percentages.<br>2. Pick one student and one subject.<br>3. In Attendance records filter by that student and subject; count Present, Absent and Late.<br>4. Calculate Present / (Present + Absent + Late) x 100, rounded to 2 decimals.<br>5. Check the Percentages screen shows the same value (Late does not count as attended).<br>6. Repeat for a second student. |
| Expected result | Displayed percentages equal Present / total x 100 rounded to 2 decimals; Late is not counted as attended. |
| Actual observed result | All 5 checks met. Observed: rohan: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended) (hand calc 83.33; API 83.33); rohan: Percentages screen shows the same value rounded to 2 decimals (screen '83.33%'; 2-dp value 83.33 (83.33%)); vikram: backend percentage = Present/(P+A+L)x100 to 2 dp (Late not attended) (hand calc 58.33; API 58.33); vikram: Percentages screen shows the same value rounded to 2 decimals (screen '58.33%'; 2-dp value 58.33 (58.33%)); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-04_11_01_percentages_subject.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-04_11_02_records_rohan.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-04_11_03_records_vikram.png` |
| Supporting evidence | Executed 2026-11-17 08:30:00 to 08:30:03 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 5 of 5 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-04_11_main.log` |
| Defect / gap ID | MV-02 |
| Result history | 2026-11-17 manual validation run: FAIL; 2026-11-17 regression run: PASS (changed) |

### 7. SYS_NFR-02_06 - Perceived load time on the demo machine

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-02_06 |
| Requirement | NFR-02 - Performance |
| Test level | System |
| Test scenario | Perceived load time on the demo machine |
| Assigned team member | Jagadeesh |
| Preconditions | Demo data seeded (scripts/seed_demo_data.py) |
| Test data | Teacher account |
| Test steps | 1. Open the browser DevTools (F12) and the Network tab; tick 'Disable cache'.<br>2. Log in as prof.mehta.<br>3. Reload Overview; note the 'Load' time at the bottom of the Network tab.<br>4. Open Mark attendance, Attendance records and Percentages; note the time until data appears.<br>5. Record each time; all must be under 3 seconds. |
| Expected result | Every section loads within 3 seconds. |
| Actual observed result | All 6 checks met. Observed: overview (Load event) under 3 seconds (29 ms); overview (data shown) under 3 seconds (208 ms); mark under 3 seconds (56 ms); records under 3 seconds (235 ms); percentages under 3 seconds (205 ms); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-02_06_01_overview.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-02_06_02_mark.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-02_06_03_records.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-02_06_04_percentages.png` |
| Supporting evidence | Executed 2026-11-17 08:30:03 to 08:30:05 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 6 of 6 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_NFR-02_06_main.log` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

*Not assessed by the automated execution:* Timings taken on the development Mac with the cache disabled through the DevTools protocol, not on a separate demo machine.

