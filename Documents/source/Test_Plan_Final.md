---
title: Software Test Plan
subtitle: Attendance Management System
version: 2.1
date: 2026-11-17
course: Software Engineering - Project Documentation
team: Sumukh, Jagadeesh, Tharith
status: Final draft - pending instructor approval
---

# Document Control {#document-control}

## Document Information

| Item | Value |
|---|---|
| Document | Software Test Plan |
| System | Attendance Management System |
| Version | 2.1 |
| Date | 2026-11-17 |
| Team | Sumukh, Jagadeesh, Tharith |
| Baseline | `Documents/Test_Plan.pdf` (version 1.0, 75 test cases) |
| Detailed test cases | `docs/Test_Case_Document.md` / `.xlsx` version {{tcd_version}} ({{cases}} test cases) |
| Status | Final draft, pending instructor approval |

## Revision History

| Version | Date | Description | Prepared by |
|---|---|---|---|
| 1.0 | 2026-10-15 (in repository by this date) | Test plan overview, requirements covered (FR-01 to FR-06, NFR-01 to NFR-03), 75 test cases with "Pending" results | Project team |
| 2.0 | 2026-11-17 | Complete IEEE-style test plan reconciled with the Deliverable 3 testing: test items, strategy, environment, criteria, security validation, coverage matrix, recorded results, coverage, defects and traceability. All 75 original test case IDs preserved. | Sumukh, Jagadeesh, Tharith |
| 2.1 | 2026-11-17 | Regression run after fixing SYS_FR-04_11, SYS_FR-05_10, SYS_FR-06_08, SYS_FR-10_10, SYS_FR-12_10 and SYS_NFR-05_04; results, coverage, defect register and traceability updated from `docs/evidence/regression/`. The original results are kept as history. | Sumukh, Jagadeesh, Tharith |

## Approval Status

| Role | Name | Decision | Date |
|---|---|---|---|
| Course instructor | Pending | Pending approval | Pending |
| Team review | Sumukh, Jagadeesh, Tharith | Pending review | Pending |

[[TOC]]

# 1. Introduction {#introduction}

## 1.1 Purpose

This plan defines how the Attendance Management System is tested against the SRS (`Documents/SRS_Final.pdf`): what is tested, with which methods and tools, in which environment, under which criteria, and with what results. It replaces the version 1.0 plan, whose 75 test cases are all retained.

## 1.2 Scope

In scope: all 15 functional requirements (FR-01 to FR-15) and all 6 non-functional requirements (NFR-01 to NFR-06), at unit, integration and system level, including the browser user interface. Out of scope: Optional Sprint 3 features (not implemented), HTTPS deployment (no deployment environment), load testing beyond the 1,500-record performance data set, and penetration testing.

## 1.3 References

| Reference | Location |
|---|---|
| SRS v2.0 / SAD v2.0 | `Documents/SRS_Final.pdf`, `Documents/SAD_Final.pdf` |
| Test Plan v1.0 | `Documents/Test_Plan.pdf` |
| Test Case Document v{{tcd_version}} | `docs/Test_Case_Document.md`, `.xlsx`, `.docx`, `.pdf` |
| Unit Test Report | `docs/Unit_Test_Report.md` |
| System Validation Report | `docs/System_Validation_Report.md` |
| Code and Branch Coverage Reports | `docs/Code_Coverage_Report.md`, `docs/Branch_Coverage_Report.md` |
| Manual validation checklists | `docs/manual_validation/{Sumukh,Jagadeesh,Tharith}_Checklist.md` |
| Manual Validation Automation Report | `docs/Manual_Validation_Automation_Report.md` |
| Evidence | `docs/evidence/` (baseline, final, browsers, coverage, phase3, manual_validation_automation) |
| IEEE 829-2008 | Standard for Software and System Test Documentation (structure followed) |

## 1.4 Definitions

| Term | Meaning |
|---|---|
| Test case ID | `<TYPE>_<REQ>_<NN>`, e.g. `SYS_FR-04_11`; TYPE is UT (unit), IT (integration) or SYS (system) |
| Method A / B / M | A = automated pytest; B = automated real-browser test (Playwright); M = manual (executed by Playwright automation in the manual validation run, instructor-approved) |
| PASS | Expected result verified by recorded evidence |
| FAIL | Actual result differs from the expected result |
| BLOCKED | Execution prevented by a documented environment or dependency issue |
| NOT RUN | Not executed, or only partly verified |
| NOT APPLICABLE | Outside the SRS, with the reason given |
| Defect IDs | D-xx defects, O-xx observations, MV-xx defects found by the manual validation run, G-xx known gaps |

