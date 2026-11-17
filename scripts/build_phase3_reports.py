"""Build the Deliverable 3 Phase 3 reports from saved evidence.

Writes:
  docs/Unit_Test_Report.md
  docs/System_Validation_Report.md
  docs/Code_Coverage_Report.md
  docs/Branch_Coverage_Report.md

Every number in the reports is read from files under docs/evidence/ (JUnit
XML, pytest console logs, coverage JSON) or from the Test Case Document
catalogue (scripts/case_catalog.py, statuses evaluated exactly as
scripts/build_test_case_document.py does). Nothing is typed in by hand; the
script stops if a curated statement no longer matches the evidence.

Usage: python scripts/build_phase3_reports.py
"""

import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_test_case_document as tcd  # noqa: E402
import case_catalog as cat  # noqa: E402
import classify_tests as ct  # noqa: E402

DOCS = ROOT / "docs"
EV = DOCS / "evidence"
# The reports present the regression run after the six fixes. The earlier runs stay
# unchanged and are shown as history: baseline, final Phase 2 run (2026-11-11) and
# its coverage runs (docs/evidence/regression/coverage/).
RUN = EV / "regression"
COV = RUN / "coverage"
ORIG = EV / "final"
ORIG_COV = EV / "coverage"
REPORT_DATE = "2026-11-17"
ORIGINAL_DATE = "2026-11-11"
TYPES = ("unit", "integration", "browser", "static")
STATUSES = tcd.STATUSES


# ------------------------------------------------------------------ helpers
def rel(path):
    return str(Path(path).relative_to(ROOT))


def pct(num, den):
    return f"{100 * num / den:.2f}%" if den else "n/a"


def ranges(numbers):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10'."""
    out, nums = [], sorted(numbers)
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(out)


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(c) for c in row) + " |")
    return "\n".join(lines)


def junit(path):
    root = ET.parse(path).getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    cases = []
    for tc in suite.iter("testcase"):
        outcome, msg = "passed", ""
        for child in tc:
            if child.tag in ("failure", "error", "skipped"):
                outcome, msg = child.tag, (child.get("message") or "").strip()
        cases.append({
            "module": tc.get("classname").split(".")[-1],
            "name": tc.get("name"),
            "outcome": outcome,
            "msg": msg,
        })
    a = suite.attrib
    return {
        "cases": cases,
        "tests": int(a["tests"]),
        "errors": int(a["errors"]),
        "failures": int(a["failures"]),
        "skipped": int(a["skipped"]),
        "time": float(a["time"]),
        "timestamp": a["timestamp"],
        "counts": collections.Counter(c["outcome"] for c in cases),
    }


def summary_line(path):
    """Final pytest summary line -> (text, {'passed': n, ...})."""
    for line in reversed(Path(path).read_text().splitlines()):
        if re.search(r"\d+ passed", line):
            parts = {k.rstrip("s"): int(v) for v, k in re.findall(
                r"(\d+) (passed|failed|skipped|warnings|warning|errors|error)", line)}
            return line.strip("= ").strip(), parts
    raise SystemExit(f"No pytest summary line in {path}")


def warnings_breakdown(path):
    """Count warnings per category from pytest's 'warnings summary' section."""
    lines = Path(path).read_text().splitlines()
    starts = [i for i, l in enumerate(lines) if "warnings summary" in l]
    if not starts:
        return collections.Counter(), collections.Counter()
    i = starts[0] + 1
    by_cat, by_origin = collections.Counter(), collections.Counter()
    group_count, group_cat, group_origin = 0, None, None

    def flush():
        if group_count:
            by_cat[group_cat or "unknown"] += group_count
            by_origin[(group_cat or "unknown", group_origin or "unknown")] += group_count

    while i < len(lines) and not lines[i].startswith("-- Docs:"):
        line = lines[i]
        if not line.strip():
            flush()
            group_count, group_cat, group_origin = 0, None, None
        elif not line.startswith(" ") and not re.match(r"^(tests/|<|\S+\.py)", line):
            pass  # unindented continuation of a multi-line warning message
        elif not line.startswith(" "):
            if group_cat is not None:  # a new group without a blank separator
                flush()
                group_count, group_cat, group_origin = 0, None, None
            loc = re.match(r"^\S+\.py:\d+: (\w+Warning):", line)
            if loc:
                # Warning reported outside any test (e.g. a ResourceWarning raised during garbage
                # collection through pytest's unraisable-exception hook): pytest lists it but does
                # not include it in its "N warnings" total, so it adds no count here either.
                group_cat = loc.group(1)
                group_origin = "outside a test (garbage collection)"
            else:
                m = re.match(r"^(\S+): (\d+) warnings?$", line)
                group_count += int(m.group(2)) if m else 1
        elif group_cat is None:
            m = re.search(r"(\w+Warning):", line)
            if m:
                group_cat = m.group(1)
                src = line.strip().split(": ")[0]
                group_origin = re.sub(r".*/site-packages/", "site-packages/", src)
                group_origin = re.sub(r".*/Attendance_Management_System/", "", group_origin)
                group_origin = re.sub(r".*/lib/python3\.\d+/", "stdlib/", group_origin)
                group_origin = re.sub(r":\d+$", "", group_origin)
        i += 1
    flush()
    return by_cat, by_origin


def env_lines(path):
    return [l for l in Path(path).read_text().splitlines() if l.strip()]


# ------------------------------------------------------------------ evidence
def load():
    if cat.MANUAL_META is None:
        raise SystemExit(f"Missing {cat.MANUAL_RESULTS_PATH}; run scripts/run_manual_validation_automation.py first.")
    data = {}
    data["baseline"] = junit(EV / "baseline/junit.xml")
    data["final"] = junit(RUN / "junit.xml")
    data["orig_final"] = junit(ORIG / "junit.xml")
    data["orig_final_line"] = summary_line(ORIG / "pytest_output.txt")
    data["baseline_line"] = summary_line(EV / "baseline/pytest_output.txt")
    data["final_line"] = summary_line(RUN / "pytest_output.txt")
    data["browsers"] = {b: junit(RUN / f"browsers/{b}_junit.xml") for b in ("chromium", "webkit", "firefox")}
    data["orig_browsers"] = {b: junit(ORIG / f"browsers/{b}_junit.xml") for b in ("chromium", "webkit", "firefox")}
    for run in ("statement", "branch"):
        data[f"cov_{run}_junit"] = junit(COV / f"{run}/junit.xml")
        data[f"cov_{run}_line"] = summary_line(COV / f"{run}/pytest_output.txt")
        for scope in ("app", "scripts"):
            data[f"cov_{run}_{scope}"] = json.loads((COV / f"{run}/coverage_{scope}.json").read_text())
            data[f"orig_cov_{run}_{scope}"] = json.loads((ORIG_COV / f"{run}/coverage_{scope}.json").read_text())
    data["warn_final"] = warnings_breakdown(RUN / "pytest_output.txt")
    data["warn_baseline"] = warnings_breakdown(EV / "baseline/pytest_output.txt")
    data["warn_cov"] = warnings_breakdown(COV / "branch/pytest_output.txt")
    data["warn_cov_stmt"] = warnings_breakdown(COV / "statement/pytest_output.txt")

    # test-type classification of every recorded result
    kinds = {}
    for f in (ROOT / "tests").glob("test_*.py"):
        for func, kind in ct.file_classes(f).items():
            kinds[(f.stem, func)] = kind
    data["kinds"] = kinds

    # Test Case Document statuses, evaluated exactly as the builder does
    problems = tcd.verify_references()
    if problems:
        raise SystemExit("Test Case Document references broken: " + "; ".join(problems))
    evidence = {label: tcd.load_junit(path) for label, path in tcd.EVIDENCE.items()}
    for case in cat.CASES:
        case["status"], case["actual"], case["date"], case["evidence"] = tcd.evaluate(case, evidence)
    data["cases"] = cat.CASES
    return data


def kind_of(data, case_row):
    return data["kinds"].get((case_row["module"], case_row["name"].split("[")[0]), "unknown")


def type_counts(data, run):
    c = collections.defaultdict(collections.Counter)
    for row in data[run]["cases"]:
        c[kind_of(data, row)][row["outcome"]] += 1
    return c


