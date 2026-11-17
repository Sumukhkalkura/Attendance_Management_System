"""Cross-check the generated Deliverable 3 documents against each other.

Parses the written files (not the generators' internal data) and fails if any
status, count, owner or defect disagrees between:

    docs/evidence/manual_validation_automation/results.json
    docs/manual_validation/{Sumukh,Jagadeesh,Tharith}_Checklist.md
    docs/Test_Case_Document.md and docs/Test_Case_Document.xlsx
    docs/System_Validation_Report.md, docs/Unit_Test_Report.md
    docs/Manual_Validation_Automation_Report.md

Usage:
    python scripts/check_report_consistency.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STATUSES = ["PASS", "FAIL", "BLOCKED", "NOT RUN", "NOT APPLICABLE"]
OWNERS = {"Sumukh": 5, "Jagadeesh": 7, "Tharith": 7}
EXPECTED_MANUAL = None   # read from the current results file (see main)
MV = {"MV-01": "SYS_FR-10_10", "MV-02": "SYS_FR-04_11", "MV-03": "SYS_FR-05_10",
      "D-01": "SYS_NFR-05_04", "D-02": "SYS_FR-06_08", "D-03": "SYS_FR-12_10"}
ID_RE = r"(?:UT|IT|SYS)_N?FR-\d+_\d+"

problems, passed = [], []


def check(name, ok, detail=""):
    (passed if ok else problems).append(name + (f" -> {detail}" if detail and not ok else ""))


def rows_with_id(text):
    """Yield (id, cells) for every markdown table row whose first cell is a case ID."""
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            for i, c in enumerate(cells[:2]):
                if re.fullmatch(ID_RE, c):
                    yield c, cells
                    break


def status_in(cells):
    found = [c.strip("* ") for c in cells if c.strip("* ") in STATUSES]
    return found[0] if found else None


REQUIRED_FIELDS = {"Test Case ID", "Requirement", "Test level", "Test scenario", "Assigned team member", "Preconditions",
                   "Test data", "Test steps", "Expected result", "Actual observed result", "Status", "Execution method",
                   "Execution date", "Screenshot evidence", "Supporting evidence", "Defect / gap ID"}
COMPARE_FIELDS = ["Status", "Assigned team member", "Actual observed result", "Defect / gap ID", "Screenshot evidence",
                  "Supporting evidence", "Test steps", "Expected result"]
AUTOMATED_OWNER = "Project team (automated regression suite)"
ANNOT = re.compile(r"\b((?:UT|IT|SYS)_N?FR-\d+_\d+)\**\s*(?:\(|:|=)\s*\**(PASS|FAIL|BLOCKED|NOT RUN|NOT APPLICABLE)\b")


def parse_records(text):
    """Return {case id: {field: value}} for every '### [n. ]ID - scenario' heading followed by a field table."""
    recs = {}
    for m in re.finditer(r"^#{3,4} (?:\d+\. )?((?:UT|IT|SYS)_N?FR-\d+_\d+) - .*?\n\n\| Field \| Details \|\n\|---\|---\|\n((?:\|.*\|\n)+)",
                         text, re.M):
        fields = {}
        for line in m.group(2).splitlines():
            k, _, v = line.strip("|").partition(" | ")
            fields[k.strip()] = v.strip().strip("*").strip() if k.strip() == "Status" else v.strip()
        recs[m.group(1)] = fields
    return recs


def main():
    # ---- results.json
    sys.path.insert(0, str(ROOT / "scripts"))
    import case_catalog as cat  # noqa: WPS433
    global EXPECTED_MANUAL
    res = json.loads(cat.MANUAL_RESULTS_PATH.read_text())
    EXPECTED_MANUAL = dict(Counter(r["status"] for r in res["results"]))
    check("validation results come from the regression run", cat.IS_REGRESSION_RUN, cat.MANUAL_RUN_DIR)
    results = {r["id"]: r for r in res["results"]}
    check("results.json has 19 unique cases", len(res["results"]) == len(results) == 19)
    check("regression validation run has no failed case", "FAIL" not in EXPECTED_MANUAL, str(EXPECTED_MANUAL))
    check("results.json owners are 5/7/7", Counter(r["tester"] for r in results.values()) == OWNERS)
    check("attendance.db unchanged during the run", res["meta"]["attendance_db_unchanged"] is True)
    for r in results.values():
        for p in r["screenshots"] + r["logs"]:
            if not (ROOT / p).exists():
                check(f"evidence file exists: {p}", False)
    check("every referenced screenshot and log exists",
          all((ROOT / p).exists() for r in results.values() for p in r["screenshots"] + r["logs"]))

    # ---- checklists (traditional test records)
    seen = {}
    for owner, n in OWNERS.items():
        text = (DOCS / f"manual_validation/{owner}_Checklist.md").read_text()
        summary = text.split("## Summary of results", 1)[1].split("\n## ", 1)[0]
        rows = {cid: status_in(cells) for cid, cells in rows_with_id(summary)}
        recs = parse_records(text)
        check(f"{owner} checklist lists {n} cases", len(rows) == n == len(recs), f"{len(rows)} summary rows, {len(recs)} records")
        for cid, st in rows.items():
            rec = recs.get(cid, {})
            check(f"{owner} checklist {cid} summary status = results.json", st == results[cid]["status"], f"{st} vs {results[cid]['status']}")
            check(f"{owner} checklist {cid} record status", rec.get("Status") == st, rec.get("Status"))
            check(f"{owner} checklist {cid} assigned team member", rec.get("Assigned team member") == owner == results[cid]["tester"])
            check(f"{owner} checklist {cid} has every record field", not (REQUIRED_FIELDS - set(rec)), str(REQUIRED_FIELDS - set(rec)))
            check(f"{owner} checklist {cid} execution method names Playwright", "Playwright" in rec.get("Execution method", ""))
            seen[cid] = owner
        check(f"{owner} checklist states the execution method in its header", "executed by Playwright browser automation" in text)
    check("checklists cover the 19 cases exactly once", set(seen) == set(results) and len(seen) == 19)

    # ---- Test Case Document (md)
    tcd = (DOCS / "Test_Case_Document.md").read_text()
    m = re.search(r"\*\*Status:\*\* (.+?)\.\n", tcd)
    tcd_counts = {s: int(n) for s, n in re.findall(r"(PASS|FAIL|BLOCKED|NOT RUN|NOT APPLICABLE) (\d+)", m.group(1))}
    tcd_recs = parse_records(tcd.split("## 9. Test case records", 1)[1])
    md_status = {cid: r.get("Status") for cid, r in tcd_recs.items()}
    check("TCD md has 197 test case records", len(tcd_recs) == 197, str(len(tcd_recs)))
    missing_fields = {cid: REQUIRED_FIELDS - set(r) for cid, r in tcd_recs.items() if REQUIRED_FIELDS - set(r)}
    check("every TCD record has every required field", not missing_fields, str(list(missing_fields.items())[:3]))
    check("TCD md headline counts = records", all(Counter(md_status.values())[s] == tcd_counts.get(s, 0) for s in STATUSES), f"{tcd_counts}")
    total_row = re.search(r"\| \*\*Total\*\* \| \|(.+)\|", tcd).group(1)
    totals = [int(x.strip("* ")) for x in total_row.split("|") if x.strip()]
    check("TCD md summary table total row = headline", totals[4:] == [tcd_counts.get(s, 0) for s in STATUSES], str(totals))
    for cid, r in results.items():
        check(f"TCD md {cid} status = results.json", md_status.get(cid) == r["status"])
        check(f"TCD md {cid} owner = results.json", tcd_recs[cid].get("Assigned team member") == r["tester"])
    auto_owner = {r.get("Assigned team member") for cid, r in tcd_recs.items() if cid not in results}
    check("automated cases are assigned to the team's automated suite", auto_owner == {AUTOMATED_OWNER}, str(auto_owner))
    no_defect = [cid for cid, r in tcd_recs.items() if r.get("Status") == "FAIL" and r.get("Defect / gap ID") in (None, "None")]
    check("every FAIL record names a defect ID", not no_defect, str(no_defect))
    shots = {p for r in tcd_recs.values() for p in re.findall(r"`([^`]+\.png)`", r.get("Screenshot evidence", ""))}
    check("every screenshot referenced in a record exists", all((ROOT / p).exists() for p in shots),
          str([p for p in shots if not (ROOT / p).exists()][:3]))
    manual_line = ", ".join(f"{EXPECTED_MANUAL[x]} {x}" for x in STATUSES if EXPECTED_MANUAL.get(x))
    check("TCD md manual results line", f"Manual validation results: {manual_line}" in tcd, manual_line)

    # ---- Test Case Document (xlsx)
    from openpyxl import load_workbook
    wb = load_workbook(DOCS / "Test_Case_Document.xlsx")
    ws = wb["Test Cases"]
    hdr = [c.value for c in ws[1]]
    ci, cs, co, cm = (hdr.index("Test Case ID"), hdr.index("Status"), hdr.index("Assigned Team Member"),
                      hdr.index("Execution Method"))
    cd, csh = hdr.index("Defect / Gap ID"), hdr.index("Screenshot Evidence")
    xl = {r[ci]: r for r in ws.iter_rows(min_row=2, values_only=True) if r[ci]}
    check("xlsx has 197 case rows", len(xl) == 197, str(len(xl)))
    check("xlsx statuses = md records", all(xl[k][cs] == md_status[k] for k in md_status),
          str([k for k in md_status if xl[k][cs] != md_status[k]]))
    check("xlsx defect IDs = md records", all(xl[k][cd] == tcd_recs[k]["Defect / gap ID"] for k in tcd_recs),
          str([k for k in tcd_recs if xl[k][cd] != tcd_recs[k]["Defect / gap ID"]][:3]))
    check("xlsx owners for the 19 = results.json", all(xl[k][co] == r["tester"] for k, r in results.items()))
    check("xlsx method names Playwright for the 19", all("Playwright" in xl[k][cm] for k in results))
    check("xlsx manual owners 5/7/7", Counter(r[co] for k, r in xl.items() if k in results) == OWNERS)
    check("xlsx screenshot evidence filled for every row", all(xl[k][csh] for k in xl))
    check("xlsx status column is L (Summary formulas)", hdr.index("Status") == 11)
    xl_def = {r[0]: r for r in wb["Defects"].iter_rows(min_row=2, values_only=True)}

    # ---- defect register
    for d, cid in MV.items():
        check(f"{d} in TCD md defect register", re.search(rf"\| {d} \|.*{cid} FAIL \(original run\)", tcd) is not None)
        check(f"{d} in xlsx Defects sheet", d in xl_def and f"{cid} FAIL (original run)" in xl_def[d][4])
        fixed = d in xl_def and str(xl_def[d][5]).startswith("Fixed")
        check(f"{d} register status agrees with {cid} ({md_status[cid]})", fixed == (md_status[cid] == "PASS"),
              str(xl_def.get(d, ["?"] * 6)[5])[:60])
        check(f"{d}: record of {cid} names {d}", d in tcd_recs[cid]["Defect / gap ID"])

    # ---- System Validation Report
    svr = (DOCS / "System_Validation_Report.md").read_text()
    allrow = re.search(r"\| \*\*All\*\* \| (\d+) \|(.+)\|", svr)
    svr_counts = [int(x) for x in allrow.group(2).split("|")]
    check("SVR overall counts = TCD", int(allrow.group(1)) == 197 and svr_counts == [tcd_counts.get(s, 0) for s in STATUSES],
          str(svr_counts))
    svr_recs = parse_records(svr.split("## 3. Workflow validation", 1)[1].split("## 5. ", 1)[0])
    expected_svr = {cid for cid, r in tcd_recs.items() if cid.startswith("SYS_") or r["Status"] != "PASS"}
    check("SVR records every system-level and every not-passed case", set(svr_recs) == expected_svr,
          f"{len(svr_recs)} records; missing {sorted(expected_svr - set(svr_recs))[:3]}")
    diff = [cid for cid, r in svr_recs.items() if any(r.get(f) != tcd_recs[cid].get(f) for f in COMPARE_FIELDS)]
    check("SVR records identical to TCD records (status, owner, actual, defect, evidence)", not diff, str(diff[:3]))
    sec10 = svr.split("## 10. Manual validation", 1)[1].split("Aspects the automated run", 1)[0]
    svr_manual = {cid: status_in(cells) for cid, cells in rows_with_id(sec10)}
    check("SVR section 10.1 lists the 19 cases", set(svr_manual) == set(results))
    check("SVR section 10.1 statuses = results.json", all(svr_manual[k] == results[k]["status"] for k in results))
    sec9 = svr.split("## 9. Outstanding defects", 1)[1].split("## 10.", 1)[0]
    check("SVR defect table contains MV-01..MV-03", all(f"| {d} |" in sec9 for d in MV))
    check("SVR Safari row is BLOCKED", re.search(r"\| Safari application \|.*\| BLOCKED \|", svr) is not None)
    check("SVR no longer says manual validation pending", "manual validation pending" not in svr.lower())

    # ---- Word and PDF editions carry the same record statuses as the Markdown
    import zipfile
    import pymupdf
    REC = re.compile(r"Test Case ID ((?:UT|IT|SYS)_N?FR-\d+_\d+) Requirement .*? Status (PASS|FAIL|BLOCKED|NOT RUN|NOT APPLICABLE) Execution method")
    editions = {"docs/Test_Case_Document": 197, "docs/System_Validation_Report": len(svr_recs)}
    editions.update({f"docs/manual_validation/{o}_Checklist": n for o, n in OWNERS.items()})
    for base, n in editions.items():
        for ext in (".pdf", ".docx"):
            path = ROOT / (base + ext)
            if ext == ".pdf":
                text = " ".join(pg.get_text() for pg in pymupdf.open(path))
            else:
                text = re.sub(r"<[^>]+>", " ", zipfile.ZipFile(path).read("word/document.xml").decode())
            text = re.sub(r"\s+", " ", text.replace("\u2011", "-"))
            found = {m.group(1): m.group(2) for m in REC.finditer(text)}
            wrong = [k for k, v in found.items() if md_status.get(k) != v]
            check(f"{base}{ext}: {n} records, statuses = Markdown", len(found) == n and not wrong,
                  f"{len(found)} records; differing {wrong[:3]}")

    # ---- no contradictory status annotation anywhere ("ID (STATUS" / "ID STATUS")
    sys.path.insert(0, str(ROOT / "scripts"))
    import case_catalog as cat  # noqa: WPS433
    annotated = {"gap register": "\n".join(" | ".join(g) for g in cat.GAPS),
                 "defect register": "\n".join(" | ".join(d) for d in cat.DEFECTS)}
    for f in [x for x in DOCS.rglob("*.md") if "evidence" not in x.parts] + list((ROOT / "Documents/source").glob("*.md")):
        annotated[str(f.relative_to(ROOT))] = f.read_text()
    contradictions = []
    for name, text in annotated.items():
        for mm in ANNOT.finditer(text):
            if mm.group(1) in md_status and md_status[mm.group(1)] != mm.group(2):
                contradictions.append(f"{name}: {mm.group(1)} says {mm.group(2)}, verified {md_status[mm.group(1)]}")
    check("no contradictory status annotation in any report or register", not contradictions, "; ".join(contradictions[:4]))

    # ---- Unit Test Report per-requirement table
    utr = (DOCS / "Unit_Test_Report.md").read_text()
    table = utr.split("| Req. | Module | Cases | UT passed |", 1)[1]
    total = next(l for l in table.splitlines() if l.startswith("| **Total**"))
    cells = [c.strip() for c in total.strip("|").split("|")]
    passed_sum = sum(int(c.split("/")[0]) for c in cells[3:6])
    check("Unit Test Report cases/PASS/FAIL/BLOCKED/NOT RUN/N/A = TCD",
          [int(cells[2]), passed_sum] + [int(c) for c in cells[6:10]]
          == [197] + [tcd_counts.get(s, 0) for s in STATUSES], str(cells))

    # ---- Manual Validation Automation Report
    mvr = (DOCS / "Manual_Validation_Automation_Report.md").read_text()
    sec2 = mvr.split("## 3. Summary", 1)[1].split("## 4.", 1)[0]
    mvr_status = {cid: status_in(cells) for cid, cells in rows_with_id(sec2)}
    check("Automation report statuses = results.json", mvr_status == {k: r["status"] for k, r in results.items()})
    for s, n in EXPECTED_MANUAL.items():
        check(f"Automation report count {s} = {n}", re.search(rf"\| {s} \| {n}\b", sec2) is not None)
    check("Automation report lists MV-01..MV-03", all(f"| {d} |" in mvr for d in MV if d.startswith("MV-")))
    check("Automation report shows the run history (original and regression runs)",
          "## 2. Run history" in mvr and cat.ORIGINAL_MANUAL_RUN_DIR in mvr and cat.REGRESSION_MANUAL_RUN_DIR in mvr)

    # ---- hygiene
    docs_text = "\n".join(p.read_text() for p in [DOCS / "Test_Case_Document.md", DOCS / "System_Validation_Report.md",
                                                  DOCS / "Manual_Validation_Automation_Report.md"]
                          + list((DOCS / "manual_validation").glob("*.md")))
    check("No reference to Kailash", "kailash" not in docs_text.lower())
    cred = ROOT / "demo_credentials.txt"
    if cred.exists():
        pw = [l.split(":", 1)[1].strip() for l in cred.read_text().splitlines() if l.startswith("password:")][0]
        leak = [str(p.relative_to(ROOT)) for p in list(DOCS.rglob("*.md")) + list((DOCS / "evidence/manual_validation_automation").rglob("*"))
                if p.is_file() and p.suffix in (".md", ".log", ".json", ".txt") and pw in p.read_text(errors="ignore")]
        check("Demo password absent from docs and evidence", not leak, str(leak))

    print(f"{len(passed)} checks passed, {len(problems)} failed")
    for p in problems:
        print("  FAIL:", p)
    print(f"Manual validation: {dict(Counter(r['status'] for r in results.values()))}; "
          f"all cases: {tcd_counts}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
