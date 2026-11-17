"""Build the Test Case Document and the manual validation checklists.

Usage:
    python scripts/build_test_case_document.py

Outputs:
    docs/Test_Case_Document.md
    docs/Test_Case_Document.xlsx
    docs/manual_validation/<Tester>_Checklist.md

Data comes from scripts/case_catalog.py. Statuses of automated cases are
derived only from recorded JUnit XML evidence (EVIDENCE below):

* a reference ``module::function`` matches every recorded result of that
  test function; ``module::function[param`` narrows to parametrized results
  whose id starts with ``param``; a trailing ``@label`` reads the browser
  evidence file for that label instead of the main run;
* an "auto" case is PASS only when every reference matched at least one
  result and none of the matched results failed or errored; FAIL if any
  matched result failed/errored; NOT RUN if a reference matched nothing.

Before writing anything the script checks that every referenced test
function exists under tests/. Requires openpyxl (requirements-dev.txt).
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import case_catalog as cat  # noqa: E402

DOCS = ROOT / "docs"
MD_PATH = DOCS / "Test_Case_Document.md"
XLSX_PATH = DOCS / "Test_Case_Document.xlsx"
CHECKLIST_DIR = DOCS / "manual_validation"

VERSION = "2.6"
DOC_DATE = "2026-11-17"
STATUSES = ["PASS", "FAIL", "BLOCKED", "NOT RUN", "NOT APPLICABLE"]
TYPES = ["UT", "IT", "SYS"]
METHOD_TEXT = {"A": "Automated (pytest)", "B": "Automated browser (Playwright)", "M": "Manual / human"}
TESTERS = ["Sumukh", "Jagadeesh", "Tharith"]
TESTER_SCOPE = {
    "Sumukh": "Admin dashboard, user management, class and subject management, enrollment, password management, overall integration.",
    "Jagadeesh": "Teacher dashboard, attendance marking, editing and deletion, percentage calculations, attendance filtering, low-attendance alerts, performance, teacher session logout.",
    "Tharith": "Student dashboard, attendance viewing, dashboard summaries, frontend usability, responsive design, browser compatibility, student session logout.",
}

# Evidence of the run whose results this document reports: the regression run
# after the six fixes. The Phase 2/3 final run (2026-11-11) is kept unchanged in
# docs/evidence/final/ and its statuses are shown as history.
EVIDENCE = {
    "main": "docs/evidence/regression/junit.xml",
    "chromium": "docs/evidence/regression/browsers/chromium_junit.xml",
    "firefox": "docs/evidence/regression/browsers/firefox_junit.xml",
    "webkit": "docs/evidence/regression/browsers/webkit_junit.xml",
}
ORIGINAL_EVIDENCE = {
    "main": "docs/evidence/final/junit.xml",
    "chromium": "docs/evidence/final/browsers/chromium_junit.xml",
    "firefox": "docs/evidence/final/browsers/firefox_junit.xml",
    "webkit": "docs/evidence/final/browsers/webkit_junit.xml",
}

# Failures that are environmental (browser not installed / cannot start);
# used only to judge the whole-suite regression case SYS_NFR-06_05.
ENVIRONMENTAL = re.compile(
    r"^tests\.test_nfr05_browser_compatibility::(test_.*\[(edge|firefox)[^\]]*\]|test_report_tested_browser_versions)$"
)


# ----------------------------------------------------------------- evidence
def load_junit(path):
    """Return ({'module::name': outcome}, run date) for one JUnit file."""
    file = ROOT / path
    if not file.exists():
        return None, ""
    root = ET.parse(file).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    results = {}
    for case in suite.findall("testcase"):
        outcome = "passed"
        for tag in ("failure", "error", "skipped"):
            if case.find(tag) is not None:
                outcome = tag
                break
        key = f"{case.get('classname')}::{case.get('name')}"
        # A test with a passing call and a failing teardown appears twice.
        if results.get(key) in ("failure", "error"):
            continue
        results[key] = outcome
    return results, (suite.get("timestamp") or "")[:10]


def split_ref(ref):
    label = "main"
    if "@" in ref:
        ref, label = ref.rsplit("@", 1)
    module, func = ref.split("::", 1)
    param = None
    if "[" in func:
        func, param = func.split("[", 1)
        param = param.rstrip("]")
    return label, module, func, param


def match(results, module, func, param):
    out = []
    for key, outcome in results.items():
        cls, name = key.split("::", 1)
        if cls != f"tests.{module}":
            continue
        base, _, ids = name.partition("[")
        if base != func:
            continue
        if param is not None and not ids.startswith(param):
            continue
        out.append(outcome)
    return out


def evaluate(case, evidence):
    """Return (status, actual, date, evidence_text)."""
    rule = case["exec"]
    used = sorted({split_ref(r)[0] for r in case["refs"] if "::" in r})
    ev_text = case.get("evidence_override") or "; ".join(EVIDENCE[l] for l in used)
    run_date = evidence["main"][1]

    if isinstance(rule, dict):
        status, actual = rule["status"], rule["actual"]
        if actual == "SUITE":
            results = evidence["main"][0] or {}
            bad = [k for k, v in results.items() if v in ("failure", "error")]
            non_env = [k for k in bad if not ENVIRONMENTAL.match(k)]
            passed = sum(1 for v in results.values() if v == "passed")
            if not results:
                return "NOT RUN", "Final run not recorded yet.", "", ""
            status = "PASS" if not non_env else "FAIL"
            actual = (f"Final full run: {passed} passed; {len(bad)} failed/errored, "
                      f"{len(bad) - len(non_env)} of them environmental (Edge/Firefox cannot launch); "
                      f"{len(non_env)} other failures.")
            return status, actual, run_date, EVIDENCE["main"]
        if status in ("NOT RUN",) and not actual:
            return status, "", "", ""
        date = (rule.get("date") or run_date) if status != "NOT RUN" else ""
        return status, actual, date, (ev_text if case["refs"] or case.get("evidence_override") else "")

    pyrefs = [r for r in case["refs"] if "::" in r]
    if not pyrefs:
        return "NOT RUN", "Not yet executed (no automated test linked).", "", ""
    total, missing, bad = 0, [], []
    for ref in pyrefs:
        label, module, func, param = split_ref(ref)
        results = evidence[label][0]
        outcomes = match(results, module, func, param) if results else []
        if not outcomes:
            missing.append(ref)
            continue
        total += len(outcomes)
        if any(o in ("failure", "error") for o in outcomes):
            bad.append(ref)
    if bad:
        return "FAIL", f"{len(bad)} linked test(s) failed: " + ", ".join(bad), run_date, ev_text
    if missing:
        return "NOT RUN", "Linked test(s) not found in the recorded run: " + ", ".join(missing), "", ""
    return ("PASS", f"Expected result verified: {len(pyrefs)} linked test(s), {total} recorded result(s), all passed.",
            run_date, ev_text)


def verify_references():
    problems = []
    for case in cat.CASES:
        for ref in case["refs"]:
            if "::" not in ref:
                continue
            _label, module, func, _param = split_ref(ref)
            path = ROOT / "tests" / f"{module}.py"
            if not path.exists():
                problems.append(f"{case['id']}: missing file {path.name}")
            elif not re.search(rf"^\s*def {re.escape(func)}\(", path.read_text(), re.M):
                problems.append(f"{case['id']}: {ref} not found")
        if case["tester"] and case["tester"] not in TESTERS:
            problems.append(f"{case['id']}: unknown tester {case['tester']}")
    for dup, n in Counter(c["id"] for c in cat.CASES).items():
        if n > 1:
            problems.append(f"duplicate test case id {dup}")
    return problems


# ----------------------------------------------------------------- helpers
def method_label(code):
    return " + ".join(METHOD_TEXT[c] for c in code.split("+"))


def case_method(case):
    """Design method; manual cases also name how they were executed."""
    label = method_label(case["method"])
    return label + "; executed by Playwright automation (manual validation run)" if case.get("manual_run") else label


def manual_counts(cases=None):
    cases = [c for c in (cases or cat.CASES) if c.get("manual_run")]
    counts = Counter(c["status"] for c in cases)
    return ", ".join(f"{counts[s]} {s}" for s in STATUSES if counts[s])


# ----------------------------------------------------------------- test records (traditional format)
AUTOMATED_OWNER = "Project team (automated regression suite)"
LEVEL = {"UT": "Unit", "IT": "Integration", "SYS": "System"}
BROWSER_SHOTS = "docs/evidence/final/browsers/screenshots"


def owner(case):
    """Assigned team member: the manual-validation owner, otherwise the team's automated suite."""
    return case["tester"] or AUTOMATED_OWNER