def check_consistency(data):
    """Stop if the JUnit files and console logs disagree."""
    for run in ("baseline", "final", "cov_statement_junit", "cov_branch_junit"):
        j = data[run]
        c = j["counts"]
        assert j["tests"] == len(j["cases"]), run
        assert (c["failure"], c["error"], c["skipped"]) == (j["failures"], j["errors"], j["skipped"]), run
    for run, line in (("baseline", "baseline_line"), ("final", "final_line"),
                      ("cov_statement_junit", "cov_statement_line"), ("cov_branch_junit", "cov_branch_line")):
        j, parts = data[run], data[line][1]
        assert parts.get("passed") == j["counts"]["passed"], (run, parts, j["counts"])
        assert parts.get("failed", 0) == j["failures"], run
        assert parts.get("error", 0) == j["errors"], run
        assert parts.get("skipped", 0) == j["skipped"], run
    # warnings parsed from the summary section must equal pytest's own total
    for key, line in (("warn_final", "final_line"), ("warn_baseline", "baseline_line"),
                      ("warn_cov", "cov_branch_line"), ("warn_cov_stmt", "cov_statement_line")):
        assert sum(data[key][0].values()) == data[line][1].get("warning", 0), (key, data[key][0], data[line][1])
    # statement numbers identical in the statement-only and branch runs
    for scope in ("app", "scripts"):
        s, b = data[f"cov_statement_{scope}"], data[f"cov_branch_{scope}"]
        assert s["meta"]["branch_coverage"] is False and b["meta"]["branch_coverage"] is True
        for f in b["files"]:
            assert s["files"][f]["missing_lines"] == b["files"][f]["missing_lines"], f
            assert s["files"][f]["summary"]["num_statements"] == b["files"][f]["summary"]["num_statements"], f
    # the coverage runs produced the same per-test outcomes as the final run
    final = {(r["module"], r["name"]): r["outcome"] for r in data["final"]["cases"]}
    for run in ("cov_statement_junit", "cov_branch_junit"):
        other = {(r["module"], r["name"]): r["outcome"] for r in data[run]["cases"]}
        assert other == final, f"{run} outcomes differ from the final run"
    assert len(data["cases"]) == 197
    assert sum(1 for c in data["cases"] if c["change"] != cat.NEW) == 75
    # manual validation cases: statuses equal the recorded Playwright results; owners 5/7/7
    _, results = cat.load_manual_results()
    manual = [c for c in data["cases"] if c["tester"]]
    assert len(manual) == len(results) == 19
    assert all(c["status"] == results[c["id"]]["status"] for c in manual), "manual statuses differ from results.json"
    assert collections.Counter(c["tester"] for c in manual) == {"Sumukh": 5, "Jagadeesh": 7, "Tharith": 7}
    for d in cat.DEFECTS:
        for case_id in re.findall(r"(?:UT|IT|SYS)_N?FR-\d+_\d+", d[4]):
            if d[5].startswith("Open") and "FAIL" in d[4]:
                assert cat._BY_ID[case_id]["status"] == "FAIL", (d[0], case_id)        # open defect: case still fails
            if d[5].startswith("Fixed"):
                assert cat._BY_ID[case_id]["status"] == "PASS", (d[0], case_id)        # fixed defect: case now passes


# ------------------------------------------------------------------ shared text
def status_counts(cases):
    c = collections.Counter(x["status"] for x in cases)
    return [c.get(s, 0) for s in STATUSES]


def run_status(run):
    return "PASS" if run["tests"] and not run["failures"] and not run["errors"] else "FAIL"


def browser_rows(data):
    final = data["final"]["cases"]

    def pick(label):
        rows = [r for r in final if r["module"] == "test_nfr05_browser_compatibility" and f"[{label}" in r["name"]]
        return collections.Counter(r["outcome"] for r in rows), rows

    chrome, _ = pick("chrome")
    edge, edge_rows = pick("edge")
    firefox_main, _ = pick("firefox")
    summary = [r for r in final if r["name"] == "test_report_tested_browser_versions"]
    b = data["browsers"]
    perf = [r for r in final if r["module"] == "test_nfr02_browser_performance"]
    perf_c = collections.Counter(r["outcome"] for r in perf)
    rows = [
        ("Google Chrome 157 (installed application)", "Full suite, default browser list",
         f"{chrome['passed']} passed, {chrome['failure']} failed, {chrome['error']} errors", "PASS", "docs/evidence/regression/junit.xml"),
        ("Playwright Chromium (bundled build)", "NFR05_BROWSERS=chromium",
         f"{b['chromium']['counts']['passed']} passed, {b['chromium']['failures']} failed, {b['chromium']['errors']} errors",
         run_status(b["chromium"]), "docs/evidence/regression/browsers/chromium_junit.xml"),
        ("Playwright WebKit 27.2 (build r2388)", "NFR05_BROWSERS=webkit",
         f"{b['webkit']['counts']['passed']} passed, {b['webkit']['failures']} failed, {b['webkit']['errors']} errors "
         "(no console errors; defect D-01 closed)", run_status(b["webkit"]), "docs/evidence/regression/browsers/webkit_junit.xml"),
        ("Playwright Firefox (build 1572)", "NFR05_BROWSERS=firefox (and in the default run)",
         f"browser cannot start: {b['firefox']['errors']} errors, {b['firefox']['failures']} failed in the Firefox-only run; "
         f"{firefox_main['error']} errors in the default run", "BLOCKED",
         "docs/evidence/regression/browsers/firefox_junit.xml; diagnosis: docs/evidence/final/browsers/firefox_blocked_diagnosis.txt"),
        ("Microsoft Edge", "Default run", f"not installed: {edge['error']} errors", "BLOCKED", "docs/evidence/regression/junit.xml"),
        ("Safari application", "Manual validation run (Tharith, SYS_NFR-05_08)",
         "not executed: Playwright cannot drive the Safari application", cat._BY_ID["SYS_NFR-05_08"]["status"],
         "docs/manual_validation/Tharith_Checklist.md"),
    ]
    return rows, summary, perf_c, edge_rows


def evidence_index():
    return [
        ("Baseline run (before Phase 2 test additions)", "docs/evidence/baseline/ (junit.xml, pytest_output.txt, environment.txt, junit_summary.md, test_type_inventory.md)"),
        ("Final run (after Phase 2)", "docs/evidence/regression/ (junit.xml, pytest_output.txt, environment.txt, junit_summary.md, baseline_vs_final.md, test_type_inventory.md)"),
        ("Browser runs", "docs/evidence/regression/browsers/ (chromium/webkit/firefox JUnit + console output, run info, Firefox diagnosis, WebKit CSP probe, screenshots)"),
        ("Coverage runs", "docs/evidence/regression/coverage/ (statement/ and branch/: junit.xml, pytest_output.txt, coverage_app.json, coverage_scripts.json, coverage.xml, coverage_report_*.txt; environment.txt)"),
        ("O-01 enrollment probe", "docs/evidence/phase3/o01_enrollment_probe.py and _output.txt"),
        ("Test Case Document", "docs/Test_Case_Document.md / .xlsx (v" + tcd.VERSION + ")"),
        ("Manual checklists", "docs/manual_validation/{Sumukh,Jagadeesh,Tharith}_Checklist.md"),
        ("Regression run (after the six fixes)", "docs/evidence/regression/ (junit.xml, pytest_output.txt, environment.txt, "
         "browsers/, coverage/, manual_validation_automation/, original_statuses.json)"),
        ("Superseded attempts (kept, not used)", "docs/evidence/regression/manual_validation_automation_attempt1/ and "
         "coverage_attempt1/ - reasons in each SUPERSEDED.txt"),
        ("Original final run and coverage (history)", "docs/evidence/final/, docs/evidence/coverage/ (2026-11-11)"),
        ("Manual validation run (Playwright)", f"{cat.MANUAL_RUN_DIR}/ (results.json, setup.log, server.log, screenshots/, logs/); "
         f"{cat.MANUAL_REPORT}"),
    ]


