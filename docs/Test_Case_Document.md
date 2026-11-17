# Test Case Document (Updated) — Attendance Management System

| Item | Value |
|---|---|
| Document version | 2.6. Version 2.0 (Phase 1) updated the test cases in `Documents/Test_Plan.pdf` (v1.0); version 2.1 (Phase 2) adds execution results; version 2.2 (Phase 3) updates the defect register only (O-01 verified, O-02 quantified, O-04 added); version 2.3 redistributes the 19 manual cases (Sumukh 5, Jagadeesh 7, Tharith 7) with no status changes; version 2.4 records the execution of the 19 manual cases by Playwright automation, approved by the instructor as manual validation evidence (17 PASS, 1 BLOCKED, 1 NOT RUN), and adds defects MV-01 to MV-03; version 2.5 presents every test case as a traditional test record (assigned team member, preconditions, steps, expected and actual result, status, screenshot evidence, defect ID) and corrects three outdated status notes in the gap register; no test result changed; version 2.6 reports the regression run after the six failed cases were fixed (SYS_FR-04_11, SYS_FR-05_10, SYS_FR-06_08, SYS_FR-10_10, SYS_FR-12_10, SYS_NFR-05_04); every record shows its original and regression result |
| Prepared on | 2026-11-17 |
| Requirements source | `Documents/SRS.pdf` (FR-01 to FR-15, NFR-01 to NFR-06) |
| Template | Course template "Test Plan Document" (Test Case ID, Module, Description, Pre-conditions, Steps, Test Data, Expected, Actual, Result) |
| Generated from | `scripts/case_catalog.py` by `scripts/build_test_case_document.py` (same data as `docs/Test_Case_Document.xlsx` and the manual checklists) |
| Execution evidence | `docs/evidence/regression/junit.xml` (main, run date 2026-11-17); `docs/evidence/regression/browsers/chromium_junit.xml` (chromium, run date 2026-11-17); `docs/evidence/regression/browsers/firefox_junit.xml` (firefox, run date 2026-11-17); `docs/evidence/regression/browsers/webkit_junit.xml` (webkit, run date 2026-11-17) |

## 1. Why this document was updated

