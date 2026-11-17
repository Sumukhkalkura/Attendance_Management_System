"""Classify every collected test result as unit, integration, browser or static.

Used for docs/Unit_Test_Report.md (Deliverable 3). Classification is derived
from the test source, not from test names:

* browser      - drives a real browser through Playwright (NFR-05 / NFR-02
                 browser files).
* integration  - sends requests through the Flask test client (directly or via
                 a local helper/fixture), so routing, authentication, the API
                 handler and a temporary SQLite database run together; also
                 tests that build the app and then exercise its SQLite schema.
* static       - structural checks: inspects source files, the AST, the import
                 graph or the application's URL map without sending a request
                 (all non-HTTP NFR-06 maintainability checks are in this group).
* unit         - calls a single function or module directly, with no Flask
                 application, HTTP request or browser.

Usage: python scripts/classify_tests.py docs/evidence/final/junit.xml
Prints a Markdown table per file and writes nothing.
"""

import ast
import collections
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "tests"
BROWSER_FILES = {"test_nfr05_browser_compatibility", "test_nfr02_browser_performance"}
# Names that mean the code sends a request through the Flask test client.
HTTP_MARKERS = {"client", "test_client"}
# Names that mean the code builds or inspects the application object.
APP_MARKERS = {"create_app", "app", "application", "url_map"}


def names_in(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.arg):
            out.add(n.arg)
    return out


def _closure(funcs, seeds, markers):
    """Local helpers/fixtures that (transitively) use any of `markers`."""
    found = set(seeds)
    changed = True
    while changed:
        changed = False
        for name, fn in funcs.items():
            if name not in found and names_in(fn) & (markers | found):
                found.add(name)
                changed = True
    return found


def file_classes(path):
    tree = ast.parse(path.read_text())
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    http = _closure({k: v for k, v in funcs.items() if not k.startswith("test")}, {"client"}, HTTP_MARKERS)
    result = {}
    for name, fn in funcs.items():
        if not name.startswith("test"):
            continue
        used = names_in(fn)
        if path.stem in BROWSER_FILES:
            kind = "browser"
        elif used & (http | HTTP_MARKERS) or (used & APP_MARKERS and "execute" in used):
            kind = "integration"
        elif path.stem == "test_nfr06_maintainability" or used & APP_MARKERS or used & {
            "ast", "inspect", "read_text", "subprocess", "importlib", "rglob", "glob", "modules"
        }:
            kind = "static"
        else:
            kind = "unit"
        result[name] = kind
    return result


def main(junit):
    root = ET.parse(junit).getroot()
    cache = {}
    table = collections.defaultdict(collections.Counter)
    totals = collections.Counter()
    for tc in root.iter("testcase"):
        module = tc.get("classname").split(".")[-1]
        func = tc.get("name").split("[")[0]
        if module not in cache:
            cache[module] = file_classes(TESTS / f"{module}.py")
        kind = cache[module].get(func, "unknown")
        outcome = "passed"
        for child in tc:
            if child.tag in ("failure", "error", "skipped"):
                outcome = child.tag
        table[(module, kind)][outcome] += 1
        totals[(kind, outcome)] += 1
    print("| Test file | Type | Results | Passed | Failed | Errors | Skipped |")
    print("|---|---|---|---|---|---|---|")
    for (module, kind), c in sorted(table.items()):
        print(f"| {module}.py | {kind} | {sum(c.values())} | {c['passed']} | {c['failure']} | {c['error']} | {c['skipped']} |")
    print()
    print("| Type | Results | Passed | Failed | Errors | Skipped |")
    print("|---|---|---|---|---|---|")
    for kind in ("unit", "integration", "browser", "static", "unknown"):
        c = {o: totals[(kind, o)] for o in ("passed", "failure", "error", "skipped")}
        n = sum(c.values())
        if n:
            print(f"| {kind} | {n} | {c['passed']} | {c['failure']} | {c['error']} | {c['skipped']} |")
    n_all = sum(totals.values())
    print(f"| **total** | **{n_all}** | | | | |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/evidence/final/junit.xml")