def exec_method(case):
    executed = case["status"] in ("PASS", "FAIL")
    if case.get("manual_run"):
        if executed:
            return "Manual validation procedure, executed by Playwright browser automation (instructor-approved)"
        return ("Manual validation procedure; attempted with Playwright browser automation (instructor-approved) "
                "but not executable - see actual observed result")
    label = method_label(case["method"])
    return label if executed else f"{label} (planned method; case not fully executed - see actual observed result)"


def test_steps(case):
    steps = cat.MANUAL_STEPS.get(case["id"]) or [x.strip() for x in re.split(r";\s*", case["steps"]) if x.strip()]
    return [x[:1].upper() + x[1:] for x in steps]


def screenshots(case):
    run = case.get("manual_run")
    if run and run["screenshots"]:
        return list(run["screenshots"])
    shots = []
    for label in ("chromium", "webkit"):
        if any(f"@{label}" in r for r in case["refs"]):
            shots += [f"{BROWSER_SHOTS}/{label}_{role}_overview.png" for role in ("admin", "teacher", "student")]
    return shots


def screenshot_text(case, sep="<br>"):
    shots = screenshots(case)
    if shots:
        return sep.join(f"`{x}`" for x in shots)
    if "B" in case["method"] or case.get("manual_run"):
        return "None captured for this case (automated browser assertions; see supporting evidence)"
    return "Not applicable (API / unit-level test)"


