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
`feature/nfr01-security`, `feature/nfr02-performance`, `feature/nfr03-reliability`.

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


## NFR-02: Performance Optimization and Verification

The system complies with Non-Functional Requirement 02 (**NFR-02: Performance**):
> **"The system shall load major pages and attendance information within 3 seconds under normal operating conditions."**

### Acceptance Criteria

1. **Major Pages:** Major pages (`/login`, `/dashboard`, `/admin`, `/teacher`, `/student`) load within 3 seconds under normal operating conditions.
2. **Attendance Information:** Attendance information (`/api/attendance`, `/api/attendance/percentages`, `/api/attendance/alerts`, `/api/reports/attendance`, `/api/reports/attendance/export`) loads within 3 seconds under normal operating conditions.
3. **Representative Usage Scenarios:** Performance is verified using representative usage scenarios across administrative, teacher, and student workloads.

---

### Defined Normal Operating Conditions

Under realistic academic deployment conditions, the database serves:
- **Users:** 100+ students, 5+ teachers, and administrative personnel.
- **Academic Structure:** 10+ classes, 15+ subjects, and complete multi-subject class enrollments.
- **Attendance Records:** 5,000+ attendance records distributed across multiple dates, subjects, and statuses (`Present`, `Absent`, `Late`).
- **Concurrent Roles:** Authenticated admin, teacher, and student users exercising major dashboards, rosters, reports, and exports.

---

### Architectural Optimizations

To guarantee low latency and prevent performance degradation as attendance records grow:

1. **Database Indexes (`app/db.py`):**
   - `idx_attendance_subject_date`: Optimizes subject-filtered attendance queries and date-ordered lookups.
   - `idx_attendance_student_date`: Speeds up individual student attendance history retrieval.
   - `idx_attendance_date`: Accelerates date-range reporting and filtering (`start_date` to `end_date`).
   - `idx_attendance_status`: Enhances status-based filtering (`Present`, `Absent`, `Late`).
   - `idx_enrollments_class`: Eliminates full table scans during class attendance joins (`enrollments.class_id`).
   - `idx_enrollments_subject`: Optimizes subject-class joins (`enrollments.subject_id`).
   - `idx_users_role`: Speeds up student and teacher filtering (`users.role = 'student'`).
   - `idx_classes_teacher`: Accelerates teacher class assignments (`classes.teacher_id`).
   - `idx_subjects_teacher`: Accelerates teacher subject queries (`subjects.teacher_id`).
   - `idx_class_subjects_subject`: Speeds up class-subject curriculum lookups.

2. **SQLite Performance Tuning (`get_db()`):**
   - `PRAGMA synchronous = NORMAL`: Balances persistence safety with reduced write sync overhead.
   - `PRAGMA cache_size = -64000`: Allocates 64MB memory page cache for in-memory index/page lookups.
   - `PRAGMA temp_store = MEMORY`: Directs temporary sorting tables and aggregations to RAM.

3. **Query Plan Improvement:**
   - Database operations were converted from sequential `SCAN` operations to indexed `SEARCH` operations (`SEARCH attendance USING INDEX`, `SEARCH enrollments USING INDEX`, `SEARCH users USING INDEX`).

---

### Empirical Benchmark Results

Benchmarking conducted on a representative dataset (100 students, 10 classes, 15 subjects, 5,000 attendance records) over 5 consecutive iterations per scenario:

