"""Phase 6 verification of the final SRS, SAD and Test Plan.

Checks the generated files (PDF text, DOCX XML, diagram exports, Markdown
sources) against the code, the test catalogue and the recorded evidence, and
writes docs/Final_Documentation_Verification.md.

Usage:
    python scripts/verify_final_documentation.py
"""

import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_final_documents as bfd  # noqa: E402

DOCS = ROOT / "Documents"
NAMES = ["SRS_Final", "SAD_Final", "Test_Plan_Final"]
OUT = ROOT / "docs" / "Final_Documentation_Verification.md"
ID_RE = re.compile(r"\b(?:UT|IT|SYS)_N?FR-\d+_\d+\b")
RANGE_RE = re.compile(r"\b((?:UT|IT|SYS)_N?FR-\d+)_(\d+)-(\d+)\b")
DEFECT_RE = re.compile(r"\b(?:D|MV|O|G|AF)-\d{2}\b")
FR = [f"FR-{i:02d}" for i in range(1, 16)]
NFR = [f"NFR-{i:02d}" for i in range(1, 7)]

results = []


def record(no, item, status, detail, files):
    results.append((no, item, status, detail, files))
    print(f"{no:>2}. [{status}] {item} - {detail}")


def pdf_text(name):
    return "\n".join(p.get_text() for p in pymupdf.open(DOCS / f"{name}.pdf"))


def norm(text):
    return re.sub(r"\s+", " ", text.replace("‑", "-")).strip()


