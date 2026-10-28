# NFR-03: Reliability and Daily Database Backups

## Overview

The Attendance Management System uses SQLite.

The backup utility in `scripts/backup_db.py` creates a consistent database
backup using SQLite's backup API and verifies the backup using
`PRAGMA integrity_check`.

The scheduler in `scripts/schedule_daily_backup.py` installs and manages
a daily cron job on the machine hosting the application.

GitHub Actions does not access the SQLite database on a developer's
computer or production server. The schedule must be configured on the
machine that has access to the actual database file.

## Requirements

- Python installed on the host.
- The project and its `scripts/backup_db.py` file installed on the host.
- Read access to the source database.
- Write access to the backup directory and log file.
- `cron` and the `crontab` command available on the host.

## Install a daily schedule

From the project root, activate the virtual environment if one is used.

Run:

```bash
python scripts/schedule_daily_backup.py --show
```

This displays the proposed schedule without installing it.

Install the default daily schedule:

```bash
python scripts/schedule_daily_backup.py --install
```

The default schedule runs every day at 02:00 in the host's local time zone.

Choose a different time using `HH:MM`:

```bash
python scripts/schedule_daily_backup.py --install --time 04:30
```

The scheduler preserves unrelated cron jobs and replaces its own previously
installed entry when run again.

## Verify the schedule

Inspect the current user's crontab:

```bash
crontab -l
```

Look for the marker:

```text
# Attendance Management System NFR-03 daily backup
```

The scheduled job runs the backup utility using absolute paths.

## Backup and log locations

By default, the scheduler uses:

- Database: `attendance.db` in the project root.
- Backup directory: `backups/` in the project root.
- Log file: `backup.log` in the project root.

Each successful run creates a timestamped file named similar to:

```text
backups/attendance_backup_20261028T020000000000Z.db
```

The backup directory and log file are local runtime data and must not be
committed to Git.

## Verify a backup manually

Run:

```bash
python scripts/backup_db.py \
  --database attendance.db \
  --backup-dir backups
```

Inspect the backup files:

```bash
ls -lh backups
```

Inspect the log after a scheduled run:

```bash
cat backup.log
```

A successful run logs a message beginning with:

```text
Backup created successfully:
```

Check the backup integrity:

```bash
python - <<'PY'
import sqlite3
from pathlib import Path

files = sorted(
    Path("backups").glob("attendance_backup_*.db"),
    key=lambda path: path.stat().st_mtime,
)

if not files:
    raise SystemExit("No backups found")

latest = files[-1]

with sqlite3.connect(latest) as db:
    result = db.execute("PRAGMA integrity_check").fetchone()

print("Latest backup:", latest)
print("Integrity:", result[0])

if result != ("ok",):
    raise SystemExit("Backup integrity verification failed")
PY
```

## Remove the scheduled job

Run:

```bash
python scripts/schedule_daily_backup.py --remove
```

This removes the scheduler's managed entry and preserves unrelated cron jobs.

## Operational considerations

- The host must be awake and cron must be running at the scheduled time.
- Cron jobs may not execute while a laptop is asleep.
- Use the actual database path if the deployment overrides the default.
- Keep backups in a protected location with appropriate filesystem permissions.
- Backups on the same disk do not protect against disk failure or loss of the host.
- Production deployments should consider a separate backup destination, retention
  policy, monitoring, and periodic restore tests.
- Configure the schedule on every relevant host; do not rely on GitHub Actions
  to back up a database it cannot access.