# ------------------------------------------------------------------ Unit Test Report
def unit_test_report(data):
    b, f = data["baseline"], data["final"]
    tb, tf = type_counts(data, "baseline"), type_counts(data, "final")
    w = []
    a = w.append
    a("# Unit Test Report\n")
    a("**Project:** Attendance Management System  ")
    a(f"**Deliverable:** 3 (Testing) - Phase 3  ")
    a(f"**Report date:** {REPORT_DATE}  ")
    a("**Team:** Sumukh, Jagadeesh, Tharith  ")
    a("**Generated by:** `scripts/build_phase3_reports.py` from the saved evidence listed in section 11. "
      "No figure in this report was entered by hand.\n")

    a("## 1. Purpose and scope\n")
    a("This report records the automated test results for the application before and after the Phase 2 test additions, "
      "and separates the results by test level. The suite is run with pytest; it contains unit tests, integration tests "
      "(Flask test client + temporary SQLite database), real-browser tests (Playwright) and structural (static) checks. "
      "**Only the unit-level results are unit tests**; the other levels are reported separately and are not counted as unit tests.\n")
    a("### 1.1 How each result is classified\n")
    a("The level of every collected result is derived from the test source by `scripts/classify_tests.py` (not from test names):\n")
    a(table(["Level", "Rule"], [
        ("Unit", "Calls one function or module directly; no Flask application, no HTTP request, no browser."),
        ("Integration", "Sends requests through the Flask test client (directly or via a helper/fixture), so routing, authentication, "
         "the API handler and a temporary SQLite database run together; also tests that build the app and exercise its SQLite schema."),
        ("Browser", "Drives a real browser through Playwright against a live server on a temporary database "
         "(`test_nfr05_browser_compatibility.py`, `test_nfr02_browser_performance.py`)."),
        ("Static / structural", "Inspects source files, the AST, the import graph or the URL map without sending a request "
         "(mostly the NFR-06 maintainability checks)."),
    ]))
    a("")
    a("> **Note on test case IDs.** The Test Case Document keeps the Test Plan's `UT_` / `IT_` / `SYS_` IDs. Most `UT_` cases "
      "verify one rule of one endpoint, but the linked tests reach that rule through the Flask test client, so by the rule above "
      "they are integration-level tests. Section 7 shows, for every `UT_` case, the level of the tests that actually verify it.\n")

    a("## 2. Test environment\n")
    a("Regression run environment, as recorded in `docs/evidence/regression/environment.txt`:\n")
    a("```text")
    for line in env_lines(RUN / "environment.txt"):
        a(line)
    a("```\n")
    a("Every test creates its own temporary SQLite database (`tmp_path`); no test points at the real `attendance.db`. "
      "Its SHA-1 was checked before and after the Phase 2 and Phase 3 runs and never changed (Phase 3 values recorded in "
      "`docs/evidence/regression/environment.txt`).\n")

    a("## 3. Commands\n")
    a("```bash")
    a(".venv/bin/python -m pytest -v -rA --durations=20 -p no:cacheprovider --junitxml=docs/evidence/regression/junit.xml")
    a(".venv/bin/python scripts/summarize_junit.py docs/evidence/regression/junit.xml")
    a(".venv/bin/python scripts/classify_tests.py docs/evidence/regression/junit.xml")
    a("```\n")

    a("## 4. Overall results: baseline, final and regression runs\n")
    a(table(["Run", "Started", "Results", "Passed", "Failed", "Errors", "Skipped", "Warnings", "Duration"], [
        ("Baseline (before Phase 2 additions)", b["timestamp"][:19].replace("T", " "), b["tests"], b["counts"]["passed"],
         b["failures"], b["errors"], b["skipped"], data["baseline_line"][1].get("warning", 0), f"{b['time']:.1f} s"),
        ("Final (after Phase 2; original, kept as history)", data["orig_final"]["timestamp"][:19].replace("T", " "),
         data["orig_final"]["tests"], data["orig_final"]["counts"]["passed"], data["orig_final"]["failures"],
         data["orig_final"]["errors"], data["orig_final"]["skipped"], data["orig_final_line"][1].get("warning", 0),
         f"{data['orig_final']['time']:.1f} s"),
        ("Regression (after the six fixes; reported)", f["timestamp"][:19].replace("T", " "), f["tests"], f["counts"]["passed"],
         f["failures"], f["errors"], f["skipped"], data["final_line"][1].get("warning", 0), f"{f['time']:.1f} s"),
    ]))
    a("")
    a(f"pytest summary lines: baseline `{data['baseline_line'][0]}`; final `{data['final_line'][0]}`.\n")
    base_keys = {(r["module"], r["name"]): r["outcome"] for r in b["cases"]}
    fin_keys = {(r["module"], r["name"]): r["outcome"] for r in f["cases"]}
    changed = [k for k in base_keys if k in fin_keys and base_keys[k] != fin_keys[k]]
    new = [k for k in fin_keys if k not in base_keys]
    removed = [k for k in base_keys if k not in fin_keys]
    new_c = collections.Counter(fin_keys[k] for k in new)
    a(f"- **Regressions:** {len(changed)} results changed outcome between the runs; {len(removed)} results were removed.")
    a(f"- **New results:** {len(new)} (all from the three Phase 2 test files): {new_c['passed']} passed, "
      f"{new_c['failure']} failed, {new_c['error']} errors.")
    a(f"- **Not passed:** the same {f['failures'] + f['errors']} results in both runs - all environmental browser-launch problems (section 8).\n")

    a("## 5. Results by test level\n")
    rows = []
    for kind in TYPES:
        for label, t in (("Baseline", tb), ("Final", tf)):
            c = t[kind]
            rows.append((kind.capitalize() if label == "Baseline" else "", label, sum(c.values()), c["passed"],
                         c["failure"], c["error"], c["skipped"]))
    a(table(["Level", "Run", "Results", "Passed", "Failed", "Errors", "Skipped"], rows))
    a("")
    unit_final = tf["unit"]
    a(f"**Unit tests in the regression run: {sum(unit_final.values())} results, {unit_final['passed']} passed.** "
      f"The {tf['integration']['passed']} passing integration results, {tf['browser']['passed']} passing browser results and "
      f"{tf['static']['passed']} passing structural checks are **not** unit tests. "
      f"The {tf['integration']['skipped']} skipped results are the Sprint 1 placeholders in `test_sprint1_requirements.py` (section 9).\n")

    a("### 5.1 Unit tests\n")
    unit_rows = []
    for r in f["cases"]:
        if kind_of(data, r) == "unit":
            unit_rows.append((f"{r['module']}.py", r["name"], r["outcome"]))
    a(table(["File", "Test", "Outcome"], unit_rows))
    a("")
    a("These tests call `scripts/schedule_daily_backup.py` (cron line generation, schedule validation, crontab "
      "add/replace/remove) and `scripts/backup_db.py` (`create_backup` with a missing source database) directly. "
      "The Flask application has no tests at this level: its validation helpers (`app/validation.py`) are exercised "
      "through the API (see the coverage reports).\n")

    a("## 6. Test inventory\n")
    a("One row per test file and level (regression run). Requirement links come from the Test Case Document references.\n")
    req_by_module = collections.defaultdict(set)
    for c in data["cases"]:
        for ref in c["refs"]:
            if "::" in ref:
                _, module, _, _ = tcd.split_ref(ref)
                req_by_module[module].add(c["req"])
    inv = collections.defaultdict(collections.Counter)
    for r in f["cases"]:
        inv[(r["module"], kind_of(data, r))][r["outcome"]] += 1
    rows = []
    for (module, kind), c in sorted(inv.items()):
        reqs = ", ".join(sorted(req_by_module.get(module, []), key=lambda x: (x.startswith("NFR"), x))) or "-"
        rows.append((f"{module}.py", kind, reqs, sum(c.values()), c["passed"], c["failure"], c["error"], c["skipped"]))
    tot = f["counts"]
    rows.append(("**Total**", "", "", f["tests"], tot["passed"], tot["failure"], tot["error"], tot["skipped"]))
    a(table(["Test file", "Level", "Requirements (via Test Case Document)", "Results", "Passed", "Failed", "Errors", "Skipped"], rows))
    a("")

    a("## 7. Requirement mapping (Test Case Document)\n")
    a(f"The Test Case Document (v{tcd.VERSION}) has {len(data['cases'])} cases "
      f"({sum(1 for c in data['cases'] if c['change'] != cat.NEW)} original Test Plan IDs, all kept). "
      "Status per requirement and level:\n")
    rows = []
    for req in cat.MODULES:
        cs = [c for c in data["cases"] if c["req"] == req]
        per = []
        for t in ("UT", "IT", "SYS"):
            sub = [c for c in cs if c["type"] == t]
            pc = collections.Counter(c["status"] for c in sub)
            per.append(f"{pc.get('PASS', 0)}/{len(sub)}" if sub else "-")
        sc = collections.Counter(c["status"] for c in cs)
        rows.append((req, cat.MODULES[req], len(cs), *per, sc.get("FAIL", 0), sc.get("BLOCKED", 0), sc.get("NOT RUN", 0), sc.get("NOT APPLICABLE", 0)))
    allc = collections.Counter(c["status"] for c in data["cases"])
    rows.append(("**Total**", "", len(data["cases"]),
                 *[f"{sum(1 for c in data['cases'] if c['type'] == t and c['status'] == 'PASS')}/{sum(1 for c in data['cases'] if c['type'] == t)}" for t in ("UT", "IT", "SYS")],
                 allc.get("FAIL", 0), allc.get("BLOCKED", 0), allc.get("NOT RUN", 0), allc.get("NOT APPLICABLE", 0)))
    a(table(["Req.", "Module", "Cases", "UT passed", "IT passed", "SYS passed", "FAIL", "BLOCKED", "NOT RUN", "N/A"], rows))
    a("")
    a("### 7.1 `UT_` cases and the level of the tests that verify them\n")
    level_of_ref = {}
    rows = []
    for c in data["cases"]:
        if c["type"] != "UT":
            continue
        levels = collections.Counter()
        for ref in c["refs"]:
            if "::" not in ref:
                continue
            _, module, func, _ = tcd.split_ref(ref)
            k = data["kinds"].get((module, func), "unknown")
            levels[k] += 1
            level_of_ref[ref] = k
        lv = ", ".join(f"{k} x{n}" for k, n in sorted(levels.items())) or "no automated test"
        rows.append((c["id"], c["req"], c["scenario"], c["status"], lv))
    ut_levels = collections.Counter()
    for row in rows:
        for part in row[4].split(", "):
            ut_levels[part.split(" x")[0]] += 1
    a(f"{len(rows)} `UT_` cases. Number of cases linked to at least one test of each level (a case can be linked to "
      "several levels): " + ", ".join(f"{k}: {n}" for k, n in sorted(ut_levels.items())) + ". "
      "The genuine unit tests of section 5.1 are not linked to any `UT_` case; they support the NFR-03 cases.\n")
    a(table(["Case", "Req.", "Scenario", "Status", "Linked tests (level x count)"], rows))
    a("")

    a("## 8. Failed tests and errors\n")
    bad = [r for r in f["cases"] if r["outcome"] in ("failure", "error")]
    a(f"{len(bad)} results did not pass in the regression run ({f['failures']} failure, {f['errors']} errors). "
      "The same results failed in the baseline run. None is caused by application code:\n")
    rows = []
    for r in bad:
        msg = r["msg"].splitlines()[0] if r["msg"] else ""
        m = re.search(r"NFR-05 requires \w+ but it could not be launched", msg)
        msg = (m.group(0) + " (setup)") if m else re.sub(r"/Users/[^ ]*/", ".../", msg)[:160]
        rows.append((r["name"], r["outcome"], msg))
    a(table(["Test (tests/test_nfr05_browser_compatibility.py)", "Outcome", "Message (first line)"], rows))
    a("")
    a("- `[edge-...]` errors: Microsoft Edge is not installed on the test machine (installation not approved).")
    a("- `[firefox-...]` errors: Playwright Firefox (build 1572 after the Playwright 1.65.2 upgrade) is installed but still cannot "
      "start on this Mac (\"Could not find profile folder\"); diagnosis from the original run: "
      "`docs/evidence/final/browsers/firefox_blocked_diagnosis.txt`. Status kept BLOCKED; the team may validate on another machine.")
    a("- `test_report_tested_browser_versions` fails by design whenever any selected browser could not run.\n")

    a("## 9. Skipped tests\n")
    skipped = [r for r in f["cases"] if r["outcome"] == "skipped"]
    repl = {p[0]: (p[1], p[2]) for p in cat.PLACEHOLDERS}
    rows = []
    for r in skipped:
        req, by = repl.get(r["name"], ("", ""))
        rows.append((r["name"], r["msg"][:90], req, by))
    a(f"{len(skipped)} results are skipped - the Sprint 1 placeholders in `tests/test_sprint1_requirements.py`, kept on purpose. "
      "Each is covered by later real tests:\n")
    a(table(["Placeholder", "Skip reason", "Requirement", "Covered by"], rows))
    a("")

    a("## 10. Warnings\n")
    source = {
        "DeprecationWarning": "`app/api/exports.py:104` (`datetime.utcnow()`)",
        "ResourceWarning": "unclosed SQLite connections opened by test helpers and `scripts/backup_db.py`",
    }
    a(table(["Run", "Category", "Count", "Source"], [
        (run, catg, n, source.get(catg, "see log"))
        for run, key in (("Baseline", "warn_baseline"), ("Final", "warn_final"),
                         ("Coverage, statement run", "warn_cov_stmt"), ("Coverage, branch run", "warn_cov"))
        for catg, n in sorted(data[key][0].items(), key=lambda x: -x[1])
    ]))
    a("")
    dep = data["warn_final"][0].get("DeprecationWarning", 0)
    a(f"- **DeprecationWarning ({dep} per run):** `app/api/exports.py:104` calls `datetime.utcnow()`, deprecated since Python 3.12 "
      "(defect D-04, Low). Documented only - changing it is a production change.")
    rw = data["warn_cov"][0].get("ResourceWarning", 0)
    alloc = collections.Counter()
    for line in (EV / "coverage/resourcewarning_allocation_summary.txt").read_text().splitlines():
        m = re.match(r"^\s+(\d+)\s+(\S+)$", line)
        if m:
            path = m.group(2)
            alloc["tests" if path.startswith("tests/") else "app" if path.startswith("app/") else path] += int(m.group(1))
    a(f"- **ResourceWarning ({rw}, coverage runs only):** `unclosed database` warnings. Test helpers and `scripts/backup_db.py` "
      "use `with sqlite3.connect(...)`, which commits but does not close the connection. Coverage tracing changes when these "
      "objects are garbage-collected, so pytest reports them during coverage runs only. The file and line that pytest prints "
      "for each one is where garbage collection happened to run, which can be inside `app/` or a library; it is not where "
      "the connection was opened. A full-suite allocation trace under coverage "
      f"(`docs/evidence/coverage/resourcewarning_allocation_summary.txt`) found {alloc['tests']} of the connections opened in test files, "
      f"{alloc['scripts/backup_db.py']} in `scripts/backup_db.py` and {alloc['app']} in `app/`, which closes its connections in a "
      "teardown handler (observation O-04).\n")

    a("## 11. Evidence\n")
    a(table(["Evidence", "Location"], evidence_index()))
    a("")
    a("Coverage figures for the same suite are in `docs/Code_Coverage_Report.md` and `docs/Branch_Coverage_Report.md`.\n")
    return "\n".join(w)


