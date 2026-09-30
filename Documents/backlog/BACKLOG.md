# Product Backlog – Attendance Management System (GitHub)

The backlog is managed in GitHub: **Issues** for epics and user stories, **labels** for priority / story points / epic, **milestones** as sprints, and a **Project board** for status.

## 1. Epics

| Epic | Name | Requirements | Stories | Points |
|---|---|---|---|---|
| E1 | Authentication & Access Control | FR-01, FR-13, FR-15, NFR-01 | 5 | 18 |
| E2 | Attendance Marking & Records | FR-02, FR-03 | 5 | 21 |
| E3 | Attendance Viewing & Search | FR-05, FR-10 | 3 | 11 |
| E4 | Percentage & Alerts | FR-04, FR-11 | 2 | 8 |
| E5 | Reporting | FR-06, FR-12 | 2 | 11 |
| E6 | Administration | FR-07, FR-08, FR-09 | 3 | 13 |
| E7 | Dashboard | FR-14 | 1 | 5 |
| E8 | Quality & Non-Functional | NFR-01 to NFR-06 | 5 | 13 |
| | **Total** | | **26** | **100** |

## 2. Product backlog (prioritised by sprint)

| ID | Epic | User story | Req | Priority | Points | Sprint |
|---|---|---|---|---|---|---|
| US-01 | E1 | Log in with role-based access | FR-01 | High | 5 | Sprint 1 |
| US-02 | E1 | Handle invalid credentials and locked accounts | FR-01 | High | 3 | Sprint 1 |
| US-06 | E2 | Select class, subject and date | FR-02 | High | 3 | Sprint 1 |
| US-07 | E2 | Mark Present, Absent or Late | FR-02 | High | 5 | Sprint 1 |
| US-08 | E2 | Save attendance records | FR-03 | High | 5 | Sprint 1 |
| US-09 | E2 | Prevent duplicate attendance and allow updates | FR-03 | High | 5 | Sprint 1 |
| US-19 | E6 | Manage classes and subjects | FR-08 | Medium | 5 | Sprint 1 |
| US-20 | E6 | Enroll students in classes and subjects | FR-09 | Medium | 3 | Sprint 1 |
| US-05 | E1 | Restrict pages and data by role | NFR-01 | High | 5 | Sprint 2 |
| US-11 | E3 | View my attendance as a student | FR-05 | High | 5 | Sprint 2 |
| US-12 | E3 | View class attendance as a teacher | FR-05 | High | 3 | Sprint 2 |
| US-14 | E4 | Calculate attendance percentage automatically | FR-04 | High | 5 | Sprint 2 |
| US-16 | E5 | Generate attendance reports | FR-06 | High | 8 | Sprint 2 |
| US-24 | E8 | Protect data in transit | NFR-01 | High | 2 | Sprint 2 |
| US-18 | E6 | Manage user accounts | FR-07 | Medium | 5 | Sprint 2 |
| US-22 | E8 | Pages load within 3 seconds | NFR-02 | High | 3 | Sprint 3 |
| US-23 | E8 | Back up attendance data regularly | NFR-03 | High | 3 | Sprint 3 |
| US-10 | E2 | Keep entered data when a save fails | NFR-03 | Medium | 3 | Sprint 3 |
| US-13 | E3 | Search and filter attendance records | FR-10 | Medium | 3 | Sprint 3 |
| US-15 | E4 | Alert on low attendance | FR-11 | Medium | 3 | Sprint 3 |
| US-17 | E5 | Export reports | FR-12 | Medium | 3 | Sprint 3 |
| US-25 | E8 | Consistent, easy-to-use interface | NFR-04 | Medium | 3 | Sprint 3 |
| US-26 | E8 | Work on modern browsers | NFR-05 | Medium | 2 | Sprint 3 |
| US-03 | E1 | Log out securely | FR-15 | Low | 2 | Sprint 3 |
| US-04 | E1 | Change my password | FR-13 | Low | 3 | Sprint 3 |
| US-21 | E7 | See a role-based dashboard summary | FR-14 | Low | 5 | Sprint 3 |

## 3. Sprint plan

| Sprint | Due | Goal | Stories | Points |
|---|---|---|---|---|
| Sprint 1 | 2026-10-14 | Foundation: login, class setup and core attendance marking | 8 | 34 |
| Sprint 2 | 2026-10-28 | Viewing, percentage calculation, reports and user administration | 7 | 33 |
| Sprint 3 | 2026-11-11 | Search, alerts, export, dashboard, security hardening and quality (NFRs) | 11 | 33 |

Due dates are placeholders; change them in `backlog_data.py` before running the script if your sprint dates differ.

## 4. Planned burndown (ideal line, story points remaining)

| Start | After Sprint 1 | After Sprint 2 | After Sprint 3 |
|---|---|---|---|
| 100 | 66 | 33 | 0 |

## 5. How the backlog is organised in GitHub

- **Epics** are issues labelled `epic` (title `[EPIC] E1: …`). Each epic holds a checklist of its stories, so GitHub shows progress on it.
- **User stories** are issues labelled `user-story`. Each has `priority: high|medium|low`, `SP-n` (story points) and `epic: En` labels, plus a **milestone** (the sprint).
- **Sprints** are milestones (Sprint 1–3); the milestone page shows % complete.
- **Project board** columns: `Backlog → Ready → In Progress → In Review → Done`. Every issue starts in Backlog; stories of the current sprint move to Ready.
- **Definition of Done** (in every story): code reviewed and merged, acceptance criteria tested, documentation updated.
- **Prioritisation rule:** High-priority stories first. Medium stories US-19 and US-20 are pulled into Sprint 1 because marking attendance depends on classes and enrolment.
