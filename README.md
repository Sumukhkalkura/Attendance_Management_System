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


## FR-11: Attendance Alert API

The Attendance Alert system identifies students whose attendance percentage falls strictly below a specified attendance threshold. It enables teachers and administrators to proactively track students who require attendance intervention.

### Acceptance Criteria

1. **Threshold Specification:** An attendance threshold can be specified via application configuration, runtime API, or dynamic request parameters (defaulting to 75.0%).
2. **Student Identification:** The system calculates attendance percentages using the established data model and accurately identifies students whose percentage is strictly below the threshold (`percentage < threshold`).
3. **Clear Indication:** Students below the threshold are clearly distinguished with explicit alert flags (`below_threshold: true`, `is_alert: true`, `alert_status: "BELOW_THRESHOLD"`), and prioritized by lowest percentage first.

### Attendance Percentage Formula

The calculation strictly reuses the FR-04 attendance data model:

$$\\text{Attendance Percentage} = \\left(\\frac{\\text{Present Attendance}}{\\text{Total Eligible Attendance}}\\right) \\times 100$$

- **Eligible Attendance:** Total records with status `Present`, `Absent`, or `Late`.
- **Present Attendance:** Records with status `Present`.
- **Late Policy:** Consistent with FR-04, records marked `Late` count toward total eligible classes conducted, but do not count toward present attendance.
- **Zero Eligible Attendance:** If a student has zero attendance records (`total_classes == 0`), the percentage evaluates safely to `0.0%` without division-by-zero errors. By default, untracked students without attendance are not flagged as false-positive alerts (`alert_status: "NO_RECORDS"`).
- **Strict Inequality:** A student must be strictly below the threshold. A student with 75.0% attendance when the threshold is 75.0% is not flagged as an alert; a student with 74.99% is flagged.

### Threshold Configuration

The attendance alert threshold can be configured at multiple levels:
- **Application Default:** Configured via `DEFAULT_ATTENDANCE_THRESHOLD` in Flask application settings (default: `75.0%`).
- **Dynamic Request Parameter:** Overridden on any alert query using the `threshold` parameter (e.g., `?threshold=80`).
- **Threshold API:** Retrieved by authenticated users and updated dynamically by administrators (`admin` role only):
  - `GET /api/attendance/threshold`: Returns current persisted threshold and system default.
  - `POST /api/attendance/threshold` or `PUT /api/attendance/threshold`: Admin-only endpoint that persists the global threshold in the database `settings` table (`{"threshold": 80.0}`). Non-admin users (e.g. teachers and students) receive `HTTP 403 Forbidden`, and unauthenticated requests receive `HTTP 401 Unauthorized`.
- **Database Persistence:** The global threshold is persisted in the SQLite `settings` table under key `attendance_threshold`, surviving server restarts and read upon application factory instantiation.

#### Threshold Validation Rules
- Accepted values: Numeric values (integers or floats) between `0.0` and `100.0` inclusive.
- Rejected values: Negative numbers (`< 0`), values greater than `100`, non-numeric strings, empty values, booleans, nulls, and malformed payloads return `HTTP 400 Bad Request`.

### Endpoints

- `GET /api/attendance/alerts` (canonical alerts endpoint)
- `GET /api/attendance/alerts/student/<int:student_id>`
- `GET /api/attendance/alerts/class/<int:class_id>`
- `GET /api/attendance/alerts/subject/<int:subject_id>`
- `POST /api/attendance/alerts` (supports JSON body parameter overrides)
- Aliases: `GET /api/attendance/alert`, `GET /api/alerts/attendance`
- Configuration: `GET /api/attendance/threshold`, `POST /api/attendance/threshold`, `PUT /api/attendance/threshold`

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `threshold` | float | `75.0` | Attendance threshold percentage (0.0 to 100.0) |
| `student_id` | integer | `None` | Filter alerts for a specific student (validated; students restricted to own ID) |
| `class_id` | integer | `None` | Filter alerts for students enrolled in a specific class |
| `subject_id` | integer | `None` | Filter alerts for a specific subject (teachers restricted to assigned subjects) |
| `only_alerts` | boolean | `false` | If true, returns only students below threshold in `students` list |
| `include_zero` | boolean | `false` | If true, treats students with 0 eligible classes as alerts |

### Sample Request

```http
GET /api/attendance/alerts?subject_id=2&threshold=75.0
```

### Sample Response (HTTP 200 OK)

```json
{
  "threshold": 75.0,
  "count": 1,
  "alerts_count": 1,
  "total_students": 3,
  "alerts": [
    {
      "student_id": 6,
      "student_name": "student3",
      "username": "student3",
      "classes_attended": 2,
      "total_classes": 4,
      "attendance_percentage": 50.0,
      "threshold": 75.0,
      "below_threshold": true,
      "is_alert": true,
      "alert_status": "BELOW_THRESHOLD"
    }
  ],
  "students": [
    {
      "student_id": 4,
      "student_name": "student1",
      "username": "student1",
      "classes_attended": 4,
      "total_classes": 4,
      "attendance_percentage": 100.0,
      "threshold": 75.0,
      "below_threshold": false,
      "is_alert": false,
      "alert_status": "NORMAL"
    },
    {
      "student_id": 5,
      "student_name": "student2",
      "username": "student2",
      "classes_attended": 3,
      "total_classes": 4,
      "attendance_percentage": 75.0,
      "threshold": 75.0,
      "below_threshold": false,
      "is_alert": false,
      "alert_status": "NORMAL"
    },
    {
      "student_id": 6,
      "student_name": "student3",
      "username": "student3",
      "classes_attended": 2,
      "total_classes": 4,
      "attendance_percentage": 50.0,
      "threshold": 75.0,
      "below_threshold": true,
      "is_alert": true,
      "alert_status": "BELOW_THRESHOLD"
    }
  ],
  "filters": {
    "threshold": 75.0,
    "student_id": null,
    "class_id": null,
    "subject_id": 2,
    "include_zero": false,
    "only_alerts": false
  },
  "subject": {
    "id": 2,
    "name": "Mathematics"
  }
}
```

### Running Tests

```bash
# Run FR-11 specific tests:
python -m pytest tests/test_fr11_attendance_alert.py -v

# Run the complete test suite:
python -m pytest
```
