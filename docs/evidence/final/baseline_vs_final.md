# Baseline vs final comparison

| Run | Results | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|
| Baseline | 830 | 810 | 1 | 12 | 7 |
| Final | 856 | 836 | 1 | 12 | 7 |

- Regressions (passed in baseline, not passed in final): 0 []
- Tests removed: 0 []
- Outcome changes for existing tests: 0 []
- New test results: 26 (all passed: True)
  - tests.test_fr01_session_expiry_and_auth_failure: 6
  - tests.test_fr04_percentage_test_plan_cases: 9
  - tests.test_fr09_enrollment_validation: 11
- Non-passing set identical in both runs: True (13 results: 12 Edge/Firefox launch errors + test_report_tested_browser_versions)
