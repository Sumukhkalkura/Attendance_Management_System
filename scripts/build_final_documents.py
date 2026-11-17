"""Build the final SRS, SAD and Test Plan as A4 .docx and .pdf files.

Sources (editable Markdown):   Documents/source/<Name>.md
Diagrams (PlantUML exports):   Documents/diagrams/exported/*.png|*.svg
Outputs:                       Documents/<Name>.docx, Documents/<Name>.pdf

Usage:
    python scripts/build_final_documents.py            # all three documents
    python scripts/build_final_documents.py SRS_Final  # one document

Markdown conventions understood by this script:
* A metadata block between two '---' lines at the top (title, subtitle,
  version, date, course, team, status) produces the title page.
* '[[TOC]]' on its own line inserts the table of contents.
* '## Heading {#anchor}' sets an explicit anchor; '[text](#anchor)' links to it.
* '![Figure N: caption](../diagrams/exported/name.png)' inserts a figure with a
  caption (the PDF uses the .svg next to the .png when it exists).
* A paragraph starting with 'Table N:' is a table caption.
* '<!-- pagebreak -->' forces a page break. Every level-1 heading starts a page.

PDF: rendered by Google Chrome through Playwright (A4, page numbers in the
footer, bookmarks, clickable internal links). Table-of-contents page numbers
come from a first rendering pass. DOCX: written with python-docx (A4, page
numbers, bookmarks, internal hyperlinks, a Word TOC field that Word fills in
when the document is opened and fields are updated).
"""

import html
import re
import sys
from pathlib import Path

import pymupdf
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DOCS = ROOT / "Documents"
SRC = DOCS / "source"
NAMES = ["SRS_Final", "SAD_Final", "Test_Plan_Final"]
ACCENT = "1F3864"

MD = MarkdownIt("commonmark", {"html": True}).enable("table")


# =============================================================================
# Parsing
# =============================================================================

def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", text).strip("-")


def parse_source(path, report=False):
    """Read a Markdown source. report=True: a generated report in docs/ (its H1 becomes the title page,
    headings move up one level, and a table of contents is inserted before the first section)."""
    raw = path.read_text(encoding="utf-8")
    meta = {}
    if report:
        lines_in = raw.splitlines()
        first = next(i for i, l in enumerate(lines_in) if l.startswith("# "))
        body = lines_in[first + 1:]
        out, fence, toc_done = [], False, False
        for line in body:
            if line.startswith("```"):
                fence = not fence
            if not fence and re.match(r"^#{2,6} ", line):
                if not toc_done:
                    preface = "\n".join(out).strip()
                    out = (["# Document Information", "", preface, ""] if preface else []) + ["[[TOC]]", ""]
                    toc_done = True
                line = line[1:]
            out.append(line)
        raw = "\n".join(out) + "\n"
    m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        raw = raw[m.end():]
    if not report:
        raw = fill(raw)
    # explicit heading anchors (made unique)
    anchors = []
    lines = []
    in_fence = False
    for line in raw.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        hm = None if in_fence else re.match(r"^(#{1,6})\s+(.*?)\s*(\{#([\w.-]+)\})?\s*$", line)
        if hm:
            text = hm.group(2)
            anchor = hm.group(4) or slugify(text)
            base, k = anchor, 2
            while anchor in anchors:
                anchor, k = f"{base}-{k}", k + 1
            anchors.append(anchor)
            line = f"{hm.group(1)} {text}"
        lines.append(line)
    return meta, "\n".join(lines) + "\n", anchors


def vlabel(meta):
    v = meta.get("version", "")
    return f"v{v}" if v[:1].isdigit() else v


def inline_text(tok):
    return "".join(c.content for c in (tok.children or []) if c.type in ("text", "code_inline"))


def headings(tokens, anchors):
    out, i = [], 0
    for idx, t in enumerate(tokens):
        if t.type == "heading_open":
            out.append((int(t.tag[1]), inline_text(tokens[idx + 1]), anchors[i]))
            i += 1
    return out


# =============================================================================
# Data tables generated from the test catalogue, evidence and route table
# =============================================================================

