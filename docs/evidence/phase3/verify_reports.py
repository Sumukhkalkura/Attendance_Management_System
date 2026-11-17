"""Independent cross-check of the Phase 3 reports against the raw evidence.

Does not import the report generator. Reads the raw tool outputs (coverage
CLI text reports, pytest console summary lines, JUnit XML, the Test Case
Document Markdown and Excel files) and checks that every headline figure
in docs/*_Report.md matches them.

Run: .venv/bin/python docs/evidence/phase3/verify_reports.py
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EV = ROOT / "docs/evidence"
DOCS = ROOT / "docs"
results = []


def check(label, ok, detail=""):
    results.append((ok, label, detail))


def read(p):
    return (ROOT / p).read_text()


def pytest_line(p):
    line = [l for l in read(p).splitlines() if re.search(r"\d+ passed", l)][-1]
    return {k.rstrip("s"): int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|warnings|errors)", line)}


def coverage_total(p):
    """TOTAL row of a `coverage report` text file -> dict."""
    text = read(p)
    header = [l for l in text.splitlines() if l.startswith("Name")][0].split()
    total = [l for l in text.splitlines() if l.startswith("TOTAL")][0].split()
    return dict(zip(header, total))


def coverage_rows(p):
    rows = {}
    lines = read(p).splitlines()
    header = [l for l in lines if l.startswith("Name")][0].split()
    for l in lines:
        if l.startswith(("app/", "scripts/")):
            parts = l.split()
            rows[parts[0]] = dict(zip(header, parts[: len(header)]))
    return rows


uts = read("docs/Unit_Test_Report.md")
svr = read("docs/System_Validation_Report.md")
ccr = read("docs/Code_Coverage_Report.md")
bcr = read("docs/Branch_Coverage_Report.md")

# ---- 1. pytest results (console summary lines) vs Unit Test Report table
for run, p in (("Baseline", "docs/evidence/baseline/pytest_output.txt"), ("Final", "docs/evidence/final/pytest_output.txt")):
    s = pytest_line(p)
    row = [l for l in uts.splitlines() if l.startswith(f"| {run} (")][0]
    cells = [c.strip() for c in row.strip("|").split("|")]
    total = s["passed"] + s.get("failed", 0) + s.get("error", 0) + s.get("skipped", 0)
    expected = [str(total), str(s["passed"]), str(s.get("failed", 0)), str(s.get("error", 0)),
                str(s.get("skipped", 0)), str(s.get("warning", 0))]
    check(f"Unit Test Report {run} row = pytest console summary", cells[2:8] == expected, f"{cells[2:8]} vs {expected}")

# ---- 2. JUnit totals
for run in ("baseline", "final"):
    suite = ET.parse(EV / run / "junit.xml").getroot().find("testsuite")
    s = pytest_line(f"docs/evidence/{run}/pytest_output.txt")
    check(f"{run} JUnit tests attr = console total", int(suite.get("tests")) ==
          s["passed"] + s.get("failed", 0) + s.get("error", 0) + s.get("skipped", 0))

# ---- 3. Unit-level count: the level table must add up to the JUnit total
lv = re.findall(r"^\| (Unit|Integration|Browser|Static)? *\| Final \| (\d+) \| (\d+) \|", uts, re.M)
check("Unit Test Report level rows (final) sum to 856", sum(int(x[1]) for x in lv) == 856, str(lv))
lines = uts.splitlines()
i = next(n for n, l in enumerate(lines) if l.startswith("| Unit | Baseline |"))
unit_final = [c.strip() for c in lines[i + 1].strip("|").split("|")]
check("Unit-level results reported as 12 (not 836)", unit_final[1] == "Final" and unit_final[2] == "12"
      and "**Unit tests in the final run: 12 results, 12 passed.**" in uts, str(unit_final))
inv = read("docs/evidence/final/test_type_inventory.md")
check("Level table matches saved test_type_inventory.md",
      "| unit | 12 | 12 |" in inv and "| integration | 665 | 658 |" in inv and "| browser | 25 | 12 |" in inv and "| static | 154 | 154 |" in inv)

# ---- 4. Coverage: CLI text report vs JSON-derived report figures
st = coverage_total("docs/evidence/coverage/statement/coverage_report_app.txt")
stmt_pct = 100 * (int(st["Stmts"]) - int(st["Miss"])) / int(st["Stmts"])
check("Statement CLI TOTAL Cover = computed statement %", st["Cover"] == f"{stmt_pct:.2f}%", f"{st['Cover']} vs {stmt_pct:.2f}%")
check("Code Coverage Report headline matches CLI", f"| {st['Stmts']} | {int(st['Stmts']) - int(st['Miss'])} | {st['Miss']} | 0 | **{st['Cover']}** |" in ccr)
br = coverage_total("docs/evidence/coverage/branch/coverage_report_app.txt")
check("Branch run statements identical to statement run", (br["Stmts"], br["Miss"]) == (st["Stmts"], st["Miss"]))
covered_br = None
cx = ET.parse(EV / "coverage/branch/coverage.xml").getroot()
# Cobertura XML includes both scopes; take the app package total from the JSON-independent XML attributes per file
app_valid = app_cov = 0
for cls in cx.iter("class"):
    if cls.get("filename") not in ("backup_db.py", "schedule_daily_backup.py"):  # paths are relative to <source>
        for line in cls.iter("line"):
            if line.get("branch") == "true":
                m = re.match(r"\d+% \((\d+)/(\d+)\)", line.get("condition-coverage", ""))
                if m:
                    app_cov += int(m.group(1))
                    app_valid += int(m.group(2))
check("Cobertura XML app/ branch count = CLI Branch column", app_valid == int(br["Branch"]), f"{app_valid} vs {br['Branch']}")
branch_pct = 100 * app_cov / app_valid
check("Branch Coverage Report headline = XML-derived branch %", f"**Branch coverage of `app/`: {app_cov} of {app_valid} branch outcomes = {branch_pct:.2f}%.**" in bcr,
      f"{app_cov}/{app_valid} = {branch_pct:.2f}%")
check("Branch report quotes the CLI combined figure correctly", f"= {br['Cover']}" in bcr, br["Cover"])
check("Branch report partial-line total = CLI BrPart", f"| {br['Branch']} | {app_cov} | {app_valid - app_cov} | {br['BrPart']} |" in bcr)
# per-module statement rows
for name, row in coverage_rows("docs/evidence/coverage/statement/coverage_report_app.txt").items():
    executed = int(row["Stmts"]) - int(row["Miss"])
    ok = f"| `{name}` | {row['Stmts']} | {executed} | {row['Miss']} | 0 | {row['Cover']} |" in ccr
    check(f"Statement row {name}", ok)
for name, row in coverage_rows("docs/evidence/coverage/branch/coverage_report_app.txt").items():
    ok = re.search(rf"\| `{re.escape(name)}` \| {row['Branch']} \| \d+ \| \d+ \| {row['BrPart']} \|", bcr) is not None
    check(f"Branch row {name}", ok)
sc = coverage_total("docs/evidence/coverage/statement/coverage_report_scripts.txt")
check("Scripts statement total matches CLI", f"| {sc['Stmts']} | {int(sc['Stmts']) - int(sc['Miss'])} | {sc['Miss']} | 0 | {sc['Cover']} |" in ccr)

# ---- 5. Coverage runs had the same test outcomes
for run in ("statement", "branch"):
    s = pytest_line(f"docs/evidence/coverage/{run}/pytest_output.txt")
    f = pytest_line("docs/evidence/final/pytest_output.txt")
    check(f"Coverage {run} run pass/fail/error/skip = final run",
          all(s.get(k, 0) == f.get(k, 0) for k in ("passed", "failed", "error", "skipped")))

# ---- 6. Test Case Document (MD + XLSX) vs System Validation Report
md = read("docs/Test_Case_Document.md")
md_status = Counter(re.findall(r"^\| (?:UT|IT|SYS)_[A-Z]+-\d\d_\d\d \|.*?\| (PASS|FAIL|BLOCKED|NOT RUN|NOT APPLICABLE) \|", md, re.M))
ids = re.findall(r"^\| ((?:UT|IT|SYS)_[A-Z]+-\d\d_\d\d) \|", md, re.M)
check("Test Case Document lists 197 unique case IDs", len(set(ids)) == 197, str(len(set(ids))))
try:
    import openpyxl

    ws = openpyxl.load_workbook(ROOT / "docs/Test_Case_Document.xlsx", read_only=True)["Test Cases"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = list(rows[0])
    xs = Counter(r[hdr.index("Test Result (Status)")] for r in rows[1:] if r[0])
    xids = {r[0] for r in rows[1:] if r[0]}
    check("XLSX has the same 197 IDs as the Markdown", xids == set(ids))
except Exception as exc:  # noqa: BLE001
    xs = None
    check("XLSX readable", False, repr(exc))
row = [l for l in svr.splitlines() if l.startswith("| **All** |")][0]
cells = [c.strip() for c in row.strip("|").split("|")]
svr_counts = dict(zip(["PASS", "FAIL", "BLOCKED", "NOT RUN", "NOT APPLICABLE"], map(int, cells[2:7])))
check("SVR status totals = XLSX Status column", xs is not None and all(xs[k] == v for k, v in svr_counts.items()), f"{svr_counts} vs {xs}")
check("SVR total cases = 197", cells[1] == "197")

# 75 original Test Plan IDs (extracted text of Documents/Test_Plan.pdf is not available here;
# compare against the Change column of the XLSX instead)
if xs is not None:
    ch = Counter(r[hdr.index("Change vs v1.0")] for r in rows[1:] if r[0])
    original = sum(v for k, v in ch.items() if k and k.startswith("Original"))
    check("75 original Test Plan IDs kept (XLSX Change column)", original == 75, str(ch))

# ---- 7. Manual cases still NOT RUN with no execution date
if xs is not None:
    tcol, scol, dcol = hdr.index("Tester"), hdr.index("Test Result (Status)"), hdr.index("Execution Date")
    manual = [r for r in rows[1:] if r[0] and tcol is not None and r[tcol]]
    check("19 manual cases, all NOT RUN", len(manual) == 19 and all(r[scol] == "NOT RUN" for r in manual), f"{len(manual)}")
    if dcol is not None:
        check("Manual cases have no execution date", all(not r[dcol] for r in manual))

# ---- report
fails = [r for r in results if not r[0]]
for ok, label, detail in results:
    print(("PASS " if ok else "FAIL ") + label + (f"  [{detail}]" if detail and not ok else ""))
print(f"\n{len(results) - len(fails)} of {len(results)} checks passed.")
sys.exit(1 if fails else 0)
