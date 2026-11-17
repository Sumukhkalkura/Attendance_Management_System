# Manual Validation Checklist - Tharith

| Item | Details |
|---|---|
| Assigned team member | Tharith |
| Scope | Student dashboard, attendance viewing, dashboard summaries, frontend usability, responsive design, browser compatibility, student session logout. |
| Test cases | 7 (5 PASS, 1 BLOCKED, 1 NOT RUN) |
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
| 1 | UT_FR-05_04 | FR-05 | Empty result handling | PASS | - |
| 2 | SYS_FR-05_10 | FR-05 | Responsive viewing | PASS | MV-03 |
| 3 | SYS_FR-14_08 | FR-14 | Dashboard summary displayed in browser | PASS | - |
| 4 | SYS_FR-15_07 | FR-15 | Back button after logout | PASS | - |
| 5 | IT_NFR-04_04 | NFR-04 | Keyboard and accessibility | PASS | - |
| 6 | SYS_NFR-04_06 | NFR-04 | Human usability walkthrough | NOT RUN | - |
| 7 | SYS_NFR-05_08 | NFR-05 | Main workflows in the Apple Safari application | BLOCKED | G-09 |

## Test case records

### 1. UT_FR-05_04 - Empty result handling

| Field | Details |
|---|---|
| Test Case ID | UT_FR-05_04 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Unit |
| Test scenario | Empty result handling |
| Assigned team member | Tharith |
| Preconditions | No matching records |
| Test data | Nonexistent date |
| Test steps | 1. Log in as a demo student; open Attendance history.<br>2. Choose a date on which you have no attendance (e.g. a Sunday far in the past).<br>3. Check that a clear message says there are no records (not an empty table without explanation).<br>4. Click Clear filters (if shown) and check records return. |
| Expected result | API returns an empty list; UI shows a clear empty-state message. |
| Actual observed result | All 4 checks met. Observed: Choose a date with no attendance (Sun 2020-01-05) -> clear 'no records' message (message: 'No matching records\nTry different filters.'; count line '0 of 23 record(s) shown.'); API returns an empty list for that date (200 {'count': 0, 'records': []}); Clearing the date by hand returns the records (23 records (clear button present: False)); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/UT_FR-05_04_01_empty_state.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/UT_FR-05_04_02_records_back.png` |
| Supporting evidence | Executed 2026-11-17 08:30:05 to 08:30:06 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 4 of 4 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/UT_FR-05_04_main.log`<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_empty_results` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

*Not assessed by the automated execution:* Whether the message is 'clear' to a student is a wording judgement that automation cannot make.

### 2. SYS_FR-05_10 - Responsive viewing

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-05_10 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | System |
| Test scenario | Responsive viewing |
| Assigned team member | Tharith |
| Preconditions | Supported browser/device |
| Test data | Desktop/mobile widths |
| Test steps | 1. Log in as a demo student.<br>2. Open DevTools device toolbar (Ctrl/Cmd+Shift+M).<br>3. View My attendance and Attendance history at 375 px, 768 px and 1280 px wide.<br>4. At each width check that text is readable, nothing overlaps, and no sideways scrolling is needed.<br>5. Repeat for the teacher Attendance records screen. |
| Expected result | Content remains readable with no horizontal overflow. |
| Actual observed result | All 29 checks met. Observed: student_overview at 375px: no page-level sideways scrolling (page overflow 0px; elements past right edge 0); student_overview at 375px: tables fit without their own sideways scroll (table-wrap overflow [] px); student_overview at 375px: no status badge or action button cut off (0 clipped); student_history at 375px: no page-level sideways scrolling (page overflow 0px; elements past right edge 0); student_history at 375px: tables fit without their own sideways scroll (table-wrap overflow [] px); student_history at 375px: no status badge or action button cut off (0 clipped); student_overview at 768px: no page-level sideways scrolling (page overflow 0px; elements past right edge 0); student_overview at 768px: tables fit without their own sideways scroll (table-wrap overflow [] px); student_overview at 768px: no status badge or action button cut off (0 clipped); student_history at 768px: no p. |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_01_student_overview_375px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_02_student_history_375px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_03_student_overview_768px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_04_student_history_768px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_05_student_overview_1280px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_06_student_history_1280px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_07_teacher_records_375px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_08_teacher_records_768px.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-05_10_09_teacher_records_1280px.png` |
| Supporting evidence | Executed 2026-11-17 08:30:06 to 08:30:12 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 29 of 29 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-05_10_aarav.log`, `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-05_10_prof.log`<br>Automated test reference: `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chrome]`, `test_nfr04_usability::test_nfr04_interface_supports_responsive_layout` |
| Defect / gap ID | MV-03 |
| Result history | 2026-11-17 manual validation run: FAIL; 2026-11-17 regression run: PASS (changed) |

*Not assessed by the automated execution:* Readability and visual overlap were not judged by a person; only overflow was measured.

### 3. SYS_FR-14_08 - Dashboard summary displayed in browser

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-14_08 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | System |
| Test scenario | Dashboard summary displayed in browser |
| Assigned team member | Tharith |
| Preconditions | Each role logged in to browser |
| Test data | Seeded data |
| Test steps | 1. Log in as a demo student; note the numbers on My attendance (overall %, present, absent, total).<br>2. Open Attendance history and count the records yourself; check the numbers match.<br>3. Log in as prof.mehta; check the Overview cards (subjects, classes, students, average) against the Percentages screen.<br>4. Log in as demo.admin; check the Overview counts against the Users, Classes and Subjects lists. |
| Expected result | Summary cards show figures matching the data; no errors. |
| Actual observed result | All 4 checks met. Observed: Student: My attendance numbers match the History records (cards {'overallPercent': '95.65%', 'countPresent': '22', 'countAbsent': '0', 'countLate': '1', 'countTotal': '); Teacher: Overview cards match Percentages / Mark attendance screens (cards {'statSubjects': '3', 'statClasses': '3', 'statStudents': '8', 'statAverage': '83.16%'}; screens: subjec); Admin: Overview counts match the Users, Classes and Subjects lists (cards {'statStudents': '9', 'statTeachers': '2', 'statClasses': '3', 'statSubjects': '5'}; lists: students 9, ); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-14_08_01_student_overview.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-14_08_02_teacher_overview.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-14_08_03_admin_overview.png` |
| Supporting evidence | Executed 2026-11-17 08:30:12 to 08:30:17 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 4 of 4 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-14_08_main.log`<br>Automated test reference: `test_nfr02_browser_performance::test_browser_main_dashboard_overview_renders_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 4. SYS_FR-15_07 - Back button after logout

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-15_07 |
| Requirement | FR-15 - Logout |
| Test level | System |
| Test scenario | Back button after logout |
| Assigned team member | Tharith |
| Preconditions | User logged out in browser |
| Test data | - |
| Test steps | 1. Log in as a demo student; open Attendance history.<br>2. Log out and confirm.<br>3. Press Back.<br>4. Check that attendance data is not shown and you are sent to the login page when you interact or reload. |
| Expected result | Protected content is not shown again (no-store caching; redirect to login). |
| Actual observed result | All 4 checks met. Observed: Press Back: attendance data is not shown (url http://127.0.0.1:5001/login#history; record rows visible 0); Press Back: user is on the login page (http://127.0.0.1:5001/login#history); Reload -> login page (http://127.0.0.1:5001/login#history); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_FR-15_07_01_after_back.png` |
| Supporting evidence | Executed 2026-11-17 08:30:17 to 08:30:20 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 4 of 4 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_FR-15_07_main.log` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

### 5. IT_NFR-04_04 - Keyboard and accessibility

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-04_04 |
| Requirement | NFR-04 - Usability |
| Test level | Integration |
| Test scenario | Keyboard and accessibility |
| Assigned team member | Tharith |
| Preconditions | Dashboards render |
| Test data | Keyboard only |
| Test steps | 1. Log in as demo.admin using only the keyboard (Tab, Shift+Tab, Enter, Space).<br>2. Tab through the sidebar; check a visible focus outline on every item.<br>3. Open each section with Enter; open and close a dialog with the keyboard (Esc closes it).<br>4. Repeat on the teacher Mark attendance screen and select statuses with the keyboard. |
| Expected result | Visible focus; controls reachable and labelled. |
| Actual observed result | All 9 checks met. Observed: Log in as demo.admin using only the keyboard (http://127.0.0.1:5001/admin); Tab through the sidebar: visible focus style on every item (9 items: ['Overview', 'Users', 'Classes', 'Subjects', 'Enrollments', 'Attendance', 'Reports', 'Change password); Every focused control has an accessible name (unnamed: []); Open a dialog with the keyboard and close it with Esc (opened True; closed by Esc True); Choose class and subject with the keyboard (class value '1', subject value '1'); Reach 'Load students' with Tab (loadRosterButton); Select attendance statuses with the keyboard (arrow keys in the status group) (focused 'Present' (Present); after ArrowRight Absent:true; focus style True); No uncaught JavaScript errors ([]). |
| Status | **PASS** |
| Execution method | Manual validation procedure, executed by Playwright browser automation (instructor-approved) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/IT_NFR-04_04_01_focus_nav_users.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/IT_NFR-04_04_02_dialog_opened_keyboard.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/IT_NFR-04_04_03_roster_keyboard_status.png` |
| Supporting evidence | Executed 2026-11-17 08:30:20 to 08:30:23 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 9 of 9 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/IT_NFR-04_04_main.log`, `docs/evidence/regression/manual_validation_automation/logs/IT_NFR-04_04_teacher.log`<br>Automated test reference: `test_nfr04_usability::test_nfr04_navigation_controls_are_accessible`, `test_nfr04_usability::test_nfr04_interface_supports_keyboard_focus` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: PASS; 2026-11-17 regression run: PASS |

*Not assessed by the automated execution:* Focus styles were detected programmatically; how visible they are to a person, and screen-reader use, were not assessed.

### 6. SYS_NFR-04_06 - Human usability walkthrough

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-04_06 |
| Requirement | NFR-04 - Usability |
| Test level | System |
| Test scenario | Human usability walkthrough |
| Assigned team member | Tharith |
| Preconditions | Seeded demo data |
| Test data | One user per role |
| Test steps | 1. Ask a person who has not used the app (or a team member) to do these tasks without help:<br>2. As student: find your overall attendance and your attendance for one subject.<br>3. As teacher: mark attendance for one class today, then correct one status.<br>4. As admin: create a student and enroll them in a class and subject.<br>5. Record time taken, any hesitation or confusion, and their comments. |
| Expected result | Tasks completed easily; observations recorded. |
| Actual observed result | NOT RUN: Smoke - student: find overall and one subject's attendance (95.65%; 'Discrete Mathematics\n11 of 12 classes attended'). Smoke - teacher: mark today's attendance and correct one status (Saved attendance for 4 student(s).). Smoke - admin: create a student and enroll them (usability_s1 enrolled in Year 1 / Programming Fundamentals). Scripted task flows completed in 5.6 s (machine speed, not human effort). |
| Status | **NOT RUN** |
| Execution method | Manual validation procedure; attempted with Playwright browser automation (instructor-approved) but not executable - see actual observed result |
| Execution date | - |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-04_06_01_student_task.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-04_06_02_teacher_task.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-04_06_03_admin_task.png` |
| Supporting evidence | Executed 2026-11-17 08:30:23 to 08:30:29 in Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless); 0 of 0 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_NFR-04_06_main.log` |
| Defect / gap ID | None |
| Result history | 2026-11-17 manual validation run: NOT RUN; 2026-11-17 regression run: NOT RUN |

*Not assessed by the automated execution:* Requires a human participant; not automatable.

### 7. SYS_NFR-05_08 - Main workflows in the Apple Safari application

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_08 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | Main workflows in the Apple Safari application |
| Assigned team member | Tharith |
| Preconditions | Safari on macOS; app running locally (python run.py) |
| Test data | Seeded demo data |
| Test steps | 1. Open the Safari application on a Mac.<br>2. Go to http://127.0.0.1:5001/login.<br>3. Log in as demo.admin; create a user; log out.<br>4. Log in as prof.mehta; mark attendance; correct one status; log out.<br>5. Log in as a demo student; view My attendance and Attendance history.<br>6. Open Safari's Web Inspector (Develop > Show Web Inspector; enable Develop menu in Safari Settings > Advanced) and note any console errors, especially 'Refused to apply a stylesheet' (defect D-01). |
| Expected result | All tasks work as in other browsers; no layout or script errors. |
| Actual observed result | BLOCKED: Open the Safari application on a Mac (Safari.app installed: True. Playwright cannot drive the Safari application. safaridriver is present, but using). [WebKit] admin: create a user; log out (created webkit_s1). [WebKit] teacher: mark attendance; correct one status; log out (Saved attendance for 5 student(s).). [WebKit] student: view My attendance and Attendance history (24 records). [WebKit] console errors (D-01 'Refused to apply a stylesheet') (4 console.error line(s); 4 CSP-related; page errors 0). Supplementary engine-level run in Playwright WebKit 27.2 (NOT the Safari application). WebKit CSP-related console lines: 4; first: 08:30:32.054 console.error: Refused to apply a stylesheet because its hash, its nonce, or 'unsafe-inline' appears in neither the style-src directive nor the default-src directive of the Content Securi |
| Status | **BLOCKED** |
| Execution method | Manual validation procedure; attempted with Playwright browser automation (instructor-approved) but not executable - see actual observed result |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-05_08_01_webkit_admin.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-05_08_02_webkit_teacher.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-05_08_03_webkit_student_overview.png`<br>`docs/evidence/regression/manual_validation_automation/screenshots/SYS_NFR-05_08_04_webkit_student_history.png` |
| Supporting evidence | Executed 2026-11-17 08:30:29 to 08:30:36 in Safari application: not automatable by Playwright (supplementary run: Playwright WebKit); 0 of 0 automated checks met<br>Results: `docs/evidence/regression/manual_validation_automation/results.json`; report: `docs/Manual_Validation_Automation_Report.md`<br>Browser logs: `docs/evidence/regression/manual_validation_automation/logs/SYS_NFR-05_08_webkit_supplementary.log` |
| Defect / gap ID | G-09 |
| Result history | 2026-11-17 manual validation run: BLOCKED; 2026-11-17 regression run: BLOCKED |

*Not assessed by the automated execution:* Requires the real Safari application; WebKit is engine-level evidence only.