def defect_ids(case):
    pat = re.compile(rf"\b{re.escape(case['id'])}\b")
    ids = [d[0] for d in cat.DEFECTS if pat.search(d[4])]
    if case["status"] != "PASS":
        ids += [g[0] for g in cat.GAPS if pat.search(g[6])]
    return ids


def supporting_evidence(case, sep="<br>"):
    parts = []
    run = case.get("manual_run")
    if run:
        parts.append(f"Executed {run['started'].replace('T', ' ')} to {run['finished'][11:]} in {run['browser']}; "
                     f"{run['checks_total'] - run['checks_failed']} of {run['checks_total']} automated checks met")
        parts.append(f"Results: `{cat.MANUAL_RUN_DIR}/results.json`; report: `{cat.MANUAL_REPORT}`")
        parts.append("Browser logs: " + ", ".join(f"`{x}`" for x in run["logs"]))
    elif case["evidence"]:
        parts.append(f"Results: {case['evidence']}")
    refs = [r for r in case["refs"] if "::" in r]
    if refs:
        parts.append("Automated test reference: " + ", ".join(f"`{r}`" for r in refs))
    return sep.join(parts) or "None (not executed)"


_ORIGINAL = None


def original_status(case):
    """Status before the six fixes (frozen in docs/evidence/regression/original_statuses.json)."""
    global _ORIGINAL
    if _ORIGINAL is None:
        path = cat.ORIGINAL_STATUSES_PATH
        _ORIGINAL = json.loads(path.read_text())["cases"] if path.exists() else {}
    return _ORIGINAL.get(case["id"])


def result_history(case):
    orig = original_status(case)
    if not orig:
        return "-"
    when = "2026-11-17 manual validation run" if case.get("manual_run") else "2026-11-11 final run"
    now = "2026-11-17 regression run"
    change = "" if orig["status"] == case["status"] else " (changed)"
    return f"{when}: {orig['status']}; {now}: {case['status']}{change}"