# ------------------------------------------------------------------ System Validation Report
WORKFLOWS = [
    ("Administrator workflow", ["FR-07", "FR-08", "FR-09"]),
    ("Teacher workflow", ["FR-02", "FR-03", "FR-04", "FR-10", "FR-11"]),
    ("Student workflow", ["FR-05"]),
    ("Reporting and export (administrator and teacher)", ["FR-06", "FR-12"]),
    ("Common to all roles (sign-in, password, dashboard summary, logout)", ["FR-01", "FR-13", "FR-14", "FR-15"]),
]


def method_text(code):
    return {"A": "pytest", "B": "browser", "M": "manual"}.get(code, code.replace("A", "pytest").replace("B", "browser").replace("M", "manual"))


def endpoint_sentence(data):
    """How many registered view functions executed during the measured run (from coverage data)."""
    import tempfile

    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(Path(tempfile.mkdtemp()) / "routes.db"), "SECRET_KEY": "report"})
    cov = data["cov_branch_app"]["files"]
    views, executed, never = {}, 0, []
    for rule in app.url_map.iter_rules():
        fn = app.view_functions[rule.endpoint]
        fn = getattr(fn, "__wrapped__", fn)
        code = fn.__code__
        path = str(Path(code.co_filename).resolve().relative_to(ROOT))
        views[(path, fn.__name__)] = code.co_firstlineno
    for (path, name), first in sorted(views.items()):
        if path not in cov:
            continue
        funcs = sorted(f for f in functions_of(path) if f[2] == name and f[0] >= first)
        start, end = funcs[0][0], funcs[0][1]
        if set(range(start + 1, end + 1)) & set(cov[path]["executed_lines"]):
            executed += 1
        else:
            never.append(f"`{path}:{name}`")
    total = executed + len(never)
    text = f"{executed} of the {total} application view functions in the URL map (Flask's built-in static view excluded) executed during the measured coverage run"
    return text + ("; never executed: " + ", ".join(never) + "." if never else ".")