# Implementation status per requirement (see docs/Documentation_Compliance_Audit.md).
REQ_STATUS = {
    "FR-01": "IMPLEMENTED", "FR-02": "IMPLEMENTED", "FR-03": "IMPLEMENTED", "FR-04": "IMPLEMENTED",
    "FR-05": "IMPLEMENTED", "FR-06": "IMPLEMENTED", "FR-07": "IMPLEMENTED", "FR-08": "IMPLEMENTED",
    "FR-09": "IMPLEMENTED", "FR-10": "IMPLEMENTED", "FR-11": "IMPLEMENTED", "FR-12": "IMPLEMENTED",
    "FR-13": "IMPLEMENTED", "FR-14": "IMPLEMENTED", "FR-15": "IMPLEMENTED",
    "NFR-01": "PARTIAL", "NFR-02": "IMPLEMENTED", "NFR-03": "PARTIAL", "NFR-04": "PARTIAL",
    "NFR-05": "PARTIAL", "NFR-06": "IMPLEMENTED",
}
USE_CASES = {
    "FR-01": "UC-01", "FR-02": "UC-02, UC-03", "FR-03": "UC-04", "FR-04": "UC-06", "FR-05": "UC-05",
    "FR-06": "UC-07", "FR-07": "UC-08", "FR-08": "UC-09", "FR-09": "UC-10", "FR-10": "UC-11",
    "FR-11": "UC-12, UC-17", "FR-12": "UC-13", "FR-13": "UC-14", "FR-14": "UC-15", "FR-15": "UC-16",
    "NFR-01": "UC-01, UC-05 (cross-cutting)", "NFR-02": "UC-05, UC-06, UC-07 (cross-cutting)",
    "NFR-03": "UC-04 (cross-cutting)", "NFR-04": "All UI use cases", "NFR-05": "All UI use cases", "NFR-06": "-",
}
COMPONENTS = {
    "FR-01": "Auth and session (app/auth.py, api/auth_routes.py); Page routes (app/pages.py)",
    "FR-02": "Attendance management (api/attendance_records.py: class_roster, mark_attendance); teacher.js",
    "FR-03": "Attendance management (api/attendance_records.py, api/attendance_management.py); attendance UNIQUE constraint",
    "FR-04": "Percentage and alerts (api/percentages.py); student.js percentOf()",
    "FR-05": "Attendance management (api/attendance_view.py); teacher.js, student.js, admin.js",
    "FR-06": "Reporting and export (api/reports.py); Reports screen (static/js/reports.js)",
    "FR-07": "Admin management (api/users.py); admin.js",
    "FR-08": "Admin management (api/academics.py); admin.js",
    "FR-09": "Admin management (api/enrollments.py); admin.js",
    "FR-10": "Attendance management (api/attendance_view.py filters); dashboard search, subject, class, date-range, status filters and Clear filters",
    "FR-11": "Percentage and alerts (api/alerts.py); overview tables in admin.js, teacher.js",
    "FR-12": "Reporting and export (api/reports.py, api/exports.py); export buttons in static/js/reports.js",
    "FR-13": "Auth and session (api/auth_routes.py change_password); common.js dialog",
    "FR-14": "Web UI overview sections (admin.js, teacher.js, student.js) using existing APIs",
    "FR-15": "Auth and session (api/session_routes.py logout); common.js",
    "NFR-01": "login_required, CSRF origin check, security headers, session cookie settings (app/__init__.py, app/auth.py)",
    "NFR-02": "Indexes in app/db.py; aggregate SQL in api/percentages.py",
    "NFR-03": "Transactions in API modules; scripts/backup_db.py, scripts/schedule_daily_backup.py",
    "NFR-04": "Templates and app/static/css/app.css (focus styles, ARIA labels, responsive layout)",
    "NFR-05": "Standards-mode HTML, polyfills in common.js, fixed MIME types (app/__init__.py)",
    "NFR-06": "Feature modules in app/api/ on one blueprint; URL map frozen by tests/test_nfr06_maintainability.py",
}


def _catalog():
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_test_case_document as tcd  # noqa: WPS433
    import case_catalog as cat  # noqa: WPS433
    if not getattr(_catalog, "done", False):
        ev = {label: tcd.load_junit(path) for label, path in tcd.EVIDENCE.items()}
        for c in cat.CASES:
            c["status"], c["actual"], c["date"], c["evidence"] = tcd.evaluate(c, ev)
        _catalog.done = True
        _catalog.ev = ev
    return cat, tcd


_CODE = re.compile(r"^(?:(?:UT|IT|SYS)_N?FR-\d+_\d+|N?FR-\d+|[A-Z]{1,2}-\d+)$")


def _cell(x):
    text = str(x).replace("|", "/").replace("\n", " ")
    return f'<span class="nw">{text}</span>' if _CODE.match(text) else text


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(_cell(x) for x in r) + " |")
    return "\n".join(out)


def _nw(text):
    """Keep a test case ID on one line (PDF: nowrap span; DOCX: non-breaking hyphens)."""
    return f'<span class="nw">{text}</span>'


def _ids(cases):
    return ", ".join(_nw(c["id"]) for c in cases)


def _ranges(cases):
    """Compress IDs into inclusive ranges per prefix: UT_FR-01_01-03, 11-13; IT_FR-01_04-07."""
    from collections import OrderedDict
    groups = OrderedDict()
    for c in cases:
        prefix, num = c["id"].rsplit("_", 1)
        groups.setdefault(prefix, []).append(int(num))
    parts = []
    for prefix, nums in groups.items():
        nums.sort()
        runs, start, prev = [], nums[0], nums[0]
        for n in nums[1:] + [None]:
            if n is not None and n == prev + 1:
                prev = n
                continue
            runs.append(f"{start:02d}" if start == prev else f"{start:02d}-{prev:02d}")
            if n is not None:
                start = prev = n
        parts.append(_nw(f"{prefix}_{runs[0]}") + "".join(", " + r for r in runs[1:]))
    return "; ".join(parts)


def _defects_for(cat, req):
    return [d[0] for d in cat.DEFECTS if d[1] == req and not d[5].startswith("Documented")]


