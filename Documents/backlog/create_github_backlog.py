#!/usr/bin/env python3
"""
Creates the product backlog in GitHub: labels, sprint milestones, epic issues,
user-story issues (linked to epics, with points/priority/sprint) and, optionally,
a GitHub Project board.

Usage:
    gh auth login                              # once
    gh auth refresh -s project                 # once, only if you want --project
    python create_github_backlog.py --repo OWNER/REPO --dry-run     # preview
    python create_github_backlog.py --repo OWNER/REPO --project     # create for real

Run it ONCE per repository (running twice creates duplicate issues).
"""
import argparse, json, shutil, subprocess, sys
from backlog_data import *

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True, help="OWNER/REPO where issues are created")
ap.add_argument("--project", action="store_true", help="also create a GitHub Project board and add all issues")
ap.add_argument("--owner", help="project owner (default: repo owner)")
ap.add_argument("--force", action="store_true", help="create even if epics already exist")
ap.add_argument("--dry-run", action="store_true", help="print what would happen, change nothing")
args = ap.parse_args()
OWNER = args.owner or args.repo.split("/")[0]

if not args.dry_run and not shutil.which("gh"):
    sys.exit("GitHub CLI 'gh' not found. Install it from https://cli.github.com and run 'gh auth login'.")

_fake = {"n": 0}
def gh(cmd, stdin=None, check=True):
    """Run a gh command (list of args). In dry-run, just print it."""
    if args.dry_run:
        print("  $ gh " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
        _fake["n"] += 1
        return f"https://github.com/{args.repo}/issues/{_fake['n']}"
    r = subprocess.run(["gh"] + cmd, input=stdin, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0 and check:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()

def issue_number(url): return int(url.rstrip("/").split("/")[-1])


# ------------------------------------------------ safety: do not create the backlog twice
if not args.dry_run and not args.force:
    existing = gh(["issue", "list", "--repo", args.repo, "--label", "epic", "--state", "all", "--json", "number", "--limit", "1"], check=False)
    if existing and existing.strip() not in ("", "[]"):
        sys.exit("This repo already has epic issues, so the backlog was probably created already. Use --force to create it again.")

# ------------------------------------------------ labels
print("\n[1/5] Labels")
labels = [("epic", "3E4B9E", "Large body of work grouping user stories"),
          ("user-story", "1D76DB", "A user story in the product backlog")]
labels += [(f"priority: {p.lower()}", c, f"{p} priority") for p, c in PRIORITY_COLORS.items()]
labels += [(f"SP-{p}", "EDEDED", f"{p} story points") for p in POINTS]
labels += [(f"epic: {e[0]}", e[2], e[1]) for e in EPICS]
for name, color, desc in labels:
    try: gh(["label", "create", name, "--repo", args.repo, "--color", color, "--description", desc, "--force"])
    except RuntimeError as ex: print("  ! label", name, "->", ex)

# ------------------------------------------------ milestones = sprints
print("\n[2/5] Sprint milestones")
for n, s in SPRINTS.items():
    try:
        gh(["api", f"repos/{args.repo}/milestones", "-f", f"title={s['title']}", "-f", f"description={s['goal']}",
            "-f", f"due_on={s['due']}", "-f", "state=open"])
    except RuntimeError as ex: print("  ! milestone", s["title"], "->", ex)

# ------------------------------------------------ epics
print("\n[3/5] Epic issues")
epic_no, epic_url, epic_meta = {}, {}, {}
for eid, etitle, color, reqs in EPICS:
    body = (f"**Epic {eid}** covering requirements: {reqs}\n\n"
            "### User stories\n_(filled in automatically when the stories are created)_\n")
    url = gh(["issue", "create", "--repo", args.repo, "--title", f"[EPIC] {eid}: {etitle}",
              "--body-file", "-", "--label", "epic", "--label", f"epic: {eid}"], stdin=body)
    epic_no[eid], epic_url[eid], epic_meta[eid] = issue_number(url), url, (etitle, reqs)

# ------------------------------------------------ stories
print("\n[4/5] User-story issues")
story_by_epic = {e[0]: [] for e in EPICS}
story_urls = {}
for sid, eid, title, story, criteria, pts, prio, sprint, req, uc in STORIES:
    ctx = f"**Requirement:** {req}" + (f"  ·  **Use case:** {uc}" if uc else "")
    body = (f"**Epic:** {eid} – {epic_meta[eid][0]} (#{epic_no[eid]})\n{ctx}\n"
            f"**Priority:** {prio}  ·  **Story points:** {pts}  ·  **Sprint:** {SPRINTS[sprint]['title']}\n\n"
            f"### User story\n{story}\n\n### Acceptance criteria\n" +
            "\n".join(f"- [ ] {c}" for c in criteria) +
            "\n\n### Definition of Done\n- [ ] Code reviewed and merged\n- [ ] Tested (acceptance criteria met)\n- [ ] Documentation updated\n")
    url = gh(["issue", "create", "--repo", args.repo, "--title", f"{sid}: {title}", "--body-file", "-",
              "--label", "user-story", "--label", f"priority: {prio.lower()}", "--label", f"SP-{pts}",
              "--label", f"epic: {eid}", "--milestone", SPRINTS[sprint]["title"]], stdin=body)
    story_urls[sid] = url
    story_by_epic[eid].append((sid, title, issue_number(url), pts))

# link stories back into each epic as a checklist (GitHub shows progress on it)
for eid, items in story_by_epic.items():
    total = sum(p for *_, p in items)
    lines = "\n".join(f"- [ ] #{n} {sid}: {t} ({p} pts)" for sid, t, n, p in items)
    body = (f"**Epic {eid}** covering requirements: {epic_meta[eid][1]}\n\n**Total story points:** {total}\n\n"
            f"### User stories\n{lines}\n")
    gh(["issue", "edit", str(epic_no[eid]), "--repo", args.repo, "--body-file", "-"], stdin=body)

# ------------------------------------------------ project board (best effort)
print("\n[5/5] Project board")
if not args.project:
    print("  skipped (add --project to create it, or create it in the GitHub UI and add the issues)")
else:
    try:
        raw = gh(["project", "create", "--owner", OWNER, "--title", PROJECT_TITLE, "--format", "json"])
        proj = json.loads(raw) if not args.dry_run else {"number": 1, "id": "PVT_x", "url": "(dry-run)"}
        num, pid = str(proj["number"]), proj["id"]
        gh(["project", "link", num, "--owner", OWNER, "--repo", args.repo], check=False)
        fid = None
        try:
            f = gh(["project", "field-create", num, "--owner", OWNER, "--name", "Story Points",
                    "--data-type", "NUMBER", "--format", "json"])
            fid = json.loads(f)["id"] if not args.dry_run else "PVTF_x"
        except Exception as ex: print("  ! could not create Story Points field:", ex)
        allissues = [(f"[EPIC] {e[0]}", epic_url[e[0]], None) for e in EPICS] + \
                    [(s[0], story_urls[s[0]], s[5]) for s in STORIES]
        for label, url, pts in allissues:
            out = gh(["project", "item-add", num, "--owner", OWNER, "--url", url, "--format", "json"])
            if pts and fid and not args.dry_run:
                try:
                    gh(["project", "item-edit", "--id", json.loads(out)["id"], "--project-id", pid,
                        "--field-id", fid, "--number", str(pts)])
                except Exception as ex: print("  ! could not set points for", label, "->", ex)
        print("  Project board:", proj.get("url"))
    except Exception as ex:
        print("  ! Project step failed:", ex)
        print("    Run 'gh auth refresh -s project' and retry, or create the Project in the GitHub UI\n"
              "    (Projects tab -> New project -> Board) and use 'Add item' to add the issues.")

print("\nDone. Open https://github.com/%s/issues to see the backlog." % args.repo)