# 2. Test Items {#test-items}

Table 1: Test items

| Module / item | Code | Requirements |
|---|---|---|
| Authentication, sessions, roles | `app/auth.py`, `app/api/auth_routes.py`, `app/api/session_routes.py`, `app/pages.py` | FR-01, FR-13, FR-15, NFR-01 |
| Attendance marking and records | `app/api/attendance_records.py`, `attendance_management.py`, `attendance_view.py` | FR-02, FR-03, FR-05, FR-10 |
| Percentages and alerts | `app/api/percentages.py`, `alerts.py`, `student.js` | FR-04, FR-11 |
| Reporting and export | `app/api/reports.py`, `exports.py` | FR-06, FR-12 |
| Administration | `app/api/users.py`, `academics.py`, `enrollments.py` | FR-07, FR-08, FR-09 |
| Dashboards (browser UI) | `app/templates/`, `app/static/` | FR-14, NFR-04, NFR-05 |
| Database schema | `app/db.py` | FR-03, NFR-02, NFR-03 |
| Security middleware | `app/__init__.py` | NFR-01, NFR-05 |
| Backup scripts | `scripts/backup_db.py`, `scripts/schedule_daily_backup.py` | NFR-03 |
| Module structure | `app/api/__init__.py` | NFR-06 |

Features not tested: Optional Sprint 3 items; the placeholder route `GET /` (observation O-03).

# 3. Test Strategy {#test-strategy}

Table 2: Test approaches and their use

| Approach | Used | How | Evidence |
|---|---|---|---|
| Unit testing | Yes | pytest with the Flask test client on a temporary SQLite database per test; validation helpers, calculations, single endpoints (72 UT cases) | `docs/evidence/final/junit.xml` |
| Integration testing | Yes | API workflows across modules and the database: login -> mark -> view -> percentage -> report; role checks; transactions (76 IT cases) | same |
| System testing | Yes | Real browser (Playwright) against a live server; manual validation scenarios executed by Playwright (49 SYS cases) | `docs/evidence/final/browsers/`, `docs/evidence/manual_validation_automation/` |
| Functional testing | Yes | Every FR has cases for normal, boundary and error inputs | Test Case Document |
| Security testing | Yes | Authentication, RBAC, session expiry and invalidation, CSRF origin check, headers, CSV injection, SQL-injection style input (section 5) | `tests/test_nfr01_security.py` and others |
| Performance testing | Yes | Backend timing and browser page-load timing against the 3-second target with 1,500 records | `test_nfr02_performance.py`, `test_nfr02_browser_performance.py`, SYS_NFR-02_06 |
| Reliability testing | Partly | Persistence, rollback, backup creation and integrity; restore not tested (no restore tool) | `test_nfr03_reliability.py`, `test_nfr03_scheduling.py` |
| Usability testing | Partly | Automated accessibility checks (focus, labels, keyboard); human walkthrough not performed | `test_nfr04_usability.py`, IT_NFR-04_04 |
| Compatibility testing | Partly | Chrome, Chromium and WebKit runs; Firefox, Edge and Safari blocked | `test_nfr05_browser_compatibility.py`, `docs/NFR05_COMPATIBILITY.md` |
| Regression testing | Yes | Full suite on every push (GitHub Actions `tests.yml`); final full run recorded; URL map frozen by `test_nfr06_maintainability.py` | `.github/workflows/tests.yml` |

Statuses in the Test Case Document are derived automatically by `scripts/build_test_case_document.py` from the recorded JUnit evidence and the manual-validation results file; they are never typed in by hand. A case is PASS only if every linked test ran and passed.

# 4. Test Environment and Execution {#environment}

## 4.1 Environment

Table 3: Test environment (final run, 2026-11-11)

