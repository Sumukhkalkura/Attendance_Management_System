# Attendance Management System — Sprint 1 Starter

This is a **starter scaffold**, not a completed Attendance Management System.

## Local setup

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python run.py
```

Open http://127.0.0.1:5000/ and http://127.0.0.1:5000/api/health.

## Architecture

- `app/routes.py`: REST API and business-feature entry points
- `app/db.py`: SQLite data layer
- `app/__init__.py`: Flask application factory
- `tests/test_foundation.py`: implemented scaffold checks
- `tests/test_sprint1_requirements.py`: **skipped** requirements checklist; implement tests with each feature
- `.github/workflows/tests.yml`: run pytest on pushes and pull requests

## Important limitations

Authentication, authorization, session handling, admin workflows, attendance operations,
percentages, backups and production HTTPS are **not yet implemented**. Placeholder routes
return HTTP 501. The sample schema uses a placeholder password hash in one database test;
never use this pattern for real user passwords. Before deployment, replace the development
secret, add proper password hashing, secure session handling, HTTPS, and authorization.

## Suggested feature branches

`feature/fr01-auth`, `feature/fr07-users`, `feature/fr08-classes`,
`feature/fr09-enrollment`, `feature/fr15-logout`, `feature/fr02-marking`,
`feature/fr03-records`, `feature/fr04-percentage`, `feature/fr05-viewing`,
`feature/nfr01-security`, `feature/nfr03-reliability`.

Run tests and review pull requests before merging. Skipped tests do not count as passing acceptance tests.

## FR-06: Attendance Reporting API

The system provides flexible attendance reporting based on student, class, subject, or selected date range with summary statistics (total records, present/absent/late counts, and percentage).

### Endpoints

- `GET /api/reports/attendance` (canonical reporting endpoint)
- `GET /api/reports/attendance/student/<int:student_id>`
- `GET /api/reports/attendance/class/<int:class_id>`
- `GET /api/reports/attendance/subject/<int:subject_id>`
- Aliases: `GET /api/attendance/report`, `GET /api/attendance/reports`

### Query Parameters

| Parameter | Type | Description |
|---|---|---|
| `student_id` | integer | Filter by student ID (validated against existing students; students can only view own records) |
| `class_id` | integer | Filter by class ID (validated against existing classes; returns records associated with the class) |
| `subject_id` | integer | Filter by subject ID (validated against existing subjects; teachers can only access assigned subjects) |
| `start_date` (or `from_date`) | string (YYYY-MM-DD) | Start date for inclusive date-range filtering |
| `end_date` (or `to_date`) | string (YYYY-MM-DD) | End date for inclusive date-range filtering |
| `status` | string | Optional filter by status (`Present`, `Absent`, or `Late`) |

### Date Range Boundary Convention

Date filtering is inclusive: records where `start_date <= attendance_date <= end_date` are included.
- If only `start_date` is provided, all records on or after `start_date` are included.
- If only `end_date` is provided, all records on or before `end_date` are included.
- If both are provided, `start_date` must not be later than `end_date`.

### Sample Request

```http
GET /api/reports/attendance?student_id=4&class_id=1&start_date=2026-10-01&end_date=2026-10-31
```

### Sample Response (HTTP 200 OK)

```json
{
  "report_type": "attendance_report",
  "filters": {
    "student_id": 4,
    "class_id": 1,
    "subject_id": null,
    "start_date": "2026-10-01",
    "end_date": "2026-10-31",
    "status": null
  },
  "summary": {
    "total_records": 4,
    "present_count": 3,
    "absent_count": 1,
    "late_count": 0,
    "attendance_percentage": 75.0
  },
  "count": 4,
  "total_records": 4,
  "present_count": 3,
  "absent_count": 1,
  "late_count": 0,
  "attendance_percentage": 75.0,
  "student": {
    "id": 4,
    "name": "student1",
    "username": "student1"
  },
  "class": {
    "id": 1,
    "name": "Class 10-A"
  },
  "records": [
    {
      "id": 1,
      "attendance_id": 1,
      "student_id": 4,
      "student_name": "student1",
      "student_username": "student1",
      "class_id": 1,
      "class_name": "Class 10-A",
      "subject_id": 2,
      "subject_name": "Mathematics",
      "attendance_date": "2026-10-25",
      "date": "2026-10-25",
      "status": "Present"
    }
  ]
}
```

### Running Tests

```bash
# Run FR-06 specific tests:
python -m pytest tests/test_fr06_attendance_reporting.py -v

# Run the complete test suite:
python -m pytest
```