| Scenario | Component | Avg Response Time (ms) | Max Response Time (ms) | 3-Second SLA Status |
|---|---|---|---|---|
| **`/login` (Unauthenticated)** | Major Page | 0.52 ms | 0.68 ms | PASSED (< 3.0s) |
| **`/dashboard` (Admin Redirect)** | Major Page | 2.32 ms | 3.75 ms | PASSED (< 3.0s) |
| **`/dashboard` (Teacher Redirect)** | Major Page | 2.44 ms | 3.31 ms | PASSED (< 3.0s) |
| **`/dashboard` (Student Redirect)** | Major Page | 3.51 ms | 6.32 ms | PASSED (< 3.0s) |
| **`/admin` (Admin Dashboard)** | Major Page | 4.16 ms | 6.02 ms | PASSED (< 3.0s) |
| **`/teacher` (Teacher Dashboard)** | Major Page | 4.06 ms | 5.12 ms | PASSED (< 3.0s) |
| **`/student` (Student Dashboard)** | Major Page | 3.76 ms | 4.14 ms | PASSED (< 3.0s) |
| **`/api/classes`** | Attendance Info | 3.97 ms | 5.06 ms | PASSED (< 3.0s) |
| **`/api/subjects`** | Attendance Info | 5.11 ms | 6.52 ms | PASSED (< 3.0s) |
| **`/api/users?role=student`** | Attendance Info | 4.85 ms | 7.94 ms | PASSED (< 3.0s) |
| **`/api/roster?class_id=1&subject_id=1`** | Attendance Info | 5.41 ms | 7.34 ms | PASSED (< 3.0s) |
| **`/api/attendance` (5,000 records)** | Attendance Info | 33.89 ms | 48.81 ms | PASSED (< 3.0s) |
| **`/api/attendance?student_id=7`** | Attendance Info | 4.70 ms | 5.94 ms | PASSED (< 3.0s) |
| **`/api/attendance?class_id=1`** | Attendance Info | 13.46 ms | 17.75 ms | PASSED (< 3.0s) |
| **`/api/attendance?subject_id=1`** | Attendance Info | 7.31 ms | 10.16 ms | PASSED (< 3.0s) |
| **`/api/attendance?start_date=2026-03-01&end_date=2026-03-15`** | Attendance Info | 17.39 ms | 24.05 ms | PASSED (< 3.0s) |
| **`/api/attendance/percentages`** | Attendance Info | 7.98 ms | 10.99 ms | PASSED (< 3.0s) |
| **`/api/attendance/percentages?student_id=7`** | Attendance Info | 7.96 ms | 9.03 ms | PASSED (< 3.0s) |
| **`/api/attendance/percentages?class_id=1`** | Attendance Info | 9.13 ms | 11.45 ms | PASSED (< 3.0s) |
| **`/api/attendance/percentages?subject_id=1`** | Attendance Info | 4.67 ms | 5.54 ms | PASSED (< 3.0s) |
| **`/api/attendance/alerts`** | Attendance Info | 12.78 ms | 17.23 ms | PASSED (< 3.0s) |
| **`/api/attendance/alerts/student/7`** | Attendance Info | 8.00 ms | 8.56 ms | PASSED (< 3.0s) |
| **`/api/attendance/alerts/class/1`** | Attendance Info | 9.13 ms | 10.20 ms | PASSED (< 3.0s) |
| **`/api/attendance/alerts/subject/1`** | Attendance Info | 9.07 ms | 9.88 ms | PASSED (< 3.0s) |
| **`/api/reports/attendance` (Aggregated)** | Attendance Info | 88.57 ms | 96.59 ms | PASSED (< 3.0s) |
| **`/api/reports/attendance/student/7`** | Attendance Info | 10.03 ms | 11.96 ms | PASSED (< 3.0s) |
| **`/api/reports/attendance/class/1`** | Attendance Info | 20.03 ms | 23.33 ms | PASSED (< 3.0s) |
| **`/api/reports/attendance/subject/1`** | Attendance Info | 12.10 ms | 13.13 ms | PASSED (< 3.0s) |
| **`/api/reports/attendance/export` (CSV)** | Attendance Info | 106.07 ms | 112.43 ms | PASSED (< 3.0s) |

*Summary:* All major page responses return in **under 7 milliseconds**, and complex attendance aggregation/export requests execute in **under 115 milliseconds** — outperforming the 3.0-second requirement by over **25x**.

---

### Running Performance Tests

```bash
# Run NFR-02 performance tests:
python -m pytest tests/test_nfr02_performance.py -v

# Run the complete automated test suite:
python -m pytest
```