| Item | Version / setting |
|---|---|
| Operating system | macOS 27.0 (arm64); CI: Ubuntu (GitHub Actions) |
| Python | 3.13.7 (CI: 3.11) |
| Flask / Werkzeug / Jinja2 | 3.1.3 / 3.1.9 / 3.1.6 |
| SQLite | Python `sqlite3` module; temporary database file per test |
| pytest | 9.1.1 |
| Playwright | 1.65.2 in the regression run (Chromium build 1255, Firefox 1572, WebKit 27.2 build 2388); 1.64.1 in the original runs (Chromium 1248, Firefox 1555, WebKit 2370) |
| Coverage.py / pytest-cov | 7.17.2 / 7.1.0 |
| Google Chrome | 157.0.8103.79 (regression run); 157.0.8103.39 (original final run); 157.0.8103.51 (original manual validation run) |
| Microsoft Edge | Not installed (installation not approved) |
| Test databases | Temporary SQLite files created by fixtures; manual validation on a seeded `validation_demo.db`; the real `attendance.db` is never used (SHA-256 unchanged before and after runs) |

## 4.2 Execution Commands

```
# full suite (as recorded in the final run)
python -m pytest -v -rA --durations=20 -p no:cacheprovider --junitxml=docs/evidence/regression/junit.xml

# complete regression evidence set (suite, browsers, six-failure tests, coverage, CSP probe)
python scripts/run_regression_suite.py

# browser subsets
NFR05_BROWSERS=chromium python -m pytest tests/test_nfr05_browser_compatibility.py
NFR05_BROWSERS=webkit   python -m pytest tests/test_nfr05_browser_compatibility.py

# coverage (statement and branch runs)
python -m pytest --cov --cov-config=.coveragerc
python -m pytest --cov --cov-branch --cov-config=.coveragerc

# manual validation scenarios (Playwright, isolated validation_demo.db on port 5001)
python scripts/run_manual_validation_automation.py

# regenerate documents and check consistency
python scripts/build_test_case_document.py
python scripts/build_phase3_reports.py
python scripts/check_report_consistency.py
```

## 4.3 Entry and Exit Criteria

| Type | Criteria |
|---|---|
| Entry | Code builds and starts; dependencies from `requirements.txt` installed; Playwright browsers installed; test cases reviewed and linked to tests; isolated test database available |
| Exit | Every test case has a recorded status; all High-priority FRs have no FAIL in automated cases; every FAIL has a defect ID; every BLOCKED and NOT RUN case has a reason; coverage reports produced; reports consistent (`check_report_consistency.py` passes) |

## 4.4 Pass/Fail Criteria

A test case passes when every check of its expected result is met by recorded evidence. It fails when any check differs. A requirement is considered verified when all its cases pass; FAIL, BLOCKED and NOT RUN cases are reported with their reason. NFR-02 passes only below 3.0 seconds.

## 4.5 Suspension and Resumption Criteria

| Suspend when | Resume when |
|---|---|
| The application cannot start or the database cannot be created | The startup problem is fixed and the smoke tests (`test_foundation.py`) pass |
| More than 20% of a module's tests fail because of the environment | The environment is repaired; the module is re-run in full |
| A required browser cannot be launched | The browser is installed or the case is recorded as BLOCKED |
| The real `attendance.db` would be touched | Tests are reconfigured to a temporary database |

## 4.6 Evidence Collection

JUnit XML and console output for every run (`docs/evidence/baseline/`, `final/`, `final/browsers/`, `coverage/`); environment files; coverage JSON/XML; screenshots and browser logs of the manual validation run (73 screenshots, 21 logs); a results file per run. Evidence is kept in the repository and never edited by hand.

## 4.7 Defect Reporting

Each failure is recorded in the defect register (Test Case Document section 6) with an ID, requirement, severity (Medium / Low / Observation), description, test impact and status. A fix that changes production code needs team approval; no defect was fixed during Deliverable 3 testing.

## 4.8 Roles and Responsibilities

Table 4: Roles

| Member | Responsibility |
|---|---|
| Sumukh | Test planning, admin and integration testing; manual validation owner of 5 cases (user, class/subject, enrollment, password) |
| Jagadeesh | Teacher and attendance testing (marking, editing, percentages, filters, alerts, performance, logout); owner of 7 cases |
| Tharith | Student and frontend testing (viewing, summaries, responsive design, accessibility, browsers, usability); owner of 7 cases |

## 4.9 Risks and Limitations

| Risk / limitation | Effect | Handling |
|---|---|---|
| Firefox (also build 1572) cannot start on the test Mac; Edge not installed; Safari not automatable | NFR-05 not proven for these browsers | Recorded as BLOCKED; run elsewhere when possible |
| No HTTPS deployment | Secure transmission cannot be tested | SYS_NFR-01_04 BLOCKED |
| No restore tool | Backup restore cannot be tested | IT_NFR-03_03 NOT RUN |
| Manual cases executed by automation | Human judgement aspects (readability, usability) not assessed | Listed per case in the Manual Validation Automation Report; SYS_NFR-04_06 NOT RUN |
| Single test machine | Timing results depend on that machine | 3-second target with margin; CI repeats functional tests |