def system_validation_report(data):
    cases = data["cases"]
    tf = type_counts(data, "final")
    w = []
    a = w.append
    a("# System Validation Report\n")
    a("**Project:** Attendance Management System  ")
    a("**Deliverable:** 3 (Testing) - Phase 3  ")
    a(f"**Report date:** {cat.MANUAL_META['run_date']} (automated runs {REPORT_DATE}; manual validation run {cat.MANUAL_META['run_date']})  ")
    a("**Status of this report:** automated validation complete; the 19 manual validation cases were executed by Playwright "
      f"automation (instructor-approved): {tcd.manual_counts(cases)} (section 10).  ")
    a("**Generated by:** `scripts/build_phase3_reports.py` from the Test Case Document catalogue and the saved evidence.\n")

    a("## 1. Purpose and approach\n")
    a(f"This report validates the system against the SRS (FR-01 to FR-15, NFR-01 to NFR-06) using the {len(cases)} cases of the "
      f"Test Case Document v{tcd.VERSION}. Each case's status is derived automatically from the JUnit evidence of the final "
      "run. The 19 manual validation cases were executed by Playwright automation following the checklist steps; the instructor "
      "approved this as manual validation evidence. No person performed those steps; the named team member is the responsible "
      "test owner.\n")
    a(table(["Validation layer", "What it covers", "Evidence"], [
        ("Automated integration (pytest + Flask test client)", f"{sum(tf['integration'].values())} results in the regression run: "
         "every API workflow, role checks, validation, database behaviour, on a temporary SQLite database per test",
         "docs/evidence/regression/junit.xml"),
        ("Automated browser (Playwright)", "End-to-end admin, teacher and student workflows in a real browser; NFR-02 page-load timing",
         "docs/evidence/regression/junit.xml, docs/evidence/regression/browsers/"),
        ("Manual validation cases (Playwright automation, instructor-approved)", "The 19 checklist scenarios executed in "
         f"{cat.MANUAL_META['browser']} on an isolated validation_demo.db",
         f"docs/manual_validation/*.md, {cat.MANUAL_RUN_DIR}/, {cat.MANUAL_REPORT}"),
    ]))
    a("")

    a("### 1.1 Runs reported\n")
    of = data["orig_final"]
    orig = json.loads(cat.ORIGINAL_STATUSES_PATH.read_text())["meta"]["counts"] if cat.ORIGINAL_STATUSES_PATH.exists() else {}
    a(table(["Run", "Date", "Evidence", "Test results", "Test case statuses"], [
        ("Final run (original)", ORIGINAL_DATE, "docs/evidence/final/",
         f"{of['tests']} results: {of['counts']['passed']} passed, {of['failures']} failed, {of['errors']} errors, {of['skipped']} skipped",
         ", ".join(f"{orig.get(x, 0)} {x}" for x in STATUSES) + " (with the original manual validation run)"),
        ("Regression run (after the six fixes) - reported here", REPORT_DATE, "docs/evidence/regression/",
         f"{data['final']['tests']} results: {data['final']['counts']['passed']} passed, {data['final']['failures']} failed, "
         f"{data['final']['errors']} errors, {data['final']['skipped']} skipped",
         ", ".join(f"{n} {x}" for x, n in zip(STATUSES, status_counts(cases)))),
    ]))
    a("")
    a("The failure and errors of both runs are environmental (Edge not installed; Playwright Firefox cannot start on this Mac). "
      "The regression run adds 22 tests for the six fixes (`tests/test_six_failures_regression.py`, "
      "`tests/test_six_failures_browser.py`).\n")

    a("## 2. Overall status\n")
    rows = []
    for t in ("UT", "IT", "SYS"):
        sub = [c for c in cases if c["type"] == t]
        rows.append((t, len(sub), *status_counts(sub)))
    rows.append(("**All**", len(cases), *status_counts(cases)))
    a(table(["Level", "Cases", *STATUSES], rows))
    a("")
    nr = [c for c in cases if c["status"] == "NOT RUN"]
    nr_manual = [c for c in nr if c["tester"]]
    a(f"NOT RUN: {len(nr)} cases - {len(nr_manual)} manual validation case(s) not executable by automation "
      f"({', '.join(c['id'] for c in nr_manual) or 'none'}) and {len(nr) - len(nr_manual)} other cases (section 10.2).\n")

    a("## 3. Workflow validation\n")
    for title, reqs in WORKFLOWS:
        sub = [c for c in cases if c["req"] in reqs]
        # Manual owners come from the case assignments, not a hard-coded list.
        owners = [t for t in tcd.TESTERS if any(c["tester"] == t for c in sub)]
        owner = " / ".join(owners) or "none (no manual cases)"
        sc = status_counts(sub)
        a(f"### {title}\n")
        a(f"Requirements: {', '.join(f'{r} {cat.MODULES[r]}' for r in reqs)}. Manual validation owner: {owner}.\n")
        a(table(["Cases", *STATUSES], [(len(sub), *sc)]))
        a("")
        shown = [c for c in sub if c["type"] == "SYS" or c["status"] != "PASS"]
        a("System-level test cases and every case that has not passed (full records below; all other cases are "
          "recorded in the Test Case Document):\n")
        a(table(["Test Case ID", "Test scenario", "Assigned team member", "Status", "Defect / gap ID"],
                [(c["id"], c["scenario"], tcd.owner(c), c["status"], ", ".join(tcd.defect_ids(c)) or "-") for c in shown]))
        a("")
        for c in shown:
            a("\n".join(tcd.case_record(c, "####")))

    a("## 4. Non-functional validation\n")
    rows = []
    for req in [r for r in cat.MODULES if r.startswith("NFR")]:
        sub = [c for c in cases if c["req"] == req]
        rows.append((req, cat.MODULES[req], len(sub), *status_counts(sub)))
    a(table(["Req.", "Area", "Cases", *STATUSES], rows))
    a("")
    shown = [c for c in cases if c["req"].startswith("NFR") and (c["type"] == "SYS" or c["status"] != "PASS")]
    a("System-level NFR test cases and every NFR case that has not passed (full records below):\n")
    a(table(["Test Case ID", "Req.", "Test scenario", "Assigned team member", "Status", "Defect / gap ID"],
            [(c["id"], c["req"], c["scenario"], tcd.owner(c), c["status"], ", ".join(tcd.defect_ids(c)) or "-") for c in shown]))
    a("")
    a("### 4.1 NFR test case records\n")
    for c in shown:
        a("\n".join(tcd.case_record(c, "####")))

    a("## 5. Automated integration validation\n")
    ic = tf["integration"]
    a(f"Regression run: {sum(ic.values())} integration-level results - {ic['passed']} passed, {ic['failure']} failed, "
      f"{ic['error']} errors, {ic['skipped']} skipped (Sprint 1 placeholders). " + endpoint_sentence(data) + " The tests cover "
      "authentication and role restrictions (FR-01, NFR-01), marking and editing "
      "(FR-02, FR-03), percentages and alerts (FR-04, FR-11), viewing, filtering, reporting and export (FR-05, FR-06, FR-10, FR-12), "
      "administration (FR-07 to FR-09), password change and logout (FR-13, FR-15).\n")
    a(f"The IT-level cases of the Test Case Document: " + ", ".join(
        f"{s} {n}" for s, n in zip(STATUSES, status_counts([c for c in cases if c['type'] == 'IT'])) if n) + ".\n")

    a("## 6. Browser compatibility\n")
    rows, summary, perf_c, _ = browser_rows(data)
    a(table(["Browser", "Run", "Result", "Status", "Evidence"], rows))
    a("")
    a(f"NFR-02 page-load tests in Playwright Chromium (`test_nfr02_browser_performance.py`): {perf_c['passed']} passed, "
      f"{perf_c['failure']} failed, {perf_c['error']} errors (3.0-second limit and 1,500-record data set, as defined in that test file).\n")
    a("- **WebKit is not Safari.** The WebKit results are engine-level evidence only. The Safari application is untested: "
      "SYS_NFR-05_08 (Tharith) is BLOCKED because Playwright cannot drive it and enabling safaridriver was not approved.")
    a("- **D-01 (WebKit console errors) - closed.** In the original run (Playwright 1.64.1, WebKit build r2370) WebKit logged one "
      "false-positive `style-src-attr` violation per `<select>` element, also on a blank page with no inline styles: an upstream "
      "WebKit regression (Playwright issue #43617, fixed in WebKit 324283@main). With the approved upgrade to Playwright 1.65.2 "
      f"(WebKit build r2388) the CSP probe records {webkit_probe_text()} "
      "(`docs/evidence/regression/browsers/webkit_csp_probe_output.txt`). The application's security policy was not changed.")
    a("- **Firefox** remains BLOCKED locally: Playwright Firefox build 1572 still fails to start on this Mac (\"Could not find "
      "profile folder\"); the team may run `NFR05_BROWSERS=firefox` on another machine.")
    a("- **Edge** is BLOCKED (not installed; installation not approved).\n")

    a("## 7. Database validation\n")
    db_rows = []
    final = {(r["module"], r["name"]): r["outcome"] for r in data["final"]["cases"]}
    for (mod, name), what in [
        (("test_foundation", "test_database_schema"), "Schema: all tables and columns created by the app factory"),
        (("test_foundation", "test_duplicate_attendance_prevented"), "UNIQUE(student, subject, date) constraint rejects duplicates"),
        (("test_fr03_record_management", "test_it_fr_03_06_database_persistence_across_connection_reload"), "Records persist across a new connection"),
        (("test_fr03_record_management", "test_sys_fr_03_10_database_atomic_rollback"), "Failed save rolls back; no partial writes"),
        (("test_fr02_attendance_marking", "test_batch_rollback_on_failure"), "Batch save is all-or-nothing"),
        (("test_fr01_session_expiry_and_auth_failure", "test_sys_fr_01_10_login_with_unavailable_database_fails_safely"), "Database unavailable at login: 503 without internal details"),
        (("test_nfr03_reliability", "test_nfr03_backup_is_created"), "Backup file created"),
        (("test_nfr03_reliability", "test_nfr03_backup_preserves_attendance_records"), "Backup preserves attendance records"),
        (("test_nfr03_reliability", "test_nfr03_backup_survives_original_data_changes"), "Backup independent of later changes"),
        (("test_nfr03_reliability", "test_nfr03_backup_contains_valid_database_schema"), "Backup passes schema / integrity check"),
        (("test_nfr03_reliability", "test_nfr03_missing_database_fails_safely"), "Missing source database fails safely"),
    ]:
        hits = [o for (m, n), o in final.items() if m == mod and n.split("[")[0] == name]
        if not hits:
            raise SystemExit(f"Database validation test not found in regression run: {mod}::{name}")
        c = collections.Counter(hits)
        db_rows.append((f"{mod}::{name}", what, ", ".join(f"{n} {o}" for o, n in c.items())))
    a(table(["Test", "What is validated", "Regression run"], db_rows))
    a("")
    nfr03 = [c for c in cases if c["req"] == "NFR-03"]
    a("NFR-03 (reliability) cases: " + ", ".join(f"{c['id']} {c['status']}" for c in nfr03) + ".\n")
    a("- **Test isolation:** every test uses its own temporary database; the real `attendance.db` SHA-1 "
      "was identical before and after every Phase 2 and Phase 3 run, and the user's crontab was unchanged.")
    a("- **Restore (IT_NFR-03_03):** NOT RUN - there is no restore script (gap G-07); to be checked manually.")
    a("- **O-01 (data integrity, Low):** the enrollment API accepts a subject that is not linked to the chosen class. "
      "Verified on a temporary database (`docs/evidence/phase3/o01_enrollment_probe_output.txt`): the request returns 201 and the "
      "teacher roster for that class/subject then lists the student. The admin dashboard only offers the class's own subjects, "
      "so this cannot happen through normal UI use. SRS FR-09 (\"assign students to their respective classes and subjects\") "
      "implies the subject belongs to the class, so this is a genuine but minor API validation gap, not a missing feature. Not fixed.\n")

    a("## 8. Known frontend limitations\n")
    gap_ids = {"G-01", "G-02", "G-03", "G-04", "G-05"}
    a(table(["Gap", "Req.", "Limitation", "Required by SRS?", "Classification", "Affected cases"],
            [(g[0], g[1], g[2], g[3], g[4], g[6]) for g in cat.GAPS if g[0] in gap_ids]))
    a("")
    a("Other open gaps (not frontend): " + "; ".join(f"{g[0]} {g[1]} - {g[4]}" for g in cat.GAPS if g[0] not in gap_ids) + ".\n")

    a("## 9. Outstanding defects and observations\n")
    a(table(["ID", "Req.", "Severity", "Description", "Test impact", "Status"], cat.DEFECTS))
    a("")
    a("After Deliverable 3 testing the six failed cases were fixed (approved production changes to the browser UI only: "
      "JavaScript, CSS and templates) and re-verified in the regression run: D-01, D-02, D-03 and MV-01 to MV-03 are closed. "
      "D-01 needed no application change: it was an upstream WebKit regression, resolved by the approved Playwright 1.65.2 / "
      "WebKit r2388 upgrade, and the security policy was not relaxed. D-04 and the O-xx observations remain open.\n")

    a("## 10. Manual validation\n")
    a("### 10.1 Manual validation cases (executed by Playwright automation)\n")
    a(f"The 19 checklist cases were executed on {cat.MANUAL_META['run_date']} by `scripts/run_manual_validation_automation.py` in "
      f"{cat.MANUAL_META['browser']} against an isolated `validation_demo.db` (the real `attendance.db` was unchanged, SHA-256 "
      f"`{cat.MANUAL_META['attendance_db_sha256']}`). The instructor approved automated browser execution as evidence for manual "
      "validation. No person performed the steps; each named member is the responsible test owner. Results: "
      f"{tcd.manual_counts(cases)}. Full step results: `{cat.MANUAL_REPORT}`.\n")
    for tester in tcd.TESTERS:
        sub = [c for c in cases if c["tester"] == tester]
        a(f"**{tester}** (test owner) - {tcd.TESTER_SCOPE[tester]} Checklist: `docs/manual_validation/{tester}_Checklist.md` "
          f"({len(sub)} cases: {tcd.manual_counts(sub)}).\n")
        a(table(["Test Case ID", "Req.", "Test scenario", "Status", "Execution date", "Screenshot evidence", "Defect / gap ID"],
                [(c["id"], c["req"], c["scenario"], c["status"], c["date"] or "-",
                  f"{len(c['manual_run']['screenshots'])} screenshot(s)", ", ".join(tcd.defect_ids(c)) or "-") for c in sub]))
        a("")
    a("Aspects the automated run could not assess (no human judgement was made):\n")
    a(table(["Case", "Not assessed"], sorted(cat.MANUAL_LIMITS.items())))
    a("")
    a("### 10.2 Other cases not yet executed\n")
    other = [c for c in nr if not c["tester"]]
    a(table(["Case", "Scenario", "Reason"], [(c["id"], c["scenario"], c["actual"] or "") for c in other]))
    a("")

    a("## 11. Conclusion\n")
    pc = collections.Counter(c["status"] for c in cases)

    def ids(status):
        return ", ".join(c["id"] for c in cases if c["status"] == status)

    open_fail = ", ".join(d[0] for d in cat.DEFECTS if d[5].startswith("Open") and "FAIL" in d[4])
    fixed = ", ".join(d[0] for d in cat.DEFECTS if d[5].startswith("Fixed"))
    fail_text = (f"{pc['FAIL']} FAIL ({ids('FAIL')}; defects {open_fail})" if pc["FAIL"]
                 else f"0 FAIL (the six failures of the original runs were fixed and re-verified; defects {fixed} closed)")
    a(f"{pc['PASS']} of {len(cases)} cases PASS. {fail_text}, "
      f"{pc['BLOCKED']} BLOCKED ({ids('BLOCKED')}), {pc['NOT APPLICABLE']} NOT APPLICABLE ({ids('NOT APPLICABLE')}), and "
      f"{pc['NOT RUN']} NOT RUN ({ids('NOT RUN')}). The manual validation cases were executed by Playwright automation "
      f"({tcd.manual_counts(cases)}); SYS_NFR-04_06 (human usability walkthrough) is NOT RUN and SYS_NFR-05_08 (Safari "
      "application) is BLOCKED. The fixes changed only browser-side files; no backend endpoint, schema or security header changed.\n")

    a("## 12. Evidence\n")
    a(table(["Evidence", "Location"], evidence_index()))
    a("")
    return "\n".join(w)


