# JUnit summary: `docs/evidence/final/junit.xml`

- Timestamp (from XML): 2026-11-11T09:40:13.434286+05:30
- Host: Sumukhs-MacBook-Air.local
- pytest-reported time: 134.09 s
- Test results recorded: 856
- Outcomes: passed 836, failure 1, error 12, skipped 7

## Per file

| File | Passed | Failed | Error | Skipped |
|---|---|---|---|---|
| tests.test_foundation | 11 | 0 | 0 | 0 |
| tests.test_fr01_authentication | 23 | 0 | 0 | 0 |
| tests.test_fr01_session_expiry_and_auth_failure | 6 | 0 | 0 | 0 |
| tests.test_fr02_attendance_marking | 19 | 0 | 0 | 0 |
| tests.test_fr03_record_management | 16 | 0 | 0 | 0 |
| tests.test_fr04_percentage_test_plan_cases | 9 | 0 | 0 | 0 |
| tests.test_fr04_percentages | 14 | 0 | 0 | 0 |
| tests.test_fr05_attendance_viewing | 15 | 0 | 0 | 0 |
| tests.test_fr05_attendance_viewing_extra | 24 | 0 | 0 | 0 |
| tests.test_fr06_attendance_reporting | 31 | 0 | 0 | 0 |
| tests.test_fr07_user_management | 60 | 0 | 0 | 0 |
| tests.test_fr08_class_subject_management | 43 | 0 | 0 | 0 |
| tests.test_fr09_enrollment_validation | 11 | 0 | 0 | 0 |
| tests.test_fr09_student_enrollment | 6 | 0 | 0 | 0 |
| tests.test_fr10_attendance_search_filter | 41 | 0 | 0 | 0 |
| tests.test_fr11_attendance_alert | 30 | 0 | 0 | 0 |
| tests.test_fr12_implementation | 29 | 0 | 0 | 0 |
| tests.test_fr13_password_management | 58 | 0 | 0 | 0 |
| tests.test_fr14_dashboard_summary | 15 | 0 | 0 | 0 |
| tests.test_fr15_logout | 3 | 0 | 0 | 0 |
| tests.test_frontend_pages | 43 | 0 | 0 | 0 |
| tests.test_nfr01_security | 6 | 0 | 0 | 0 |
| tests.test_nfr02_browser_performance | 6 | 0 | 0 | 0 |
| tests.test_nfr02_performance | 18 | 0 | 0 | 0 |
| tests.test_nfr03_reliability | 5 | 0 | 0 | 0 |
| tests.test_nfr03_scheduling | 11 | 0 | 0 | 0 |
| tests.test_nfr04_usability | 14 | 0 | 0 | 0 |
| tests.test_nfr05_browser_compatibility | 6 | 1 | 12 | 0 |
| tests.test_nfr05_implementation | 91 | 0 | 0 | 0 |
| tests.test_nfr06_maintainability | 170 | 0 | 0 | 0 |
| tests.test_sprint1_requirements | 2 | 0 | 0 | 7 |

## Not passed

| Test | Outcome | Message |
|---|---|---|
| tests.test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[edge] | error | failed on setup with "Failed: NFR-05 requires edge but it could not be launched. Install it with 'python -m playwright install msedge'. Original error: BrowserType.launch: Chromium distribution 'msedg |
| tests.test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[edge] | error | failed on setup with "Failed: NFR-05 requires edge but it could not be launched. Install it with 'python -m playwright install msedge'. Original error: BrowserType.launch: Chromium distribution 'msedg |
| tests.test_nfr05_browser_compatibility::test_student_views_own_attendance[edge] | error | failed on setup with "Failed: NFR-05 requires edge but it could not be launched. Install it with 'python -m playwright install msedge'. Original error: BrowserType.launch: Chromium distribution 'msedg |
| tests.test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[edge] | error | failed on setup with "Failed: NFR-05 requires edge but it could not be launched. Install it with 'python -m playwright install msedge'. Original error: BrowserType.launch: Chromium distribution 'msedg |
| tests.test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[edge-1280-800] | error | failed on setup with "Failed: NFR-05 requires edge but it could not be launched. Install it with 'python -m playwright install msedge'. Original error: BrowserType.launch: Chromium distribution 'msedg |
| tests.test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[edge-375-812] | error | failed on setup with "Failed: NFR-05 requires edge but it could not be launched. Install it with 'python -m playwright install msedge'. Original error: BrowserType.launch: Chromium distribution 'msedg |
| tests.test_nfr05_browser_compatibility::test_login_page_validation_and_role_redirect[firefox] | error | failed on setup with "Failed: NFR-05 requires firefox but it could not be launched. Install it with 'python -m playwright install firefox'. Original error: BrowserType.launch: Failed to launch the bro |
| tests.test_nfr05_browser_compatibility::test_teacher_marks_corrects_attendance_and_logs_out[firefox] | error | failed on setup with "Failed: NFR-05 requires firefox but it could not be launched. Install it with 'python -m playwright install firefox'. Original error: BrowserType.launch: Failed to launch the bro |
| tests.test_nfr05_browser_compatibility::test_student_views_own_attendance[firefox] | error | failed on setup with "Failed: NFR-05 requires firefox but it could not be launched. Install it with 'python -m playwright install firefox'. Original error: BrowserType.launch: Failed to launch the bro |
| tests.test_nfr05_browser_compatibility::test_admin_creates_user_through_dialog[firefox] | error | failed on setup with "Failed: NFR-05 requires firefox but it could not be launched. Install it with 'python -m playwright install firefox'. Original error: BrowserType.launch: Failed to launch the bro |
| tests.test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[firefox-1280-800] | error | failed on setup with "Failed: NFR-05 requires firefox but it could not be launched. Install it with 'python -m playwright install firefox'. Original error: BrowserType.launch: Failed to launch the bro |
| tests.test_nfr05_browser_compatibility::test_dashboard_layout_has_no_horizontal_overflow[firefox-375-812] | error | failed on setup with "Failed: NFR-05 requires firefox but it could not be launched. Install it with 'python -m playwright install firefox'. Original error: BrowserType.launch: Failed to launch the bro |
| tests.test_nfr05_browser_compatibility::test_report_tested_browser_versions | failure | AssertionError: Not every selected browser was exercised: {'chrome': 'chromium/chrome 157.0.8103.39'} |
| tests.test_sprint1_requirements::test_fr01_authentication | skipped | FR-01 pending: valid/invalid/blank login, role restrictions, timeout |
| tests.test_sprint1_requirements::test_admin_management | skipped | FR-07/08/09 pending: admin user/class/subject/enrollment workflows |
| tests.test_sprint1_requirements::test_fr04_percentages | skipped | FR-04 pending: 100%, 50%, zero records, late policy, filters |
| tests.test_sprint1_requirements::test_fr05_viewing | skipped | FR-05 pending: student/teacher scopes, filters, empty results |
| tests.test_sprint1_requirements::test_fr15_logout | skipped | FR-15 pending: logout revokes access |
| tests.test_sprint1_requirements::test_nfr01_security | skipped | NFR-01 pending: permissions, session protection, HTTPS deployment |
| tests.test_sprint1_requirements::test_nfr03_reliability | skipped | NFR-03 pending: backup creation, restore, failure recovery |
