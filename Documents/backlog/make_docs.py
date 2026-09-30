import csv
from collections import defaultdict
from backlog_data import *

ep = {e[0]: e for e in EPICS}
tot = defaultdict(int); cnt = defaultdict(int)
for s in STORIES: tot[s[7]] += s[5]; cnt[s[7]] += 1
total = sum(tot.values())

with open("product_backlog.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ID","Epic","Title","Requirement","Use case","Priority","Story points","Sprint","User story","Acceptance criteria"])
    for sid, eid, t, story, crit, pts, prio, sp, req, uc in STORIES:
        w.writerow([sid, f"{eid} {ep[eid][1]}", t, req, uc, prio, pts, SPRINTS[sp]["title"], story, " | ".join(crit)])

L = []
L.append("# Product Backlog – Attendance Management System (GitHub)\n")
L.append("The backlog is managed in GitHub: **Issues** for epics and user stories, **labels** for priority / story points / epic, **milestones** as sprints, and a **Project board** for status.\n")
L.append("## 1. Epics\n")
L.append("| Epic | Name | Requirements | Stories | Points |\n|---|---|---|---|---|")
for eid, name, _, reqs in EPICS:
    ss = [s for s in STORIES if s[1] == eid]
    L.append(f"| {eid} | {name} | {reqs} | {len(ss)} | {sum(s[5] for s in ss)} |")
L.append(f"| | **Total** | | **{len(STORIES)}** | **{total}** |\n")
L.append("## 2. Product backlog (prioritised by sprint)\n")
L.append("| ID | Epic | User story | Req | Priority | Points | Sprint |\n|---|---|---|---|---|---|---|")
for sid, eid, t, story, crit, pts, prio, sp, req, uc in sorted(STORIES, key=lambda s: (s[7], {"High":0,"Medium":1,"Low":2}[s[6]], s[0])):
    L.append(f"| {sid} | {eid} | {t} | {req} | {prio} | {pts} | {SPRINTS[sp]['title']} |")
L.append("\n## 3. Sprint plan\n")
L.append("| Sprint | Due | Goal | Stories | Points |\n|---|---|---|---|---|")
for n, s in SPRINTS.items():
    L.append(f"| {s['title']} | {s['due'][:10]} | {s['goal']} | {cnt[n]} | {tot[n]} |")
L.append("\nDue dates are placeholders; change them in `backlog_data.py` before running the script if your sprint dates differ.\n")
L.append("## 4. Planned burndown (ideal line, story points remaining)\n")
L.append("| Start | After Sprint 1 | After Sprint 2 | After Sprint 3 |\n|---|---|---|---|")
r1 = total - tot[1]; r2 = r1 - tot[2]; r3 = r2 - tot[3]
L.append(f"| {total} | {r1} | {r2} | {r3} |\n")
L.append("## 5. How the backlog is organised in GitHub\n")
L.append("""- **Epics** are issues labelled `epic` (title `[EPIC] E1: …`). Each epic holds a checklist of its stories, so GitHub shows progress on it.
- **User stories** are issues labelled `user-story`. Each has `priority: high|medium|low`, `SP-n` (story points) and `epic: En` labels, plus a **milestone** (the sprint).
- **Sprints** are milestones (Sprint 1–3); the milestone page shows % complete.
- **Project board** columns: `Backlog → Ready → In Progress → In Review → Done`. Every issue starts in Backlog; stories of the current sprint move to Ready.
- **Definition of Done** (in every story): code reviewed and merged, acceptance criteria tested, documentation updated.
- **Prioritisation rule:** High-priority stories first. Medium stories US-19 and US-20 are pulled into Sprint 1 because marking attendance depends on classes and enrolment.""")
open("BACKLOG.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("docs written", total, dict(tot))