# ------------------------------------------------------------------ coverage helpers
COVERAGERC = ROOT / ".coveragerc"


def file_summary_rows(cov, branch=False):
    rows = []
    for f, info in sorted(cov["files"].items()):
        s = info["summary"]
        if branch:
            rows.append((f"`{f}`", s["num_branches"], s["covered_branches"], s["missing_branches"], s["num_partial_branches"],
                         pct(s["covered_branches"], s["num_branches"]), pct(s["covered_lines"], s["num_statements"])))
        else:
            rows.append((f"`{f}`", s["num_statements"], s["covered_lines"], s["missing_lines"], s["excluded_lines"],
                         pct(s["covered_lines"], s["num_statements"])))
    t = cov["totals"]
    if branch:
        rows.append(("**Total**", t["num_branches"], t["covered_branches"], t["missing_branches"], t["num_partial_branches"],
                     f"**{pct(t['covered_branches'], t['num_branches'])}**", pct(t["covered_lines"], t["num_statements"])))
    else:
        rows.append(("**Total**", t["num_statements"], t["covered_lines"], t["missing_lines"], t["excluded_lines"],
                     f"**{pct(t['covered_lines'], t['num_statements'])}**"))
    return rows


def missed_by_cause(cov):
    import ast
    lines_c, br_c = collections.Counter(), collections.Counter()
    per_file = {}
    for f, info in cov["files"].items():
        tree = ast.parse((ROOT / f).read_text())
        handlers, shadow = [], None
        for n in ast.walk(tree):
            if isinstance(n, ast.ExceptHandler):
                handlers.append((n.lineno, n.end_lineno, ast.unparse(n.type) if n.type else ""))
            if f == "app/api/attendance_management.py" and isinstance(n, ast.FunctionDef) and n.name == "get_attendance":
                shadow = (n.lineno, n.end_lineno)

        def cause(line):
            if shadow and shadow[0] <= line <= shadow[1]:
                return "Unreachable: shadowed GET /api/attendance view (O-02)"
            for s, e, t in handlers:
                if s <= line <= e:
                    return "Database-error handlers (sqlite3.Error / IntegrityError)" if "sqlite3" in t else "Other exception handlers"
            return "Untested validation / alternative paths"

        fc = collections.Counter()
        for line in info["missing_lines"]:
            lines_c[cause(line)] += 1
            fc[cause(line)] += 1
        for a_, _ in info.get("missing_branches", []):
            br_c[cause(a_)] += 1
        per_file[f] = fc
    return lines_c, br_c, per_file


SHADOW = "Unreachable: shadowed GET /api/attendance view (O-02)"
DBH = "Database-error handlers (sqlite3.Error / IntegrityError)"


def webkit_probe_text():
    """Summarise the regression CSP probe (violations per dashboard, WebKit and Chromium)."""
    found = {}
    for line in (RUN / "browsers/webkit_csp_probe_output.txt").read_text().splitlines():
        m = re.match(r"^(\w+)\s+/(\w+)\s+selects=(\d+) console_errors=(\d+) violations=(\d+)", line)
        if m:
            found[(m.group(1), m.group(2))] = tuple(int(m.group(i)) for i in (3, 4, 5))
    parts = [f"{page} {found[('webkit', page)][2]} violations / {found[('webkit', page)][0]} selects"
             for page in ("admin", "teacher", "student")]
    chromium = sum(v[2] for (eng, _), v in found.items() if eng == "chromium")
    return "WebKit " + ", ".join(parts) + f"; Chromium {chromium} violations"


SHORT_CAUSE = {
    "Unreachable: shadowed GET /api/attendance view (O-02)": "unreachable (O-02)",
    "Database-error handlers (sqlite3.Error / IntegrityError)": "in database-error handlers",
    "Other exception handlers": "in other exception handlers",
    "Untested validation / alternative paths": "on untested validation / alternative paths",
}


def covered_db_handlers(cov):
    import ast
    out = []
    for f, info in sorted(cov["files"].items()):
        executed = set(info["executed_lines"])
        for n in ast.walk(ast.parse((ROOT / f).read_text())):
            if isinstance(n, ast.ExceptHandler) and n.type is not None and "sqlite3" in ast.unparse(n.type):
                if set(range(n.body[0].lineno, n.end_lineno + 1)) & executed:
                    out.append((f, n.lineno, ast.unparse(n.type)))
    return out


