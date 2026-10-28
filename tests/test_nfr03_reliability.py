"""Tests for NFR-03: Reliability and database backups."""

import sqlite3

import pytest

from scripts.backup_db import create_backup


@pytest.fixture
def reliability_data(client):
    """Insert test attendance data into the temporary test database."""

    database_path = client.application.config["DATABASE"]

    with sqlite3.connect(database_path) as db:
        db.execute("PRAGMA foreign_keys = ON")

        # Create a student account.
        db.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                role,
                active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "nfr03_student",
                "test-password-hash",
                "student",
                1,
            ),
        )

        student_id = db.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            ("nfr03_student",),
        ).fetchone()[0]

        # Create a subject.
        db.execute(
            """
            INSERT INTO subjects (name)
            VALUES (?)
            """,
            ("NFR03 Mathematics",),
        )

        subject_id = db.execute(
            """
            SELECT id
            FROM subjects
            WHERE name = ?
            """,
            ("NFR03 Mathematics",),
        ).fetchone()[0]

        # Create an attendance record.
        db.execute(
            """
            INSERT INTO attendance (
                student_id,
                subject_id,
                attendance_date,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                student_id,
                subject_id,
                "2026-10-28",
                "Present",
            ),
        )

        db.commit()

    return {
        "database_path": database_path,
        "student_id": student_id,
        "subject_id": subject_id,
    }


def test_nfr03_backup_is_created(client, reliability_data, tmp_path):
    """Verify that a backup file is created successfully."""

    backup_dir = tmp_path / "backups"

    backup_path = create_backup(
        reliability_data["database_path"],
        backup_dir,
    )

    assert backup_path.is_file()
    assert backup_path.parent == backup_dir
    assert backup_path.stat().st_size > 0


def test_nfr03_backup_preserves_attendance_records(
    client,
    reliability_data,
    tmp_path,
):
    """Verify that attendance records are preserved in the backup."""

    backup_path = create_backup(
        reliability_data["database_path"],
        tmp_path / "backups",
    )

    with sqlite3.connect(backup_path) as backup_db:
        records = backup_db.execute(
            """
            SELECT
                student_id,
                subject_id,
                attendance_date,
                status
            FROM attendance
            """
        ).fetchall()

    assert records == [
        (
            reliability_data["student_id"],
            reliability_data["subject_id"],
            "2026-10-28",
            "Present",
        )
    ]


def test_nfr03_backup_survives_original_data_changes(
    client,
    reliability_data,
    tmp_path,
):
    """Verify that the backup remains intact if source data changes."""

    backup_path = create_backup(
        reliability_data["database_path"],
        tmp_path / "backups",
    )

    # Delete the attendance record from the original database.
    with sqlite3.connect(
        reliability_data["database_path"]
    ) as original_db:
        original_db.execute("PRAGMA foreign_keys = ON")
        original_db.execute("DELETE FROM attendance")
        original_db.commit()

    # The backup must still contain the original record.
    with sqlite3.connect(backup_path) as backup_db:
        count = backup_db.execute(
            "SELECT COUNT(*) FROM attendance"
        ).fetchone()[0]

    assert count == 1


def test_nfr03_backup_contains_valid_database_schema(
    client,
    reliability_data,
    tmp_path,
):
    """Verify that the backup contains the application tables."""

    backup_path = create_backup(
        reliability_data["database_path"],
        tmp_path / "backups",
    )

    with sqlite3.connect(backup_path) as backup_db:
        result = backup_db.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        tables = {
            row[0]
            for row in backup_db.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

    assert result == ("ok",)

    assert {
        "users",
        "subjects",
        "attendance",
    }.issubset(tables)


def test_nfr03_missing_database_fails_safely(tmp_path):
    """Verify that a nonexistent database produces a clear error."""

    missing_database = tmp_path / "missing.db"
    backup_dir = tmp_path / "backups"

    with pytest.raises(FileNotFoundError):
        create_backup(
            missing_database,
            backup_dir,
        )

    # The script must not create an empty backup.
    assert not backup_dir.exists()
"""

### Why these five tests matter

| Test | What it verifies |
|---|---|
| `test_nfr03_backup_is_created` | A backup file is successfully created. |
| `test_nfr03_backup_preserves_attendance_records` | Attendance information is copied correctly. |
| `test_nfr03_backup_survives_original_data_changes` | The backup remains usable if the original data changes. |
| `test_nfr03_backup_contains_valid_database_schema` | The backup is a valid database containing the required tables. |
| `test_nfr03_missing_database_fails_safely` | A missing database does not result in an accidental empty backup. |

These tests use your existing Flask fixture, so the actual application schema is initialized in a temporary database for testing.

The test records are isolated from your real database.

---

# 5. Step 4 — Update `.gitignore`

Your repository already ignores local SQLite database files.

We should also ignore backup files and backup logs so they do not get accidentally pushed to your public GitHub repository.

Open `.gitignore`.

Add the following lines at the end of the existing file:

```gitignore
# NFR-03: Database backups and backup logs
backups/
backup.log
"""