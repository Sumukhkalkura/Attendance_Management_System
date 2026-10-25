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