def case_record(case, heading="####", title=None, extras=False):
    """One test case as a traditional test record (heading + field table)."""
    steps = "<br>".join(f"{n}. {esc(x)}" for n, x in enumerate(test_steps(case), 1))
    rows = [
        ("Test Case ID", case["id"]),
        ("Requirement", f"{case['req']} - {cat.MODULES[case['req']]}"),
        ("Test level", LEVEL[case["type"]]),
        ("Test scenario", esc(case["scenario"])),
        ("Assigned team member", owner(case)),
        ("Preconditions", esc(case["pre"])),
        ("Test data", esc(case["data"])),
        ("Test steps", steps),
        ("Expected result", esc(case["expected"])),
        ("Actual observed result", esc(case["actual"] or "Not executed.")),
        ("Status", f"**{case['status']}**"),
        ("Execution method", exec_method(case)),
        ("Execution date", case["date"] or "-"),
        ("Screenshot evidence", screenshot_text(case)),
        ("Supporting evidence", supporting_evidence(case)),
        ("Defect / gap ID", ", ".join(defect_ids(case)) or "None"),
        ("Result history", result_history(case)),
    ]
    if extras:
        rows += [("Change from Test Plan v1.0", esc(case["change"])),
                 ("Review notes", esc(case["review"] or "-")),
                 ("Remarks", esc(case["remarks"] or "-"))]
    out = [f"{heading} {title or case['id']} - {esc(case['scenario'])}", "", "| Field | Details |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in rows]
    return out + [""]


def esc(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def refs_md(refs):
    return "<br>".join(f"`{r}`" for r in refs) if refs else "None"


def groups():
    order = OrderedDict()
    for req in cat.MODULES:
        order[req] = [c for c in cat.CASES if c["req"] == req]
    return order


# ----------------------------------------------------------------- markdown
def build_markdown(grouped, evidence):
    total = len(cat.CASES)
    by_change = Counter(c["change"] for c in cat.CASES)
    by_status = Counter(c["status"] for c in cat.CASES)
    original = by_change[cat.ORIGINAL] + by_change[cat.UPDATED]
    lines = []
    w = lines.append
    w("# Test Case Document (Updated) — Attendance Management System")
    w("")
    w("| Item | Value |")
    w("|---|---|")
    w(f"| Document version | {VERSION}. Version 2.0 (Phase 1) updated the test cases in `Documents/Test_Plan.pdf` (v1.0); version 2.1 (Phase 2) adds execution results; version 2.2 (Phase 3) updates the defect register only (O-01 verified, O-02 quantified, O-04 added); version 2.3 redistributes the 19 manual cases (Sumukh 5, Jagadeesh 7, Tharith 7) with no status changes; "
      f"version 2.4 records the execution of the 19 manual cases by Playwright automation, approved by the instructor as manual "
      f"validation evidence ({manual_counts()}), and adds defects MV-01 to MV-03; version 2.5 presents every test case as a "
      f"traditional test record (assigned team member, preconditions, steps, expected and actual result, status, screenshot "
      f"evidence, defect ID) and corrects three outdated status notes in the gap register; no test result changed; "
      f"version 2.6 reports the regression run after the six failed cases were fixed (SYS_FR-04_11, SYS_FR-05_10, "
      f"SYS_FR-06_08, SYS_FR-10_10, SYS_FR-12_10, SYS_NFR-05_04); every record shows its original and regression result |")
    w(f"| Prepared on | {DOC_DATE} |")
    w("| Requirements source | `Documents/SRS.pdf` (FR-01 to FR-15, NFR-01 to NFR-06) |")
    w("| Template | Course template \"Test Plan Document\" (Test Case ID, Module, Description, Pre-conditions, Steps, Test Data, Expected, Actual, Result) |")
    w("| Generated from | `scripts/case_catalog.py` by `scripts/build_test_case_document.py` (same data as `docs/Test_Case_Document.xlsx` and the manual checklists) |")
    w("| Execution evidence | " + "; ".join(f"`{p}` ({l}, run date {evidence[l][1] or 'not recorded'})" for l, p in EVIDENCE.items()) + " |")
    w("")
    w("## 1. Why this document was updated")
    w("")
    w("The original Test Plan (version 1.0) was written before development. It had 75 test cases covering only "
      "FR-01 to FR-06 and NFR-01 to NFR-03, and every result was `Pending`. During the sprints all 21 requirements "
      "were implemented (GitHub issues #1–#21 closed; PRs #22–#48 merged).")
    w("")
    w("- **Phase 1:** kept all 75 original IDs, updated expected results to the implemented behaviour, added test cases for "
      "FR-07 to FR-15 and NFR-04 to NFR-06, and linked each case to automated tests.")
    w("- **Phase 2:** read every linked test. Where a test did not prove the expected result, the link or the expected result was corrected "
      "(column *Phase 2 review*). Missing tests were added. The full suite and the browser suites were run, and statuses were derived from that evidence.")
    w("")
    w("## 2. Conventions")
    w("")
    w("- **Test Case ID** — `<TYPE>_<REQ>_<NN>`. `UT` = unit, `IT` = integration, `SYS` = system.")
    w("- **Method** — " + "; ".join(f"`{k}` = {v}" for k, v in METHOD_TEXT.items()) + ".")
    w("- **Change** — `Original (unchanged)`, `Original (updated)` or `New`.")
    w("- **Status:**")
    w("  - `PASS`: expected result verified by recorded evidence.")
    w("  - `FAIL`: actual result differs from the expected result.")
    w("  - `BLOCKED`: execution prevented by a documented environment or dependency issue.")
    w("  - `NOT RUN`: not executed, or only partly verified (the actual result says which part).")
    w("  - `NOT APPLICABLE`: outside the SRS, with the reason given.")
    w("- **How automated statuses are derived** — by `scripts/build_test_case_document.py` from the JUnit XML evidence. A case is PASS only if every linked test ran and passed. "
      "A case whose expected result needs something the tests do not prove is set to NOT RUN, and the actual result states what was and was not verified.")
    w("- **Browser references** — `[chrome]` = Google Chrome result in the main run; `@chromium` / `@webkit` / `@firefox` = separate browser runs.")
    w("- **Manual cases** — The 19 cases in `docs/manual_validation/` were executed on "
      f"{cat.MANUAL_META['run_date']} by Playwright automation ({cat.MANUAL_META['browser']}) against an isolated "
      "`validation_demo.db`, following the checklist steps. The instructor approved automated browser execution as evidence for "
      "manual validation. The steps were executed by the automation, not by a person; the named team member is the assigned "
      f"owner. Statuses come from `{cat.MANUAL_RUN_DIR}/results.json`; browser, timestamps and logs are recorded in each "
      f"record's *Supporting evidence* field and in `{cat.MANUAL_REPORT}`.")
    w(f"- **Assigned team member** - the owner of each manual validation case (Sumukh 5, Jagadeesh 7, Tharith 7); automated "
      f"cases belong to the team's automated regression suite (`{AUTOMATED_OWNER}`).")
    w("- **Screenshot evidence** - screenshots recorded for the case; API and unit-level tests have none by nature.")
    w("- **Defect / gap ID** - defects whose test impact names the case, and gaps affecting a case that did not pass.")
    w("- **Result history** - the result before the six fixes (automated cases: final run 2026-11-11, `docs/evidence/final/`; "
      "manual validation cases: run of 2026-11-17, `docs/evidence/manual_validation_automation/`) and the result of the "
      "regression run after the fixes (2026-11-17, `docs/evidence/regression/`), which is the status reported in this version.")
    w("")
    w("## 3. Summary")
    w("")
    w(f"Total test cases: **{total}** — original {original} ({by_change[cat.ORIGINAL]} unchanged, {by_change[cat.UPDATED]} updated) + {by_change[cat.NEW]} new.")
    w("")
    w("**Status:** " + ", ".join(f"{s} {by_status.get(s, 0)}" for s in STATUSES) + ".")
    w("")
    hdr = ["UT", "IT", "SYS", "Total"] + STATUSES
    w("| Requirement | Module | " + " | ".join(hdr) + " |")
    w("|---|---|" + "---|" * len(hdr))
    totals = Counter()
    for req, cases in grouped.items():
        t = Counter(c["type"] for c in cases)
        s = Counter(c["status"] for c in cases)
        row = [t["UT"], t["IT"], t["SYS"], len(cases)] + [s[x] for x in STATUSES]
        for k, v in zip(hdr, row):
            totals[k] += v
        w(f"| {req} | {cat.MODULES[req]} | " + " | ".join(str(v) for v in row) + " |")
    w("| **Total** | | " + " | ".join(f"**{totals[k]}**" for k in hdr) + " |")
    w("")
    w("Manual cases assigned: " + ", ".join(f"{t} {sum(1 for c in cat.CASES if c['tester'] == t)}" for t in TESTERS)
      + f" (see `docs/manual_validation/`). Manual validation results: {manual_counts()}.")
    w("")
    w("## 4. Cases that did not pass")
    w("")
    w("| Test Case ID | Status | Actual observed result | Assigned team member | Defect / gap ID |")
    w("|---|---|---|---|---|")
    for c in cat.CASES:
        if c["status"] != "PASS":
            w(f"| {c['id']} | {c['status']} | {esc(c['actual'] or 'Not executed.')} | {owner(c)} | {', '.join(defect_ids(c)) or '-'} |")
    w("")
    w("## 5. Known gaps (checked against the SRS)")
    w("")
    w("| Gap | Req | Description | Required by SRS? | Classification | Impact on testing | Affected cases |")
    w("|---|---|---|---|---|---|---|")
    for g in cat.GAPS:
        w("| " + " | ".join(esc(x) for x in g) + " |")
    w("")
    w("## 6. Defects and observations")
    w("")
    w("| ID | Req | Severity | Description | Test impact | Status |")
    w("|---|---|---|---|---|---|")
    for d in cat.DEFECTS:
        w("| " + " | ".join(esc(x) for x in d) + " |")
    w("")
    w("## 7. Skipped placeholder tests (kept on purpose)")
    w("")
    w("`tests/test_sprint1_requirements.py` contains 7 tests that are permanently skipped. They were a Sprint 1 checklist "
      "written before the features existed and contain no assertions (`raise NotImplementedError`). They are kept unchanged as agreed "
      "and appear as **skipped**, never as passed. The requirements they named are tested by:")
    w("")
    w("| Skipped placeholder | Requirement(s) | Replacement tests |")
    w("|---|---|---|")
    for p in cat.PLACEHOLDERS:
        w("| `" + p[0] + "` | " + " | ".join(esc(x) for x in p[1:]) + " |")
    w("")
    w("## 8. Changes to original test cases")
    w("")
    w("| Test Case ID | Phase 1 reason | Phase 2 review |")
    w("|---|---|---|")
    for c in cat.CASES:
        if c["change"] == cat.UPDATED:
            w(f"| {c['id']} | {esc(c['remarks'])} | {esc(c['review'])} |")
    w("")
    w("## 9. Test case records")
    w("")
    w("Each test case is recorded in the same format: identification, assigned team member, preconditions, steps, "
      "expected and actual observed result, status, execution method and date, screenshot and supporting evidence, "
      "and the related defect or gap. Records are grouped by requirement.")
    w("")
    for req, cases in grouped.items():
        w(f"### {req} - {cat.MODULES[req]}")
        w("")
        w(f"> SRS: {cat.SRS_TEXT[req]}")
        w("")
        w("| Test Case ID | Test scenario | Assigned team member | Status | Defect / gap ID |")
        w("|---|---|---|---|---|")
        for c in cases:
            w(f"| {c['id']} | {esc(c['scenario'])} | {owner(c)} | {c['status']} | {', '.join(defect_ids(c)) or '-'} |")
        w("")
        for c in cases:
            lines.extend(case_record(c, "####", extras=True))
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------- checklists
SETUP = """## Test environment and procedure

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
"""


def build_checklist(tester):
    cases = [c for c in cat.CASES if c["tester"] == tester]
    meta = cat.MANUAL_META
    counts = Counter(c["status"] for c in cases)
    summary = ", ".join(f"{counts[s]} {s}" for s in STATUSES if counts[s])
    lines = [f"# Manual Validation Checklist - {tester}", "",
             "| Item | Details |", "|---|---|",
             f"| Assigned team member | {tester} |",
             f"| Scope | {TESTER_SCOPE[tester]} |",
             f"| Test cases | {len(cases)} ({summary}) |",
             f"| Execution date | {meta['run_date']} |",
             f"| Browser | {meta['browser']} |",
             "| Execution method | Manual validation procedure executed by Playwright browser automation (instructor-approved) |",
             "| Source | Generated from `scripts/case_catalog.py` and the recorded results; the same records appear in "
             "`docs/Test_Case_Document.md` / `.xlsx` |",
             "", SETUP, "## Summary of results", "",
             "| # | Test Case ID | Requirement | Test scenario | Status | Defect / gap ID |", "|---|---|---|---|---|---|"]
    for i, c in enumerate(cases, 1):
        lines.append(f"| {i} | {c['id']} | {c['req']} | {esc(c['scenario'])} | {c['status']} | {', '.join(defect_ids(c)) or '-'} |")
    lines += ["", "## Test case records", ""]
    for i, c in enumerate(cases, 1):
        lines += case_record(c, "###", title=f"{i}. {c['id']}")
        limit = cat.MANUAL_LIMITS.get(c["id"])
        if limit:
            lines += [f"*Not assessed by the automated execution:* {esc(limit)}", ""]
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------- xlsx
def build_xlsx(grouped, evidence):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    font = Font(name="Arial", size=10)
    bold = Font(name="Arial", size=10, bold=True)
    head = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    title = Font(name="Arial", size=14, bold=True)
    head_fill = PatternFill("solid", fgColor="1F3864")
    input_fill = PatternFill("solid", fgColor="FFF2CC")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    wb = Workbook()
    ws = wb.active
    ws.title = "Cover"
    rows = [
        ("Test Case Document (Updated) — Attendance Management System", None),
        (None, None),
        ("Document version", f"{VERSION} (2.0 = Phase 1 updation of Documents/Test_Plan.pdf v1.0; 2.1 = Phase 2 execution results; 2.2 = Phase 3 defect register update; 2.3 = manual cases redistributed 5/7/7, no status changes; 2.4 = 19 manual cases executed by Playwright automation (instructor-approved), defects MV-01 to MV-03 added)"),
        ("Prepared on", DOC_DATE),
        ("Requirements source", "Documents/SRS.pdf"),
        ("Generated from", "scripts/case_catalog.py via scripts/build_test_case_document.py"),
        ("Execution evidence", "; ".join(f"{p} ({l}, {evidence[l][1] or 'not recorded'})" for l, p in EVIDENCE.items())),
        (None, None),
        ("Manual validation", f"The 19 manual cases (yellow columns) were executed by Playwright automation on {cat.MANUAL_META['run_date']} "
                              f"({cat.MANUAL_META['browser']}); instructor-approved as manual validation evidence. No person performed the steps; "
                              f"the Test Owner is the responsible team member. Results: {manual_counts()}. Details: {cat.MANUAL_REPORT}."),
        ("Status values", "PASS, FAIL, BLOCKED, NOT RUN, NOT APPLICABLE (drop-down). Never mark PASS without evidence."),
        ("Method codes", "; ".join(f"{k} = {v}" for k, v in METHOD_TEXT.items())),
        ("Execution method", cat.MANUAL_EXEC_METHOD),
    ]
    for r, (a, b) in enumerate(rows, start=1):
        ws.cell(r, 1, a).font = title if r == 1 else bold
        if b is not None:
            c = ws.cell(r, 2, b)
            c.font, c.alignment = font, wrap
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 110

    ws = wb.create_sheet("Test Cases")
    cols = [("Test Case ID", 15), ("Requirement ID", 11), ("Name of Module", 20), ("Test Level", 11),
            ("Test Scenario", 28), ("Assigned Team Member", 18), ("Pre-conditions", 26), ("Test Steps", 40),
            ("Test Data", 22), ("Expected Result", 40), ("Actual Observed Result", 45), ("Status", 13),
            ("Execution Method", 24), ("Execution Date", 13), ("Screenshot Evidence", 40), ("Supporting Evidence", 45),
            ("Defect / Gap ID", 13), ("Automated Test Reference", 45), ("Change vs v1.0", 18),
            ("Phase 2 Review", 40), ("Remarks", 40)]
    for i, (name, width) in enumerate(cols, start=1):
        c = ws.cell(1, i, name)
        c.font, c.fill, c.alignment, c.border = head, head_fill, wrap, border
        ws.column_dimensions[get_column_letter(i)].width = width
    plain = lambda text: text.replace("`", "").replace("**", "")  # noqa: E731
    r = 2
    for cases in grouped.values():
        for case in cases:
            vals = [case["id"], case["req"], case["module"], LEVEL[case["type"]], case["scenario"], owner(case),
                    case["pre"], "\n".join(f"{n}. {x}" for n, x in enumerate(test_steps(case), 1)), case["data"],
                    case["expected"], case["actual"] or "Not executed.", case["status"], exec_method(case),
                    case["date"] or "-", plain(screenshot_text(case, "\n")), plain(supporting_evidence(case, "\n")),
                    ", ".join(defect_ids(case)) or "None", "\n".join(case["refs"]) or "None",
                    case["change"], case["review"], case["remarks"]]
            for i, v in enumerate(vals, start=1):
                c = ws.cell(r, i, v)
                c.font, c.alignment, c.border = font, wrap, border
                if case["tester"] and i in (11, 12, 14, 15):
                    c.fill = input_fill
            r += 1
    last = r - 1
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{last}"
    dv = DataValidation(type="list", formula1='"PASS,FAIL,BLOCKED,NOT RUN,NOT APPLICABLE"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"L2:L{last}")

    ws = wb.create_sheet("Summary")
    hdr = ["Requirement", "Module", "UT", "IT", "SYS", "Total"] + STATUSES
    for i, name in enumerate(hdr, start=1):
        c = ws.cell(1, i, name)
        c.font, c.fill, c.border, c.alignment = head, head_fill, border, wrap
    rng_req = f"'Test Cases'!$B$2:$B${last}"
    rng_id = f"'Test Cases'!$A$2:$A${last}"
    rng_status = f"'Test Cases'!$L$2:$L${last}"
    row = 2
    for req in grouped:
        ws.cell(row, 1, req)
        ws.cell(row, 2, cat.MODULES[req])
        for j, t in enumerate(TYPES, start=3):
            ws.cell(row, j, f'=COUNTIFS({rng_req},$A{row},{rng_id},"{t}_*")')
        ws.cell(row, 6, f"=COUNTIF({rng_req},$A{row})")
        for j, s in enumerate(STATUSES, start=7):
            ws.cell(row, j, f'=COUNTIFS({rng_req},$A{row},{rng_status},"{s}")')
        row += 1
    ws.cell(row, 1, "Total")
    for j in range(3, len(hdr) + 1):
        col = get_column_letter(j)
        ws.cell(row, j, f"=SUM({col}2:{col}{row - 1})")
    for rr in ws.iter_rows(min_row=2, max_row=row):
        for c in rr:
            c.border = border
            c.font = bold if c.row == row else font
    ws.column_dimensions["A"].width = 13
    ws.column_dimensions["B"].width = 34
    ws.cell(row + 2, 1, "Counts are formulas over the 'Test Cases' sheet and update when statuses change.").font = font

    def table(name, headers, data, widths):
        s = wb.create_sheet(name)
        for i, h in enumerate(headers, start=1):
            c = s.cell(1, i, h)
            c.font, c.fill, c.border, c.alignment = head, head_fill, border, wrap
            s.column_dimensions[get_column_letter(i)].width = widths[i - 1]
        for rr, rowvals in enumerate(data, start=2):
            for i, v in enumerate(rowvals, start=1):
                c = s.cell(rr, i, v)
                c.font, c.border, c.alignment = font, border, wrap
        s.freeze_panes = "A2"

    table("Gaps", ["Gap", "Requirement", "Description", "Required by SRS?", "Classification", "Impact on testing", "Affected cases"],
          cat.GAPS, [7, 11, 50, 45, 28, 35, 40])
    table("Defects", ["ID", "Requirement", "Severity", "Description", "Test impact", "Status"], cat.DEFECTS, [7, 11, 11, 80, 20, 40])
    table("Change Log", ["Test Case ID", "Change", "Phase 1 reason", "Phase 2 review"],
          [(c["id"], c["change"], c["remarks"], c["review"]) for c in cat.CASES if c["change"] != cat.ORIGINAL],
          [16, 20, 60, 60])
    table("Skipped Placeholders", ["Placeholder test (tests/test_sprint1_requirements.py)", "Requirement(s)", "Replacement tests"],
          cat.PLACEHOLDERS, [40, 18, 100])

    wb.calculation.fullCalcOnLoad = True
    wb.save(XLSX_PATH)


def main():
    if cat.MANUAL_META is None:
        print(f"Missing {cat.MANUAL_RESULTS_PATH}; run scripts/run_manual_validation_automation.py first.")
        return 1
    problems = verify_references()
    if problems:
        print("Reference check failed:")
        for p in problems:
            print("  -", p)
        return 1
    evidence = {label: load_junit(path) for label, path in EVIDENCE.items()}
    for case in cat.CASES:
        case["status"], case["actual"], case["date"], case["evidence"] = evaluate(case, evidence)
    grouped = groups()
    DOCS.mkdir(exist_ok=True)
    MD_PATH.write_text(build_markdown(grouped, evidence), encoding="utf-8")
    build_xlsx(grouped, evidence)
    CHECKLIST_DIR.mkdir(exist_ok=True)
    for tester in TESTERS:
        (CHECKLIST_DIR / f"{tester}_Checklist.md").write_text(build_checklist(tester), encoding="utf-8")
    counts = Counter(c["status"] for c in cat.CASES)
    print(f"{len(cat.CASES)} test cases; references verified. Status: " + ", ".join(f"{s} {counts.get(s, 0)}" for s in STATUSES))
    print("Manual: " + ", ".join(f"{t} {sum(1 for c in cat.CASES if c['tester'] == t)}" for t in TESTERS)
          + "; results: " + manual_counts())
    return 0


if __name__ == "__main__":
    sys.exit(main())