def data_block(name):
    cat, tcd = _catalog()
    cases = cat.CASES
    statuses = tcd.STATUSES
    from collections import Counter
    if name == "srs_rtm":
        rows = []
        for req in cat.MODULES:
            cs = [c for c in cases if c["req"] == req]
            rows.append((req, USE_CASES[req], COMPONENTS[req], _ids(cs), REQ_STATUS[req]))
        return _table(["Requirement", "Use case(s)", "Application component", "Test case IDs", "Implementation status"], rows)
    if name == "tp_coverage":
        rows, tot = [], Counter()
        for req in cat.MODULES:
            cs = [c for c in cases if c["req"] == req]
            t = Counter(c["type"] for c in cs)
            s = Counter(c["status"] for c in cs)
            orig = sum(1 for c in cs if c["change"] != cat.NEW)
            row = [t["UT"], t["IT"], t["SYS"], len(cs), orig] + [s[x] for x in statuses]
            for k, v in enumerate(row):
                tot[k] += v
            rows.append([req, cat.MODULES[req]] + row)
        rows.append(["**Total**", ""] + [f"**{tot[k]}**" for k in range(len(rows[0]) - 2)])
        return _table(["Req.", "Module", "UT", "IT", "SYS", "Cases", "Orig. 75"] + ["N/A" if s == "NOT APPLICABLE" else s for s in statuses], rows)
    if name == "tp_trace":
        rows = []
        for req in cat.MODULES:
            cs = [c for c in cases if c["req"] == req]
            s = Counter(c["status"] for c in cs)
            notpass = [f"{_nw(c['id'])} ({c['status']})" for c in cs if c["status"] != "PASS"]
            ev = sorted({e.split(" (")[0].split(";")[0].strip() for c in cs for e in [c["evidence"]] if e})
            rows.append((req, f"{len(cs)} cases: {_ranges(cs)}",
                         ", ".join(f"{s[x]} {x}" for x in statuses if s[x]),
                         "; ".join(notpass) or "-",
                         ", ".join(_defects_for(cat, req)) or "-",
                         "; ".join(ev) or "-"))
        return ("Test case ranges are inclusive (e.g. UT_FR-01_01-03 = UT_FR-01_01, UT_FR-01_02, UT_FR-01_03).\n\n"
                + _table(["Requirement", "Test cases", "Execution status", "Cases not passed", "Open defect IDs", "Evidence"], rows))
    if name == "tp_status_totals":
        rows = []
        for t in ("UT", "IT", "SYS"):
            cs = [c for c in cases if c["type"] == t]
            s = Counter(c["status"] for c in cs)
            rows.append([t, len(cs)] + [s[x] for x in statuses])
        s = Counter(c["status"] for c in cases)
        rows.append(["**All**", f"**{len(cases)}**"] + [f"**{s[x]}**" for x in statuses])
        return _table(["Level", "Cases"] + statuses, rows)
    if name == "tp_not_passed":
        return _table(["Test case", "Req.", "Status", "Actual result / reason", "Owner"],
                      [(c["id"], c["req"], c["status"], c["actual"] or "-", c["tester"] or "-")
                       for c in cases if c["status"] != "PASS"])
    if name == "defects":
        return _table(["ID", "Req.", "Severity", "Description", "Test impact", "Status"], cat.DEFECTS)
    if name == "gaps":
        return _table(["Gap", "Req.", "Description", "Classification", "Affected cases"],
                      [(g[0], g[1], g[2], g[4], g[6]) for g in cat.GAPS])
    if name == "tp_original":
        rows = []
        for req in cat.MODULES:
            cs = [c for c in cases if c["req"] == req and c["change"] != cat.NEW]
            if cs:
                s = Counter(c["status"] for c in cs)
                rows.append((req, len(cs), _ids(cs), ", ".join(f"{s[x]} {x}" for x in statuses if s[x])))
        rows.append(("**Total**", f"**{sum(1 for c in cases if c['change'] != cat.NEW)}**", "", ""))
        return _table(["Requirement", "Original cases", "Test case IDs (unchanged since Test Plan v1.0)", "Current status"], rows)
    if name == "manual":
        return _table(["Test case", "Owner", "Status", "Execution date"],
                      [(c["id"], c["tester"], c["status"], c["date"] or "-") for c in cases if c["tester"]])
    if name == "api_routes":
        from app import create_app  # noqa: WPS433
        import tempfile
        app = create_app({"DATABASE": str(Path(tempfile.mkdtemp()) / "routes.db"), "TESTING": True})
        roles = _route_roles()
        rows = []
        for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            if not r.rule.startswith("/api") or "/export/<" in r.rule:
                continue
            methods = ",".join(sorted(r.methods - {"HEAD", "OPTIONS"}))
            view = r.endpoint.split(".")[-1]
            rows.append((f"`{r.rule}`", methods, view, roles.get(view, "-")))
        return _table(["Route", "Method(s)", "View function", "Allowed roles"], rows)
    raise KeyError(name)