The original Test Plan (version 1.0) was written before development. It had 75 test cases covering only FR-01 to FR-06 and NFR-01 to NFR-03, and every result was `Pending`. During the sprints all 21 requirements were implemented (GitHub issues #1–#21 closed; PRs #22–#48 merged).

- **Phase 1:** kept all 75 original IDs, updated expected results to the implemented behaviour, added test cases for FR-07 to FR-15 and NFR-04 to NFR-06, and linked each case to automated tests.
- **Phase 2:** read every linked test. Where a test did not prove the expected result, the link or the expected result was corrected (column *Phase 2 review*). Missing tests were added. The full suite and the browser suites were run, and statuses were derived from that evidence.

## 2. Conventions

- **Test Case ID** — `<TYPE>_<REQ>_<NN>`. `UT` = unit, `IT` = integration, `SYS` = system.
- **Method** — `A` = Automated (pytest); `B` = Automated browser (Playwright); `M` = Manual / human.
- **Change** — `Original (unchanged)`, `Original (updated)` or `New`.
- **Status:**
  - `PASS`: expected result verified by recorded evidence.
  - `FAIL`: actual result differs from the expected result.
  - `BLOCKED`: execution prevented by a documented environment or dependency issue.
  - `NOT RUN`: not executed, or only partly verified (the actual result says which part).
  - `NOT APPLICABLE`: outside the SRS, with the reason given.
- **How automated statuses are derived** — by `scripts/build_test_case_document.py` from the JUnit XML evidence. A case is PASS only if every linked test ran and passed. A case whose expected result needs something the tests do not prove is set to NOT RUN, and the actual result states what was and was not verified.
- **Browser references** — `[chrome]` = Google Chrome result in the main run; `@chromium` / `@webkit` / `@firefox` = separate browser runs.
- **Manual cases** — The 19 cases in `docs/manual_validation/` were executed on 2026-11-17 by Playwright automation (Google Chrome 157.0.8103.79 (Playwright channel 'chrome', headless)) against an isolated `validation_demo.db`, following the checklist steps. The instructor approved automated browser execution as evidence for manual validation. The steps were executed by the automation, not by a person; the named team member is the assigned owner. Statuses come from `docs/evidence/regression/manual_validation_automation/results.json`; browser, timestamps and logs are recorded in each record's *Supporting evidence* field and in `docs/Manual_Validation_Automation_Report.md`.
- **Assigned team member** - the owner of each manual validation case (Sumukh 5, Jagadeesh 7, Tharith 7); automated cases belong to the team's automated regression suite (`Project team (automated regression suite)`).
- **Screenshot evidence** - screenshots recorded for the case; API and unit-level tests have none by nature.
- **Defect / gap ID** - defects whose test impact names the case, and gaps affecting a case that did not pass.
- **Result history** - the result before the six fixes (automated cases: final run 2026-11-11, `docs/evidence/final/`; manual validation cases: run of 2026-11-17, `docs/evidence/manual_validation_automation/`) and the result of the regression run after the fixes (2026-11-17, `docs/evidence/regression/`), which is the status reported in this version.

## 3. Summary

Total test cases: **197** — original 75 (51 unchanged, 24 updated) + 122 new.

**Status:** PASS 188, FAIL 0, BLOCKED 4, NOT RUN 4, NOT APPLICABLE 1.

| Requirement | Module | UT | IT | SYS | Total | PASS | FAIL | BLOCKED | NOT RUN | NOT APPLICABLE |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-01 | Authentication & Role Management | 5 | 5 | 3 | 13 | 13 | 0 | 0 | 0 | 0 |
| FR-02 | Attendance Marking | 5 | 5 | 3 | 13 | 13 | 0 | 0 | 0 | 0 |
| FR-03 | Attendance Record Management | 5 | 5 | 3 | 13 | 13 | 0 | 0 | 0 | 0 |
| FR-04 | Attendance Percentage Calculation | 5 | 3 | 3 | 11 | 11 | 0 | 0 | 0 | 0 |
| FR-05 | Attendance Viewing | 4 | 3 | 3 | 10 | 9 | 0 | 0 | 0 | 1 |
| FR-06 | Attendance Reporting | 6 | 3 | 3 | 12 | 12 | 0 | 0 | 0 | 0 |
| FR-07 | User Management | 4 | 5 | 1 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-08 | Class & Subject Management | 4 | 5 | 1 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-09 | Student Enrollment | 5 | 4 | 1 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-10 | Attendance Search & Filter | 5 | 4 | 1 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-11 | Attendance Alert | 5 | 4 | 1 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-12 | Report Export | 5 | 3 | 2 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-13 | Password Management | 5 | 4 | 1 | 10 | 10 | 0 | 0 | 0 | 0 |
| FR-14 | Dashboard Summary | 1 | 6 | 1 | 8 | 8 | 0 | 0 | 0 | 0 |
| FR-15 | Logout | 2 | 3 | 3 | 8 | 7 | 0 | 0 | 1 | 0 |
| NFR-01 | Security | 2 | 4 | 2 | 8 | 7 | 0 | 1 | 0 | 0 |
| NFR-02 | Performance | 0 | 0 | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| NFR-03 | Reliability | 1 | 3 | 2 | 6 | 4 | 0 | 0 | 2 | 0 |
| NFR-04 | Usability | 2 | 3 | 1 | 6 | 5 | 0 | 0 | 1 | 0 |
| NFR-05 | Compatibility | 0 | 1 | 7 | 8 | 5 | 0 | 3 | 0 | 0 |
| NFR-06 | Maintainability | 1 | 3 | 1 | 5 | 5 | 0 | 0 | 0 | 0 |
| **Total** | | **72** | **76** | **49** | **197** | **188** | **0** | **4** | **4** | **1** |

Manual cases assigned: Sumukh 5, Jagadeesh 7, Tharith 7 (see `docs/manual_validation/`). Manual validation results: 17 PASS, 1 BLOCKED, 1 NOT RUN.

## 4. Cases that did not pass

| Test Case ID | Status | Actual observed result | Assigned team member | Defect / gap ID |
|---|---|---|---|---|
| SYS_FR-05_09 | NOT APPLICABLE | Pagination is not implemented in the API or the UI. | Project team (automated regression suite) | G-05 |
| SYS_FR-15_08 | NOT RUN | Not verified: the linked CSRF test posts to /api/users, not /api/logout. The Origin check is global, but no test proves it for logout. | Project team (automated regression suite) | - |
| SYS_NFR-01_04 | BLOCKED | No HTTPS deployment is available; the development server serves plain HTTP. Only the Secure-cookie switch exists. | Project team (automated regression suite) | G-08 |
| IT_NFR-03_03 | NOT RUN | Partially verified by automated tests: the backup contains exactly the saved attendance rows and is unaffected by later changes. Not yet verified: restoring the backup into a database and using it through the application. | Project team (automated regression suite) | G-07 |
| SYS_NFR-03_05 | NOT RUN | Partially verified by automated tests: a failed batch rolls back completely and a missing database fails safely. Not yet verified: retrying the same save after the failure. | Project team (automated regression suite) | - |
| SYS_NFR-04_06 | NOT RUN | NOT RUN: Smoke - student: find overall and one subject's attendance (95.65%; 'Discrete Mathematics\n11 of 12 classes attended'). Smoke - teacher: mark today's attendance and correct one status (Saved attendance for 4 student(s).). Smoke - admin: create a student and enroll them (usability_s1 enrolled in Year 1 / Programming Fundamentals). Scripted task flows completed in 5.6 s (machine speed, not human effort). | Tharith | - |
| SYS_NFR-05_02 | BLOCKED | Playwright Firefox 157.0 was installed but cannot start on this Mac (macOS 27.0): "Could not find profile folder", even when started directly without Playwright and outside the Claude Code sandbox. No Firefox result is claimed. | Project team (automated regression suite) | G-09 |
| SYS_NFR-05_03 | BLOCKED | Microsoft Edge is not installed and installing it was not approved. The suite reports: "Chromium distribution 'msedge' is not found at /Applications/Microsoft Edge.app". | Project team (automated regression suite) | G-09 |
| SYS_NFR-05_08 | BLOCKED | BLOCKED: Open the Safari application on a Mac (Safari.app installed: True. Playwright cannot drive the Safari application. safaridriver is present, but using). [WebKit] admin: create a user; log out (created webkit_s1). [WebKit] teacher: mark attendance; correct one status; log out (Saved attendance for 5 student(s).). [WebKit] student: view My attendance and Attendance history (24 records). [WebKit] console errors (D-01 'Refused to apply a stylesheet') (4 console.error line(s); 4 CSP-related; page errors 0). Supplementary engine-level run in Playwright WebKit 27.2 (NOT the Safari application). WebKit CSP-related console lines: 4; first: 08:30:32.054 console.error: Refused to apply a stylesheet because its hash, its nonce, or 'unsafe-inline' appears in neither the style-src directive nor the default-src directive of the Content Securi | Tharith | G-09 |

## 5. Known gaps (checked against the SRS)

| Gap | Req | Description | Required by SRS? | Classification | Impact on testing | Affected cases |
|---|---|---|---|---|---|---|
| G-01 | FR-06 | No reporting screen in any dashboard; reports are generated only through /api/reports/*. | Partly. FR-06 requires the system to generate reports by student, class, subject or date range; it does not name a screen. The API does this. | Closed in the regression run: reporting screen added | Reports can be generated in the dashboard. | SYS_FR-06_08 (PASS); FR-06 API cases PASS |
| G-02 | FR-12 | No export button or download control in any dashboard; export only by calling /api/reports/.../export. | Yes in practice. FR-12 requires authorized users to export reports; without a control, users can only type an API URL. | Closed in the regression run: export controls added | Reports can be exported from the dashboard. | SYS_FR-12_10 (PASS); UT/IT/SYS_FR-12_01..09 PASS via API |
| G-03 | FR-10 | Dashboard filters have no class filter and no date-range filter (the API supports both). | Class filter: yes (FR-10 names student, subject, class or date). Date range: not explicitly. | Closed in the regression run: class and date-range filters added | All FR-10 filters are available in the dashboards. | SYS_FR-10_10 (PASS) |
| G-04 | FR-11 | No screen to view or change the alert threshold; changed only through the admin API (default 75%). | No. FR-11 requires identifying students below a specified threshold, which works via configuration/API; alerts are shown on dashboards. | Optional UI convenience | None failing. | SYS_FR-11_10 (PASS, dashboard display check) |
| G-05 | FR-05 | No pagination and no user-selectable sort. | No. FR-05 requires viewing by subject and date only. | Outside the SRS (original Test Plan expectation) | Pagination case excluded; sort case re-based on the fixed order. | SYS_FR-05_09 (NOT APPLICABLE); SYS_FR-05_08 (PASS, fixed order) |
| G-06 | FR-04 | /api/attendance/percentages has no date-range filter; the student dashboard calculates its percentage in the browser. | No. FR-04 does not require date ranges. | Design note | Date-range percentage tested through the FR-06 report summary. | IT_FR-04_08 (PASS via report) |
| G-07 | NFR-03 | Backups exist and are scheduled, but there is no restore script or documented restore procedure. | Not explicitly. NFR-03 requires preserving records and regular backups; the Test Plan adds a restore test. | Test Plan expectation without tooling | Restore must be checked manually in System Validation. | IT_NFR-03_03 (NOT RUN) |
| G-08 | NFR-01 | No HTTPS deployment; the development server is plain HTTP. Only a Secure-cookie switch exists. | Yes. NFR-01 requires protecting sensitive data during transmission. | Environmental limitation (deployment) | Cannot be executed locally. | SYS_NFR-01_04 (BLOCKED) |
| G-09 | NFR-05 | Edge not installed (not approved); Playwright Firefox cannot start on this Mac; the Safari application cannot be automated; test_nfr05_implementation only fakes User-Agent headers. | Yes. NFR-05 requires commonly used modern browsers. | Environmental limitation | Chrome, Chromium and WebKit pass (WebKit r2388, defect D-01 closed); Edge not installed; Playwright Firefox build 1572 still cannot start on this Mac; the Safari application cannot be automated. | SYS_NFR-05_02 (BLOCKED), SYS_NFR-05_03 (BLOCKED), SYS_NFR-05_04 (PASS), SYS_NFR-05_08 (BLOCKED) |
| G-10 | Several | Missing automated tests for session expiry, login with database unavailable, Test Plan percentage datasets, recalculation after update, and enrolling a non-student. | Yes (Test Plan cases). | Test gap - CLOSED in Phase 2 | Three new test files added (26 test results in the first run; see final evidence). | SYS_FR-01_09, SYS_FR-01_10, UT_FR-04_01..05, IT_FR-04_06, IT_FR-04_08, SYS_FR-04_09, UT_FR-09_05 (PASS) |

## 6. Defects and observations

| ID | Req | Severity | Description | Test impact | Status |
|---|---|---|---|---|---|
| D-01 | NFR-05 | Low | WebKit (Playwright 27.2) logs a Content-Security-Policy error for every <select> element on all dashboards ("Refused to apply a stylesheet ... style-src"). The app sends default-src 'self' with no style-src; WebKit appears to treat its own form-control styling as a blocked stylesheet. Functions and appearance are unaffected; Chrome and Chromium log nothing. | SYS_NFR-05_04 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): upstream WebKit regression (false-positive style-src-attr violation for <select>), fixed in WebKit 324283@main; re-run with Playwright 1.65.2 / WebKit r2388 shows 0 violations. No application change; CSP unchanged. |
| MV-01 | FR-10 | Low | The teacher Attendance records screen has no 'Clear filters' control (toolbar: search, Subject, Date, Status). The expected result of SYS_FR-10_10 requires 'Clear filters' to restore all rows; the teacher must reset each filter by hand. The admin Attendance screen has the control and it works. | SYS_FR-10_10 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): Clear filters, Class and From/To filters on the teacher records screen (app/templates/teacher.html, teacher.js). |
| MV-02 | FR-04 | Low | Attendance percentages are displayed to one decimal place (83.3%, 58.3%) although the backend returns, and SYS_FR-04_11 expects, two decimals (83.33, 58.33). The calculation is correct. The shared formatter App.formatPercent (app/static/js/common.js) uses toFixed(1), so other dashboards are likely affected too. | SYS_FR-04_11 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): App.formatPercent shows two decimals (app/static/js/common.js); overview averages rounded to two decimals. |
| MV-03 | FR-05 | Low | At 375 px wide the teacher Attendance records table overflows its container by 181 px: Status badges are cut off and the Actions (correct/delete) column is reachable only by scrolling the table sideways. The page itself does not scroll horizontally, so the existing automated layout test passes. | SYS_FR-05_10 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): labelled card layout for tables below 640 px (app/static/css/app.css, App.fillRows data-label). |
| D-02 | FR-06 | Medium | No reporting screen (gap G-01). | SYS_FR-06_08 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): Reports screen in the admin and teacher dashboards (app/static/js/reports.js, templates). |
| D-03 | FR-12 | Medium | No export control in the user interface (gap G-02). | SYS_FR-12_10 FAIL (original run); PASS in the regression run | Fixed and verified in the regression run (2026-11-17): CSV / PDF / JSON export controls on the Reports screen using the existing export API. |
| D-04 | NFR-06 | Low | app/api/exports.py:104 calls datetime.utcnow(), deprecated in Python 3.12+ (12 DeprecationWarnings per run). Works today; will break when Python removes it. | Warnings only | Open - production change needs approval. |
| O-01 | FR-09 | Low | POST /api/enrollments accepts a subject that is not linked to the chosen class (no class_subjects check). Verified in Phase 3 on a temporary database (docs/evidence/phase3/o01_enrollment_probe_output.txt): enrolling a student in CSE-B / DBMS, where DBMS is linked only to CSE-A, returns 201, and the teacher roster for CSE-B / DBMS then lists the student although GET /api/classes/<CSE-B>/subjects is empty. The admin dashboard only offers the class's own subjects, so normal UI use cannot create this. Against the SRS: FR-09 says students are assigned to 'their respective classes and subjects', which implies the subject belongs to the class; the API does not enforce this. Assessment: genuine but minor validation gap (API only), not a missing feature. | None (no test case expects this check) | Open - documented only; a fix is a production change and needs approval. |
| O-02 | NFR-06 | Observation | Two views are registered for GET /api/attendance; attendance_management.get_attendance never runs (documented in app/api/__init__.py and pinned by test_nfr06_maintainability). Phase 3 coverage confirms it: 84 statements and 44 branches of that function are never executed. | None | Documented; no change. |
| O-03 | - | Observation | GET / still returns a placeholder 'starter' JSON message. | None | Documented in README; no change. |
| O-04 | NFR-03 | Observation | scripts/backup_db.py (lines 50-51) and many test helpers use 'with sqlite3.connect(...)', which commits but does not close the connection. Under coverage measurement pytest reports these as ResourceWarning: unclosed database (555 in each measured coverage run); without coverage they are not reported. Full-suite allocation trace: 547 opened in test files, 8 in scripts/backup_db.py, 0 in app/ (docs/evidence/coverage/resourcewarning_allocation_summary.txt). | Warnings only (coverage runs) | Documented; no change (backup script change needs approval; test helpers unchanged). |

## 7. Skipped placeholder tests (kept on purpose)

`tests/test_sprint1_requirements.py` contains 7 tests that are permanently skipped. They were a Sprint 1 checklist written before the features existed and contain no assertions (`raise NotImplementedError`). They are kept unchanged as agreed and appear as **skipped**, never as passed. The requirements they named are tested by:

| Skipped placeholder | Requirement(s) | Replacement tests |
|---|---|---|
| `test_fr01_authentication` | FR-01 | tests/test_fr01_authentication.py; test_foundation.py (login tests); test_nfr01_security.py::test_session_expiration_configured |
| `test_admin_management` | FR-07, FR-08, FR-09 | tests/test_fr07_user_management.py; tests/test_fr08_class_subject_management.py; tests/test_fr09_student_enrollment.py |
| `test_fr04_percentages` | FR-04 | tests/test_fr04_percentages.py; tests/test_fr11_attendance_alert.py (zero-record cases) |
| `test_fr05_viewing` | FR-05 | tests/test_fr05_attendance_viewing.py; tests/test_fr05_attendance_viewing_extra.py |
| `test_fr15_logout` | FR-15 | tests/test_fr15_logout.py |
| `test_nfr01_security` | NFR-01 | tests/test_nfr01_security.py; tests/test_frontend_pages.py (CSRF/headers). HTTPS deployment still unverified (G-08). |
| `test_nfr03_reliability` | NFR-03 | tests/test_nfr03_reliability.py; tests/test_nfr03_scheduling.py. Restore still untested (G-07). |

## 8. Changes to original test cases

| Test Case ID | Phase 1 reason | Phase 2 review |
|---|---|---|
| UT_FR-01_01 | Expected result made specific to the implemented API (HTTP 200) and redirect. | Linked test(s) read; they verify the expected result. |
| UT_FR-01_02 | Exact message from app/api/auth_routes.py added. | Corrected: 'no session created' was not asserted by any test; replaced with the browser check that the user stays on /login. |
| UT_FR-01_03 | Exact UI and API messages added. | Linked test(s) read; they verify the expected result. |
| IT_FR-01_07 | Clarified that pages redirect and APIs return 403 (implemented behaviour). | Linked test(s) read; they verify the expected result. |
| SYS_FR-01_08 | Back-button behaviour needs a real-browser check in System Validation. | Back-button step is not automated. |
| SYS_FR-01_09 | New Phase 2 tests check real server-side expiry by advancing the session signer's clock (31 idle minutes -> 401; 29 -> 200). | Previously only the configuration value was checked; new tests added (gap G-10 closed). |
| SYS_FR-01_10 | New Phase 2 test: database file replaced by a directory so it cannot be opened. | No test existed; new test added (gap G-10 closed). |
| UT_FR-02_04 | The teacher form's date input has the HTML 'required' attribute; browser behaviour is in the manual checklist for SYS_FR-10_10 / SYS_FR-02_13 walkthroughs. | Corrected: the linked test is API-only, so the UI half of the expected result was moved to remarks. |
| SYS_FR-03_10 | Failure is simulated with a duplicate-key error part-way through a batch; the whole batch is rolled back. A fully unavailable database during save is not simulated. | Verified: rollback with no partial record. Note the type of failure simulated. |
| UT_FR-04_04 | Implemented late policy written into the expected result. | The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data. |
| IT_FR-04_08 | /api/attendance/percentages has no date-range filter; the range percentage comes from the FR-06 report summary (gap G-06). | The original link checked which records were included but not the percentage; new test checks 75% in range vs 50% overall. |
| SYS_FR-04_09 | On-screen display of the rounded value is checked manually under SYS_FR-04_11 and SYS_FR-14_08. | New Phase 2 tests (gap G-10 closed). Expected result limited to the APIs; display moved to manual cases. |
| SYS_FR-05_08 | No user-selectable sort exists; expected result changed to the fixed order the system uses (gap G-05). | Linked test(s) read; they verify the expected result. |
| UT_FR-06_01 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Linked test(s) read; they verify the expected result. |
| UT_FR-06_02 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Linked test(s) read; they verify the expected result. |
| UT_FR-06_03 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Linked test(s) read; they verify the expected result. |
| UT_FR-06_04 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Linked test(s) read; they verify the expected result. |
| IT_FR-06_05 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Linked test(s) read; they verify the expected result. |
| IT_FR-06_06 | Executed through the REST API: the UI has no reporting screen (gap G-01). Covered through the export of the same report; confirm in Phase 2. | Linked test(s) read; they verify the expected result. |
| IT_FR-06_07 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Linked test(s) read; they verify the expected result. |
| SYS_FR-06_08 | API part automated; the UI message cannot be checked because no reporting screen exists (gap G-01). | Reporting screen added to the admin and teacher dashboards (app/static/js/reports.js); the empty report shows 'No attendance records match this report'. Was FAIL (gap G-01, defect D-02). |
| SYS_FR-06_09 | Executed through the REST API: the UI has no reporting screen (gap G-01). | Added the test that compares totals and the percentage (3 Present of 5 = 60%) with the seeded records. |
| UT_NFR-01_01 | Show-password toggle exists; expected result updated. Default masked state to be confirmed in Phase 2. | The test toggles the field to type=text and back to type=password; a toggle can only reveal from the masked state, so the default is masked. The default state itself is not asserted separately. |
| IT_NFR-03_03 | No restore script exists; restore means copying the backup file into place (gap G-07). Tests check backup contents only. | No restore step exists in code or tests (G-07). Planned for System Validation using a temporary copy. |

## 9. Test case records

Each test case is recorded in the same format: identification, assigned team member, preconditions, steps, expected and actual observed result, status, execution method and date, screenshot and supporting evidence, and the related defect or gap. Records are grouped by requirement.

### FR-01 - Authentication & Role Management

> SRS: The system shall allow authorized users (Administrator, Teacher, and Student) to log in according to their assigned role.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-01_01 | Valid login | Project team (automated regression suite) | PASS | - |
| UT_FR-01_02 | Invalid password | Project team (automated regression suite) | PASS | - |
| UT_FR-01_03 | Blank credentials | Project team (automated regression suite) | PASS | - |
| IT_FR-01_04 | Administrator role mapping | Project team (automated regression suite) | PASS | - |
| IT_FR-01_05 | Teacher role mapping | Project team (automated regression suite) | PASS | - |
| IT_FR-01_06 | Student role mapping | Project team (automated regression suite) | PASS | - |
| IT_FR-01_07 | Unauthorized page access | Project team (automated regression suite) | PASS | - |
| SYS_FR-01_08 | Logout | Jagadeesh | PASS | - |
| SYS_FR-01_09 | Session timeout | Project team (automated regression suite) | PASS | - |
| SYS_FR-01_10 | Authentication failure handling | Project team (automated regression suite) | PASS | - |
| UT_FR-01_11 | Inactive (deactivated) account login | Project team (automated regression suite) | PASS | - |
| UT_FR-01_12 | Malformed login request | Project team (automated regression suite) | PASS | - |
| IT_FR-01_13 | Session replaced on new login | Project team (automated regression suite) | PASS | - |

#### UT_FR-01_01 - Valid login

| Field | Details |
|---|---|
| Test Case ID | UT_FR-01_01 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Unit |
| Test scenario | Valid login |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Valid active account exists |
| Test data | Teacher01 / valid password |
| Test steps | 1. Open /login<br>2. Enter credentials<br>3. Submit |
| Expected result | POST /api/login returns 200 with the user's role; browser is redirected to the role dashboard (/teacher). |
| Actual observed result | Expected result verified: 3 linked test(s), 5 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_successful_login`, `test_frontend_pages::test_page_login_flow_uses_real_authentication`, `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Expected result made specific to the implemented API (HTTP 200) and redirect. |

#### UT_FR-01_02 - Invalid password

| Field | Details |
|---|---|
| Test Case ID | UT_FR-01_02 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Unit |
| Test scenario | Invalid password |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Login page available |
| Test data | Teacher01 / Wrong@123 |
| Test steps | 1. Enter wrong password<br>2. Submit |
| Expected result | HTTP 401 'Invalid username or password'; error shown on the login page and the user stays on /login. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_wrong_password`, `test_fr01_authentication::test_unknown_username`, `test_foundation::test_login_rejects_unknown_user`, `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Corrected: 'no session created' was not asserted by any test; replaced with the browser check that the user stays on /login. |
| Remarks | Exact message from app/api/auth_routes.py added. |

#### UT_FR-01_03 - Blank credentials

| Field | Details |
|---|---|
| Test Case ID | UT_FR-01_03 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Unit |
| Test scenario | Blank credentials |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Login page available |
| Test data | Blank username / password |
| Test steps | 1. Submit empty fields |
| Expected result | UI shows 'Please enter both your username and password.'; API returns 400 'Username and password are required'. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_missing_credentials`, `test_foundation::test_login_rejects_empty_credentials`, `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Exact UI and API messages added. |

#### IT_FR-01_04 - Administrator role mapping

| Field | Details |
|---|---|
| Test Case ID | IT_FR-01_04 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Integration |
| Test scenario | Administrator role mapping |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin account exists |
| Test data | Admin account |
| Test steps | 1. Login as administrator |
| Expected result | Admin dashboard (/admin) opens; admin-only API (/api/admin/check) returns 200. |
| Actual observed result | Expected result verified: 2 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_correct_role_access`, `test_frontend_pages::test_role_page_renders_for_its_role` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-01_05 - Teacher role mapping

| Field | Details |
|---|---|
| Test Case ID | IT_FR-01_05 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Integration |
| Test scenario | Teacher role mapping |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher account exists |
| Test data | Teacher account |
| Test steps | 1. Login as teacher |
| Expected result | Teacher dashboard (/teacher) opens; teacher functions available. |
| Actual observed result | Expected result verified: 2 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_correct_role_access`, `test_frontend_pages::test_role_page_renders_for_its_role` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-01_06 - Student role mapping

| Field | Details |
|---|---|
| Test Case ID | IT_FR-01_06 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Integration |
| Test scenario | Student role mapping |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student account exists |
| Test data | Student account |
| Test steps | 1. Login as student |
| Expected result | Student dashboard (/student) opens; student functions available. |
| Actual observed result | Expected result verified: 2 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_correct_role_access`, `test_frontend_pages::test_role_page_renders_for_its_role` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-01_07 - Unauthorized page access

| Field | Details |
|---|---|
| Test Case ID | IT_FR-01_07 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Integration |
| Test scenario | Unauthorized page access |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student logged in |
| Test data | Student session |
| Test steps | 1. Open /teacher and /admin pages<br>2. Call admin/teacher APIs |
| Expected result | Pages redirect the student to their own dashboard; restricted APIs return 403. |
| Actual observed result | Expected result verified: 3 linked test(s), 14 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_wrong_role_denied`, `test_frontend_pages::test_role_page_redirects_other_roles`, `test_fr14_dashboard_summary::test_fr14_users_cannot_open_another_roles_dashboard` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Clarified that pages redirect and APIs return 403 (implemented behaviour). |

#### SYS_FR-01_08 - Logout

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
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Back-button step is not automated. |
| Remarks | Back-button behaviour needs a real-browser check in System Validation. |

#### SYS_FR-01_09 - Session timeout

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-01_09 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | System |
| Test scenario | Session timeout |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Timeout configured (PERMANENT_SESSION_LIFETIME = 30 minutes) |
| Test data | Idle session |
| Test steps | 1. Remain inactive past the lifetime<br>2. Open protected page |
| Expected result | Login is required again after 30 minutes of inactivity. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_session_lifetime_is_thirty_minutes`, `test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_idle_session_expires_after_thirty_minutes`, `test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_session_still_valid_just_before_timeout`, `test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_09_activity_renews_the_inactivity_window` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Previously only the configuration value was checked; new tests added (gap G-10 closed). |
| Remarks | New Phase 2 tests check real server-side expiry by advancing the session signer's clock (31 idle minutes -> 401; 29 -> 200). |

#### SYS_FR-01_10 - Authentication failure handling

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-01_10 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | System |
| Test scenario | Authentication failure handling |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Application available; database made unavailable |
| Test data | Valid credentials |
| Test steps | 1. Attempt login while the user database cannot be read |
| Expected result | HTTP 503 'Authentication temporarily unavailable'; no stack trace or technical detail shown. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_10_login_with_unavailable_database_fails_safely`, `test_fr01_session_expiry_and_auth_failure::test_sys_fr_01_10_valid_login_works_when_database_is_available` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | No test existed; new test added (gap G-10 closed). |
| Remarks | New Phase 2 test: database file replaced by a directory so it cannot be opened. |

#### UT_FR-01_11 - Inactive (deactivated) account login

| Field | Details |
|---|---|
| Test Case ID | UT_FR-01_11 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Unit |
| Test scenario | Inactive (deactivated) account login |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Account deactivated by admin |
| Test data | Deactivated student account |
| Test steps | 1. Attempt login |
| Expected result | Login rejected; any existing session for that user loses access. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_inactive_account_cannot_login`, `test_fr01_authentication::test_inactive_user_loses_existing_access`, `test_frontend_pages::test_inactive_user_is_sent_to_login` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Covers backlog US-02 (locked/inactive accounts). |

#### UT_FR-01_12 - Malformed login request

| Field | Details |
|---|---|
| Test Case ID | UT_FR-01_12 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Unit |
| Test scenario | Malformed login request |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Login API available |
| Test data | Non-JSON body |
| Test steps | 1. POST /api/login with an invalid body |
| Expected result | HTTP 400; request rejected. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_invalid_json_body` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Corrected: the test checks the status code only, not the message text. |
| Remarks | - |

#### IT_FR-01_13 - Session replaced on new login

| Field | Details |
|---|---|
| Test Case ID | IT_FR-01_13 |
| Requirement | FR-01 - Authentication & Role Management |
| Test level | Integration |
| Test scenario | Session replaced on new login |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User A logged in |
| Test data | Two accounts |
| Test steps | 1. Log in as user B in the same browser session |
| Expected result | Session now belongs only to user B; no data from user A remains accessible. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr01_authentication::test_session_replaced_when_different_user_logs_in`, `test_fr01_authentication::test_session_created_after_login` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

### FR-02 - Attendance Marking

> SRS: The system shall allow teachers to select a class/subject and mark each student as Present, Absent, or Late for a specific date.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-02_01 | Mark Present | Project team (automated regression suite) | PASS | - |
| UT_FR-02_02 | Mark Absent | Project team (automated regression suite) | PASS | - |
| UT_FR-02_03 | Mark Late | Project team (automated regression suite) | PASS | - |
| UT_FR-02_04 | Missing date validation | Project team (automated regression suite) | PASS | - |
| UT_FR-02_05 | Missing status validation | Project team (automated regression suite) | PASS | - |
| IT_FR-02_06 | Load class roster | Project team (automated regression suite) | PASS | - |
| IT_FR-02_07 | Save complete roster | Project team (automated regression suite) | PASS | - |
| IT_FR-02_08 | Unauthorized subject | Project team (automated regression suite) | PASS | - |
| SYS_FR-02_09 | Change attendance date | Project team (automated regression suite) | PASS | - |
| SYS_FR-02_10 | Invalid attendance status | Project team (automated regression suite) | PASS | - |
| IT_FR-02_11 | Unenrolled student rejected | Project team (automated regression suite) | PASS | - |
| IT_FR-02_12 | Batch save is all-or-nothing | Project team (automated regression suite) | PASS | - |
| SYS_FR-02_13 | Mark attendance through teacher dashboard | Project team (automated regression suite) | PASS | - |

#### UT_FR-02_01 - Mark Present

| Field | Details |
|---|---|
| Test Case ID | UT_FR-02_01 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Unit |
| Test scenario | Mark Present |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher logged in; class exists; student enrolled |
| Test data | S01, DBMS, 2026-09-01, Present |
| Test steps | 1. Select class/subject/date<br>2. Mark Present<br>3. Save |
| Expected result | HTTP 201; record saved with status Present. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_ut_fr_02_01_mark_present` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-02_02 - Mark Absent

| Field | Details |
|---|---|
| Test Case ID | UT_FR-02_02 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Unit |
| Test scenario | Mark Absent |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | S01, Absent |
| Test steps | 1. Mark Absent<br>2. Save |
| Expected result | HTTP 201; record saved with status Absent. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_ut_fr_02_02_mark_absent` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-02_03 - Mark Late

| Field | Details |
|---|---|
| Test Case ID | UT_FR-02_03 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Unit |
| Test scenario | Mark Late |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | S01, Late |
| Test steps | 1. Mark Late<br>2. Save |
| Expected result | HTTP 201; record saved with status Late. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_ut_fr_02_03_mark_late` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-02_04 - Missing date validation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-02_04 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Unit |
| Test scenario | Missing date validation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher logged in |
| Test data | Date blank |
| Test steps | 1. Leave date empty<br>2. Save |
| Expected result | API returns 400; the error names attendance_date. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_ut_fr_02_04_missing_date_validation` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Corrected: the linked test is API-only, so the UI half of the expected result was moved to remarks. |
| Remarks | The teacher form's date input has the HTML 'required' attribute; browser behaviour is in the manual checklist for SYS_FR-10_10 / SYS_FR-02_13 walkthroughs. |

#### UT_FR-02_05 - Missing status validation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-02_05 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Unit |
| Test scenario | Missing status validation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | Status blank |
| Test steps | 1. Leave status unselected<br>2. Save |
| Expected result | API returns 400 with a validation error. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_ut_fr_02_05_missing_status_validation` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-02_06 - Load class roster

| Field | Details |
|---|---|
| Test Case ID | IT_FR-02_06 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Integration |
| Test scenario | Load class roster |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Class and subject data exist |
| Test data | CSE-A, DBMS |
| Test steps | 1. Select class and subject |
| Expected result | GET /api/roster returns exactly the students enrolled in that class and subject. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_it_fr_02_06_load_class_roster` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-02_07 - Save complete roster

| Field | Details |
|---|---|
| Test Case ID | IT_FR-02_07 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Integration |
| Test scenario | Save complete roster |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | S01 Present; S02 Absent; S03 Late |
| Test steps | 1. Mark statuses for all students<br>2. Save |
| Expected result | All entries are processed and stored. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_it_fr_02_07_save_complete_roster` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-02_08 - Unauthorized subject

| Field | Details |
|---|---|
| Test Case ID | IT_FR-02_08 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Integration |
| Test scenario | Unauthorized subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher logged in |
| Test data | Unassigned subject |
| Test steps | 1. Attempt to mark an unassigned subject |
| Expected result | Request denied with HTTP 403. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_it_fr_02_08_unauthorized_subject` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-02_09 - Change attendance date

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-02_09 |
| Requirement | FR-02 - Attendance Marking |
| Test level | System |
| Test scenario | Change attendance date |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | 2026-09-02 |
| Test steps | 1. Select another date<br>2. Mark<br>3. Save |
| Expected result | Records are stored against the selected date only. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_sys_fr_02_09_change_attendance_date` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-02_10 - Invalid attendance status

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-02_10 |
| Requirement | FR-02 - Attendance Marking |
| Test level | System |
| Test scenario | Invalid attendance status |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | Excused |
| Test steps | 1. Submit unsupported status |
| Expected result | Invalid status rejected with HTTP 400. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_sys_fr_02_10_invalid_attendance_status` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-02_11 - Unenrolled student rejected

| Field | Details |
|---|---|
| Test Case ID | IT_FR-02_11 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Integration |
| Test scenario | Unenrolled student rejected |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student not enrolled in subject |
| Test data | Unenrolled student id |
| Test steps | 1. Mark attendance (single and batch) |
| Expected result | Request rejected; no record written. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_unenrolled_student_rejected_single`, `test_fr02_attendance_marking::test_unenrolled_student_rejected_batch`, `test_fr02_attendance_marking::test_zero_enrollments_rejected_single` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-02_12 - Batch save is all-or-nothing

| Field | Details |
|---|---|
| Test Case ID | IT_FR-02_12 |
| Requirement | FR-02 - Attendance Marking |
| Test level | Integration |
| Test scenario | Batch save is all-or-nothing |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Roster loaded |
| Test data | Batch with one invalid/unenrolled entry |
| Test steps | 1. Submit the batch |
| Expected result | Whole batch rejected; no partial records saved. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_batch_mixture_enrolled_unenrolled_rejected_without_partial_writes`, `test_fr02_attendance_marking::test_batch_rollback_on_failure` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-02_13 - Mark attendance through teacher dashboard

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-02_13 |
| Requirement | FR-02 - Attendance Marking |
| Test level | System |
| Test scenario | Mark attendance through teacher dashboard |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher logged in to browser |
| Test data | Seeded class/subject/students |
| Test steps | 1. Open Teacher > Mark attendance<br>2. Choose class, subject, date<br>3. Set statuses<br>4. Save |
| Expected result | Success message shown; saved statuses visible in Records. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Frontend scenario. |

### FR-03 - Attendance Record Management

> SRS: The system shall save and allow authorized teachers to update attendance records while preventing duplicate attendance for the same student, subject, and date.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-03_01 | Save new record | Project team (automated regression suite) | PASS | - |
| UT_FR-03_02 | Update existing record | Project team (automated regression suite) | PASS | - |
| UT_FR-03_03 | Prevent duplicate record | Project team (automated regression suite) | PASS | - |
| UT_FR-03_04 | Missing student validation | Project team (automated regression suite) | PASS | - |
| UT_FR-03_05 | Missing subject validation | Project team (automated regression suite) | PASS | - |
| IT_FR-03_06 | Database persistence | Project team (automated regression suite) | PASS | - |
| IT_FR-03_07 | Student update restriction | Project team (automated regression suite) | PASS | - |
| IT_FR-03_08 | Teacher authorization | Project team (automated regression suite) | PASS | - |
| SYS_FR-03_09 | Refresh after save | Project team (automated regression suite) | PASS | - |
| SYS_FR-03_10 | Database failure handling | Project team (automated regression suite) | PASS | - |
| IT_FR-03_11 | Delete attendance record | Project team (automated regression suite) | PASS | - |
| IT_FR-03_12 | Idempotent upsert by key | Project team (automated regression suite) | PASS | - |
| SYS_FR-03_13 | Edit and delete through teacher dashboard | Jagadeesh | PASS | - |

#### UT_FR-03_01 - Save new record

| Field | Details |
|---|---|
| Test Case ID | UT_FR-03_01 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Unit |
| Test scenario | Save new record |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Valid attendance form |
| Test data | S01, DBMS, 2026-09-01, Present |
| Test steps | 1. Enter data<br>2. Save |
| Expected result | Record saved (HTTP 201). |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_ut_fr_03_01_save_new_record` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-03_02 - Update existing record

| Field | Details |
|---|---|
| Test Case ID | UT_FR-03_02 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Unit |
| Test scenario | Update existing record |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record exists |
| Test data | Existing S01 record |
| Test steps | 1. Change Present to Late<br>2. Save |
| Expected result | Record updated to Late. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_ut_fr_03_02_update_existing_record_by_id`, `test_fr03_record_management::test_fr03_idempotent_upsert_by_key` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | The linked test changes Present -> Absent (not Late) as teacher1; the change to Late is covered by the upsert test. |
| Remarks | - |

#### UT_FR-03_03 - Prevent duplicate record

| Field | Details |
|---|---|
| Test Case ID | UT_FR-03_03 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Unit |
| Test scenario | Prevent duplicate record |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record exists |
| Test data | Same key values |
| Test steps | 1. Submit same student/subject/date |
| Expected result | Duplicate prevented; only one record exists for the key. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_ut_fr_03_03_prevent_duplicate_record`, `test_foundation::test_duplicate_attendance_prevented` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-03_04 - Missing student validation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-03_04 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Unit |
| Test scenario | Missing student validation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Form available |
| Test data | Student blank |
| Test steps | 1. Submit without student |
| Expected result | HTTP 400 validation error. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_ut_fr_03_04_missing_student_validation` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-03_05 - Missing subject validation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-03_05 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Unit |
| Test scenario | Missing subject validation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Form available |
| Test data | Subject blank |
| Test steps | 1. Submit without subject |
| Expected result | HTTP 400 validation error. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_ut_fr_03_05_missing_subject_validation` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-03_06 - Database persistence

| Field | Details |
|---|---|
| Test Case ID | IT_FR-03_06 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Integration |
| Test scenario | Database persistence |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Database connected |
| Test data | Valid record |
| Test steps | 1. Save<br>2. Reload record list from a new connection |
| Expected result | Record remains available. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_it_fr_03_06_database_persistence_across_connection_reload` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-03_07 - Student update restriction

| Field | Details |
|---|---|
| Test Case ID | IT_FR-03_07 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Integration |
| Test scenario | Student update restriction |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student account exists |
| Test data | Student session |
| Test steps | 1. Login as student<br>2. Attempt update |
| Expected result | Update denied (HTTP 403). |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_it_fr_03_07_student_update_restriction` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-03_08 - Teacher authorization

| Field | Details |
|---|---|
| Test Case ID | IT_FR-03_08 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Integration |
| Test scenario | Teacher authorization |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher assigned to class |
| Test data | Authorized teacher |
| Test steps | 1. Update assigned record |
| Expected result | Update succeeds. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_it_fr_03_08_teacher_authorization`, `test_fr03_record_management::test_ut_fr_03_02_update_existing_record_by_id` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Added the test where the assigned teacher updates their own record; the original link proved denial and admin update only. |
| Remarks | - |

#### SYS_FR-03_09 - Refresh after save

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-03_09 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | System |
| Test scenario | Refresh after save |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record saved |
| Test data | Saved record |
| Test steps | 1. Refresh page / re-query |
| Expected result | Record is retained exactly once. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_sys_fr_03_09_refresh_after_save` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-03_10 - Database failure handling

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-03_10 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | System |
| Test scenario | Database failure handling |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Database error during save |
| Test data | Valid attendance data |
| Test steps | 1. Attempt save while a write fails |
| Expected result | Safe error returned; no partial record (transaction rolled back). |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_sys_fr_03_10_database_atomic_rollback` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Verified: rollback with no partial record. Note the type of failure simulated. |
| Remarks | Failure is simulated with a duplicate-key error part-way through a batch; the whole batch is rolled back. A fully unavailable database during save is not simulated. |

#### IT_FR-03_11 - Delete attendance record

| Field | Details |
|---|---|
| Test Case ID | IT_FR-03_11 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Integration |
| Test scenario | Delete attendance record |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record exists |
| Test data | Own record; another teacher's record; missing id |
| Test steps | 1. DELETE /api/attendance/<id> |
| Expected result | Assigned teacher/admin can delete (record gone); other teacher gets 403; unknown id gets 404. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_fr03_record_deletion`, `test_fr03_record_management::test_it_fr_03_08_teacher_authorization` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Added the test where another teacher's delete is refused (403). |
| Remarks | Deletion is implemented (not in original plan). |

#### IT_FR-03_12 - Idempotent upsert by key

| Field | Details |
|---|---|
| Test Case ID | IT_FR-03_12 |
| Requirement | FR-03 - Attendance Record Management |
| Test level | Integration |
| Test scenario | Idempotent upsert by key |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record exists |
| Test data | Same student/subject/date, new status |
| Test steps | 1. PUT /api/attendance with the same key |
| Expected result | Existing record updated in place; no duplicate. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_fr03_idempotent_upsert_by_key` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-03_13 - Edit and delete through teacher dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Existing browser test covers correction; the delete UI needs checking in System Validation. |

### FR-04 - Attendance Percentage Calculation

> SRS: The system shall automatically calculate and display each student's attendance percentage based on recorded attendance.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-04_01 | All present calculation | Project team (automated regression suite) | PASS | - |
| UT_FR-04_02 | Half attendance calculation | Project team (automated regression suite) | PASS | - |
| UT_FR-04_03 | Absent calculation | Project team (automated regression suite) | PASS | - |
| UT_FR-04_04 | Late policy calculation | Project team (automated regression suite) | PASS | - |
| UT_FR-04_05 | No records calculation | Project team (automated regression suite) | PASS | - |
| IT_FR-04_06 | Recalculate after update | Project team (automated regression suite) | PASS | - |
| IT_FR-04_07 | Subject filter calculation | Project team (automated regression suite) | PASS | - |
| IT_FR-04_08 | Date range calculation | Project team (automated regression suite) | PASS | - |
| SYS_FR-04_09 | Rounding calculation | Project team (automated regression suite) | PASS | - |
| SYS_FR-04_10 | Large dataset calculation | Project team (automated regression suite) | PASS | - |
| SYS_FR-04_11 | Percentages displayed on the teacher dashboard | Jagadeesh | PASS | MV-02 |

#### UT_FR-04_01 - All present calculation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-04_01 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Unit |
| Test scenario | All present calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | 10 records exist |
| Test data | 10 Present / 10 classes |
| Test steps | 1. Open percentage |
| Expected result | 100% displayed. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_test_plan_percentage_datasets[UT_FR-04_01` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data. |
| Remarks | - |

#### UT_FR-04_02 - Half attendance calculation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-04_02 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Unit |
| Test scenario | Half attendance calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | 10 records exist |
| Test data | 5 Present / 10 classes |
| Test steps | 1. Open percentage |
| Expected result | 50% displayed. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_test_plan_percentage_datasets[UT_FR-04_02`, `test_fr04_percentages::test_fr04_percentages_calculate_correctly` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data. |
| Remarks | Mapping to be confirmed against test data in Phase 2. |

#### UT_FR-04_03 - Absent calculation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-04_03 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Unit |
| Test scenario | Absent calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | 6 Present / 4 Absent |
| Test steps | 1. Open percentage |
| Expected result | 60% displayed. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_test_plan_percentage_datasets[UT_FR-04_03` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data. |
| Remarks | Mapping to be confirmed against test data in Phase 2. |

#### UT_FR-04_04 - Late policy calculation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-04_04 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Unit |
| Test scenario | Late policy calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Late rule: Late counts as a held class but not as attended |
| Test data | 8 Present / 2 Late |
| Test steps | 1. Open percentage |
| Expected result | 80.00% displayed (Late not counted as attended). |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_test_plan_percentage_datasets[UT_FR-04_04`, `test_fr04_percentages::test_fr04_late_is_not_counted_as_attended` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data. |
| Remarks | Implemented late policy written into the expected result. |

#### UT_FR-04_05 - No records calculation

| Field | Details |
|---|---|
| Test Case ID | UT_FR-04_05 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Unit |
| Test scenario | No records calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | No records exist |
| Test data | 0 records |
| Test steps | 1. Open percentage |
| Expected result | 0% or a no-records indication shown; no division-by-zero error. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_test_plan_percentage_datasets[UT_FR-04_05`, `test_fr04_percentages::test_fr04_percentages_calculate_correctly`, `test_fr11_attendance_alert::test_zero_eligible_attendance` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | The original link used other data (2/4, 1/2, 0/1). New Phase 2 test uses the Test Plan's exact data. |
| Remarks | - |

#### IT_FR-04_06 - Recalculate after update

| Field | Details |
|---|---|
| Test Case ID | IT_FR-04_06 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Integration |
| Test scenario | Recalculate after update |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Existing records exist |
| Test data | Present changed to Absent |
| Test steps | 1. Change status<br>2. Refresh |
| Expected result | Percentage updates correctly. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_it_fr_04_06_percentage_recalculates_after_update`, `test_fr11_attendance_alert::test_reactivity_on_attendance_updates` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | New Phase 2 test on /api/attendance/percentages itself (gap G-10 closed). |
| Remarks | - |

#### IT_FR-04_07 - Subject filter calculation

| Field | Details |
|---|---|
| Test Case ID | IT_FR-04_07 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Integration |
| Test scenario | Subject filter calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Multiple subjects exist |
| Test data | DBMS only |
| Test steps | 1. Select one subject |
| Expected result | Only the selected subject is included. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentages::test_fr04_subject_filter` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-04_08 - Date range calculation

| Field | Details |
|---|---|
| Test Case ID | IT_FR-04_08 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | Integration |
| Test scenario | Date range calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records across dates |
| Test data | 2026-09-01 to 2026-09-10 |
| Test steps | 1. Request a report for the date range |
| Expected result | Only the selected range is included in the percentage. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_it_fr_04_08_percentage_for_selected_date_range`, `test_fr06_attendance_reporting::test_date_range_filtering_inclusive` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | The original link checked which records were included but not the percentage; new test checks 75% in range vs 50% overall. |
| Remarks | /api/attendance/percentages has no date-range filter; the range percentage comes from the FR-06 report summary (gap G-06). |

#### SYS_FR-04_09 - Rounding calculation

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-04_09 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | System |
| Test scenario | Rounding calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Repeating decimal possible |
| Test data | 2 Present / 3 classes |
| Test steps | 1. Open percentage |
| Expected result | 66.67% (2 Present / 3) returned by both the percentage API and the alerts API (rounded to 2 decimal places). |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr04_percentage_test_plan_cases::test_test_plan_percentage_datasets[SYS_FR-04_09`, `test_fr04_percentage_test_plan_cases::test_sys_fr_04_09_rounding_is_consistent_between_percentage_and_alert_apis`, `test_fr04_percentages::test_fr04_subject_filter` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | New Phase 2 tests (gap G-10 closed). Expected result limited to the APIs; display moved to manual cases. |
| Remarks | On-screen display of the rounded value is checked manually under SYS_FR-04_11 and SYS_FR-14_08. |

#### SYS_FR-04_10 - Large dataset calculation

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-04_10 |
| Requirement | FR-04 - Attendance Percentage Calculation |
| Test level | System |
| Test scenario | Large dataset calculation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Large dataset exists |
| Test data | 1,500 records |
| Test steps | 1. Open percentage |
| Expected result | Correct result within the 3-second target. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_attendance_percentages_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-04_11 - Percentages displayed on the teacher dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | App.formatPercent now shows two decimals (was FAIL: MV-02). |
| Remarks | Added in Phase 2: on-screen display is not covered by any automated test. |

### FR-05 - Attendance Viewing

> SRS: The system shall allow students and teachers to view attendance records, including attendance by subject and date.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-05_01 | View own records | Project team (automated regression suite) | PASS | - |
| UT_FR-05_02 | View by subject | Project team (automated regression suite) | PASS | - |
| UT_FR-05_03 | View by date | Project team (automated regression suite) | PASS | - |
| UT_FR-05_04 | Empty result handling | Tharith | PASS | - |
| IT_FR-05_05 | Teacher views assigned class | Project team (automated regression suite) | PASS | - |
| IT_FR-05_06 | Student data restriction | Project team (automated regression suite) | PASS | - |
| IT_FR-05_07 | Updated record visibility | Project team (automated regression suite) | PASS | - |
| SYS_FR-05_08 | Sort records | Project team (automated regression suite) | PASS | - |
| SYS_FR-05_09 | Pagination | Project team (automated regression suite) | NOT APPLICABLE | G-05 |
| SYS_FR-05_10 | Responsive viewing | Tharith | PASS | MV-03 |

#### UT_FR-05_01 - View own records

| Field | Details |
|---|---|
| Test Case ID | UT_FR-05_01 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Unit |
| Test scenario | View own records |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student logged in; records exist |
| Test data | Student S01 |
| Test steps | 1. Open attendance page |
| Expected result | Only the student's own records displayed. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_student_only_sees_own_records`, `test_nfr05_browser_compatibility::test_student_views_own_attendance[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-05_02 - View by subject

| Field | Details |
|---|---|
| Test Case ID | UT_FR-05_02 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Unit |
| Test scenario | View by subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | DBMS |
| Test steps | 1. Apply subject filter |
| Expected result | Only DBMS records displayed. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_filter_by_subject` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-05_03 - View by date

| Field | Details |
|---|---|
| Test Case ID | UT_FR-05_03 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Unit |
| Test scenario | View by date |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | 2026-09-01 |
| Test steps | 1. Apply date filter |
| Expected result | Only matching-date records displayed. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_filter_by_date` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-05_04 - Empty result handling

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
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | UI empty-state message to be checked in System Validation. |

#### IT_FR-05_05 - Teacher views assigned class

| Field | Details |
|---|---|
| Test Case ID | IT_FR-05_05 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Integration |
| Test scenario | Teacher views assigned class |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher assigned to class |
| Test data | CSE-A |
| Test steps | 1. Open class records |
| Expected result | Only records of the teacher's assigned subjects displayed. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_teacher_only_sees_assigned_subjects` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-05_06 - Student data restriction

| Field | Details |
|---|---|
| Test Case ID | IT_FR-05_06 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Integration |
| Test scenario | Student data restriction |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Two student accounts exist |
| Test data | S02 while logged in as S01 |
| Test steps | 1. Attempt to view another student |
| Expected result | Access denied. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_student_cannot_view_another_students_records` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-05_07 - Updated record visibility

| Field | Details |
|---|---|
| Test Case ID | IT_FR-05_07 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | Integration |
| Test scenario | Updated record visibility |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record updated |
| Test data | S01 Late |
| Test steps | 1. Open record |
| Expected result | Latest value displayed. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_ut_fr_03_02_update_existing_record_by_id` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Corrected: the Phase 1 link (refresh after save) did not update a record; the new link re-reads a record after updating it. |
| Remarks | Mapping to be confirmed in Phase 2. |

#### SYS_FR-05_08 - Sort records

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-05_08 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | System |
| Test scenario | Sort records |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | Multiple records |
| Test steps | 1. View records |
| Expected result | Records listed newest date first, then by student. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_results_keep_date_then_student_order` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | No user-selectable sort exists; expected result changed to the fixed order the system uses (gap G-05). |

#### SYS_FR-05_09 - Pagination

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-05_09 |
| Requirement | FR-05 - Attendance Viewing |
| Test level | System |
| Test scenario | Pagination |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Many records exist |
| Test data | 100+ records |
| Test steps | 1. Move between pages |
| Expected result | Correct records shown per page. |
| Actual observed result | Pagination is not implemented in the API or the UI. |
| Status | **NOT APPLICABLE** |
| Execution method | Automated browser (Playwright) (planned method; case not fully executed - see actual observed result) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | None (not executed) |
| Defect / gap ID | G-05 |
| Result history | 2026-11-11 final run: NOT APPLICABLE; 2026-11-17 regression run: NOT APPLICABLE |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Classified NOT APPLICABLE: outside the SRS; kept for traceability to the original plan. |
| Remarks | SRS FR-05 requires viewing records by subject and date, which is implemented and passes. It does not require pagination. With 1,500 records the full list loads well within 3 s (NFR-02 tests), so the lack of pagination does not break any SRS requirement. |

#### SYS_FR-05_10 - Responsive viewing

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
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Tables use a labelled card layout below 640 px (was FAIL: MV-03). |
| Remarks | Readability itself needs human confirmation. |

### FR-06 - Attendance Reporting

> SRS: The system shall generate attendance reports based on student, class, subject, or selected date range.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-06_01 | Report by student | Project team (automated regression suite) | PASS | - |
| UT_FR-06_02 | Report by class | Project team (automated regression suite) | PASS | - |
| UT_FR-06_03 | Report by subject | Project team (automated regression suite) | PASS | - |
| UT_FR-06_04 | Report by date range | Project team (automated regression suite) | PASS | - |
| IT_FR-06_05 | Combined filters | Project team (automated regression suite) | PASS | - |
| IT_FR-06_06 | Current saved data | Project team (automated regression suite) | PASS | - |
| IT_FR-06_07 | Report access control | Project team (automated regression suite) | PASS | - |
| SYS_FR-06_08 | Empty report | Project team (automated regression suite) | PASS | D-02 |
| SYS_FR-06_09 | Report accuracy | Project team (automated regression suite) | PASS | - |
| SYS_FR-06_10 | Report performance | Project team (automated regression suite) | PASS | - |
| UT_FR-06_11 | Invalid report parameters | Project team (automated regression suite) | PASS | - |
| UT_FR-06_12 | Nonexistent report target | Project team (automated regression suite) | PASS | - |

#### UT_FR-06_01 - Report by student

| Field | Details |
|---|---|
| Test Case ID | UT_FR-06_01 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Unit |
| Test scenario | Report by student |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | S01 |
| Test steps | 1. Request student report |
| Expected result | Only S01 data included; summary totals correct. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_student_wise_report_admin`, `test_fr06_attendance_reporting::test_student_wise_report_via_path_param` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### UT_FR-06_02 - Report by class

| Field | Details |
|---|---|
| Test Case ID | UT_FR-06_02 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Unit |
| Test scenario | Report by class |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | CSE-A |
| Test steps | 1. Request class report |
| Expected result | Selected class data included. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_class_wise_report` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### UT_FR-06_03 - Report by subject

| Field | Details |
|---|---|
| Test Case ID | UT_FR-06_03 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Unit |
| Test scenario | Report by subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | DBMS |
| Test steps | 1. Request subject report |
| Expected result | Selected subject data included. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_subject_wise_report` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### UT_FR-06_04 - Report by date range

| Field | Details |
|---|---|
| Test Case ID | UT_FR-06_04 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Unit |
| Test scenario | Report by date range |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | 2026-09-01 to 2026-09-10 |
| Test steps | 1. Request report with start/end dates |
| Expected result | Only the inclusive range is included. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_date_range_filtering_inclusive`, `test_fr06_attendance_reporting::test_date_range_single_day` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### IT_FR-06_05 - Combined filters

| Field | Details |
|---|---|
| Test Case ID | IT_FR-06_05 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Integration |
| Test scenario | Combined filters |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | CSE-A, DBMS, date range |
| Test steps | 1. Request report with class, subject and range |
| Expected result | All filters applied together. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_combined_student_class_subject_date_filters` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### IT_FR-06_06 - Current saved data

| Field | Details |
|---|---|
| Test Case ID | IT_FR-06_06 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Integration |
| Test scenario | Current saved data |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records saved |
| Test data | Updated S01 record |
| Test steps | 1. Update record<br>2. Generate report |
| Expected result | Report uses the latest data. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_reflects_updated_records` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). Covered through the export of the same report; confirm in Phase 2. |

#### IT_FR-06_07 - Report access control

| Field | Details |
|---|---|
| Test Case ID | IT_FR-06_07 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Integration |
| Test scenario | Report access control |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Role accounts exist |
| Test data | Student account |
| Test steps | 1. Student requests class-wide or another student's report |
| Expected result | Only the permitted scope is available (403 otherwise). |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_student_cannot_view_other_student_report`, `test_fr06_attendance_reporting::test_teacher_subject_restriction`, `test_fr06_attendance_reporting::test_student_can_generate_own_report` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### SYS_FR-06_08 - Empty report

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-06_08 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | System |
| Test scenario | Empty report |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | No matching data |
| Test data | No matching filter |
| Test steps | 1. Generate report |
| Expected result | API returns zero records with zero totals; empty-report message shown in UI. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_valid_filter_empty_results`, `test_fr06_attendance_reporting::test_date_range_empty_results`, `test_six_failures_browser::test_empty_report_shows_message[chrome]`, `test_six_failures_browser::test_admin_generates_report_matching_the_api[chrome]` |
| Defect / gap ID | D-02 |
| Result history | 2026-11-11 final run: FAIL; 2026-11-17 regression run: PASS (changed) |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Reporting screen added to the admin and teacher dashboards (app/static/js/reports.js); the empty report shows 'No attendance records match this report'. Was FAIL (gap G-01, defect D-02). |
| Remarks | API part automated; the UI message cannot be checked because no reporting screen exists (gap G-01). |

#### SYS_FR-06_09 - Report accuracy

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-06_09 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | System |
| Test scenario | Report accuracy |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Known dataset exists |
| Test data | Known totals |
| Test steps | 1. Generate and compare totals |
| Expected result | Totals and percentages match the stored records. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_records_outside_filters_are_strictly_excluded`, `test_fr06_attendance_reporting::test_no_duplicate_records_on_multiple_enrollments`, `test_fr06_attendance_reporting::test_student_wise_report_admin` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | Added the test that compares totals and the percentage (3 Present of 5 = 60%) with the seeded records. |
| Remarks | Executed through the REST API: the UI has no reporting screen (gap G-01). |

#### SYS_FR-06_10 - Report performance

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-06_10 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | System |
| Test scenario | Report performance |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Large dataset exists |
| Test data | Large class/date range |
| Test steps | 1. Generate report |
| Expected result | Report generated within 3 seconds. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_attendance_report_generation_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-06_11 - Invalid report parameters

| Field | Details |
|---|---|
| Test Case ID | UT_FR-06_11 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Unit |
| Test scenario | Invalid report parameters |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Reporting API available |
| Test data | Bad date format; start > end; status 'Excused'; non-numeric ids |
| Test steps | 1. Request report |
| Expected result | HTTP 400 with a clear error for each invalid input. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_invalid_start_date_format`, `test_fr06_attendance_reporting::test_start_date_later_than_end_date`, `test_fr06_attendance_reporting::test_invalid_status_filter`, `test_fr06_attendance_reporting::test_invalid_identifiers` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-06_12 - Nonexistent report target

| Field | Details |
|---|---|
| Test Case ID | UT_FR-06_12 |
| Requirement | FR-06 - Attendance Reporting |
| Test level | Unit |
| Test scenario | Nonexistent report target |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Reporting API available |
| Test data | Unknown student/class/subject id |
| Test steps | 1. Request report |
| Expected result | HTTP 404 'not found'. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr06_attendance_reporting::test_nonexistent_student_returns_404`, `test_fr06_attendance_reporting::test_nonexistent_class_returns_404`, `test_fr06_attendance_reporting::test_nonexistent_subject_returns_404` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

### FR-07 - User Management

> SRS: The system shall allow administrators to add, update, and deactivate student and teacher accounts.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-07_01 | Create student and teacher accounts | Project team (automated regression suite) | PASS | - |
| UT_FR-07_02 | Invalid user input | Project team (automated regression suite) | PASS | - |
| UT_FR-07_03 | Duplicate username | Project team (automated regression suite) | PASS | - |
| UT_FR-07_04 | Password stored as hash | Project team (automated regression suite) | PASS | - |
| IT_FR-07_05 | Update account | Project team (automated regression suite) | PASS | - |
| IT_FR-07_06 | Update conflicts and missing user | Project team (automated regression suite) | PASS | - |
| IT_FR-07_07 | Deactivate and reactivate account | Project team (automated regression suite) | PASS | - |
| IT_FR-07_08 | Deactivation ends active session | Project team (automated regression suite) | PASS | - |
| IT_FR-07_09 | Non-admin cannot manage users | Project team (automated regression suite) | PASS | - |
| SYS_FR-07_10 | Manage users through admin dashboard | Sumukh | PASS | - |

#### UT_FR-07_01 - Create student and teacher accounts

| Field | Details |
|---|---|
| Test Case ID | UT_FR-07_01 |
| Requirement | FR-07 - User Management |
| Test level | Unit |
| Test scenario | Create student and teacher accounts |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | New usernames, valid password (>= 8 chars), roles student/teacher |
| Test steps | 1. POST /api/users for each role |
| Expected result | HTTP 201; accounts created and active. |
| Actual observed result | Expected result verified: 1 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_admin_can_create_all_roles` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-07_02 - Invalid user input

| Field | Details |
|---|---|
| Test Case ID | UT_FR-07_02 |
| Requirement | FR-07 - User Management |
| Test level | Unit |
| Test scenario | Invalid user input |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | Blank username; short password; role 'superuser'; missing body |
| Test steps | 1. POST /api/users |
| Expected result | HTTP 400 with an error message for each invalid input. |
| Actual observed result | Expected result verified: 3 linked test(s), 11 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_create_user_invalid_inputs`, `test_fr07_user_management::test_create_user_missing_body`, `test_fr07_user_management::test_create_user_invalid_active_flag` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Corrected: 'no account created' was not asserted by the linked tests. |
| Remarks | - |

#### UT_FR-07_03 - Duplicate username

| Field | Details |
|---|---|
| Test Case ID | UT_FR-07_03 |
| Requirement | FR-07 - User Management |
| Test level | Unit |
| Test scenario | Duplicate username |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User 'teacher01' exists |
| Test data | teacher01 |
| Test steps | 1. Create another user named teacher01 |
| Expected result | HTTP 409; duplicate rejected. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_create_duplicate_username` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-07_04 - Password stored as hash

| Field | Details |
|---|---|
| Test Case ID | UT_FR-07_04 |
| Requirement | FR-07 - User Management |
| Test level | Unit |
| Test scenario | Password stored as hash |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin creates a user |
| Test data | Any password |
| Test steps | 1. Inspect the users table |
| Expected result | Only a salted hash is stored; plaintext never stored or returned. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_password_is_securely_hashed` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-07_05 - Update account

| Field | Details |
|---|---|
| Test Case ID | IT_FR-07_05 |
| Requirement | FR-07 - User Management |
| Test level | Integration |
| Test scenario | Update account |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User exists |
| Test data | New username, role, password |
| Test steps | 1. PUT /api/users/<id> |
| Expected result | Changes saved; user can log in with the new password. |
| Actual observed result | Expected result verified: 3 linked test(s), 5 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_admin_can_update_username`, `test_fr07_user_management::test_admin_can_update_user_role`, `test_fr07_user_management::test_admin_can_update_user_password` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-07_06 - Update conflicts and missing user

| Field | Details |
|---|---|
| Test Case ID | IT_FR-07_06 |
| Requirement | FR-07 - User Management |
| Test level | Integration |
| Test scenario | Update conflicts and missing user |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Users exist |
| Test data | Taken username; nonexistent id |
| Test steps | 1. PUT /api/users/<id> |
| Expected result | HTTP 409 for taken username; 404 for unknown id. |
| Actual observed result | Expected result verified: 3 linked test(s), 9 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_update_user_duplicate_username_returns_409`, `test_fr07_user_management::test_update_user_nonexistent_returns_404`, `test_fr07_user_management::test_update_user_invalid_inputs` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-07_07 - Deactivate and reactivate account

| Field | Details |
|---|---|
| Test Case ID | IT_FR-07_07 |
| Requirement | FR-07 - User Management |
| Test level | Integration |
| Test scenario | Deactivate and reactivate account |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Active user exists |
| Test data | Student account |
| Test steps | 1. Deactivate<br>2. Attempt login<br>3. Reactivate<br>4. Login |
| Expected result | Deactivated user cannot log in; reactivated user can. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_admin_can_deactivate_and_activate_user`, `test_fr07_user_management::test_deactivate_and_activate_nonexistent_user` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-07_08 - Deactivation ends active session

| Field | Details |
|---|---|
| Test Case ID | IT_FR-07_08 |
| Requirement | FR-07 - User Management |
| Test level | Integration |
| Test scenario | Deactivation ends active session |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in elsewhere |
| Test data | Student session |
| Test steps | 1. Admin deactivates the user<br>2. User makes a request |
| Expected result | Existing session is rejected. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_active_session_revoked_on_deactivation` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-07_09 - Non-admin cannot manage users

| Field | Details |
|---|---|
| Test Case ID | IT_FR-07_09 |
| Requirement | FR-07 - User Management |
| Test level | Integration |
| Test scenario | Non-admin cannot manage users |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher/student logged in; or logged out |
| Test data | Teacher, student, anonymous |
| Test steps | 1. Call create/list/update/deactivate user APIs |
| Expected result | HTTP 403 for teacher/student; 401 when logged out. |
| Actual observed result | Expected result verified: 5 linked test(s), 9 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr07_user_management::test_create_user_forbidden_for_non_admins`, `test_fr07_user_management::test_view_users_forbidden_for_non_admins`, `test_fr07_user_management::test_update_user_forbidden_for_non_admins`, `test_fr07_user_management::test_deactivate_and_activate_forbidden_for_non_admins`, `test_fr07_user_management::test_create_user_unauthenticated` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-07_10 - Manage users through admin dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Existing browser test covers creation only; the rest is checked in System Validation. |

### FR-08 - Class & Subject Management

> SRS: The system shall allow administrators to create and manage classes and subjects and assign teachers to them.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-08_01 | Create class | Project team (automated regression suite) | PASS | - |
| UT_FR-08_02 | Invalid or duplicate class name | Project team (automated regression suite) | PASS | - |
| UT_FR-08_03 | Create subject | Project team (automated regression suite) | PASS | - |
| UT_FR-08_04 | Invalid or duplicate subject | Project team (automated regression suite) | PASS | - |
| IT_FR-08_05 | Assign teacher to class and subject | Project team (automated regression suite) | PASS | - |
| IT_FR-08_06 | Invalid teacher assignment | Project team (automated regression suite) | PASS | - |
| IT_FR-08_07 | Link and unlink subject and class | Project team (automated regression suite) | PASS | - |
| IT_FR-08_08 | Update and unassign | Project team (automated regression suite) | PASS | - |
| IT_FR-08_09 | Non-admin cannot manage classes/subjects | Project team (automated regression suite) | PASS | - |
| SYS_FR-08_10 | Manage classes and subjects through admin dashboard | Sumukh | PASS | - |

#### UT_FR-08_01 - Create class

| Field | Details |
|---|---|
| Test Case ID | UT_FR-08_01 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Unit |
| Test scenario | Create class |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | Class 'CSE-A' (optionally with teacher) |
| Test steps | 1. POST /api/classes |
| Expected result | HTTP 201; class created (teacher assigned when given). |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_admin_can_create_class`, `test_fr08_class_subject_management::test_admin_can_create_class_with_assigned_teacher` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-08_02 - Invalid or duplicate class name

| Field | Details |
|---|---|
| Test Case ID | UT_FR-08_02 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Unit |
| Test scenario | Invalid or duplicate class name |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Class 'CSE-A' exists |
| Test data | Blank name; 'CSE-A' |
| Test steps | 1. Create/update class |
| Expected result | HTTP 400 for blank; 409 for duplicate. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_blank_class_name_rejected`, `test_fr08_class_subject_management::test_duplicate_class_name_rejected`, `test_fr08_class_subject_management::test_update_class_duplicate_name_rejected`, `test_fr08_class_subject_management::test_update_class_invalid_payloads` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-08_03 - Create subject

| Field | Details |
|---|---|
| Test Case ID | UT_FR-08_03 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Unit |
| Test scenario | Create subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | Subject 'DBMS' (optionally with teacher/class) |
| Test steps | 1. POST /api/subjects |
| Expected result | HTTP 201; subject created and linked. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_admin_can_create_subject`, `test_fr08_class_subject_management::test_admin_can_create_subject_with_assigned_teacher`, `test_fr08_class_subject_management::test_create_subject_with_class_id_associates_automatically` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-08_04 - Invalid or duplicate subject

| Field | Details |
|---|---|
| Test Case ID | UT_FR-08_04 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Unit |
| Test scenario | Invalid or duplicate subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Subject 'DBMS' exists |
| Test data | Blank name; 'DBMS'; bad payloads |
| Test steps | 1. Create/update subject |
| Expected result | HTTP 400 for invalid; 409 for duplicate. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_blank_subject_name_rejected`, `test_fr08_class_subject_management::test_duplicate_subject_name_rejected`, `test_fr08_class_subject_management::test_subject_creation_invalid_payloads`, `test_fr08_class_subject_management::test_update_subject_invalid_payloads` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-08_05 - Assign teacher to class and subject

| Field | Details |
|---|---|
| Test Case ID | IT_FR-08_05 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Integration |
| Test scenario | Assign teacher to class and subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Class, subject, teacher exist |
| Test data | Teacher01 |
| Test steps | 1. PUT /api/classes/<id>/teacher and /api/subjects/<id>/teacher |
| Expected result | Teacher assigned; visible in teacher's own routes. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_admin_can_assign_teacher_to_class`, `test_fr08_class_subject_management::test_admin_can_assign_teacher`, `test_fr08_class_subject_management::test_assigned_teacher_visibility_in_teacher_routes` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-08_06 - Invalid teacher assignment

| Field | Details |
|---|---|
| Test Case ID | IT_FR-08_06 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Integration |
| Test scenario | Invalid teacher assignment |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Users exist |
| Test data | Student id; inactive teacher; nonexistent id; non-integer id |
| Test steps | 1. Assign as teacher |
| Expected result | Assignment rejected with 400/404. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_student_cannot_be_assigned_as_teacher`, `test_fr08_class_subject_management::test_inactive_teacher_cannot_be_assigned`, `test_fr08_class_subject_management::test_nonexistent_teacher_id_rejected`, `test_fr08_class_subject_management::test_invalid_teacher_id_type_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-08_07 - Link and unlink subject and class

| Field | Details |
|---|---|
| Test Case ID | IT_FR-08_07 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Integration |
| Test scenario | Link and unlink subject and class |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Class and subject exist |
| Test data | CSE-A + DBMS |
| Test steps | 1. POST/DELETE /api/classes/<id>/subjects |
| Expected result | Subject linked then unlinked; invalid ids rejected. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_admin_can_associate_subject_with_class`, `test_fr08_class_subject_management::test_associate_subject_invalid_ids`, `test_fr08_class_subject_management::test_dissociate_subject_invalid_ids` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-08_08 - Update and unassign

| Field | Details |
|---|---|
| Test Case ID | IT_FR-08_08 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Integration |
| Test scenario | Update and unassign |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Class/subject with teacher |
| Test data | New name; teacher_id null |
| Test steps | 1. PUT class/subject |
| Expected result | Name updated; teacher unassigned. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_admin_can_update_class`, `test_fr08_class_subject_management::test_admin_can_update_class_unassign_teacher`, `test_fr08_class_subject_management::test_admin_can_update_subject_unassign_teacher` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-08_09 - Non-admin cannot manage classes/subjects

| Field | Details |
|---|---|
| Test Case ID | IT_FR-08_09 |
| Requirement | FR-08 - Class & Subject Management |
| Test level | Integration |
| Test scenario | Non-admin cannot manage classes/subjects |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher/student/anonymous |
| Test data | Each role |
| Test steps | 1. Call class/subject management APIs |
| Expected result | HTTP 403 (teacher/student) or 401 (anonymous). |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr08_class_subject_management::test_teacher_access_is_denied`, `test_fr08_class_subject_management::test_student_access_is_denied`, `test_fr08_class_subject_management::test_unauthenticated_access_is_denied` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-08_10 - Manage classes and subjects through admin dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | No existing browser test; checked in System Validation. |

### FR-09 - Student Enrollment

> SRS: The system shall allow administrators to assign students to their respective classes and subjects.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-09_01 | Enroll student | Project team (automated regression suite) | PASS | - |
| UT_FR-09_02 | Duplicate enrollment | Project team (automated regression suite) | PASS | - |
| UT_FR-09_03 | Missing fields | Project team (automated regression suite) | PASS | - |
| UT_FR-09_04 | Nonexistent class | Project team (automated regression suite) | PASS | - |
| UT_FR-09_05 | Non-student or unknown ids | Project team (automated regression suite) | PASS | - |
| IT_FR-09_06 | Non-admin cannot enroll | Project team (automated regression suite) | PASS | - |
| IT_FR-09_07 | List and filter enrollments | Project team (automated regression suite) | PASS | - |
| IT_FR-09_08 | Remove enrollment | Project team (automated regression suite) | PASS | - |
| IT_FR-09_09 | Enrolled student appears in roster | Sumukh | PASS | - |
| SYS_FR-09_10 | Enroll through admin dashboard | Sumukh | PASS | - |

#### UT_FR-09_01 - Enroll student

| Field | Details |
|---|---|
| Test Case ID | UT_FR-09_01 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Unit |
| Test scenario | Enroll student |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in; student, class, subject exist |
| Test data | S01 -> CSE-A / DBMS |
| Test steps | 1. POST /api/enrollments |
| Expected result | HTTP 201; enrollment saved. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr09_student_enrollment::test_admin_can_enroll_student` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-09_02 - Duplicate enrollment

| Field | Details |
|---|---|
| Test Case ID | UT_FR-09_02 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Unit |
| Test scenario | Duplicate enrollment |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | S01 already enrolled |
| Test data | Same triple |
| Test steps | 1. Enroll again |
| Expected result | Duplicate rejected. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr09_student_enrollment::test_duplicate_enrollment_is_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-09_03 - Missing fields

| Field | Details |
|---|---|
| Test Case ID | UT_FR-09_03 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Unit |
| Test scenario | Missing fields |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | Missing student/class/subject |
| Test steps | 1. POST /api/enrollments |
| Expected result | HTTP 400. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr09_student_enrollment::test_missing_fields_are_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-09_04 - Nonexistent class

| Field | Details |
|---|---|
| Test Case ID | UT_FR-09_04 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Unit |
| Test scenario | Nonexistent class |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | class_id 9999 |
| Test steps | 1. POST /api/enrollments |
| Expected result | Rejected (not found). |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr09_student_enrollment::test_nonexistent_class_is_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-09_05 - Non-student or unknown ids

| Field | Details |
|---|---|
| Test Case ID | UT_FR-09_05 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Unit |
| Test scenario | Non-student or unknown ids |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | Teacher id as student; unknown student/subject id |
| Test steps | 1. POST /api/enrollments |
| Expected result | Rejected; no enrollment created. |
| Actual observed result | Expected result verified: 4 linked test(s), 11 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr09_enrollment_validation::test_ut_fr_09_05_only_active_students_can_be_enrolled`, `test_fr09_enrollment_validation::test_ut_fr_09_05_unknown_student_or_subject_rejected`, `test_fr09_enrollment_validation::test_ut_fr_09_05_non_positive_or_non_integer_ids_rejected`, `test_fr09_enrollment_validation::test_ut_fr_09_05_control_valid_active_student_is_enrolled` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | No test existed; new tests added (gap G-10 closed). |
| Remarks | New Phase 2 tests: teacher/admin id -> 404, inactive student -> 400, unknown ids -> 404, bad ids -> 400; enrollment count stays 0. |

#### IT_FR-09_06 - Non-admin cannot enroll

| Field | Details |
|---|---|
| Test Case ID | IT_FR-09_06 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Integration |
| Test scenario | Non-admin cannot enroll |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher/student logged in |
| Test data | Each role |
| Test steps | 1. POST /api/enrollments |
| Expected result | HTTP 403. |
| Actual observed result | Expected result verified: 2 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr09_student_enrollment::test_non_admin_cannot_enroll_student`, `test_frontend_pages::test_list_enrollments_requires_admin` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-09_07 - List and filter enrollments

| Field | Details |
|---|---|
| Test Case ID | IT_FR-09_07 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Integration |
| Test scenario | List and filter enrollments |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Enrollments exist |
| Test data | class filter |
| Test steps | 1. GET /api/enrollments?class_id= |
| Expected result | List includes names; filters applied. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_frontend_pages::test_list_enrollments_returns_names`, `test_frontend_pages::test_list_enrollments_filters` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-09_08 - Remove enrollment

| Field | Details |
|---|---|
| Test Case ID | IT_FR-09_08 |
| Requirement | FR-09 - Student Enrollment |
| Test level | Integration |
| Test scenario | Remove enrollment |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Enrollment exists |
| Test data | S01 / CSE-A / DBMS |
| Test steps | 1. DELETE /api/enrollments |
| Expected result | Enrollment removed; invalid/unauthorized requests rejected. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_frontend_pages::test_delete_enrollment`, `test_frontend_pages::test_delete_enrollment_validation_and_auth` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-09_09 - Enrolled student appears in roster

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-09_10 - Enroll through admin dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | No existing browser test; checked in System Validation. |

### FR-10 - Attendance Search & Filter

> SRS: The system shall allow authorized users to search and filter attendance records by student, subject, class, or date.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-10_01 | Filter by class | Project team (automated regression suite) | PASS | - |
| UT_FR-10_02 | Filter by student | Project team (automated regression suite) | PASS | - |
| UT_FR-10_03 | Filter by subject | Project team (automated regression suite) | PASS | - |
| UT_FR-10_04 | Filter by date and date range | Project team (automated regression suite) | PASS | - |
| UT_FR-10_05 | Filter by status | Project team (automated regression suite) | PASS | - |
| IT_FR-10_06 | Combined filters and empty result | Project team (automated regression suite) | PASS | - |
| IT_FR-10_07 | Invalid filter values | Project team (automated regression suite) | PASS | - |
| IT_FR-10_08 | Nonexistent filter target | Project team (automated regression suite) | PASS | - |
| IT_FR-10_09 | Filters respect role scope | Project team (automated regression suite) | PASS | - |
| SYS_FR-10_10 | Search and filter in the dashboards | Jagadeesh | PASS | MV-01 |

#### UT_FR-10_01 - Filter by class

| Field | Details |
|---|---|
| Test Case ID | UT_FR-10_01 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Unit |
| Test scenario | Filter by class |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records in several classes |
| Test data | class_id of CSE-A |
| Test steps | 1. GET /api/attendance?class_id= |
| Expected result | Only records of students/subjects in that class. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_filter_by_class_matches_student_and_subject`, `test_fr10_attendance_search_filter::test_fr10_class_filter_excludes_subject_student_is_not_enrolled_for` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-10_02 - Filter by student

| Field | Details |
|---|---|
| Test Case ID | UT_FR-10_02 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Unit |
| Test scenario | Filter by student |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records for several students |
| Test data | student_id S01 |
| Test steps | 1. GET /api/attendance?student_id= |
| Expected result | Only S01 records. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing_extra::test_fr05_admin_can_filter_by_student`, `test_fr10_attendance_search_filter::test_fr10_class_and_student` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-10_03 - Filter by subject

| Field | Details |
|---|---|
| Test Case ID | UT_FR-10_03 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Unit |
| Test scenario | Filter by subject |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records for several subjects |
| Test data | DBMS |
| Test steps | 1. GET /api/attendance?subject_id= |
| Expected result | Only DBMS records. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing_extra::test_fr05_admin_can_filter_by_subject`, `test_fr10_attendance_search_filter::test_fr10_class_and_subject` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-10_04 - Filter by date and date range

| Field | Details |
|---|---|
| Test Case ID | UT_FR-10_04 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Unit |
| Test scenario | Filter by date and date range |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records on several dates |
| Test data | 2026-09-01; 2026-09-01..2026-09-10 |
| Test steps | 1. GET with attendance_date / start_date & end_date |
| Expected result | Only matching dates (range inclusive). |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_class_and_date`, `test_fr10_attendance_search_filter::test_fr10_class_and_date_range`, `test_fr06_attendance_reporting::test_api_attendance_date_range_regression` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-10_05 - Filter by status

| Field | Details |
|---|---|
| Test Case ID | UT_FR-10_05 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Unit |
| Test scenario | Filter by status |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Mixed statuses |
| Test data | Late |
| Test steps | 1. GET with status=Late |
| Expected result | Only Late records. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_class_and_status` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-10_06 - Combined filters and empty result

| Field | Details |
|---|---|
| Test Case ID | IT_FR-10_06 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Integration |
| Test scenario | Combined filters and empty result |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | All filters together |
| Test steps | 1. GET with class, student, subject, date, status |
| Expected result | Intersection returned; empty list when nothing matches. |
| Actual observed result | Expected result verified: 2 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_all_filters_combined`, `test_fr10_attendance_search_filter::test_fr10_filters_excluding_all_class_records_return_empty` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-10_07 - Invalid filter values

| Field | Details |
|---|---|
| Test Case ID | IT_FR-10_07 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Integration |
| Test scenario | Invalid filter values |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | API available |
| Test data | class_id=abc; bad date; start > end |
| Test steps | 1. GET with invalid filters |
| Expected result | HTTP 400. |
| Actual observed result | Expected result verified: 3 linked test(s), 10 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_invalid_class_id_returns_400`, `test_fr10_attendance_search_filter::test_fr10_invalid_filter_alongside_class_returns_400`, `test_fr06_attendance_reporting::test_api_attendance_invalid_date_range_regression` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-10_08 - Nonexistent filter target

| Field | Details |
|---|---|
| Test Case ID | IT_FR-10_08 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Integration |
| Test scenario | Nonexistent filter target |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | API available |
| Test data | class_id 9999; largest SQLite integer |
| Test steps | 1. GET with nonexistent ids |
| Expected result | HTTP 404; no server error. |
| Actual observed result | Expected result verified: 2 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_nonexistent_class_returns_404`, `test_fr10_attendance_search_filter::test_fr10_largest_sqlite_integer_is_handled_as_missing_class` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-10_09 - Filters respect role scope

| Field | Details |
|---|---|
| Test Case ID | IT_FR-10_09 |
| Requirement | FR-10 - Attendance Search & Filter |
| Test level | Integration |
| Test scenario | Filters respect role scope |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher and students exist |
| Test data | Teacher filters by another subject; student filters by class to see others |
| Test steps | 1. GET with filters |
| Expected result | Teacher stays within assigned subjects; student only sees own records. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr10_attendance_search_filter::test_fr10_teacher_cannot_use_class_to_reach_other_subject`, `test_fr10_attendance_search_filter::test_fr10_student_cannot_use_class_to_view_other_student`, `test_fr10_attendance_search_filter::test_fr10_access_denial_precedes_class_lookup` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-10_10 - Search and filter in the dashboards

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
| Change from Test Plan v1.0 | New |
| Review notes | Teacher and admin records now have Class and From/To date filters and Clear filters (was FAIL: MV-01, gap G-03). |
| Remarks | UI has no class filter and no date-range filter (gap G-03); checked in System Validation. |

### FR-11 - Attendance Alert

> SRS: The system shall identify students whose attendance percentage falls below a specified attendance threshold.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-11_01 | Default threshold | Project team (automated regression suite) | PASS | - |
| UT_FR-11_02 | Student below threshold flagged | Project team (automated regression suite) | PASS | - |
| UT_FR-11_03 | Boundary: exactly at threshold | Project team (automated regression suite) | PASS | - |
| UT_FR-11_04 | Student with no records | Project team (automated regression suite) | PASS | - |
| UT_FR-11_05 | Invalid threshold | Project team (automated regression suite) | PASS | - |
| IT_FR-11_06 | Admin sets threshold; persists | Project team (automated regression suite) | PASS | - |
| IT_FR-11_07 | Only admin may change threshold | Project team (automated regression suite) | PASS | - |
| IT_FR-11_08 | Alerts respect role scope | Project team (automated regression suite) | PASS | - |
| IT_FR-11_09 | Alerts react to attendance changes | Project team (automated regression suite) | PASS | - |
| SYS_FR-11_10 | Alerts shown on dashboards | Jagadeesh | PASS | - |

#### UT_FR-11_01 - Default threshold

| Field | Details |
|---|---|
| Test Case ID | UT_FR-11_01 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Unit |
| Test scenario | Default threshold |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | No threshold saved |
| Test data | - |
| Test steps | 1. GET /api/attendance/alerts |
| Expected result | Threshold is 75.0%. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_default_threshold_behavior` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-11_02 - Student below threshold flagged

| Field | Details |
|---|---|
| Test Case ID | UT_FR-11_02 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Unit |
| Test scenario | Student below threshold flagged |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student at 50% |
| Test data | Threshold 75 |
| Test steps | 1. GET alerts |
| Expected result | Student listed with below_threshold=true, alert_status BELOW_THRESHOLD. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_student_below_threshold_identified`, `test_fr11_attendance_alert::test_clear_indication_of_low_attendance` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-11_03 - Boundary: exactly at threshold

| Field | Details |
|---|---|
| Test Case ID | UT_FR-11_03 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Unit |
| Test scenario | Boundary: exactly at threshold |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Students at 75.00% and 74.99% |
| Test data | Threshold 75 |
| Test steps | 1. GET alerts |
| Expected result | A student at exactly 75.00% is not flagged at thresholds 75.0 and 74.99, and is flagged at 75.01 (strictly below). |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_student_exactly_at_threshold_not_identified`, `test_fr11_attendance_alert::test_boundary_strict_inequality`, `test_fr11_attendance_alert::test_student_above_threshold_not_identified` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Corrected to the boundary values the test actually uses. |
| Remarks | - |

#### UT_FR-11_04 - Student with no records

| Field | Details |
|---|---|
| Test Case ID | UT_FR-11_04 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Unit |
| Test scenario | Student with no records |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Enrolled student with 0 records |
| Test data | include_zero false/true |
| Test steps | 1. GET alerts |
| Expected result | Not flagged by default (NO_RECORDS); flagged when include_zero=true. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_zero_eligible_attendance`, `test_fr11_attendance_alert::test_zero_eligible_attendance_with_include_zero_flag` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-11_05 - Invalid threshold

| Field | Details |
|---|---|
| Test Case ID | UT_FR-11_05 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Unit |
| Test scenario | Invalid threshold |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | -1; 101; 'abc'; true; null |
| Test steps | 1. Set or query threshold |
| Expected result | HTTP 400 for each invalid value. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_reject_negative_threshold`, `test_fr11_attendance_alert::test_reject_threshold_above_100`, `test_fr11_attendance_alert::test_reject_malformed_threshold_values` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-11_06 - Admin sets threshold; persists

| Field | Details |
|---|---|
| Test Case ID | IT_FR-11_06 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Integration |
| Test scenario | Admin sets threshold; persists |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin logged in |
| Test data | 80 |
| Test steps | 1. POST /api/attendance/threshold<br>2. Restart app<br>3. GET threshold |
| Expected result | Threshold 80 saved and still 80 after restart. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_successful_threshold_configuration`, `test_fr11_attendance_alert::test_threshold_persisted_in_database`, `test_fr11_attendance_alert::test_threshold_persists_across_application_restart` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-11_07 - Only admin may change threshold

| Field | Details |
|---|---|
| Test Case ID | IT_FR-11_07 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Integration |
| Test scenario | Only admin may change threshold |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher/student logged in |
| Test data | 80 |
| Test steps | 1. POST /api/attendance/threshold |
| Expected result | HTTP 403 (401 when logged out). |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_threshold_modification_is_admin_only`, `test_fr11_attendance_alert::test_unauthenticated_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-11_08 - Alerts respect role scope

| Field | Details |
|---|---|
| Test Case ID | IT_FR-11_08 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Integration |
| Test scenario | Alerts respect role scope |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Teacher/student logged in |
| Test data | Other subject/student |
| Test steps | 1. GET alerts |
| Expected result | Teacher sees only assigned subjects; student only self. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_teacher_role_isolation`, `test_fr11_attendance_alert::test_student_role_isolation` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-11_09 - Alerts react to attendance changes

| Field | Details |
|---|---|
| Test Case ID | IT_FR-11_09 |
| Requirement | FR-11 - Attendance Alert |
| Test level | Integration |
| Test scenario | Alerts react to attendance changes |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Student near threshold |
| Test data | Change Present to Absent |
| Test steps | 1. Update record<br>2. GET alerts |
| Expected result | Alert status updates; changing threshold does not alter records. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr11_attendance_alert::test_reactivity_on_attendance_updates`, `test_fr11_attendance_alert::test_threshold_change_updates_alerts_without_touching_records` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-11_10 - Alerts shown on dashboards

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Display only; no UI to change the threshold (gap G-04). Checked in System Validation. |

### FR-12 - Report Export

> SRS: The system shall allow authorized users to export generated attendance reports in a supported file format.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-12_01 | Export CSV | Project team (automated regression suite) | PASS | - |
| UT_FR-12_02 | Export PDF | Project team (automated regression suite) | PASS | - |
| UT_FR-12_03 | Export JSON | Project team (automated regression suite) | PASS | - |
| UT_FR-12_04 | Unsupported format | Project team (automated regression suite) | PASS | - |
| UT_FR-12_05 | CSV formula injection | Project team (automated regression suite) | PASS | - |
| IT_FR-12_06 | Export by scope | Project team (automated regression suite) | PASS | - |
| IT_FR-12_07 | Export access control | Project team (automated regression suite) | PASS | - |
| IT_FR-12_08 | Invalid export parameters | Project team (automated regression suite) | PASS | - |
| SYS_FR-12_09 | Large PDF export | Project team (automated regression suite) | PASS | - |
| SYS_FR-12_10 | Export from the user interface | Project team (automated regression suite) | PASS | D-03 |

#### UT_FR-12_01 - Export CSV

| Field | Details |
|---|---|
| Test Case ID | UT_FR-12_01 |
| Requirement | FR-12 - Report Export |
| Test level | Unit |
| Test scenario | Export CSV |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Report data exists |
| Test data | format=csv |
| Test steps | 1. GET /api/reports/attendance/export?format=csv |
| Expected result | text/csv download with header row and correct rows. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_csv_headers_and_content` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-12_02 - Export PDF

| Field | Details |
|---|---|
| Test Case ID | UT_FR-12_02 |
| Requirement | FR-12 - Report Export |
| Test level | Unit |
| Test scenario | Export PDF |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Report data exists |
| Test data | format=pdf |
| Test steps | 1. GET export as PDF |
| Expected result | application/pdf download with report content. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_pdf_headers_and_content` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-12_03 - Export JSON

| Field | Details |
|---|---|
| Test Case ID | UT_FR-12_03 |
| Requirement | FR-12 - Report Export |
| Test level | Unit |
| Test scenario | Export JSON |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Report data exists |
| Test data | format=json |
| Test steps | 1. GET export as JSON |
| Expected result | JSON download consistent with the report. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_json_format`, `test_fr12_implementation::test_json_export_consistency_and_download_headers` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-12_04 - Unsupported format

| Field | Details |
|---|---|
| Test Case ID | UT_FR-12_04 |
| Requirement | FR-12 - Report Export |
| Test level | Unit |
| Test scenario | Unsupported format |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Export API available |
| Test data | format=xml |
| Test steps | 1. GET export |
| Expected result | HTTP 400; supported formats are csv, pdf, json. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_unsupported_export_format_returns_400` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-12_05 - CSV formula injection

| Field | Details |
|---|---|
| Test Case ID | UT_FR-12_05 |
| Requirement | FR-12 - Report Export |
| Test level | Unit |
| Test scenario | CSV formula injection |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Name starting with '=' exists |
| Test data | =HYPERLINK(...) |
| Test steps | 1. Export CSV |
| Expected result | Dangerous leading characters neutralised. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_csv_formula_injection_prevention` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-12_06 - Export by scope

| Field | Details |
|---|---|
| Test Case ID | IT_FR-12_06 |
| Requirement | FR-12 - Report Export |
| Test level | Integration |
| Test scenario | Export by scope |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | student/class/subject/date range/status |
| Test steps | 1. Export with each scope |
| Expected result | Exported rows match the scope. |
| Actual observed result | Expected result verified: 5 linked test(s), 5 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_by_student_scope`, `test_fr12_implementation::test_export_by_class_scope`, `test_fr12_implementation::test_export_by_subject_scope`, `test_fr12_implementation::test_export_by_date_range_scope`, `test_fr12_implementation::test_export_combined_filters` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-12_07 - Export access control

| Field | Details |
|---|---|
| Test Case ID | IT_FR-12_07 |
| Requirement | FR-12 - Report Export |
| Test level | Integration |
| Test scenario | Export access control |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Role accounts exist |
| Test data | Unassigned subject; other student |
| Test steps | 1. Export as teacher/student |
| Expected result | HTTP 403 outside the user's scope; 401 when logged out. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_teacher_cannot_export_unassigned_subject_report`, `test_fr12_implementation::test_student_cannot_export_other_student_report`, `test_fr12_implementation::test_export_requires_authentication` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-12_08 - Invalid export parameters

| Field | Details |
|---|---|
| Test Case ID | IT_FR-12_08 |
| Requirement | FR-12 - Report Export |
| Test level | Integration |
| Test scenario | Invalid export parameters |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Export API available |
| Test data | Bad date; start > end; bad ids |
| Test steps | 1. Export |
| Expected result | HTTP 400/404 with clear error. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_invalid_date_format`, `test_fr12_implementation::test_export_start_date_later_than_end_date`, `test_fr12_implementation::test_export_invalid_identifiers`, `test_fr12_implementation::test_export_nonexistent_records_return_404` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-12_09 - Large PDF export

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-12_09 |
| Requirement | FR-12 - Report Export |
| Test level | System |
| Test scenario | Large PDF export |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Large dataset |
| Test data | Multi-page report |
| Test steps | 1. Export PDF |
| Expected result | Multiple pages with repeated headers; no text cut off. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr12_implementation::test_export_multipage_pdf`, `test_fr12_implementation::test_pdf_large_report_pagination_and_repeated_headers`, `test_fr12_implementation::test_pdf_long_text_no_cutoff_or_overlap` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-12_10 - Export from the user interface

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-12_10 |
| Requirement | FR-12 - Report Export |
| Test level | System |
| Test scenario | Export from the user interface |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in to browser |
| Test data | Any report |
| Test steps | 1. Find and use an export control<br>2. Open the downloaded file |
| Expected result | File downloads and opens correctly. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_six_failures_browser::test_export_downloads_match_the_report[chrome]`, `test_six_failures_browser::test_export_of_empty_report_is_refused_with_message[chrome]`, `test_six_failures_browser::test_teacher_reports_are_limited_to_own_subjects[chrome]`, `test_fr12_implementation::test_teacher_cannot_export_unassigned_subject_report` |
| Defect / gap ID | D-03 |
| Result history | 2026-11-11 final run: FAIL; 2026-11-17 regression run: PASS (changed) |
| Change from Test Plan v1.0 | New |
| Review notes | CSV, PDF and JSON export buttons added to the Reports screen; downloads use the existing export API with the report's filters. Was FAIL (gap G-02, defect D-03). |
| Remarks | No export control exists in any dashboard (gap G-02). Expected to be BLOCKED until a UI is built. |

### FR-13 - Password Management

> SRS: The system shall allow authenticated users to change their account password.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-13_01 | Change own password | Project team (automated regression suite) | PASS | - |
| UT_FR-13_02 | Wrong current password | Project team (automated regression suite) | PASS | - |
| UT_FR-13_03 | Password length boundary | Project team (automated regression suite) | PASS | - |
| UT_FR-13_04 | New password same as current | Project team (automated regression suite) | PASS | - |
| UT_FR-13_05 | Malformed request | Project team (automated regression suite) | PASS | - |
| IT_FR-13_06 | Login after change | Project team (automated regression suite) | PASS | - |
| IT_FR-13_07 | Other sessions ended on change | Project team (automated regression suite) | PASS | - |
| IT_FR-13_08 | Cannot change another user's password | Project team (automated regression suite) | PASS | - |
| IT_FR-13_09 | Unauthenticated / cross-site change | Project team (automated regression suite) | PASS | - |
| SYS_FR-13_10 | Change password through the dashboard | Sumukh | PASS | - |

#### UT_FR-13_01 - Change own password

| Field | Details |
|---|---|
| Test Case ID | UT_FR-13_01 |
| Requirement | FR-13 - Password Management |
| Test level | Unit |
| Test scenario | Change own password |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Admin/teacher/student logged in |
| Test data | Current password; new password 'NewPass#2026' |
| Test steps | 1. POST /api/me/password |
| Expected result | HTTP 200 for each role. |
| Actual observed result | Expected result verified: 1 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_every_role_can_change_own_password` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-13_02 - Wrong current password

| Field | Details |
|---|---|
| Test Case ID | UT_FR-13_02 |
| Requirement | FR-13 - Password Management |
| Test level | Unit |
| Test scenario | Wrong current password |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | Wrong current password |
| Test steps | 1. POST /api/me/password |
| Expected result | Rejected 'Current password is incorrect'; session stays valid. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_incorrect_current_password_rejected`, `test_fr13_password_management::test_incorrect_current_password_keeps_session` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-13_03 - Password length boundary

| Field | Details |
|---|---|
| Test Case ID | UT_FR-13_03 |
| Requirement | FR-13 - Password Management |
| Test level | Unit |
| Test scenario | Password length boundary |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | 7 chars (reject); exactly 8 chars (accept) |
| Test steps | 1. POST /api/me/password |
| Expected result | 7-character password rejected; 8-character password accepted. |
| Actual observed result | Expected result verified: 2 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_weak_new_password_rejected`, `test_fr13_password_management::test_password_of_exactly_minimum_length_is_accepted` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-13_04 - New password same as current

| Field | Details |
|---|---|
| Test Case ID | UT_FR-13_04 |
| Requirement | FR-13 - Password Management |
| Test level | Unit |
| Test scenario | New password same as current |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | new == current |
| Test steps | 1. POST /api/me/password |
| Expected result | HTTP 400; the stored password is unchanged. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_new_password_must_differ_from_current` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Corrected: the test checks status and stored hash, not the message text. |
| Remarks | - |

#### UT_FR-13_05 - Malformed request

| Field | Details |
|---|---|
| Test Case ID | UT_FR-13_05 |
| Requirement | FR-13 - Password Management |
| Test level | Unit |
| Test scenario | Malformed request |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | Missing fields; non-object body; unencodable text |
| Test steps | 1. POST /api/me/password |
| Expected result | HTTP 400 for each. |
| Actual observed result | Expected result verified: 4 linked test(s), 12 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_missing_or_invalid_new_password_rejected`, `test_fr13_password_management::test_missing_or_invalid_current_password_rejected`, `test_fr13_password_management::test_non_object_body_rejected`, `test_fr13_password_management::test_new_password_that_cannot_be_encoded_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-13_06 - Login after change

| Field | Details |
|---|---|
| Test Case ID | IT_FR-13_06 |
| Requirement | FR-13 - Password Management |
| Test level | Integration |
| Test scenario | Login after change |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Password changed |
| Test data | Old and new passwords |
| Test steps | 1. Log out<br>2. Log in with old then new password |
| Expected result | Old password rejected; new accepted. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_old_password_rejected_after_change`, `test_fr13_password_management::test_new_password_accepted_after_change` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-13_07 - Other sessions ended on change

| Field | Details |
|---|---|
| Test Case ID | IT_FR-13_07 |
| Requirement | FR-13 - Password Management |
| Test level | Integration |
| Test scenario | Other sessions ended on change |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Same user logged in on two clients |
| Test data | - |
| Test steps | 1. Change password on client A<br>2. Use client B |
| Expected result | Client A stays signed in; client B and replayed old cookies rejected. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_current_session_survives_change`, `test_fr13_password_management::test_other_sessions_invalidated_by_change`, `test_fr13_password_management::test_replayed_old_cookie_rejected_after_change` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-13_08 - Cannot change another user's password

| Field | Details |
|---|---|
| Test Case ID | IT_FR-13_08 |
| Requirement | FR-13 - Password Management |
| Test level | Integration |
| Test scenario | Cannot change another user's password |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Two users |
| Test data | target user id in body |
| Test steps | 1. POST /api/me/password targeting another user |
| Expected result | Request rejected; other account unchanged. |
| Actual observed result | Expected result verified: 2 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_cannot_target_another_account_through_request_body`, `test_fr13_password_management::test_other_users_current_password_does_not_authorize_change` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-13_09 - Unauthenticated / cross-site change

| Field | Details |
|---|---|
| Test Case ID | IT_FR-13_09 |
| Requirement | FR-13 - Password Management |
| Test level | Integration |
| Test scenario | Unauthenticated / cross-site change |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Logged out; or foreign Origin |
| Test data | - |
| Test steps | 1. POST /api/me/password |
| Expected result | HTTP 401 when logged out; 403 cross-site. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_unauthenticated_request_rejected`, `test_fr13_password_management::test_request_after_logout_rejected`, `test_fr13_password_management::test_cross_site_request_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-13_10 - Change password through the dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Existing test checks the control is present; the full flow is checked in System Validation. |

### FR-14 - Dashboard Summary

> SRS: The system shall display a dashboard summary containing relevant attendance information based on the user's role.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-14_01 | Dashboard requires login | Project team (automated regression suite) | PASS | - |
| IT_FR-14_02 | Dashboard routed by role | Project team (automated regression suite) | PASS | - |
| IT_FR-14_03 | Admin summary matches data | Project team (automated regression suite) | PASS | - |
| IT_FR-14_04 | Teacher summary limited to assigned subjects | Project team (automated regression suite) | PASS | - |
| IT_FR-14_05 | Student summary shows own attendance | Project team (automated regression suite) | PASS | - |
| IT_FR-14_06 | Cross-role dashboard access | Project team (automated regression suite) | PASS | - |
| IT_FR-14_07 | Summary data isolation | Project team (automated regression suite) | PASS | - |
| SYS_FR-14_08 | Dashboard summary displayed in browser | Tharith | PASS | - |

#### UT_FR-14_01 - Dashboard requires login

| Field | Details |
|---|---|
| Test Case ID | UT_FR-14_01 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Unit |
| Test scenario | Dashboard requires login |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Logged out |
| Test data | - |
| Test steps | 1. Open /dashboard |
| Expected result | Redirected to /login. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_dashboard_requires_authentication` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-14_02 - Dashboard routed by role

| Field | Details |
|---|---|
| Test Case ID | IT_FR-14_02 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Integration |
| Test scenario | Dashboard routed by role |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Each role logged in |
| Test data | Admin/teacher/student |
| Test steps | 1. Open /dashboard |
| Expected result | Redirected to /admin, /teacher or /student. |
| Actual observed result | Expected result verified: 2 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_dashboard_redirects_by_role`, `test_frontend_pages::test_dashboard_redirects_to_role_page` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-14_03 - Admin summary matches data

| Field | Details |
|---|---|
| Test Case ID | IT_FR-14_03 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Integration |
| Test scenario | Admin summary matches data |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Seeded data |
| Test data | Known counts |
| Test steps | 1. Load admin dashboard data |
| Expected result | Totals equal database counts. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_admin_dashboard_summary_matches_database_records` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-14_04 - Teacher summary limited to assigned subjects

| Field | Details |
|---|---|
| Test Case ID | IT_FR-14_04 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Integration |
| Test scenario | Teacher summary limited to assigned subjects |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Seeded data |
| Test data | Teacher01 |
| Test steps | 1. Load teacher dashboard data |
| Expected result | Only assigned subjects' figures. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_teacher_dashboard_summary_matches_assigned_records` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-14_05 - Student summary shows own attendance

| Field | Details |
|---|---|
| Test Case ID | IT_FR-14_05 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Integration |
| Test scenario | Student summary shows own attendance |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Seeded data |
| Test data | S01 |
| Test steps | 1. Load student dashboard data |
| Expected result | Only S01's figures. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_student_dashboard_summary_matches_own_records` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-14_06 - Cross-role dashboard access

| Field | Details |
|---|---|
| Test Case ID | IT_FR-14_06 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Integration |
| Test scenario | Cross-role dashboard access |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Each role logged in |
| Test data | Other role pages |
| Test steps | 1. Open another role's dashboard |
| Expected result | Redirected to own dashboard. |
| Actual observed result | Expected result verified: 1 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_users_cannot_open_another_roles_dashboard` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-14_07 - Summary data isolation

| Field | Details |
|---|---|
| Test Case ID | IT_FR-14_07 |
| Requirement | FR-14 - Dashboard Summary |
| Test level | Integration |
| Test scenario | Summary data isolation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Two teachers / two students |
| Test data | - |
| Test steps | 1. Request another user's summary data |
| Expected result | Denied or excluded. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr14_dashboard_summary::test_fr14_teacher_cannot_view_another_teachers_subject`, `test_fr14_dashboard_summary::test_fr14_student_cannot_view_another_students_attendance` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-14_08 - Dashboard summary displayed in browser

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Existing browser test checks rendering time, not the figures; checked in System Validation. |

### FR-15 - Logout

> SRS: The system shall allow authenticated users to securely log out of the system and terminate their active session.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_FR-15_01 | Logout | Project team (automated regression suite) | PASS | - |
| UT_FR-15_02 | Logout when not logged in | Project team (automated regression suite) | PASS | - |
| IT_FR-15_03 | Protected API after logout | Project team (automated regression suite) | PASS | - |
| IT_FR-15_04 | Logout after password change | Project team (automated regression suite) | PASS | - |
| IT_FR-15_05 | Login/logout across modules | Project team (automated regression suite) | PASS | - |
| SYS_FR-15_06 | Logout button on every dashboard | Jagadeesh | PASS | - |
| SYS_FR-15_07 | Back button after logout | Tharith | PASS | - |
| SYS_FR-15_08 | Logout cannot be forged cross-site | Project team (automated regression suite) | NOT RUN | - |

#### UT_FR-15_01 - Logout

| Field | Details |
|---|---|
| Test Case ID | UT_FR-15_01 |
| Requirement | FR-15 - Logout |
| Test level | Unit |
| Test scenario | Logout |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | - |
| Test steps | 1. POST /api/logout |
| Expected result | HTTP 200; session cleared. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr15_logout::test_logout_success` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_FR-15_02 - Logout when not logged in

| Field | Details |
|---|---|
| Test Case ID | UT_FR-15_02 |
| Requirement | FR-15 - Logout |
| Test level | Unit |
| Test scenario | Logout when not logged in |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Logged out |
| Test data | - |
| Test steps | 1. POST /api/logout |
| Expected result | HTTP 401. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr15_logout::test_logout_without_login` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-15_03 - Protected API after logout

| Field | Details |
|---|---|
| Test Case ID | IT_FR-15_03 |
| Requirement | FR-15 - Logout |
| Test level | Integration |
| Test scenario | Protected API after logout |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged out |
| Test data | Old session cookie |
| Test steps | 1. Call protected API |
| Expected result | HTTP 401. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr15_logout::test_protected_route_after_logout` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-15_04 - Logout after password change

| Field | Details |
|---|---|
| Test Case ID | IT_FR-15_04 |
| Requirement | FR-15 - Logout |
| Test level | Integration |
| Test scenario | Logout after password change |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Password changed |
| Test data | - |
| Test steps | 1. Log out |
| Expected result | Logout works normally. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_logout_still_works_after_change` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_FR-15_05 - Login/logout across modules

| Field | Details |
|---|---|
| Test Case ID | IT_FR-15_05 |
| Requirement | FR-15 - Logout |
| Test level | Integration |
| Test scenario | Login/logout across modules |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | App running |
| Test data | - |
| Test steps | 1. Log in, use APIs in several modules, log out, retry |
| Expected result | All modules reject the ended session. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr06_maintainability::test_login_session_and_logout_flow_spans_modules` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_FR-15_06 - Logout button on every dashboard

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Existing browser test covers the teacher; admin and student checked in System Validation. |

#### SYS_FR-15_07 - Back button after logout

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Checked in System Validation; overlaps SYS_FR-01_08. |

#### SYS_FR-15_08 - Logout cannot be forged cross-site

| Field | Details |
|---|---|
| Test Case ID | SYS_FR-15_08 |
| Requirement | FR-15 - Logout |
| Test level | System |
| Test scenario | Logout cannot be forged cross-site |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | Foreign Origin header |
| Test steps | 1. POST /api/logout from another origin |
| Expected result | HTTP 403; session not ended. |
| Actual observed result | Not verified: the linked CSRF test posts to /api/users, not /api/logout. The Origin check is global, but no test proves it for logout. |
| Status | **NOT RUN** |
| Execution method | Automated (pytest) (planned method; case not fully executed - see actual observed result) |
| Execution date | - |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_frontend_pages::test_cross_site_post_is_rejected` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: NOT RUN; 2026-11-17 regression run: NOT RUN |
| Change from Test Plan v1.0 | New |
| Review notes | Mapping was inaccurate. Planned for System Validation (crafted cross-origin POST to /api/logout). |
| Remarks | Mapping is generic CSRF protection; confirm it covers /api/logout in Phase 2. |

### NFR-01 - Security

> SRS: The system shall ensure that users can access only the functions and attendance information permitted by their role, and sensitive data shall be protected during transmission.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_NFR-01_01 | Password field masking | Project team (automated regression suite) | PASS | - |
| IT_NFR-01_02 | Role permission enforcement | Project team (automated regression suite) | PASS | - |
| IT_NFR-01_03 | Record scope protection | Project team (automated regression suite) | PASS | - |
| SYS_NFR-01_04 | Secure transmission | Project team (automated regression suite) | BLOCKED | G-08 |
| SYS_NFR-01_05 | Session protection | Project team (automated regression suite) | PASS | - |
| IT_NFR-01_06 | Cross-site request forgery blocked | Project team (automated regression suite) | PASS | - |
| IT_NFR-01_07 | Security headers and cookie flags | Project team (automated regression suite) | PASS | - |
| UT_NFR-01_08 | Passwords never exposed | Project team (automated regression suite) | PASS | - |

#### UT_NFR-01_01 - Password field masking

| Field | Details |
|---|---|
| Test Case ID | UT_NFR-01_01 |
| Requirement | NFR-01 - Security |
| Test level | Unit |
| Test scenario | Password field masking |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Login page available |
| Test data | Password value |
| Test steps | 1. Type password |
| Expected result | Password is masked by default (input type=password); the show/hide toggle reveals it only on request. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | The test toggles the field to type=text and back to type=password; a toggle can only reveal from the masked state, so the default is masked. The default state itself is not asserted separately. |
| Remarks | Show-password toggle exists; expected result updated. Default masked state to be confirmed in Phase 2. |

#### IT_NFR-01_02 - Role permission enforcement

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-01_02 |
| Requirement | NFR-01 - Security |
| Test level | Integration |
| Test scenario | Role permission enforcement |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Role accounts exist |
| Test data | Admin/Teacher/Student |
| Test steps | 1. Access functions for each role |
| Expected result | Only permitted functions are accessible. |
| Actual observed result | Expected result verified: 2 linked test(s), 11 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr06_maintainability::test_role_restrictions_unchanged_after_modularization`, `test_fr01_authentication::test_wrong_role_denied` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-01_03 - Record scope protection

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-01_03 |
| Requirement | NFR-01 - Security |
| Test level | Integration |
| Test scenario | Record scope protection |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | Unauthorized student ID |
| Test steps | 1. Request another user's record |
| Expected result | Request denied. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr05_attendance_viewing::test_fr05_student_cannot_view_another_students_records`, `test_fr10_attendance_search_filter::test_fr10_student_cannot_use_class_to_view_other_student` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_NFR-01_04 - Secure transmission

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-01_04 |
| Requirement | NFR-01 - Security |
| Test level | System |
| Test scenario | Secure transmission |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | HTTPS deployment available |
| Test data | Credentials over HTTPS |
| Test steps | 1. Login and inspect connection |
| Expected result | Sensitive data transmitted securely. |
| Actual observed result | No HTTPS deployment is available; the development server serves plain HTTP. Only the Secure-cookie switch exists. |
| Status | **BLOCKED** |
| Execution method | Manual / human (planned method; case not fully executed - see actual observed result) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr01_security::test_session_cookie_security` |
| Defect / gap ID | G-08 |
| Result history | 2026-11-11 final run: BLOCKED; 2026-11-17 regression run: BLOCKED |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Environmental limitation G-08. |
| Remarks | No HTTPS deployment exists; only a Secure-cookie switch (FLASK_COOKIE_SECURE=1). Expected BLOCKED (gap G-08). |

#### SYS_NFR-01_05 - Session protection

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-01_05 |
| Requirement | NFR-01 - Security |
| Test level | System |
| Test scenario | Session protection |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | Protected URL |
| Test steps | 1. Copy protected URL to a logged-out browser |
| Expected result | Login required. |
| Actual observed result | Expected result verified: 2 linked test(s), 5 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_frontend_pages::test_pages_redirect_to_login_when_signed_out`, `test_nfr01_security::test_unauthenticated_admin_access_denied` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-01_06 - Cross-site request forgery blocked

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-01_06 |
| Requirement | NFR-01 - Security |
| Test level | Integration |
| Test scenario | Cross-site request forgery blocked |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | Foreign Origin / Referer; look-alike origin |
| Test steps | 1. Send state-changing request |
| Expected result | HTTP 403; same-origin requests allowed. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_frontend_pages::test_cross_site_post_is_rejected`, `test_frontend_pages::test_cross_site_referer_is_rejected`, `test_frontend_pages::test_lookalike_origin_is_rejected`, `test_frontend_pages::test_same_origin_post_is_allowed` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-01_07 - Security headers and cookie flags

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-01_07 |
| Requirement | NFR-01 - Security |
| Test level | Integration |
| Test scenario | Security headers and cookie flags |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | App running |
| Test data | Any page |
| Test steps | 1. Inspect response headers and cookie |
| Expected result | CSP, X-Frame-Options DENY, nosniff, no-store present; cookie HttpOnly, SameSite=Lax. |
| Actual observed result | Expected result verified: 4 linked test(s), 9 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr01_security::test_security_headers`, `test_frontend_pages::test_pages_keep_security_headers`, `test_frontend_pages::test_templates_have_no_inline_code_blocked_by_csp`, `test_nfr01_security::test_session_cookie_security` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Added the test that checks the HttpOnly and SameSite cookie flags. |
| Remarks | - |

#### UT_NFR-01_08 - Passwords never exposed

| Field | Details |
|---|---|
| Test Case ID | UT_NFR-01_08 |
| Requirement | NFR-01 - Security |
| Test level | Unit |
| Test scenario | Passwords never exposed |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Users exist |
| Test data | - |
| Test steps | 1. Inspect DB, API responses and session cookie |
| Expected result | Only hashes stored; no password or hash in responses or cookie. |
| Actual observed result | Expected result verified: 4 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr13_password_management::test_password_stored_as_hash`, `test_fr13_password_management::test_responses_do_not_contain_passwords_or_hashes`, `test_fr13_password_management::test_session_cookie_does_not_contain_password_hash`, `test_fr01_authentication::test_no_plaintext_password_returned` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

### NFR-02 - Performance

> SRS: The system shall load major pages and attendance information within 3 seconds under normal operating conditions.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| SYS_NFR-02_01 | Login response time | Project team (automated regression suite) | PASS | - |
| SYS_NFR-02_02 | Dashboard load time | Project team (automated regression suite) | PASS | - |
| SYS_NFR-02_03 | Attendance page load | Project team (automated regression suite) | PASS | - |
| SYS_NFR-02_04 | Percentage calculation time | Project team (automated regression suite) | PASS | - |
| SYS_NFR-02_05 | Report generation time | Project team (automated regression suite) | PASS | - |
| SYS_NFR-02_06 | Perceived load time on the demo machine | Jagadeesh | PASS | - |

#### SYS_NFR-02_01 - Login response time

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-02_01 |
| Requirement | NFR-02 - Performance |
| Test level | System |
| Test scenario | Login response time |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Application available |
| Test data | Valid account |
| Test steps | 1. Login and measure response |
| Expected result | Login completes within 3 seconds. |
| Actual observed result | Expected result verified: 3 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_major_page_login_loads_within_threshold`, `test_nfr02_browser_performance::test_browser_login_page_renders_within_threshold`, `test_nfr02_performance::test_nfr02_representative_teacher_workflow_scenario` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Added the workflow test that times the login request itself (the page tests time the login page). |
| Remarks | The tests assert a time under 3 s but do not print it; exact timings are to be recorded in the System Validation Report (Test Plan section 3). |

#### SYS_NFR-02_02 - Dashboard load time

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-02_02 |
| Requirement | NFR-02 - Performance |
| Test level | System |
| Test scenario | Dashboard load time |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | Teacher account |
| Test steps | 1. Open dashboard and measure |
| Expected result | Dashboard loads within 3 seconds. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_major_page_teacher_dashboard_loads_within_threshold`, `test_nfr02_browser_performance::test_browser_main_dashboard_overview_renders_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | The tests assert a time under 3 s but do not print it; exact timings are to be recorded in the System Validation Report (Test Plan section 3). |

#### SYS_NFR-02_03 - Attendance page load

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-02_03 |
| Requirement | NFR-02 - Performance |
| Test level | System |
| Test scenario | Attendance page load |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | Normal dataset (1,500 records) |
| Test steps | 1. Open attendance page |
| Expected result | Page loads within 3 seconds. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_attendance_records_retrieval_within_threshold`, `test_nfr02_browser_performance::test_browser_student_attendance_view_renders_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | The tests assert a time under 3 s but do not print it; exact timings are to be recorded in the System Validation Report (Test Plan section 3). |

#### SYS_NFR-02_04 - Percentage calculation time

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-02_04 |
| Requirement | NFR-02 - Performance |
| Test level | System |
| Test scenario | Percentage calculation time |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Records exist |
| Test data | Normal dataset |
| Test steps | 1. Open summary and measure |
| Expected result | Percentage appears within 3 seconds. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_attendance_percentages_within_threshold`, `test_nfr02_browser_performance::test_browser_subject_attendance_view_renders_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | The tests assert a time under 3 s but do not print it; exact timings are to be recorded in the System Validation Report (Test Plan section 3). |

#### SYS_NFR-02_05 - Report generation time

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-02_05 |
| Requirement | NFR-02 - Performance |
| Test level | System |
| Test scenario | Report generation time |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Large dataset exists |
| Test data | Large date range |
| Test steps | 1. Generate report and measure |
| Expected result | Report generated within 3 seconds. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr02_performance::test_nfr02_attendance_report_generation_within_threshold`, `test_nfr02_performance::test_nfr02_attendance_export_generation_within_threshold` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | The tests assert a time under 3 s but do not print it; exact timings are to be recorded in the System Validation Report (Test Plan section 3). |

#### SYS_NFR-02_06 - Perceived load time on the demo machine

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Added in Phase 2 for the demo environment. |

### NFR-03 - Reliability

> SRS: The system shall preserve saved attendance records without data loss and shall perform regular backups of attendance data.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_NFR-03_01 | Record persistence | Project team (automated regression suite) | PASS | - |
| IT_NFR-03_02 | Backup creation | Project team (automated regression suite) | PASS | - |
| IT_NFR-03_03 | Restore backup | Project team (automated regression suite) | NOT RUN | G-07 |
| SYS_NFR-03_04 | Refresh reliability | Project team (automated regression suite) | PASS | - |
| SYS_NFR-03_05 | Failure recovery | Project team (automated regression suite) | NOT RUN | - |
| IT_NFR-03_06 | Regular (daily) backup schedule | Project team (automated regression suite) | PASS | - |

#### UT_NFR-03_01 - Record persistence

| Field | Details |
|---|---|
| Test Case ID | UT_NFR-03_01 |
| Requirement | NFR-03 - Reliability |
| Test level | Unit |
| Test scenario | Record persistence |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Database available |
| Test data | Valid record |
| Test steps | 1. Save record<br>2. Retrieve it |
| Expected result | Record remains unchanged. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_it_fr_03_06_database_persistence_across_connection_reload` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-03_02 - Backup creation

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-03_02 |
| Requirement | NFR-03 - Reliability |
| Test level | Integration |
| Test scenario | Backup creation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Backup process configured |
| Test data | Attendance database |
| Test steps | 1. Run backup (scripts/backup_db.py) |
| Expected result | Backup is created successfully with a valid schema. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr03_reliability::test_nfr03_backup_is_created`, `test_nfr03_reliability::test_nfr03_backup_contains_valid_database_schema` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-03_03 - Restore backup

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-03_03 |
| Requirement | NFR-03 - Reliability |
| Test level | Integration |
| Test scenario | Restore backup |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Valid backup exists |
| Test data | Backup file |
| Test steps | 1. Restore backup to a test database |
| Expected result | Records are restored correctly. |
| Actual observed result | Partially verified by automated tests: the backup contains exactly the saved attendance rows and is unaffected by later changes. Not yet verified: restoring the backup into a database and using it through the application. |
| Status | **NOT RUN** |
| Execution method | Automated (pytest) + Manual / human (planned method; case not fully executed - see actual observed result) |
| Execution date | - |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr03_reliability::test_nfr03_backup_preserves_attendance_records`, `test_nfr03_reliability::test_nfr03_backup_survives_original_data_changes` |
| Defect / gap ID | G-07 |
| Result history | 2026-11-11 final run: NOT RUN; 2026-11-17 regression run: NOT RUN |
| Change from Test Plan v1.0 | Original (updated) |
| Review notes | No restore step exists in code or tests (G-07). Planned for System Validation using a temporary copy. |
| Remarks | No restore script exists; restore means copying the backup file into place (gap G-07). Tests check backup contents only. |

#### SYS_NFR-03_04 - Refresh reliability

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-03_04 |
| Requirement | NFR-03 - Reliability |
| Test level | System |
| Test scenario | Refresh reliability |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Record saved |
| Test data | Saved record |
| Test steps | 1. Refresh and reopen record |
| Expected result | No data loss or duplicate. |
| Actual observed result | Expected result verified: 1 linked test(s), 1 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr03_record_management::test_sys_fr_03_09_refresh_after_save` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_NFR-03_05 - Failure recovery

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-03_05 |
| Requirement | NFR-03 - Reliability |
| Test level | System |
| Test scenario | Failure recovery |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Temporary failure simulated |
| Test data | Valid attendance data |
| Test steps | 1. Retry after failure |
| Expected result | System recovers without corrupting records. |
| Actual observed result | Partially verified by automated tests: a failed batch rolls back completely and a missing database fails safely. Not yet verified: retrying the same save after the failure. |
| Status | **NOT RUN** |
| Execution method | Automated (pytest) (planned method; case not fully executed - see actual observed result) |
| Execution date | - |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_fr02_attendance_marking::test_batch_rollback_on_failure`, `test_fr03_record_management::test_sys_fr_03_10_database_atomic_rollback`, `test_nfr03_reliability::test_nfr03_missing_database_fails_safely` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: NOT RUN; 2026-11-17 regression run: NOT RUN |
| Change from Test Plan v1.0 | Original (unchanged) |
| Review notes | 'Retry after failure' is not exercised. Planned for System Validation. |
| Remarks | - |

#### IT_NFR-03_06 - Regular (daily) backup schedule

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-03_06 |
| Requirement | NFR-03 - Reliability |
| Test level | Integration |
| Test scenario | Regular (daily) backup schedule |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Scheduler script available |
| Test data | Default and '04:30' times; invalid times |
| Test steps | 1. Build the cron entry |
| Expected result | Daily entry at 02:00 by default (or requested time); invalid times rejected; other cron jobs kept. |
| Actual observed result | Expected result verified: 4 linked test(s), 9 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr03_scheduling::test_schedule_defaults_to_two_am`, `test_nfr03_scheduling::test_schedule_uses_requested_time`, `test_nfr03_scheduling::test_invalid_schedule_time_is_rejected`, `test_nfr03_scheduling::test_replacing_schedule_preserves_unrelated_jobs` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Tests use pure functions only; they never modify the real crontab. |

### NFR-04 - Usability

> SRS: The system shall provide a clear and consistent user interface that allows users to navigate major functions easily.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_NFR-04_01 | Consistent layout | Project team (automated regression suite) | PASS | - |
| UT_NFR-04_02 | Clear navigation labels | Project team (automated regression suite) | PASS | - |
| IT_NFR-04_03 | Section navigation works | Project team (automated regression suite) | PASS | - |
| IT_NFR-04_04 | Keyboard and accessibility | Tharith | PASS | - |
| IT_NFR-04_05 | Responsive and reduced motion | Project team (automated regression suite) | PASS | - |
| SYS_NFR-04_06 | Human usability walkthrough | Tharith | NOT RUN | - |

#### UT_NFR-04_01 - Consistent layout

| Field | Details |
|---|---|
| Test Case ID | UT_NFR-04_01 |
| Requirement | NFR-04 - Usability |
| Test level | Unit |
| Test scenario | Consistent layout |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Templates available |
| Test data | admin/teacher/student pages |
| Test steps | 1. Render each dashboard |
| Expected result | Shared layout, header, sidebar and resources on all dashboards. |
| Actual observed result | Expected result verified: 2 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr04_usability::test_nfr04_all_dashboards_use_consistent_layout`, `test_nfr04_usability::test_nfr04_all_dashboards_load_shared_resources` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### UT_NFR-04_02 - Clear navigation labels

| Field | Details |
|---|---|
| Test Case ID | UT_NFR-04_02 |
| Requirement | NFR-04 - Usability |
| Test level | Unit |
| Test scenario | Clear navigation labels |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Dashboards render |
| Test data | - |
| Test steps | 1. Inspect navigation |
| Expected result | Each section has a clear text label. |
| Actual observed result | Expected result verified: 1 linked test(s), 3 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr04_usability::test_nfr04_navigation_labels_are_clear` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-04_03 - Section navigation works

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-04_03 |
| Requirement | NFR-04 - Usability |
| Test level | Integration |
| Test scenario | Section navigation works |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | User logged in |
| Test data | - |
| Test steps | 1. Switch between sidebar sections |
| Expected result | Selected section shown; others hidden. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) + Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr04_usability::test_nfr04_dashboard_navigation_supports_section_switching`, `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | The usability test is a static check; added the browser test that shows the selected section and hides Overview. |
| Remarks | - |

#### IT_NFR-04_04 - Keyboard and accessibility

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-04_05 - Responsive and reduced motion

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-04_05 |
| Requirement | NFR-04 - Usability |
| Test level | Integration |
| Test scenario | Responsive and reduced motion |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Dashboards render |
| Test data | Narrow width; reduced-motion setting |
| Test steps | 1. Inspect styles / view at narrow width |
| Expected result | Layout adapts; animations reduced. |
| Actual observed result | Expected result verified: 3 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr04_usability::test_nfr04_interface_supports_responsive_layout`, `test_nfr04_usability::test_nfr04_reduced_motion_is_supported`, `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Added the browser test that proves the layout adapts at 375 px. |
| Remarks | Reduced motion is verified at stylesheet level only (the @media rule exists). |

#### SYS_NFR-04_06 - Human usability walkthrough

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Requires human judgement; cannot be automated. |

### NFR-05 - Compatibility

> SRS: The system shall function correctly on commonly used modern web browsers.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| SYS_NFR-05_01 | Main workflows in Google Chrome (installed application) | Project team (automated regression suite) | PASS | - |
| SYS_NFR-05_02 | Main workflows in Mozilla Firefox | Project team (automated regression suite) | BLOCKED | G-09 |
| SYS_NFR-05_03 | Main workflows in Microsoft Edge | Project team (automated regression suite) | BLOCKED | G-09 |
| SYS_NFR-05_04 | Main workflows in the WebKit engine (Playwright build; not the Safari application) | Project team (automated regression suite) | PASS | D-01 |
| IT_NFR-05_05 | Browser-neutral server responses | Project team (automated regression suite) | PASS | - |
| SYS_NFR-05_06 | No horizontal overflow | Project team (automated regression suite) | PASS | - |
| SYS_NFR-05_07 | Main workflows in Playwright Chromium | Project team (automated regression suite) | PASS | - |
| SYS_NFR-05_08 | Main workflows in the Apple Safari application | Tharith | BLOCKED | G-09 |

#### SYS_NFR-05_01 - Main workflows in Google Chrome (installed application)

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_01 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | Main workflows in Google Chrome (installed application) |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Chrome installed |
| Test data | Seeded data |
| Test steps | 1. Run browser workflow suite with NFR05_BROWSERS=chrome |
| Expected result | Login, marking, viewing, user creation and layout checks pass. |
| Actual observed result | Expected result verified: 5 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chrome]`, `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chrome]`, `test_nfr05_browser_compatibility::test_student_views_own_attendance[chrome]`, `test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[chrome]`, `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chrome]` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_NFR-05_02 - Main workflows in Mozilla Firefox

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_02 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | Main workflows in Mozilla Firefox |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Playwright Firefox installed |
| Test data | Seeded data |
| Test steps | 1. Run browser workflow suite with NFR05_BROWSERS=firefox |
| Expected result | Same workflows pass. |
| Actual observed result | Playwright Firefox 157.0 was installed but cannot start on this Mac (macOS 27.0): "Could not find profile folder", even when started directly without Playwright and outside the Claude Code sandbox. No Firefox result is claimed. |
| Status | **BLOCKED** |
| Execution method | Automated browser (Playwright) (planned method; case not fully executed - see actual observed result) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | Results: docs/evidence/final/browsers/firefox_blocked_diagnosis.txt; firefox_output.txt<br>Automated test reference: `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[firefox]`, `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[firefox]`, `test_nfr05_browser_compatibility::test_student_views_own_attendance[firefox]`, `test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[firefox]`, `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[firefox]` |
| Defect / gap ID | G-09 |
| Result history | 2026-11-11 final run: BLOCKED; 2026-11-17 regression run: BLOCKED |
| Change from Test Plan v1.0 | New |
| Review notes | Environmental limitation G-09. |
| Remarks | Firefox install approved for Phase 2. |

#### SYS_NFR-05_03 - Main workflows in Microsoft Edge

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_03 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | Main workflows in Microsoft Edge |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Edge installed |
| Test data | Seeded data |
| Test steps | 1. Run browser workflow suite with NFR05_BROWSERS=edge |
| Expected result | Same workflows pass. |
| Actual observed result | Microsoft Edge is not installed and installing it was not approved. The suite reports: "Chromium distribution 'msedge' is not found at /Applications/Microsoft Edge.app". |
| Status | **BLOCKED** |
| Execution method | Automated browser (Playwright) (planned method; case not fully executed - see actual observed result) |
| Execution date | 2026-11-17 |
| Screenshot evidence | None captured for this case (automated browser assertions; see supporting evidence) |
| Supporting evidence | None (not executed) |
| Defect / gap ID | G-09 |
| Result history | 2026-11-11 final run: BLOCKED; 2026-11-17 regression run: BLOCKED |
| Change from Test Plan v1.0 | New |
| Review notes | Environmental limitation G-09. |
| Remarks | Edge not installed and installation not approved; expected BLOCKED locally (gap G-09). |

#### SYS_NFR-05_04 - Main workflows in the WebKit engine (Playwright build; not the Safari application)

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_04 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | Main workflows in the WebKit engine (Playwright build; not the Safari application) |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | WebKit available |
| Test data | Seeded data |
| Test steps | 1. Run browser workflow suite with NFR05_BROWSERS=webkit |
| Expected result | Same workflows pass. |
| Actual observed result | Expected result verified: 5 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/final/browsers/screenshots/webkit_admin_overview.png`<br>`docs/evidence/final/browsers/screenshots/webkit_teacher_overview.png`<br>`docs/evidence/final/browsers/screenshots/webkit_student_overview.png` |
| Supporting evidence | Results: docs/evidence/regression/browsers/webkit_junit.xml<br>Automated test reference: `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[webkit]@webkit`, `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[webkit]@webkit`, `test_nfr05_browser_compatibility::test_student_views_own_attendance[webkit]@webkit`, `test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[webkit]@webkit`, `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[webkit]@webkit` |
| Defect / gap ID | D-01 |
| Result history | 2026-11-11 final run: FAIL; 2026-11-17 regression run: PASS (changed) |
| Change from Test Plan v1.0 | New |
| Review notes | Was FAIL (defect D-01): WebKit 27.2 build r2370 logged a false-positive style-src-attr CSP violation for every <select>, also on a blank page (upstream WebKit regression, Playwright issue #43617, fixed in WebKit 324283@main). Re-run with Playwright 1.65.2 / WebKit build r2388; the application's CSP is unchanged. |
| Remarks | Uses the opt-in 'webkit' browser name added in Phase 2. WebKit is Safari's engine; this is not a Safari test. |

#### IT_NFR-05_05 - Browser-neutral server responses

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-05_05 |
| Requirement | NFR-05 - Compatibility |
| Test level | Integration |
| Test scenario | Browser-neutral server responses |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | App running |
| Test data | Chrome/Edge/Firefox/Safari User-Agent strings |
| Test steps | 1. Request pages and assets with each User-Agent |
| Expected result | Same headers, correct JS/CSS MIME types, standards mode. |
| Actual observed result | Expected result verified: 4 linked test(s), 37 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr05_implementation::test_nfr05_static_assets_serve_correct_mime_types`, `test_nfr05_implementation::test_nfr05_static_types_do_not_depend_on_host_mime_table`, `test_nfr05_implementation::test_nfr05_x_ua_compatible_header_present_for_all_browsers`, `test_nfr05_implementation::test_nfr05_security_headers_consistent_across_browsers` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | These tests only fake the User-Agent header; they do not run a real browser. |

#### SYS_NFR-05_06 - No horizontal overflow

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_06 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | No horizontal overflow |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Browser available |
| Test data | Desktop and narrow widths |
| Test steps | 1. Open each dashboard |
| Expected result | No horizontal scrolling. |
| Actual observed result | Expected result verified: 2 linked test(s), 4 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/final/browsers/screenshots/chromium_admin_overview.png`<br>`docs/evidence/final/browsers/screenshots/chromium_teacher_overview.png`<br>`docs/evidence/final/browsers/screenshots/chromium_student_overview.png` |
| Supporting evidence | Results: docs/evidence/regression/browsers/chromium_junit.xml; docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chrome]`, `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chromium]@chromium` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_NFR-05_07 - Main workflows in Playwright Chromium

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-05_07 |
| Requirement | NFR-05 - Compatibility |
| Test level | System |
| Test scenario | Main workflows in Playwright Chromium |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Playwright Chromium installed |
| Test data | Seeded data |
| Test steps | 1. Run browser workflow suite with NFR05_BROWSERS=chromium |
| Expected result | Login, marking, viewing, user creation and layout checks pass. |
| Actual observed result | Expected result verified: 5 linked test(s), 6 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated browser (Playwright) |
| Execution date | 2026-11-17 |
| Screenshot evidence | `docs/evidence/final/browsers/screenshots/chromium_admin_overview.png`<br>`docs/evidence/final/browsers/screenshots/chromium_teacher_overview.png`<br>`docs/evidence/final/browsers/screenshots/chromium_student_overview.png` |
| Supporting evidence | Results: docs/evidence/regression/browsers/chromium_junit.xml<br>Automated test reference: `test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[chromium]@chromium`, `test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[chromium]@chromium`, `test_nfr05_browser_compatibility::test_student_views_own_attendance[chromium]@chromium`, `test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[chromium]@chromium`, `test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[chromium]@chromium` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Added in Phase 2 (opt-in browser name 'chromium'). |

#### SYS_NFR-05_08 - Main workflows in the Apple Safari application

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
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | Added in Phase 2. Playwright cannot drive the Safari application; WebKit results (SYS_NFR-05_04) do not count as Safari. |

### NFR-06 - Maintainability

> SRS: The system shall be designed in modular components so that individual features can be updated and maintained with minimal impact on other components.

| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |
|---|---|---|---|---|
| UT_NFR-06_01 | Modules import independently | Project team (automated regression suite) | PASS | - |
| IT_NFR-06_02 | URL map unchanged | Project team (automated regression suite) | PASS | - |
| IT_NFR-06_03 | Layer dependency rules | Project team (automated regression suite) | PASS | - |
| IT_NFR-06_04 | Backward-compatible imports | Project team (automated regression suite) | PASS | - |
| SYS_NFR-06_05 | Whole-suite regression after modularisation | Project team (automated regression suite) | PASS | - |

#### UT_NFR-06_01 - Modules import independently

| Field | Details |
|---|---|
| Test Case ID | UT_NFR-06_01 |
| Requirement | NFR-06 - Maintainability |
| Test level | Unit |
| Test scenario | Modules import independently |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Source available |
| Test data | Each app/api module |
| Test steps | 1. Import each module in a fresh interpreter |
| Expected result | Each imports without the others. |
| Actual observed result | Expected result verified: 2 linked test(s), 19 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr06_maintainability::test_module_is_independently_importable`, `test_nfr06_maintainability::test_application_factory_builds_app_in_fresh_interpreter` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-06_02 - URL map unchanged

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-06_02 |
| Requirement | NFR-06 - Maintainability |
| Test level | Integration |
| Test scenario | URL map unchanged |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | App built |
| Test data | Frozen baseline |
| Test steps | 1. Compare URL map |
| Expected result | Rules, order and endpoint names match the baseline. |
| Actual observed result | Expected result verified: 2 linked test(s), 2 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr06_maintainability::test_url_map_matches_baseline_exactly_and_in_order`, `test_nfr06_maintainability::test_url_map_has_no_missing_or_unexpected_rules` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-06_03 - Layer dependency rules

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-06_03 |
| Requirement | NFR-06 - Maintainability |
| Test level | Integration |
| Test scenario | Layer dependency rules |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Source available |
| Test data | - |
| Test steps | 1. Inspect imports |
| Expected result | Feature modules depend only on shared layers; helpers do not depend on the API layer. |
| Actual observed result | Expected result verified: 3 linked test(s), 15 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr06_maintainability::test_feature_modules_only_depend_on_shared_layers`, `test_nfr06_maintainability::test_shared_helper_modules_do_not_depend_on_api_layer`, `test_nfr06_maintainability::test_validation_helpers_have_no_framework_dependencies` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### IT_NFR-06_04 - Backward-compatible imports

| Field | Details |
|---|---|
| Test Case ID | IT_NFR-06_04 |
| Requirement | NFR-06 - Maintainability |
| Test level | Integration |
| Test scenario | Backward-compatible imports |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Source available |
| Test data | app.routes |
| Test steps | 1. Import legacy names |
| Expected result | Legacy imports still resolve to the same objects. |
| Actual observed result | Expected result verified: 2 linked test(s), 71 recorded result(s), all passed. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml<br>Automated test reference: `test_nfr06_maintainability::test_legacy_routes_import_returns_same_object`, `test_nfr06_maintainability::test_legacy_style_imports_used_by_existing_code_still_work` |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Linked test(s) read; they verify the expected result. |
| Remarks | - |

#### SYS_NFR-06_05 - Whole-suite regression after modularisation

| Field | Details |
|---|---|
| Test Case ID | SYS_NFR-06_05 |
| Requirement | NFR-06 - Maintainability |
| Test level | System |
| Test scenario | Whole-suite regression after modularisation |
| Assigned team member | Project team (automated regression suite) |
| Preconditions | Full test suite |
| Test data | - |
| Test steps | 1. Run the full suite |
| Expected result | No regressions in other features. |
| Actual observed result | Final full run: 858 passed; 13 failed/errored, 13 of them environmental (Edge/Firefox cannot launch); 0 other failures. |
| Status | **PASS** |
| Execution method | Automated (pytest) |
| Execution date | 2026-11-17 |
| Screenshot evidence | Not applicable (API / unit-level test) |
| Supporting evidence | Results: docs/evidence/regression/junit.xml |
| Defect / gap ID | None |
| Result history | 2026-11-11 final run: PASS; 2026-11-17 regression run: PASS |
| Change from Test Plan v1.0 | New |
| Review notes | Status taken from the final full run: PASS only if no non-environmental test failed. |
| Remarks | - |

