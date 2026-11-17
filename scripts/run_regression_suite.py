"""Regression run after fixing the six failed test cases (post Deliverable 3 testing).

Writes a complete, separate evidence set to docs/evidence/regression/ and never
touches the earlier runs (docs/evidence/baseline, final, coverage, phase3,
manual_validation_automation).

    python scripts/run_regression_suite.py

Steps: full pytest suite (default NFR-05 browsers chrome, edge, firefox);
NFR-05 browser runs in Playwright Chromium, WebKit and Firefox; the six-failure
browser regression tests in Chromium and WebKit; statement and branch coverage
(same commands and .coveragerc as Phase 3); the WebKit CSP probe. The real
attendance.db is fingerprinted before and after.
"""

import hashlib
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "regression"
PY = sys.executable


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "absent"


def run(label, args, out_file, env=None):
    start = datetime.now()
    e = dict(os.environ, **(env or {}))
    with open(out_file, "w") as fh:
        rc = subprocess.run(args, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=e).returncode
    secs = (datetime.now() - start).seconds
    line = f"{label}: exit={rc} wall={secs}s finished={datetime.now():%Y-%m-%d %H:%M:%S}"
    print(line, flush=True)
    return line


def coverage_only():
    """Repeat only the two coverage runs (same commands) and record them in coverage/run_info.txt."""
    log = []
    pytest = [PY, "-m", "pytest", "-p", "no:cacheprovider"]
    for kind, extra in (("statement", []), ("branch", ["--cov-branch"])):
        d = OUT / "coverage" / kind
        d.mkdir(parents=True, exist_ok=True)
        env = {"COVERAGE_FILE": str(d / ".coverage")}
        log.append(run(f"coverage {kind}", pytest + ["-q", "--cov", *extra, "--cov-config=.coveragerc", "--cov-report=",
                                                     f"--junitxml={d / 'junit.xml'}"], d / "pytest_output.txt", env))
        cov = [PY, "-m", "coverage"]
        for scope in ("app", "scripts"):
            subprocess.run(cov + ["json", "--rcfile=.coveragerc", f"--include={scope}/*", "-o", str(d / f"coverage_{scope}.json")],
                           cwd=ROOT, env=dict(os.environ, **env), capture_output=True)
            with open(d / f"coverage_report_{scope}.txt", "w") as fh:
                subprocess.run(cov + ["report", "-m", "--rcfile=.coveragerc", f"--include={scope}/*"],
                               cwd=ROOT, env=dict(os.environ, **env), stdout=fh, stderr=subprocess.STDOUT)
        subprocess.run(cov + ["xml", "--rcfile=.coveragerc", "-o", str(d / "coverage.xml")], cwd=ROOT,
                       env=dict(os.environ, **env), capture_output=True)
        (d / ".coverage").unlink(missing_ok=True)
    (OUT / "coverage" / "run_info.txt").write_text("\n".join(log) + "\n")


def main():
    if "--coverage-only" in sys.argv:
        return coverage_only()
    (OUT / "browsers").mkdir(parents=True, exist_ok=True)
    for kind in ("statement", "branch"):
        (OUT / "coverage" / kind).mkdir(parents=True, exist_ok=True)
    before = sha(ROOT / "attendance.db")
    log = [f"Regression run started {datetime.now():%Y-%m-%d %H:%M:%S} (local)"]
    pytest = [PY, "-m", "pytest", "-p", "no:cacheprovider"]

    log.append(run("full suite", pytest + ["-v", "-rA", "--durations=20", f"--junitxml={OUT / 'junit.xml'}"],
                   OUT / "pytest_output.txt"))
    for b in ("chromium", "webkit", "firefox"):
        log.append(run(f"NFR-05 {b}", pytest + ["-v", "-rA", "tests/test_nfr05_browser_compatibility.py",
                                                 f"--junitxml={OUT / 'browsers' / f'{b}_junit.xml'}"],
                       OUT / "browsers" / f"{b}_output.txt", {"NFR05_BROWSERS": b}))
    for b in ("chromium", "webkit"):
        log.append(run(f"six-failure browser tests {b}", pytest + ["-v", "-rA", "tests/test_six_failures_browser.py",
                                                                   f"--junitxml={OUT / 'browsers' / f'six_failures_{b}_junit.xml'}"],
                       OUT / "browsers" / f"six_failures_{b}_output.txt", {"REGRESSION_BROWSERS": b}))
    for kind, extra in (("statement", []), ("branch", ["--cov-branch"])):
        d = OUT / "coverage" / kind
        env = {"COVERAGE_FILE": str(d / ".coverage")}
        log.append(run(f"coverage {kind}", pytest + ["-q", "--cov", *extra, "--cov-config=.coveragerc", "--cov-report=",
                                                     f"--junitxml={d / 'junit.xml'}"], d / "pytest_output.txt", env))
        cov = [PY, "-m", "coverage"]
        for scope in ("app", "scripts"):
            subprocess.run(cov + ["json", "--rcfile=.coveragerc", f"--include={scope}/*", "-o", str(d / f"coverage_{scope}.json")],
                           cwd=ROOT, env=dict(os.environ, **env), capture_output=True)
            with open(d / f"coverage_report_{scope}.txt", "w") as fh:
                subprocess.run(cov + ["report", "-m", "--rcfile=.coveragerc", f"--include={scope}/*"],
                               cwd=ROOT, env=dict(os.environ, **env), stdout=fh, stderr=subprocess.STDOUT)
        subprocess.run(cov + ["xml", "--rcfile=.coveragerc", "-o", str(d / "coverage.xml")], cwd=ROOT,
                       env=dict(os.environ, **env), capture_output=True)
        (d / ".coverage").unlink(missing_ok=True)
    log.append(run("WebKit CSP probe", [PY, str(OUT / "browsers" / "webkit_csp_probe.py"), str(ROOT), "webkit,chromium"],
                   OUT / "browsers" / "webkit_csp_probe_output.txt"))

    after = sha(ROOT / "attendance.db")
    pkgs = subprocess.run([PY, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    keep = ("flask", "werkzeug", "jinja2", "pytest", "pytest-cov", "coverage", "playwright", "openpyxl")
    chrome = subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                            capture_output=True, text=True).stdout.strip() if Path("/Applications/Google Chrome.app").exists() else "not installed"
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    browsers = sorted(p.name for p in (Path.home() / "Library/Caches/ms-playwright").glob("*")) if sys.platform == "darwin" else []
    env_lines = [
        "Run: regression (after fixing SYS_FR-04_11, SYS_FR-05_10, SYS_FR-06_08, SYS_FR-10_10, SYS_FR-12_10, SYS_NFR-05_04)",
        f"Git branch: {branch}  HEAD: {head}  (uncommitted changes in app/, tests/, scripts/, docs/)",
        f"OS: {platform.platform()}", f"Python: {platform.python_version()}",
        *[l for l in pkgs.splitlines() if l.split("==")[0].lower() in keep],
        f"Playwright browsers: {' '.join(browsers)}",
        f"Google Chrome: {chrome}", "Microsoft Edge: not installed (installation not approved)",
        "Playwright upgraded 1.64.1 -> 1.65.2 for this run (approved): WebKit build r2370 -> r2388 (contains the upstream fix for the <select> CSP false positive)",
        f"attendance.db sha256 before: {before}", f"attendance.db sha256 after:  {after}  (unchanged: {before == after})",
        *log,
    ]
    (OUT / "environment.txt").write_text("\n".join(env_lines) + "\n")
    print("\n".join(env_lines[-len(log) - 2:]))


if __name__ == "__main__":
    main()