def _route_roles():
    """Read the login_required role list of each API view from the source."""
    roles = {}
    for f in (ROOT / "app" / "api").glob("*.py"):
        text = f.read_text()
        for m in re.finditer(r"@login_required\((.*?)\)\s*\ndef (\w+)", text):
            arg = m.group(1).strip()
            roles[m.group(2)] = ("any role" if not arg else
                                 ", ".join(re.findall(r'"(\w+)"', arg)))
        for m in re.finditer(r"\ndef (\w+)", text):
            roles.setdefault(m.group(1), "public")
    return roles


def number(name):
    cat, tcd = _catalog()
    from collections import Counter
    s = Counter(c["status"] for c in cat.CASES)
    junit = Counter(_catalog.ev["main"][0].values())
    values = {
        "cases": len(cat.CASES), "original": sum(1 for c in cat.CASES if c["change"] != cat.NEW),
        "new": sum(1 for c in cat.CASES if c["change"] == cat.NEW),
        "pass": s["PASS"], "fail": s["FAIL"], "blocked": s["BLOCKED"], "notrun": s["NOT RUN"], "na": s["NOT APPLICABLE"],
        "junit_passed": junit["passed"], "junit_failed": junit["failure"], "junit_errors": junit["error"],
        "junit_skipped": junit["skipped"], "junit_total": sum(junit.values()), "junit_date": _catalog.ev["main"][1],
        "manual_summary": tcd.manual_counts(), "manual_date": cat.MANUAL_META["run_date"],
        "manual_browser": cat.MANUAL_META["browser"], "tcd_version": tcd.VERSION,
    }
    import json
    for prefix, base in (("", "docs/evidence/regression/coverage"), ("orig_", "docs/evidence/coverage")):
        for run, key in (("statement", "stmt"), ("branch", "branch")):
            t = json.loads((ROOT / f"{base}/{run}/coverage_app.json").read_text())["totals"]
            values[f"{prefix}{key}_lines"] = f"{t['covered_lines']}/{t['num_statements']}"
            values[f"{prefix}{key}_pct"] = f"{100 * t['covered_lines'] / t['num_statements']:.2f}%"
            if t.get("num_branches"):
                values[f"{prefix}branch_branches"] = f"{t['covered_branches']}/{t['num_branches']}"
                values[f"{prefix}branch_only_pct"] = f"{100 * t['covered_branches'] / t['num_branches']:.2f}%"
    return str(values[name])


def req_summary(req):
    """'11 test cases, 11 PASS' / '10 test cases: 8 PASS, 1 FAIL, ...' for one requirement."""
    cat, tcd = _catalog()
    from collections import Counter
    cs = [c for c in cat.CASES if c["req"] == req]
    s = Counter(c["status"] for c in cs)
    if s["PASS"] == len(cs):
        return f"{len(cs)} test cases, {len(cs)} PASS"
    return f"{len(cs)} test cases: " + ", ".join(f"{s[x]} {x}" for x in tcd.STATUSES if s[x])


def fill(md_text):
    md_text = re.sub(r"\{\{tc:([\w-]+)\}\}", lambda m: req_summary(m.group(1)), md_text)
    md_text = re.sub(r"^\[\[DATA:(\w+)\]\]$", lambda m: data_block(m.group(1)), md_text, flags=re.M)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: number(m.group(1)), md_text)


# =============================================================================
# HTML / PDF
# =============================================================================

CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
html { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #1a1a1a; }
body { margin: 0; line-height: 1.38; }
h1, h2, h3, h4 { color: #1F3864; line-height: 1.2; page-break-after: avoid; break-after: avoid; }
h1 { font-size: 17pt; border-bottom: 2px solid #1F3864; padding-bottom: 4px; margin: 0 0 12px; break-before: page; }
h2 { font-size: 13pt; margin: 18px 0 8px; }
h3 { font-size: 11pt; margin: 14px 0 6px; }
h4 { font-size: 10pt; margin: 12px 0 4px; }
p { margin: 0 0 7px; text-align: left; }
ul, ol { margin: 0 0 8px 0; padding-left: 20px; }
li { margin: 1px 0; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; background: #f2f4f7; padding: 0 2px; border-radius: 2px; }
pre { font-family: Menlo, Consolas, monospace; font-size: 8.4pt; background: #f2f4f7; border: 1px solid #d9dee6;
      padding: 6px 8px; white-space: pre-wrap; word-break: break-word; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 12px; font-size: 8.4pt; page-break-inside: auto; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; break-inside: avoid; }
th { background: #1F3864; color: #fff; text-align: left; padding: 4px 5px; border: 1px solid #1F3864; vertical-align: bottom; }
td { padding: 3px 5px; border: 1px solid #b7c0cc; vertical-align: top; overflow-wrap: break-word; }
.nw { white-space: nowrap; }
tbody tr:nth-child(even) td { background: #f5f7fa; }
blockquote { margin: 6px 0 10px; padding: 6px 10px; border-left: 4px solid #1F3864; background: #eef2f8; }
blockquote p { margin: 0; }
p.caption { font-size: 9pt; font-weight: bold; color: #1F3864; margin: 10px 0 3px; page-break-after: avoid; break-after: avoid; }
figure { margin: 8px 0 14px; text-align: center; page-break-inside: avoid; break-inside: avoid; }
figure img { max-width: 100%; max-height: 225mm; }
figcaption { font-size: 9pt; font-weight: bold; color: #1F3864; margin-top: 4px; }
a { color: #1F4E9A; text-decoration: none; }
.titlepage { height: 245mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }
.titlepage .t1 { font-size: 26pt; font-weight: bold; color: #1F3864; margin-bottom: 8px; }
.titlepage .t2 { font-size: 16pt; color: #333; margin-bottom: 36px; }
.titlepage table { width: 70%; margin: 0 auto; font-size: 10pt; }
.titlepage td { border: none; border-bottom: 1px solid #d9dee6; background: none !important; padding: 6px; text-align: left; }
.titlepage td:first-child { font-weight: bold; width: 32%; color: #1F3864; }
.toc { break-before: page; break-after: page; }
.toc h2 { break-before: auto; }
.toc ol { list-style: none; padding-left: 0; }
.toc li { display: flex; align-items: baseline; margin: 2px 0; }
.toc li.l2 { padding-left: 18px; font-size: 9.4pt; }
.toc li.l1 { font-weight: bold; margin-top: 6px; }
.toc .dots { flex: 1; border-bottom: 1px dotted #999; margin: 0 4px; transform: translateY(-3px); }
.pagebreak { break-after: page; }
table.record { break-inside: avoid; page-break-inside: avoid; }
table.record td:first-child { width: 24%; font-weight: bold; color: #1F3864; }
"""


def build_html(meta, md_text, anchors, toc_pages=None):
    tokens = MD.parse(md_text)
    heads = headings(tokens, anchors)
    body = MD.renderer.render(tokens, MD.options, {})

    # heading ids, in order
    it = iter(anchors)
    body = re.sub(r"<h([1-6])>", lambda m: f'<h{m.group(1)} id="{next(it)}">', body)
    # figures
    def fig(m):
        src, alt = m.group(1), html.unescape(m.group(2))
        svg = src[:-4] + ".svg" if src.endswith(".png") else src
        if (SRC / svg).exists():
            src = svg
        return f'<figure><img src="{src}" alt="{html.escape(alt)}"><figcaption>{html.escape(alt)}</figcaption></figure>'
    body = re.sub(r'<p><img src="([^"]+)" alt="([^"]*)"\s*/?></p>', fig, body)
    body = re.sub(r"<p>(Table \d+:)", r'<p class="caption">\1', body)
    # test case IDs never wrap anywhere in running text
    body = re.sub(r'(?<![\w">-])((?:UT|IT|SYS)_N?FR-\d+_\d+)(?![\w<])', r'<span class="nw">\1</span>', body)
    # short identifiers (FR-01, SO-1, SR-01, UC-01, G-01 / D-02, ...) never wrap inside a table cell
    body = re.sub(r"<td>((?:(?:UT|IT|SYS)_)?N?[A-Z]{1,3}-\d+(?:_\d+)?(?:,? (?:/ )?(?:(?:UT|IT|SYS)_)?N?[A-Z]{1,3}-\d+(?:_\d+)?)*)</td>",
                  r'<td class="nw">\1</td>', body)
    body = body.replace("<!-- pagebreak -->", '<div class="pagebreak"></div>')
    # test records (Field / Details tables) are kept whole on one page
    body = body.replace("<table>\n<thead>\n<tr>\n<th>Field</th>\n<th>Details</th>", '<table class="record">\n<thead>\n<tr>\n<th>Field</th>\n<th>Details</th>')

    # title page
    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(meta[k.lower()])}</td></tr>"
                   for k in ("Version", "Date", "Course", "Team", "Status") if meta.get(k.lower()))
    title = (f'<div class="titlepage"><div class="t1">{html.escape(meta["title"])}</div>'
             f'<div class="t2">{html.escape(meta.get("subtitle", ""))}</div><table>{rows}</table></div>'
             '<div class="pagebreak"></div>')

    # table of contents (levels 1-2)
    items = []
    for n, (lvl, text, anchor) in enumerate(h for h in heads if h[0] <= 2):
        page = (toc_pages or {}).get(n, "")
        items.append(f'<li class="l{lvl}"><a href="#{anchor}">{html.escape(text)}</a>'
                     f'<span class="dots"></span><span>{page}</span></li>')
    toc = f'<div class="toc"><h2 class="tochead">Table of Contents</h2><ol>{"".join(items)}</ol></div>'
    body = body.replace("<p>[[TOC]]</p>", toc)

    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(meta["title"])}</title>'
            f"<style>{CSS}</style></head><body>{title}{body}</body></html>"), heads


def render_pdf(html_text, pdf_path, meta, browser):
    tmp = SRC / f".{pdf_path.stem}.html"
    tmp.write_text(html_text, encoding="utf-8")
    page = browser.new_page()
    page.goto(tmp.as_uri())
    page.wait_for_load_state("networkidle")
    footer = (f'<div style="font-size:7.5pt;width:100%;padding:0 18mm;color:#555;display:flex;justify-content:space-between;'
              f'font-family:Arial"><span>{html.escape(meta["title"])} - {html.escape(meta.get("subtitle", ""))} - '
              f'{html.escape(vlabel(meta))}</span>'
              '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
    page.pdf(path=str(pdf_path), format="A4", print_background=True, display_header_footer=True,
             header_template="<div></div>", footer_template=footer,
             margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"},
             outline=True, tagged=True)
    page.close()
    tmp.unlink()


def toc_pages_from_pdf(pdf_path, heads):
    """Map TOC entry index -> page number using the PDF outline (bookmarks)."""
    outline = [(lvl, title.strip(), pg) for lvl, title, pg in pymupdf.open(pdf_path).get_toc()]
    wanted = [(lvl, text) for lvl, text, _ in heads if lvl <= 2]
    pages, j = {}, 0
    for n, (lvl, text) in enumerate(wanted):
        while j < len(outline) and outline[j][1] != text.strip():
            j += 1
        if j < len(outline):
            pages[n] = outline[j][2]
            j += 1
    return pages


# =============================================================================
# DOCX
# =============================================================================

def set_cell_shading(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_field(paragraph, instr, placeholder=""):
    run = paragraph.add_run()
    for kind, text in (("begin", None), ("instr", instr), ("separate", None), ("text", placeholder), ("end", None)):
        if kind == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
            run._r.append(el)
        elif kind == "text":
            t = OxmlElement("w:t")
            t.text = text
            run._r.append(t)
        else:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
            run._r.append(el)
    return run


_BM = [0]


def add_bookmark(paragraph, name):
    _BM[0] += 1
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(_BM[0]))
    start.set(qn("w:name"), name[:40])
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(_BM[0]))
    ppr = paragraph._p.pPr
    paragraph._p.insert(1 if ppr is not None else 0, start)
    paragraph._p.append(end)


def add_internal_link(paragraph, text, anchor, bold=False, italic=False):
    link = OxmlElement("w:hyperlink")
    link.set(qn("w:anchor"), anchor[:40])
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1F4E9A")
    rpr.append(color)
    if bold:
        rpr.append(OxmlElement("w:b"))
    if italic:
        rpr.append(OxmlElement("w:i"))
    r.append(rpr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    link.append(r)
    paragraph._p.append(link)


def add_inline(paragraph, children, size=None, color=None, base_bold=False):
    bold = base_bold
    italic = False
    link = None
    for c in children or []:
        if c.type == "strong_open":
            bold = True
        elif c.type == "strong_close":
            bold = base_bold
        elif c.type == "em_open":
            italic = True
        elif c.type == "em_close":
            italic = False
        elif c.type == "link_open":
            link = c.attrs.get("href", "")
        elif c.type == "link_close":
            link = None
        elif c.type in ("softbreak",):
            paragraph.add_run(" ")
        elif c.type == "hardbreak" or (c.type == "html_inline" and c.content.lower().startswith("<br")):
            paragraph.add_run().add_break()
        elif c.type in ("text", "code_inline"):
            c.content = re.sub(r"\b(?:(?:UT|IT|SYS)_)?N?[A-Z]{1,3}-\d+(?:_\d+)?\b",
                               lambda m: m.group(0).replace("-", "\u2011"), c.content)
            if link and link.startswith("#"):
                add_internal_link(paragraph, c.content, link[1:], bold, italic)
                continue
            run = paragraph.add_run(c.content)
            run.bold = bold or None
            run.italic = italic or None
            if c.type == "code_inline":
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
            elif size:
                run.font.size = size
            if color:
                run.font.color.rgb = color


def column_widths(rows, total_cm):
    lens = []
    for col in range(len(rows[0])):
        cells = [len(r[col]) for r in rows if col < len(r)]
        longest_word = max((len(w) for r in rows if col < len(r) for w in r[col].split()), default=4)
        lens.append(max(min(max(cells), 60), longest_word * 0.9, 4))
    s = sum(lens)
    return [total_cm * l / s for l in lens]


def build_docx(meta, md_text, anchors, out_path):
    tokens = MD.parse(md_text)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.0))
    sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(2.0)
    usable = 17.0

    st = doc.styles
    st["Normal"].font.name = "Arial"
    st["Normal"].font.size = Pt(10)
    st["Normal"].paragraph_format.space_after = Pt(5)
    for lvl, size in ((1, 16), (2, 13), (3, 11), (4, 10)):
        h = st[f"Heading {lvl}"]
        h.font.name = "Arial"
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = RGBColor.from_string(ACCENT)
        h.paragraph_format.space_before = Pt(14 if lvl < 3 else 10)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        rpr = h.element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.append(fonts)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(a), "Arial")
    st["Heading 1"].paragraph_format.page_break_before = True
    cap = st["Caption"]
    cap.font.name = "Arial"
    cap.font.size = Pt(9)
    cap.font.bold = True
    cap.font.italic = False
    cap.font.color.rgb = RGBColor.from_string(ACCENT)

    # footer with page numbers; title page has a different (empty) first-page footer
    sec.different_first_page_header_footer = True
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run(f"{meta['title']} - {meta.get('subtitle', '')} - {vlabel(meta)}    Page ")
    r.font.size = Pt(8)
    add_field(fp, "PAGE", "1").font.size = Pt(8)
    fp.add_run(" of ").font.size = Pt(8)
    add_field(fp, "NUMPAGES", "1").font.size = Pt(8)

    # title page
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta["title"])
    r.bold, r.font.size, r.font.color.rgb = True, Pt(26), RGBColor.from_string(ACCENT)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta.get("subtitle", ""))
    r.font.size = Pt(16)
    doc.add_paragraph()
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k in ("Version", "Date", "Course", "Team", "Status"):
        if meta.get(k.lower()):
            cells = t.add_row().cells
            cells[0].width, cells[1].width = Cm(4), Cm(9)
            cells[0].paragraphs[0].add_run(k).bold = True
            cells[1].paragraphs[0].add_run(meta[k.lower()])
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    head_i = 0
    list_stack = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        typ = t.type
        if typ == "heading_open":
            lvl = int(t.tag[1])
            text = inline_text(tokens[i + 1])
            h = doc.add_heading(level=min(lvl, 4))
            add_inline(h, tokens[i + 1].children)
            add_bookmark(h, anchors[head_i])
            head_i += 1
            i += 3
            continue
        if typ in ("bullet_list_open", "ordered_list_open"):
            list_stack.append("bullet" if typ.startswith("bullet") else "number")
        elif typ in ("bullet_list_close", "ordered_list_close"):
            list_stack.pop()
        elif typ == "paragraph_open":
            inl = tokens[i + 1]
            text = inline_text(inl)
            if text.strip() == "[[TOC]]":
                h = doc.add_paragraph()
                r = h.add_run("Table of Contents")
                r.bold, r.font.size, r.font.color.rgb = True, Pt(14), RGBColor.from_string(ACCENT)
                p = doc.add_paragraph()
                add_field(p, 'TOC \\o "1-2" \\h \\z \\u',
                          "Right-click and choose Update Field (or press F9) to build the table of contents.")
                doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            elif inl.children and len(inl.children) == 1 and inl.children[0].type == "image":
                img = inl.children[0]
                src = (SRC / img.attrs["src"]).resolve()
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.keep_with_next = True
                p.add_run().add_picture(str(src), width=Cm(min(usable, 16.5)))
                c = doc.add_paragraph(img.content or inline_text(img), style="Caption")
                c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif list_stack:
                level = len(list_stack)
                style = ("List Bullet" if list_stack[-1] == "bullet" else "List Number") + (f" {level}" if level > 1 else "")
                p = doc.add_paragraph(style=style)
                add_inline(p, inl.children)
            elif re.match(r"Table \d+:", text):
                p = doc.add_paragraph(style="Caption")
                p.paragraph_format.keep_with_next = True
                add_inline(p, inl.children)
            else:
                p = doc.add_paragraph()
                add_inline(p, inl.children)
            i += 3
            continue
        elif typ == "blockquote_open":
            j = i + 1
            while tokens[j].type != "blockquote_close":
                if tokens[j].type == "inline":
                    p = doc.add_paragraph()
                    pPr = p._p.get_or_add_pPr()
                    bdr = OxmlElement("w:pBdr")
                    left = OxmlElement("w:left")
                    for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "6"), ("w:color", ACCENT)):
                        left.set(qn(k), v)
                    bdr.append(left)
                    pPr.append(bdr)                      # before ind, which python-docx inserts in order
                    p.paragraph_format.left_indent = Cm(0.6)
                    add_inline(p, tokens[j].children)
                j += 1
            i = j + 1
            continue
        elif typ in ("fence", "code_block"):
            for line in t.content.rstrip("\n").split("\n"):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.left_indent = Cm(0.4)
                r = p.add_run(line)
                r.font.name, r.font.size = "Consolas", Pt(8.5)
            doc.add_paragraph()
        elif typ == "html_block" and "pagebreak" in t.content:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        elif typ == "table_open":
            rows, j, cur = [], i + 1, None
            while tokens[j].type != "table_close":
                tt = tokens[j]
                if tt.type == "tr_open":
                    cur = []
                elif tt.type == "tr_close":
                    rows.append(cur)
                elif tt.type == "inline":
                    cur.append(tt)
                j += 1
            ncol = max(len(r) for r in rows)
            is_record = [inline_text(c) for c in rows[0]] == ["Field", "Details"]
            widths = column_widths([[inline_text(c) for c in r] for r in rows], usable)
            table = doc.add_table(rows=len(rows), cols=ncol)
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            for ri, row in enumerate(rows):
                tr = table.rows[ri]
                if ri == 0:
                    trPr = tr._tr.get_or_add_trPr()
                    th = OxmlElement("w:tblHeader")
                    th.set(qn("w:val"), "true")
                    trPr.append(th)
                cant = OxmlElement("w:cantSplit")
                tr._tr.get_or_add_trPr().append(cant)
                for ci in range(ncol):
                    cell = tr.cells[ci]
                    cell.width = Cm(widths[ci])
                    para = cell.paragraphs[0]
                    para.paragraph_format.space_after = Pt(0)
                    if ci < len(row):
                        add_inline(para, row[ci].children, size=Pt(8),
                                   color=RGBColor(255, 255, 255) if ri == 0 else None, base_bold=(ri == 0))
                    if is_record and ri < len(rows) - 1:
                        para.paragraph_format.keep_with_next = True   # keep a test record on one page
                    if ri == 0:
                        set_cell_shading(cell, ACCENT)
                    elif ri % 2 == 0:
                        set_cell_shading(cell, "F2F5F9")
            # grid widths too (Word honours tblGrid)
            grid = table._tbl.tblGrid
            for ci, gc in enumerate(grid.findall(qn("w:gridCol"))):
                gc.set(qn("w:w"), str(int(widths[ci] * 567)))
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
            i = j + 1
            continue
        i += 1

    # ask Word to refresh the TOC and page fields on open
    settings = doc.settings.element
    zoom = settings.find(qn("w:zoom"))
    if zoom is not None and zoom.get(qn("w:percent")) is None:
        zoom.set(qn("w:percent"), "100")
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    later = {"hdrShapeDefaults", "footnotePr", "endnotePr", "compat", "docVars", "rsids", "mathPr", "attachedSchema",
             "themeFontLang", "clrSchemeMapping", "doNotIncludeSubdocsInStats", "doNotAutoCompressPictures",
             "forceUpgrade", "captions", "readModeInkLockDown", "smartTagType", "schemaLibrary", "shapeDefaults",
             "doNotEmbedSmartTags", "decimalSymbol", "listSeparator"}
    anchor = next((el for el in settings if el.tag.split("}")[-1] in later), None)
    if anchor is not None:
        anchor.addprevious(upd)
    else:
        settings.append(upd)
    doc.core_properties.title = f"{meta['title']} - {meta.get('subtitle', '')}"
    doc.core_properties.author = meta.get("team", "")
    doc.core_properties.subject = meta.get("course", "")
    doc.save(out_path)


# =============================================================================
# Main
# =============================================================================

def report_specs():
    """Generated Deliverable 3 reports rendered to DOCX and PDF next to their Markdown."""
    cat, tcd = _catalog()
    team = "Sumukh, Jagadeesh, Tharith"
    course = "Software Engineering - Deliverable 3"
    specs = [
        (ROOT / "docs/Test_Case_Document.md", ROOT / "docs/Test_Case_Document",
         {"title": "Test Case Document", "subtitle": "Attendance Management System", "version": tcd.VERSION,
          "date": tcd.DOC_DATE, "course": course, "team": team,
          "status": f"{len(cat.CASES)} test cases with recorded results"}),
        (ROOT / "docs/System_Validation_Report.md", ROOT / "docs/System_Validation_Report",
         {"title": "System Validation Report", "subtitle": "Attendance Management System", "version": "Deliverable 3, Phase 3",
          "date": cat.MANUAL_META["run_date"], "course": course, "team": team,
          "status": "Automated and manual validation results recorded"}),
    ]
    for t in tcd.TESTERS:
        specs.append((ROOT / f"docs/manual_validation/{t}_Checklist.md", ROOT / f"docs/manual_validation/{t}_Checklist",
                      {"title": f"Manual Validation Checklist - {t}", "subtitle": "Attendance Management System",
                       "version": "Deliverable 3", "date": cat.MANUAL_META["run_date"], "course": course,
                       "team": f"Assigned team member: {t}", "status": "Executed; results recorded"}))
    return specs


def build_one(browser, meta, md_text, anchors, pdf, docx_path):
    html_text, heads = build_html(meta, md_text, anchors)
    render_pdf(html_text, pdf, meta, browser)                    # pass 1: find pages
    pages = toc_pages_from_pdf(pdf, heads)
    html_text, _ = build_html(meta, md_text, anchors, pages)
    render_pdf(html_text, pdf, meta, browser)                    # pass 2: final
    stable = toc_pages_from_pdf(pdf, heads) == pages
    build_docx(meta, md_text, anchors, docx_path)
    print(f"{pdf.relative_to(ROOT)}: {pymupdf.open(pdf).page_count} PDF pages, {len(heads)} headings, "
          f"TOC pages stable: {stable}; {docx_path.relative_to(ROOT)}")


def main(names):
    from playwright.sync_api import sync_playwright
    want_reports = not names or "reports" in names
    names = [n for n in names if n != "reports"] or ([] if "reports" in sys.argv[1:] else NAMES)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:  # noqa: BLE001
            browser = p.chromium.launch()
        for name in names:
            meta, md_text, anchors = parse_source(SRC / f"{name}.md")
            build_one(browser, meta, md_text, anchors, DOCS / f"{name}.pdf", DOCS / f"{name}.docx")
        if want_reports:
            for md_path, base, meta in report_specs():
                _, md_text, anchors = parse_source(md_path, report=True)
                build_one(browser, meta, md_text, anchors, base.with_suffix(".pdf"), base.with_suffix(".docx"))
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1:])
