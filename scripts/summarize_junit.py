"""Summarise a pytest JUnit XML file (counts, failures, errors, skips).

Usage:
    python scripts/summarize_junit.py docs/evidence/<run>/junit.xml

Prints a Markdown summary. Counts come only from the XML file.
"""

import sys
import xml.etree.ElementTree as ET
from collections import Counter


def outcome(case):
    for tag in ("failure", "error", "skipped"):
        node = case.find(tag)
        if node is not None:
            return tag, (node.get("message") or "").strip().splitlines()[0][:200] if node.get("message") else ""
    return "passed", ""


def main(path):
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    cases = suite.findall("testcase")
    results = [(c.get("classname"), c.get("name"), *outcome(c)) for c in cases]
    counts = Counter(r[2] for r in results)
    by_file = Counter()
    for cls, _name, res, _msg in results:
        by_file[(cls, res)] += 1

    print(f"# JUnit summary: `{path}`\n")
    print(f"- Timestamp (from XML): {suite.get('timestamp')}")
    print(f"- Host: {suite.get('hostname')}")
    print(f"- pytest-reported time: {float(suite.get('time', 0)):.2f} s")
    print(f"- Test results recorded: {len(cases)}")
    print("- Outcomes: " + ", ".join(
        f"{k} {counts.get(k, 0)}" for k in ("passed", "failure", "error", "skipped")))
    print("\n## Per file\n")
    print("| File | Passed | Failed | Error | Skipped |")
    print("|---|---|---|---|---|")
    files = sorted({f for f, _ in by_file})
    for f in files:
        print(f"| {f} | " + " | ".join(str(by_file[(f, k)]) for k in ("passed", "failure", "error", "skipped")) + " |")
    bad = [r for r in results if r[2] != "passed"]
    if bad:
        print("\n## Not passed\n")
        print("| Test | Outcome | Message |")
        print("|---|---|---|")
        for cls, name, res, msg in bad:
            print(f"| {cls}::{name} | {res} | {msg.replace('|', '/')} |")


if __name__ == "__main__":
    main(sys.argv[1])