# 5. Security Validation {#security-validation}

Table 5: Security tests

| Area | What is tested | Test cases / files | Result |
|---|---|---|---|
| Authentication | Valid, invalid and blank credentials; inactive accounts; database unavailable at login | UT_FR-01_01 to UT_FR-01_03, SYS_FR-01_10, UT_NFR-01_01 (password field masking); `test_fr01_authentication.py` | PASS |
| Authorization (RBAC) | Admin, teacher and student role mapping; student blocked from teacher/admin pages and APIs; teacher limited to own subjects; student limited to own records | IT_FR-01_04 to IT_FR-01_07, IT_NFR-01_02, IT_NFR-01_03; `test_nfr01_security.py` | PASS |
| Session protection | 30-minute expiry, cookie flags, logout invalidation, password change ends other sessions, Back after logout | SYS_FR-01_08, SYS_FR-01_09, FR-13 and FR-15 cases | PASS (SYS_FR-15_08 cross-site logout NOT RUN) |
| CSRF | Cross-site state-changing requests rejected | `test_frontend_pages.py`, `test_fr13_password_management.py` | PASS |
| Headers | CSP, X-Frame-Options, nosniff, Cache-Control no-store | `test_nfr01_security::test_security_headers` | PASS |
| Input validation | Invalid statuses, dates, IDs, threshold values, JSON bodies | FR-02, FR-03, FR-10, FR-11 cases | PASS |
| Export safety | CSV formula injection neutralised | FR-12 cases (`test_fr12_implementation.py`) | PASS |
| Secure transmission | HTTPS | SYS_NFR-01_04 | BLOCKED (no HTTPS deployment) |

Open security-related findings from the documentation audit (not test results): AF-01 server-side password length on admin-created accounts, AF-02 self-deactivation prevented only in the UI (`docs/Documentation_Compliance_Audit.md`).

# 6. Test Coverage Matrix {#coverage-matrix}

Every requirement maps to test cases. "Orig. 75" counts the cases kept from Test Plan v1.0.

Table 6: Requirement coverage and status

[[DATA:tp_coverage]]

# 7. Test Case Documentation {#test-cases}

The {{cases}} detailed test cases (pre-conditions, steps, test data, expected and actual results, method, automated test reference, status, date, evidence, owner) are in `docs/Test_Case_Document.md` and `docs/Test_Case_Document.xlsx` (version {{tcd_version}}). They are not duplicated here. The catalogue contains {{original}} original cases from Test Plan v1.0 with unchanged IDs and {{new}} new cases for FR-07 to FR-15 and NFR-04 to NFR-06; no ID is duplicated.

Table 7: Original Test Plan v1.0 cases (IDs preserved)

[[DATA:tp_original]]

The 19 manual validation cases (owners Sumukh 5, Jagadeesh 7, Tharith 7) were executed on {{manual_date}} by Playwright automation in {{manual_browser}}; the instructor approved this as manual validation evidence. Result: {{manual_summary}}.

# 8. Test Execution Results {#results}

## 8.1 Recorded Runs

| Run | Date | Result | Evidence |
|---|---|---|---|
| Original final full suite | 2026-11-11 | 856 results: 836 passed, 1 failed, 12 errors, 7 skipped | `docs/evidence/final/junit.xml` |
| Original browser runs | 2026-11-11 | Chromium 7 passed; WebKit workflow steps passed with CSP console errors (D-01); Firefox cannot start | `docs/evidence/final/browsers/` |
| Original manual validation (Playwright) | 2026-11-17 | 14 PASS, 3 FAIL, 1 BLOCKED, 1 NOT RUN | `docs/evidence/manual_validation_automation/` |
| **Regression full suite (after the fixes)** | {{junit_date}} | {{junit_total}} results: {{junit_passed}} passed, {{junit_failed}} failed, {{junit_errors}} errors, {{junit_skipped}} skipped | `docs/evidence/final/junit.xml` |
| **Regression browser runs** | {{junit_date}} | Chromium and WebKit (build r2388): all NFR-05 workflows pass with no console errors; six-failure browser tests pass in Chromium and WebKit; Firefox still cannot start | `docs/evidence/regression/browsers/` |
| **Regression manual validation (Playwright)** | {{manual_date}} | {{manual_summary}} | `docs/evidence/regression/manual_validation_automation/` |