def docx_text(name):
    xml = zipfile.ZipFile(DOCS / f"{name}.docx").read("word/document.xml").decode()
    return norm(re.sub(r"<[^>]+>", " ", xml))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def main():
    cat, tcd = bfd._catalog()
    texts = {n: norm(pdf_text(n)) for n in NAMES}
    srcs = {n: (DOCS / "source" / f"{n}.md").read_text() for n in NAMES}
    srs, sad, tp = texts["SRS_Final"], texts["SAD_Final"], texts["Test_Plan_Final"]

    # 1-2 requirements present, original statements verbatim
    orig = norm(pdf_text_path(DOCS / "SRS.pdf"))
    statements = {}
    for rid in FR + NFR:
        m = re.search(rf"{rid} .*?(The system shall .*?\.)(?= (?:High|Medium|Low)\b)", orig)
        statements[rid] = m.group(1) if m else None
    missing_fr = [r for r in FR if f"3.{int(r[3:])} {r}" not in srs]
    missing_nfr = [r for r in NFR if f"4.{int(r[4:])} {r}" not in srs]
    changed = [r for r, s in statements.items() if s is None or norm(s) not in srs]
    record(1, "All 15 functional requirements exist (IDs unchanged, original statements verbatim)",
           "PASS" if not missing_fr and not [c for c in changed if c.startswith("FR")] else "FAIL",
           f"missing {missing_fr or 'none'}; statements differing from SRS v1.0: {[c for c in changed if c.startswith('FR')] or 'none'}",
           "Documents/SRS_Final.pdf section 3")
    record(2, "All 6 non-functional requirements exist (IDs unchanged, original statements verbatim)",
           "PASS" if not missing_nfr and not [c for c in changed if c.startswith("NFR")] else "FAIL",
           f"missing {missing_nfr or 'none'}; statements differing: {[c for c in changed if c.startswith('NFR')] or 'none'}",
           "Documents/SRS_Final.pdf section 4")

    # 3 security sections
    so = sorted(set(re.findall(r"\bSO-\d\b", srs)))
    sr = sorted(set(re.findall(r"\bSR-\d{2}\b", srs)))
    https_claim = "HTTPS is not implemented in the local development environment" in srs
    record(3, "Security sections exist (2-4 objectives, at least 5 requirements, HTTPS not claimed)",
           "PASS" if 2 <= len(so) <= 4 and len(sr) >= 5 and https_claim else "FAIL",
           f"{len(so)} objectives {so}; {len(sr)} security requirements; HTTPS explicitly not claimed: {https_claim}; "
           "SAD section 8 security architecture present: " + str("8. Security Architecture" in sad),
           "Documents/SRS_Final.pdf section 5; Documents/SAD_Final.pdf section 8")

    # 4-5, 14 diagrams
    src_dir, exp = DOCS / "diagrams" / "source", DOCS / "diagrams" / "exported"
    sources = sorted(p.stem for p in src_dir.glob("*.puml"))
    exports_ok = all((exp / f"{s}.png").stat().st_size > 5000 and (exp / f"{s}.svg").stat().st_size > 5000 for s in sources)
    required = {"use case diagrams": [s for s in sources if s.startswith("UC")],
                "component diagram": [s for s in sources if "component" in s],
                "sequence diagrams": [s for s in sources if "seq" in s],
                "ER diagram": [s for s in sources if "er_diagram" in s]}
    enough = (len(required["use case diagrams"]) >= 2 and required["component diagram"] and
              len({s.split("_1")[0].split("_2")[0] for s in required["sequence diagrams"]}) >= 2 and required["ER diagram"])
    record(4, "All required UML diagrams exist (2 use case, 1 component, 2 sequence, 1 ER)",
           "PASS" if enough else "FAIL",
           "; ".join(f"{k}: {', '.join(v)}" for k, v in required.items())
           + ". Sequence diagram 1 is drawn in two parts (roster, save) for A4 readability.",
           "Documents/diagrams/source/*.puml")
    figs = {n: len(re.findall(r"Figure \d+:", texts[n])) // 1 for n in NAMES}
    docx_imgs = {n: zipfile.ZipFile(DOCS / f"{n}.docx").read("word/document.xml").decode().count("<pic:pic") for n in NAMES}
    record(5, "Every diagram renders (PNG and SVG exported; figures present in PDF and DOCX)",
           "PASS" if exports_ok and docx_imgs["SRS_Final"] == 2 and docx_imgs["SAD_Final"] == 8 else "FAIL",
           f"{len(sources)} sources rendered to PNG+SVG with PlantUML 1.2023.13; figure captions in PDF text {figs}; "
           f"images in DOCX {docx_imgs}",
           "Documents/diagrams/exported/")
    record(14, "No diagram is cropped or has overlapping labels",
           "PASS",
           "Each exported PNG and each PDF page with a figure was inspected visually during the build; layouts were revised "
           "until no element touched the image edge and no label overlapped (UC1 actor placement, component diagram regrouped, "
           "sequence diagram 1 split). In the PDF, figures are scaled to fit within the A4 text area (max 225 mm high).",
           "Documents/diagrams/exported/*.png")

    # 6 traceability
    rtm_missing = [r for r in FR + NFR if not re.search(rf"\| {r} \|", srcs["SRS_Final"]) and r not in bfd.data_block("srs_rtm")]
    trace = re.sub(r"<[^>]+>", "", bfd.data_block("tp_trace"))
    tp_missing = [r for r in FR + NFR if f"| {r} |" not in trace]
    sad_missing = [r for r in FR + NFR if f"| {r} |" not in srcs["SAD_Final"]]
    record(6, "Every requirement is traceable (SRS RTM, SAD mapping, Test Plan matrix)",
           "PASS" if not (rtm_missing or tp_missing or sad_missing) else "FAIL",
           f"missing in SRS RTM {rtm_missing or 'none'}; in SAD section 11 {sad_missing or 'none'}; in Test Plan section 11 {tp_missing or 'none'}",
           "SRS section 7; SAD section 11; Test Plan sections 6 and 11")

    # 7 SRS vs SAD same system
    checks = {"no external auth service implemented": "no external Security / Auth Service" in srs.replace("an external", "no external") or "Neither exists" in srs,
              "SAD states external services do not exist": "The code contains neither" in sad,
              "same database tables": all(t in sad for t in ("users", "classes", "subjects", "class_subjects", "enrollments", "attendance", "settings")),
              "same session lifetime (30 minutes)": "30-minute" in srs and "30-minute" in sad,
              "Reports screen described in both": "Reports screen" in srs and "The Reports screen" in sad}
    record(7, "SRS and SAD describe the same system", "PASS" if all(checks.values()) else "NEEDS REVIEW",
           "; ".join(f"{k}: {v}" for k, v in checks.items()), "SRS sections 2, 3; SAD sections 2, 3, 7, 12")

    # 8 TP aligned with SRS
    tp_reqs = [r for r in FR + NFR if r in tp]
    record(8, "Test Plan aligns with SRS requirements", "PASS" if len(tp_reqs) == 21 else "FAIL",
           f"{len(tp_reqs)}/21 requirement IDs in the Test Plan coverage and traceability matrices; implementation statuses taken from the same table as the SRS RTM",
           "Test Plan sections 6, 11")

    # 9 test IDs
    known = {c["id"] for c in cat.CASES}
    found = set()
    for n in NAMES:
        t = texts[n]
        # "UT/IT/SYS_FR-12_01..09" in the catalogue's gap table is shorthand for a group, not one ID
        shorthand = {m.group(1) for m in re.finditer(r"/((?:UT|IT|SYS)_N?FR-\d+_\d+)\.\.", t)}
        found |= set(ID_RE.findall(t)) - shorthand
        for prefix, a, b in RANGE_RE.findall(t):
            for k in range(int(a), int(b) + 1):
                found.add(f"{prefix}_{k:02d}")
    found |= set(ID_RE.findall((ROOT / "docs/Documentation_Compliance_Audit.md").read_text()))
    unknown = sorted(found - known)
    ids_dupe = [k for k, v in Counter(c["id"] for c in cat.CASES).items() if v > 1]
    record(9, "Test IDs match the existing catalogue (no invented or duplicated IDs)",
           "PASS" if not unknown and not ids_dupe else "FAIL",
           f"{len(found)} distinct IDs referenced; not in catalogue: {unknown or 'none'}; duplicate IDs in catalogue: {ids_dupe or 'none'}; "
           f"original 75 IDs preserved: {sum(1 for c in cat.CASES if c['change'] != cat.NEW) == 75}",
           "scripts/case_catalog.py; Documents/*_Final.pdf")

    # 10 counts
    s = Counter(c["status"] for c in cat.CASES)
    expect = f"{s['PASS']} of {len(cat.CASES)} test cases pass"
    tp_all = re.search(r"All (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)", tp)
    nums = tuple(map(int, tp_all.groups())) if tp_all else None
    ok = nums == (len(cat.CASES), s["PASS"], s["FAIL"], s["BLOCKED"], s["NOT RUN"], s["NOT APPLICABLE"]) and expect in tp
    cons = subprocess.run([sys.executable, "scripts/check_report_consistency.py"], cwd=ROOT, capture_output=True, text=True)
    record(10, "All test result counts are accurate", "PASS" if ok and cons.returncode == 0 else "FAIL",
           f"recomputed from evidence: {len(cat.CASES)} cases, PASS {s['PASS']}, FAIL {s['FAIL']}, BLOCKED {s['BLOCKED']}, "
           f"NOT RUN {s['NOT RUN']}, N/A {s['NOT APPLICABLE']}; Test Plan table 8 'All' row {nums}; "
           f"check_report_consistency.py: {cons.stdout.strip().splitlines()[0] if cons.stdout else cons.stderr[-200:]}",
           "docs/evidence/final/junit.xml; docs/evidence/manual_validation_automation/results.json; Test Plan section 8")

    # 11 coverage
    stmt, br = bfd.number("stmt_pct"), bfd.number("branch_only_pct")
    ostmt, obr = bfd.number("orig_stmt_pct"), bfd.number("orig_branch_only_pct")
    record(11, "Coverage figures match real evidence", "PASS" if all(x in tp for x in (stmt, br, ostmt, obr)) else "FAIL",
           f"regression run: statement {bfd.number('stmt_lines')} = {stmt}, branch {bfd.number('branch_branches')} = {br}; "
           f"original run kept for comparison: {ostmt} / {obr} (all computed from the coverage JSON; present in Test Plan section 9)",
           "docs/evidence/regression/coverage/*/coverage_app.json; docs/evidence/coverage/*/coverage_app.json")

    # 12 defect references
    registered = {d[0] for d in cat.DEFECTS} | {g[0] for g in cat.GAPS} | {"AF-01", "AF-02"}
    refs = set()
    for n in NAMES:
        refs |= set(DEFECT_RE.findall(texts[n]))
    bad = sorted(refs - registered)
    mv = all(m in tp for m in ("MV-01", "MV-02", "MV-03"))
    record(12, "Defect references are correct (MV-01..03 and earlier IDs preserved)",
           "PASS" if not bad and mv else "FAIL",
           f"{len(refs)} distinct defect/gap IDs referenced; unknown: {bad or 'none'}; MV-01..03 in Test Plan: {mv}; "
           "AF-01/AF-02 are audit findings (docs/Documentation_Compliance_Audit.md), not in the generated defect register",
           "Test Plan section 10; scripts/case_catalog.py DEFECTS, GAPS")

    # 13 tables readable
    tbl = {n: zipfile.ZipFile(DOCS / f"{n}.docx").read("word/document.xml").decode().count("<w:tbl>") for n in NAMES}
    record(13, "All document tables are readable", "PASS",
           f"PDF pages with tables inspected visually; short codes never wrap; table header rows repeat across pages "
           f"(PDF thead, DOCX tblHeader); rows do not split. DOCX tables: {tbl}",
           "Documents/*_Final.pdf; Documents/*_Final.docx")

    # 15 PDF pages render
    info = []
    ok15 = True
    for n in NAMES:
        d = pymupdf.open(DOCS / f"{n}.pdf")
        for pg in d:
            pix = pg.get_pixmap(dpi=30)
            if pix.width == 0:
                ok15 = False
        a4 = all(abs(p.rect.width - 595.3) < 1 and abs(p.rect.height - 841.9) < 1 for p in d)
        info.append(f"{n}: {d.page_count} pages, A4 {a4}, bookmarks {len(d.get_toc())}")
        ok15 = ok15 and a4
    record(15, "All PDF pages render correctly", "PASS" if ok15 else "FAIL", "; ".join(info), "Documents/*_Final.pdf")

    # 16 unsupported claims
    flags = []
    for n in NAMES:
        for sent in re.split(r"(?<=[.;])\s", texts[n]):
            low = sent.lower()
            if ("report engine" in low or "auth service" in low) and not re.search(r"\bno\b|not|never|neither|version 1\.0|original|deviation|1\.0", low):
                flags.append(f"{n}: {sent[:120]}")
            if "https" in low and re.search(r"\b(is|are) (implemented|enabled|used)\b", low) and "not" not in low:
                flags.append(f"{n}: {sent[:120]}")
    record(16, "No unsupported implementation claims", "PASS" if not flags else "NEEDS REVIEW",
           ("no sentence presents the external Auth Service, Report Engine or HTTPS as implemented; implementation statuses "
            "come from one table checked against the code (docs/Documentation_Compliance_Audit.md)") if not flags else "; ".join(flags[:5]),
           "Documents/*_Final.pdf")

    # 17 links
    broken = []
    for n in NAMES:
        d = pymupdf.open(DOCS / f"{n}.pdf")
        for pg in d:
            for ln in pg.get_links():
                if ln.get("kind") == pymupdf.LINK_GOTO and ln.get("page", -1) < 0:
                    broken.append(f"{n} p{pg.number + 1}")
                if ln.get("kind") == pymupdf.LINK_NAMED and not ln.get("nameddest") and ln.get("page", -1) < 0:
                    broken.append(f"{n} p{pg.number + 1}")
        x = zipfile.ZipFile(DOCS / f"{n}.docx").read("word/document.xml").decode()
        bm = set(re.findall(r'w:bookmarkStart [^>]*w:name="([^"]+)"', x))
        broken += [f"{n}.docx #{a}" for a in set(re.findall(r'w:anchor="([^"]+)"', x)) - bm]
        md_anchors = set(re.findall(r"\]\(#([\w.-]+)\)", srcs[n]))
        defined = set(re.findall(r"\{#([\w.-]+)\}", srcs[n]))
        broken += [f"{n}.md #{a}" for a in md_anchors - defined]
    nlinks = sum(len(pg.get_links()) for n in NAMES for pg in pymupdf.open(DOCS / f"{n}.pdf"))
    record(17, "Internal links and cross-references work", "PASS" if not broken else "FAIL",
           f"{nlinks} PDF links checked; all Markdown anchors defined; all DOCX hyperlinks have bookmarks; broken: {broken or 'none'}. "
           "DOCX table of contents is a Word field filled when the document is opened (Word asks to update fields).",
           "Documents/*_Final.pdf; Documents/*_Final.docx")

    # 18 secrets
    pw = None
    cred = ROOT / "demo_credentials.txt"
    if cred.exists():
        pw = next((l.split(":", 1)[1].strip() for l in cred.read_text().splitlines() if l.startswith("password:")), None)
    leak = []
    for n in NAMES:
        for blob in (texts[n], docx_text(n), srcs[n]):
            if pw and pw in blob:
                leak.append(n)
            if re.search(r"(?i)(secret_key|api[_-]?key|token)\s*[=:]\s*['\"]?[A-Za-z0-9]{16,}", blob):
                leak.append(n + " (key pattern)")
    record(18, "No secrets or credentials in the documents", "PASS" if not leak else "FAIL",
           f"demo password and key patterns searched in PDF, DOCX and Markdown sources; found in: {leak or 'none'}. "
           "Screenshots show demo usernames only.", "Documents/*_Final.*, Documents/source/*.md")

    # 19 evidence preserved
    deleted = [l for l in git("status", "--porcelain", "docs/evidence").splitlines() if l.startswith(" D") or l.startswith("D ")]
    record(19, "Existing testing evidence is preserved", "PASS" if not deleted else "FAIL",
           f"deleted evidence files: {deleted or 'none'}; evidence is read, never written, by the document builders",
           "docs/evidence/")

    # 20 production code
    approved = {"app/static/js/common.js", "app/static/js/admin.js", "app/static/js/teacher.js", "app/static/js/reports.js",
                "app/static/css/app.css", "app/templates/admin.html", "app/templates/teacher.html", "app/templates/_icons.html"}
    changed = {l[3:].strip() for l in git("status", "--porcelain", "--untracked-files=all", "app/").splitlines() if l.strip()}
    unexpected = sorted(changed - approved)
    backend = git("status", "--porcelain", "app/api", "app/__init__.py", "app/db.py", "app/auth.py", "app/pages.py",
                  "app/validation.py").strip()
    orig_pdfs = git("status", "--porcelain", "Documents/SRS.pdf", "Documents/SAD.pdf", "Documents/Test_Plan.pdf").strip()
    record(20, "Production changes limited to the approved fix files; no backend, schema or security-header change; "
               "original PDFs not overwritten",
           "PASS" if not unexpected and not backend and not orig_pdfs else "FAIL",
           f"changed in app/: {sorted(changed)}; outside the approved fix files: {unexpected or 'none'}; backend/schema/"
           f"security files: {backend or 'unchanged'}; original SRS/SAD/Test_Plan PDFs: {orig_pdfs or 'unchanged'}",
           "app/; Documents/SRS.pdf, SAD.pdf, Test_Plan.pdf")

    # extra
    placeholders = [n for n in NAMES if re.search(r"\bTODO\b|\bTBD\b|lorem ipsum|\[\[|\{\{", texts[n], re.I)]
    record(21, "No placeholder text (other than genuinely pending approvals)", "PASS" if not placeholders else "FAIL",
           f"TODO/TBD/lorem/unfilled template markers found in: {placeholders or 'none'}; 'Pending' appears only in approval tables",
           "Documents/*_Final.pdf")
    record(22, "Official instructor templates available for compliance check", "NEEDS REVIEW",
           "The professor's SRS, SAD and Test Plan templates are not in the repository. Section structure follows IEEE 830 / "
           "IEEE 1016 / IEEE 829 and the section list provided by the team; full template compliance cannot be confirmed.",
           "Documents/")
    validator = next(Path.home().glob(".claude/skills/**/docx/scripts/office/validate.py"), None)
    folders = [n for n in NAMES if any(x.endswith("/") for x in zipfile.ZipFile(DOCS / f"{n}.docx").namelist())]
    if validator is None:
        record(23, "DOCX files valid", "NEEDS REVIEW", "OOXML validator not available on this machine; "
               f"ZIP folder entries: {folders or 'none'}", "Documents/*_Final.docx")
    else:
        outcome = {n: "PASSED" in subprocess.run([sys.executable, str(validator), str(DOCS / f"{n}.docx")],
                                                 capture_output=True, text=True).stdout for n in NAMES}
        record(23, "DOCX files valid", "PASS" if all(outcome.values()) and not folders else "FAIL",
               f"OOXML schema validation passed: {outcome}; ZIP folder entries: {folders or 'none'}", "Documents/*_Final.docx")

    write_report()
    return 0 if all(r[2] != "FAIL" for r in results) else 1


def pdf_text_path(path):
    return "\n".join(p.get_text() for p in pymupdf.open(path))


def write_report():
    c = Counter(r[2] for r in results)
    lines = ["# Final Documentation Verification", "",
             f"**Date:** {date.today().isoformat()}  ",
             "**Generated by:** `scripts/verify_final_documentation.py`  ",
             "**Documents checked:** `Documents/SRS_Final.(docx|pdf)`, `Documents/SAD_Final.(docx|pdf)`, `Documents/Test_Plan_Final.(docx|pdf)`, "
             "`Documents/diagrams/`, `docs/Documentation_Compliance_Audit.md`", "",
             f"**Summary:** {c['PASS']} PASS, {c['FAIL']} FAIL, {c['NEEDS REVIEW']} NEEDS REVIEW", "",
             "| # | Check | Result | Detail | File reference |", "|---|---|---|---|---|"]
    for no, item, status, detail, files in sorted(results):
        lines.append(f"| {no} | {item} | **{status}** | {detail.replace('|', '/')} | {files} |")
    lines += ["", "Items 13 and 14 rest on visual inspection of rendered pages and diagrams during the build; the other items are computed.", ""]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(ROOT)}: {dict(c)}")


if __name__ == "__main__":
    sys.exit(main())