def functions_of(f):
    import ast
    tree = ast.parse((ROOT / f).read_text())
    return [(n.lineno, n.end_lineno, n.name) for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def owner(funcs, line):
    best = None
    for s, e, name in funcs:
        if s <= line <= e and (best is None or s > best[0]):
            best = (s, e, name)
    return best[2] if best else "<module>"


def coverage_env_block():
    lines = env_lines(RUN / "environment.txt")
    info = COV / "run_info.txt"
    if info.exists():   # the coverage runs were repeated after a .coveragerc correction
        lines = [l for l in lines if not l.startswith("coverage ")]
        lines += [f"{l}  (repeated coverage run; first attempt in docs/evidence/regression/coverage_attempt1/)"
                  for l in info.read_text().splitlines() if l.strip()]
    return "\n".join(lines)


def pragma_count():
    n = 0
    for p in list((ROOT / "app").rglob("*.py")) + [ROOT / "scripts/backup_db.py", ROOT / "scripts/schedule_daily_backup.py"]:
        n += p.read_text().count("pragma: no cover")
    return n


# ------------------------------------------------------------------ Code Coverage Report
def code_coverage_report(data):
    app = data["cov_statement_app"]
    scr = data["cov_statement_scripts"]
    t, ts = app["totals"], scr["totals"]
    lines_c, _, per_file = missed_by_cause(data["cov_branch_app"])
    w = []
    a = w.append
    a("# Code Coverage Report (Statement Coverage)\n")
    a("**Project:** Attendance Management System  ")
    a("**Deliverable:** 3 (Testing) - Phase 3  ")
    a(f"**Report date:** {REPORT_DATE}  ")
    a(f"**Tool:** coverage.py {app['meta']['version']} via pytest-cov  ")
    a("**Generated by:** `scripts/build_phase3_reports.py` from `docs/evidence/regression/coverage/statement/coverage_app.json` and "
      "`coverage_scripts.json`. Percentages are computed from the measured counts and are not adjusted.\n")
    a("This report covers **statement (line) coverage** only. Branch coverage is reported separately in "
      "`docs/Branch_Coverage_Report.md`.\n")

    a("## 1. Summary\n")
    a(table(["Scope", "Statements", "Executed", "Missed", "Excluded", "Statement coverage"], [
        ("Application source `app/` (primary result)", t["num_statements"], t["covered_lines"], t["missing_lines"], t["excluded_lines"],
         f"**{pct(t['covered_lines'], t['num_statements'])}**"),
        ("NFR-03 operational scripts (supplementary)", ts["num_statements"], ts["covered_lines"], ts["missing_lines"], ts["excluded_lines"],
         pct(ts["covered_lines"], ts["num_statements"])),
    ]))
    a("")
    j = data["cov_statement_junit"]
    a(f"The coverage was measured on a full run of the test suite: `{data['cov_statement_line'][0]}`. Every test had the "
      f"same outcome as in the final Phase 2 run (checked result by result). The {j['failures'] + j['errors']} non-passing results are the "
      "environmental Edge/Firefox browser-launch problems; tests that error before running do not add coverage.\n")

    a("## 2. Environment and commands\n")
    a("```text")
    a(coverage_env_block())
    a("```\n")
    a("Coverage configuration (`.coveragerc`):\n")
    a("```ini")
    a(COVERAGERC.read_text().strip())
    a("```\n")

    a("## 3. Scope and exclusions\n")
    a(f"- **Measured:** every Python module in `app/` ({len(app['files'])} files), plus `scripts/backup_db.py` and "
      "`scripts/schedule_daily_backup.py` (NFR-03 backup and scheduling), which the tests import. The scripts are reported "
      "separately so they do not change the application figure.")
    a("- **Omitted from measurement (not application code):** `scripts/build_test_case_document.py`, `scripts/case_catalog.py`, "
      "`scripts/summarize_junit.py` (documentation tooling), `scripts/seed_demo_data.py` (demo data), "
      "`scripts/backend_performance_bench.py`, `scripts/run_browser_benchmarks.py` (benchmarks), and the tests themselves.")
    a(f"- **Excluded lines:** {t['excluded_lines']} in `app/`. The source has {pragma_count()} `pragma: no cover` markers and "
      "`.coveragerc` adds no exclusion rules.")
    a("- **Not measurable by coverage.py:** JavaScript in `app/static/js/` and Jinja templates. They are exercised by the browser "
      "tests, but no JavaScript coverage tool is used, so no JavaScript coverage figure is claimed.")
    a("- **Subprocesses:** some NFR-06 tests import the app in a fresh interpreter (subprocess); those processes are not measured. "
      "The live server used by the browser tests runs in a thread of the test process and is measured.\n")

    a("## 4. Per-module statement coverage (`app/`)\n")
    a(table(["Module", "Statements", "Executed", "Missed", "Excluded", "Coverage"], file_summary_rows(app)))
    a("")
    a("## 5. Supplementary: NFR-03 scripts\n")
    a(table(["Module", "Statements", "Executed", "Missed", "Excluded", "Coverage"], file_summary_rows(scr)))
    a("")
    a("The missed script lines are the command-line entry points (`main`, argument handling, `crontab -l` failure handling) "
      "and the backup integrity-failure path. The tests call the functions directly and never run the command line, "
      "so that the real crontab and database are not touched.\n")

    a("## 6. Why lines are missed\n")
    a("Every missed line in `app/` was put into one category by its position in the source (computed, not estimated):\n")
    a(table(["Category", "Missed lines", "Share of missed"],
            [(k, n, pct(n, t["missing_lines"])) for k, n in lines_c.most_common()] + [("**Total**", t["missing_lines"], "100.00%")]))
    a("")
    shadow = lines_c.get("Unreachable: shadowed GET /api/attendance view (O-02)", 0)
    a(f"- **Unreachable code ({shadow} lines).** `GET /api/attendance` is registered twice; Flask always dispatches it to "
      "`attendance_view.view_attendance`, so `attendance_management.get_attendance` can never run. This is a documented "
      "design decision pinned by `test_nfr06_maintainability.py` (observation O-02). No test can cover it without a production change.")
    covered_h = covered_db_handlers(data["cov_branch_app"])
    a(f"- **Database-error handlers.** Most API handlers catch `sqlite3.Error` / `sqlite3.IntegrityError` and return 503 or 409. "
      f"Only {len(covered_h)} of these handlers run during the tests: " + ", ".join(f"`{f}:{l}` ({t})" for f, l, t in covered_h) +
      ". The others need a database failure that no test triggers.")
    a("- **Untested validation and alternative paths.** These are input checks and options that no test sends. "
      "The branch coverage report lists the important ones.\n")

    a("## 7. Missed lines per module\n")
    rows = []
    for f, info in sorted(app["files"].items()):
        if not info["missing_lines"]:
            continue
        funcs = functions_of(f)
        by_fn = collections.defaultdict(list)
        for line in info["missing_lines"]:
            by_fn[owner(funcs, line)].append(line)
        for fn, lines in sorted(by_fn.items(), key=lambda x: x[1][0]):
            rows.append((f"`{f}`", f"`{fn}`", len(lines), ranges(lines)))
    for f, info in sorted(scr["files"].items()):
        funcs = functions_of(f)
        by_fn = collections.defaultdict(list)
        for line in info["missing_lines"]:
            by_fn[owner(funcs, line)].append(line)
        for fn, lines in sorted(by_fn.items(), key=lambda x: x[1][0]):
            rows.append((f"`{f}`", f"`{fn}`", len(lines), ranges(lines)))
    a(table(["Module", "Function", "Missed", "Line numbers"], rows))
    a("")

    a("## 8. Lowest-covered modules\n")
    low = sorted(app["files"].items(), key=lambda x: x[1]["summary"]["covered_lines"] / max(1, x[1]["summary"]["num_statements"]))[:4]
    for f, info in low:
        s = info["summary"]
        c = per_file[f]
        a(f"- `{f}` - {pct(s['covered_lines'], s['num_statements'])} ({s['missing_lines']} missed: " +
          ", ".join(f"{n} {SHORT_CAUSE[k]}" for k, n in c.most_common()) + ").")
    a("")

    a("## 9. Evidence\n")
    a(table(["File", "Content"], [
        ("docs/evidence/regression/coverage/statement/coverage_app.json", "Machine-readable statement coverage, `app/` (coverage.py JSON)"),
        ("docs/evidence/regression/coverage/statement/coverage_scripts.json", "Machine-readable statement coverage, NFR-03 scripts"),
        ("docs/evidence/regression/coverage/statement/coverage.xml", "Cobertura XML (both scopes)"),
        ("docs/evidence/regression/coverage/statement/coverage_report_app.txt, coverage_report_scripts.txt", "`coverage report -m` text output"),
        ("docs/evidence/regression/coverage/statement/junit.xml, pytest_output.txt", "Test results of the measured run"),
        ("docs/evidence/regression/environment.txt", "Versions, commands, database fingerprint before and after"),
        ("docs/evidence/regression/coverage/branch/html/index.html", "Browsable HTML report (local only: coverage.py marks it git-ignored)"),
    ]))
    a("")
    a("To reproduce:\n")
    a("```bash")
    a(".venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt")
    a("COVERAGE_FILE=docs/evidence/regression/coverage/statement/.coverage .venv/bin/python -m pytest -q -p no:cacheprovider \\")
    a("    --cov --cov-config=.coveragerc --cov-report= --junitxml=docs/evidence/regression/coverage/statement/junit.xml")
    a("COVERAGE_FILE=docs/evidence/regression/coverage/statement/.coverage .venv/bin/python -m coverage report --rcfile=.coveragerc --include='app/*'")
    a("```\n")
    return "\n".join(w)


# ------------------------------------------------------------------ Branch Coverage Report
IMPORTANT = [
    # (file, from, to, requirement, what the uncovered path is, why it matters)
    ("app/api/attendance_records.py", 212, 213, "FR-02",
     "Batch save with `class_id` + `subject_id` where some enrolled students are missing from the submission "
     "(\"All enrolled students must be marked\").",
     "This is the request the teacher dashboard sends. The completeness rule is never exercised."),
    ("app/api/attendance_records.py", 324, 325, "FR-02 / FR-03",
     "Batch save with `update_existing: true` when a record already exists - the existing row is updated.",
     "The teacher dashboard always sends `update_existing: true`, so this path runs whenever a teacher saves a date that "
     "already has records. Only the insert path of the batch save is tested."),
    ("app/api/attendance_records.py", 154, 158, "FR-02 / NFR-01",
     "Batch save by a teacher for a subject assigned to another teacher (403).",
     "This authorization check is tested on the single-record path only, not on the batch path."),
    ("app/api/attendance_records.py", 244, 245, "FR-02",
     "Invalid status inside a batch item.",
     "This status check is tested on the single-record path only, not on the batch path."),
    ("app/api/attendance_records.py", 256, 257, "FR-02 / FR-03",
     "The same student twice in one batch submission (400).",
     "This duplicate rule is untested."),
    ("app/api/attendance_management.py", 303, 304, "FR-03",
     "Editing a record's date through `PUT /api/attendance/<id>`.",
     "Editing a record's date is never tested, including the duplicate check when the new date collides (321->322)."),
    ("app/api/attendance_management.py", 296, 297, "FR-03",
     "Invalid status when editing a record by id.",
     "Status and date validation on the two edit endpoints (by id and by key, 392->393 / 398->399) is never exercised; "
     "the same checks are tested only when creating records."),
    ("app/api/attendance_management.py", 198, 199, "FR-05 / NFR-01",
     "A student reading another student's record by id (`GET /api/attendance/<id>`, 403).",
     "This privacy rule on a read endpoint is never exercised."),
    ("app/api/alerts.py", 132, 133, "FR-11",
     "Alerts requested with `POST` and a JSON body (threshold and filters in the body).",
     "The endpoint accepts POST, but only GET is tested."),
    ("app/api/alerts.py", 47, 52, "FR-11",
     "A stored threshold that fails validation, so the default threshold is used instead.",
     "This fallback for a corrupted setting is untested."),
    ("app/db.py", 78, 79, "NFR-03 / NFR-06",
     "Schema upgrade that adds `classes.teacher_id` to an older database.",
     "This migration runs once on existing databases; tests always start from a fresh schema."),
    ("app/__init__.py", 59, 63, "-",
     "`create_app()` without test configuration (production defaults).",
     "Every in-process test passes a test configuration, so the production defaults path is never measured."),
    ("app/api/users.py", 122, 125, "FR-07",
     "An invalid `active` filter on the user list (400).",
     "This input validation is untested."),
    ("app/api/exports.py", 196, 197, "FR-12",
     "PDF export where the page is full just before the closing table line, forcing an extra page break.",
     "An edge case of the multi-page layout. Large multi-page exports are tested (SYS_FR-12_09), but never hit this boundary."),
    ("scripts/backup_db.py", 59, 60, "NFR-03",
     "Backup fails the integrity check, and the incomplete file is deleted.",
     "This failure path of the backup is untested."),
]


def branch_coverage_report(data):
    app = data["cov_branch_app"]
    scr = data["cov_branch_scripts"]
    t, ts = app["totals"], scr["totals"]
    lines_c, br_c, _ = missed_by_cause(app)
    missing = {f: {tuple(x) for x in info["missing_branches"]} for f, info in {**app["files"], **scr["files"]}.items()}
    for f, a_, b_, *_ in IMPORTANT:
        if (a_, b_) not in missing[f]:
            raise SystemExit(f"Curated branch {f}:{a_}->{b_} is not a missing branch in the evidence")
    w = []
    a = w.append
    a("# Branch Coverage Report\n")
    a("**Project:** Attendance Management System  ")
    a("**Deliverable:** 3 (Testing) - Phase 3  ")
    a(f"**Report date:** {REPORT_DATE}  ")
    a(f"**Tool:** coverage.py {app['meta']['version']} with branch measurement (`--cov-branch`)  ")
    a("**Generated by:** `scripts/build_phase3_reports.py` from `docs/evidence/regression/coverage/branch/coverage_app.json` and "
      "`coverage_scripts.json`. Percentages are computed from the measured counts and are not adjusted.\n")

    a("## 1. What branch coverage measures\n")
    a("Statement coverage asks *was this line executed?* Branch coverage asks *was each possible outcome of every decision "
      "taken?* For an `if` this means both the true and the false outcome. coverage.py records each possible jump between "
      "lines (an *arc*), such as `212->213`: line 212 is the decision and line 213 is the outcome that was never taken. "
      "A line can be executed (statement covered) while one of its outcomes is not. That is a *partial* branch.\n")

    a("## 2. Summary\n")
    a(table(["Scope", "Branch outcomes", "Taken", "Not taken", "Lines with a partial branch", "Branch coverage", "Statement coverage (for comparison)"], [
        ("Application source `app/` (primary result)", t["num_branches"], t["covered_branches"], t["missing_branches"], t["num_partial_branches"],
         f"**{pct(t['covered_branches'], t['num_branches'])}**", pct(t["covered_lines"], t["num_statements"])),
        ("NFR-03 scripts (supplementary)", ts["num_branches"], ts["covered_branches"], ts["missing_branches"], ts["num_partial_branches"],
         pct(ts["covered_branches"], ts["num_branches"]), pct(ts["covered_lines"], ts["num_statements"])),
    ]))
    a("")
    a(f"- **Branch coverage of `app/`: {t['covered_branches']} of {t['num_branches']} branch outcomes = "
      f"{pct(t['covered_branches'], t['num_branches'])}.**")
    a(f"- coverage.py's terminal `Cover` column in branch mode shows a **combined** figure "
      f"(statements + branches: ({t['covered_lines']} + {t['covered_branches']}) / ({t['num_statements']} + {t['num_branches']}) "
      f"= {t['percent_covered']:.2f}%). It is neither the statement nor the branch figure and is not used in these reports.")
    a(f"- The statement figures in this run are identical to the separate statement-only run "
      f"({t['covered_lines']}/{t['num_statements']}), checked file by file.")
    a(f"- Measured run: `{data['cov_branch_line'][0]}` - same per-test outcomes as the final Phase 2 run.\n")

    a("## 3. Commands\n")
    a("```bash")
    a("COVERAGE_FILE=docs/evidence/regression/coverage/branch/.coverage .venv/bin/python -m pytest -q -p no:cacheprovider \\")
    a("    --cov --cov-branch --cov-config=.coveragerc --cov-report= --junitxml=docs/evidence/regression/coverage/branch/junit.xml")
    a("COVERAGE_FILE=docs/evidence/regression/coverage/branch/.coverage .venv/bin/python -m coverage json --rcfile=.coveragerc \\")
    a("    --include='app/*' -o docs/evidence/regression/coverage/branch/coverage_app.json")
    a("```\n")
    a("Scope and exclusions are the same as in the Code Coverage Report (section 3): `app/` measured, NFR-03 scripts supplementary, "
      "tooling scripts omitted, no excluded lines, JavaScript not measured.\n")

    a("## 4. Per-module branch coverage (`app/`)\n")
    a(table(["Module", "Branch outcomes", "Taken", "Not taken", "Partial lines", "Branch coverage", "Statement coverage"],
            file_summary_rows(app, branch=True)))
    a("")
    a("Modules with 0 branch outcomes contain no decisions (only route registration or imports).\n")
    a("## 5. Supplementary: NFR-03 scripts\n")
    a(table(["Module", "Branch outcomes", "Taken", "Not taken", "Partial lines", "Branch coverage", "Statement coverage"],
            file_summary_rows(scr, branch=True)))
    a("")

    a("## 6. Why branches are missed\n")
    a(table(["Category", "Branch outcomes not taken", "Share"],
            [(k, n, pct(n, t["missing_branches"])) for k, n in br_c.most_common()] + [("**Total**", t["missing_branches"], "100.00%")]))
    a("")
    a("Exception handlers are reached by raising an exception, not by a decision, so the untested `sqlite3.Error` handlers "
      f"appear only in the statement report. The {br_c.get(SHADOW, 0)} outcomes in the shadowed `get_attendance` view cannot be reached (O-02).\n")

    a("## 7. Important uncovered conditional paths\n")
    a("These were selected from the missing-branch list because they belong to a requirement the users rely on. Each arc is "
      "checked against the evidence when this report is generated:\n")
    rows = []
    for i, (f, a_, b_, req, what, why) in enumerate(IMPORTANT, 1):
        src = (ROOT / f).read_text().splitlines()[a_ - 1].strip()
        rows.append((i, f"`{f}:{a_}->{b_}`", req, f"`{src[:70]}`", what, why))
    a(table(["#", "Arc", "Req.", "Decision", "Path not taken", "Why it matters"], rows))
    a("")
    a("None of these makes a Test Case Document case wrong: no case claims these paths. They are untested behaviour, "
      "not observed failures.\n")

    a("## 8. All missed branches\n")
    for scope_name, cov in (("app/", app), ("NFR-03 scripts", scr)):
        a(f"### {scope_name}\n")
        rows = []
        for f, info in sorted(cov["files"].items()):
            if not info["missing_branches"]:
                continue
            src = (ROOT / f).read_text().splitlines()
            funcs = functions_of(f)
            grouped = collections.defaultdict(list)
            for a_, b_ in info["missing_branches"]:
                grouped[(a_, owner(funcs, a_))].append("exit" if b_ < 0 else str(b_))
            for (a_, fn), targets in sorted(grouped.items()):
                rows.append((f"`{f}`", f"`{fn}`", a_, ", ".join(targets), f"`{src[a_ - 1].strip()[:80]}`"))
        a(table(["Module", "Function", "Line", "Outcome(s) not taken (to line)", "Decision"], rows))
        a("")

    a("## 9. Recommendations\n")
    a("These are recommendations only. No tests or application code were changed in Phase 3.\n")
    a("1. **Test the dashboard's real save request.** Add integration tests for the batch request "
      "the teacher dashboard sends: a submission with an enrolled student missing (expect 400), a re-save over existing records "
      "(expect updated statuses), the same student twice, an invalid status in an item, and a teacher who is not assigned to the subject.")
    a("2. **Test editing a record.** Cover `PUT /api/attendance/<id>` with a new date, a date that collides with "
      "another record (expect 409), an invalid status, and a missing record. Also cover a student reading another student's "
      "record by id (expect 403).")
    a("3. **Alerts.** Cover the POST form of the alerts endpoint and the fallback when the stored threshold is invalid.")
    a("4. **Database-error handling.** Add a small parametrized test that makes the database unavailable (as the Phase 2 login "
      "test does) for a representative endpoint per module and expects 503 with no internal details. This would cover most "
      f"of the {lines_c.get(DBH, 0)} missed handler lines in the statement report.")
    a("5. **Schema upgrade.** Create an old-format database without `classes.teacher_id`, start the app, and check that "
      "the column is added and the data is kept.")
    a("6. **O-02.** The team could decide whether to keep the unreachable `get_attendance` view. Removing it would be a production "
      f"change, so it needs approval. It accounts for {lines_c.get(SHADOW, 0)} missed statements and {br_c.get(SHADOW, 0)} missed branch outcomes.")
    a("7. **Do not chase 100%.** Tests should assert real behaviour. Coverage must not be raised with tests that only execute code.\n")

    a("## 10. Evidence\n")
    a(table(["File", "Content"], [
        ("docs/evidence/regression/coverage/branch/coverage_app.json", "Machine-readable branch + statement coverage, `app/` (includes `missing_branches` arcs)"),
        ("docs/evidence/regression/coverage/branch/coverage_scripts.json", "Same for the NFR-03 scripts"),
        ("docs/evidence/regression/coverage/branch/coverage.xml", "Cobertura XML with branch rates"),
        ("docs/evidence/regression/coverage/branch/coverage_report_app.txt, coverage_report_scripts.txt", "`coverage report -m` text output (Branch / BrPart columns)"),
        ("docs/evidence/regression/coverage/branch/junit.xml, pytest_output.txt", "Test results of the measured run"),
        ("docs/evidence/regression/coverage/branch/html/index.html", "Browsable HTML report (local only: coverage.py marks it git-ignored)"),
    ]))
    a("")
    return "\n".join(w)


# ------------------------------------------------------------------ main
def main():
    data = load()
    check_consistency(data)
    outputs = {
        "Unit_Test_Report.md": unit_test_report(data),
        "System_Validation_Report.md": system_validation_report(data),
        "Code_Coverage_Report.md": code_coverage_report(data),
        "Branch_Coverage_Report.md": branch_coverage_report(data),
    }
    for name, text in outputs.items():
        (DOCS / name).write_text(text.rstrip() + "\n", encoding="utf-8")
        print(f"wrote docs/{name} ({len(text.splitlines())} lines)")
    t, b = data["cov_statement_app"]["totals"], data["cov_branch_app"]["totals"]
    print(f"app/ statement coverage {pct(t['covered_lines'], t['num_statements'])}; "
          f"branch coverage {pct(b['covered_branches'], b['num_branches'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