The 1 failure and 12 errors of the full run are environmental: the Edge and Firefox browser tests cannot launch on the test machine, and `test_report_tested_browser_versions` fails by design when a selected browser did not run. The 7 skipped tests are the Sprint 1 placeholders in `tests/test_sprint1_requirements.py` (no assertions; never counted as passed).

## 8.2 Test Case Status

Table 8: Test case status by level

[[DATA:tp_status_totals]]

Table 9: Test cases that did not pass

[[DATA:tp_not_passed]]

# 9. Coverage Results {#coverage}

Coverage of the application package `app/`, measured with Coverage.py 7.17.2 in two runs (statement-only and branch) on the same suite and the same `.coveragerc`. The regression run is the current measurement; the original measurement is kept for comparison.

Table 10: Coverage

| Measure | Regression run (after the fixes) | Original run (2026-11-11) |
|---|---|---|
| Statement coverage | {{stmt_lines}} statements = {{stmt_pct}} | {{orig_stmt_lines}} statements = {{orig_stmt_pct}} |
| Branch coverage | {{branch_branches}} branches = {{branch_only_pct}} | {{orig_branch_branches}} branches = {{orig_branch_only_pct}} |

The figures are read from `docs/evidence/regression/coverage/{statement,branch}/coverage_app.json` and, for the original run, `docs/evidence/coverage/{statement,branch}/coverage_app.json`. The six fixes changed only browser-side files (JavaScript, CSS, templates), which Coverage.py does not measure; no Python file in `app/` changed. The totals rose by one statement and one branch: the new export browser test downloads a PDF for a report filtered by student and subject, which executes the subject line of the PDF header in `app/api/exports.py` (lines 121-122) for the first time. Uncovered code is analysed in `docs/Code_Coverage_Report.md` and `docs/Branch_Coverage_Report.md`; it includes the shadowed `attendance_management.get_attendance` view (observation O-02) and database-error branches. No target percentage is set, and coverage was not raised with tests that only execute code.

# 10. Defect Management {#defects}

Table 11: Defect register (from the Test Case Document v{{tcd_version}})

[[DATA:defects]]

Table 12: Known gaps and limitations

[[DATA:gaps]]

Additional audit findings (not yet in the register): AF-01 and AF-02 (section 5).

# 11. Traceability Matrix {#traceability}

Requirement -> test cases -> execution status -> open defect IDs -> evidence.

Table 13: Requirements to tests, results, defects and evidence

[[DATA:tp_trace]]

# 12. Test Summary and Conclusion {#conclusion}

**Verified.** {{pass}} of {{cases}} test cases pass in the regression run of {{junit_date}}. The six cases that failed in the original runs now pass: SYS_FR-04_11 (two-decimal percentages, MV-02), SYS_FR-05_10 (phone table layout, MV-03), SYS_FR-06_08 (Reports screen, D-02), SYS_FR-10_10 (Clear filters, class and date-range filters, MV-01), SYS_FR-12_10 (export controls, D-03) and SYS_NFR-05_04 (WebKit build r2388 without the upstream CSP false positive, D-01). Authentication, role-based access, attendance marking and correction, duplicate prevention, percentages, viewing, reporting, export, enrollment, alerts, password change, logout and performance are verified by automated tests and the Playwright validation run.

**Failed ({{fail}}).** No test case fails in the regression run. The original runs had 6 failures (listed above, defects D-01 to D-03 and MV-01 to MV-03); all were fixed and re-verified. The application's Content Security Policy was not relaxed.

**Blocked ({{blocked}}).** HTTPS transmission (SYS_NFR-01_04), Firefox (SYS_NFR-05_02), Edge (SYS_NFR-05_03) and the Safari application (SYS_NFR-05_08).

**Not run ({{notrun}}) and not applicable ({{na}}).** Cross-site logout test (SYS_FR-15_08), backup restore (IT_NFR-03_03), retry after failure (SYS_NFR-03_05), human usability walkthrough (SYS_NFR-04_06); pagination is outside the SRS (SYS_FR-05_09).

**Coverage.** Statement {{stmt_pct}}, branch {{branch_only_pct}} for `app/`.

**Remaining risks.** No HTTPS, no backup restore procedure, untested Firefox/Edge/Safari, and the human usability walkthrough not performed. Testing of the implemented scope is complete within these documented limitations.
