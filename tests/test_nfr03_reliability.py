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
            "SELECT id FROM users WHERE username = ?",
            ("nfr03_student",),
        ).fetchone()[0]

        db.execute(
            "INSERT INTO subjects (name) VALUES (?)",
            ("NFR03 Mathematics",),
        )

        subject_id = db.execute(
            "SELECT id FROM subjects WHERE name = ?",
            ("NFR03 Mathematics",),
        ).fetchone()[0]

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


def test_nfr03_backup_is_created(
    client, reliability_data, tmp_path
):
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
    client, reliability_data, tmp_path
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
    client, reliability_data, tmp_path
):
    """Verify that the backup survives changes to the original database."""

    backup_path = create_backup(
        reliability_data["database_path"],
        tmp_path / "backups",
    )

    with sqlite3.connect(
        reliability_data["database_path"]
    ) as original_db:
        original_db.execute("PRAGMA foreign_keys = ON")
        original_db.execute("DELETE FROM attendance")
        original_db.commit()

    with sqlite3.connect(backup_path) as backup_db:
        count = backup_db.execute(
            "SELECT COUNT(*) FROM attendance"
        ).fetchone()[0]

    assert count == 1


def test_nfr03_backup_contains_valid_database_schema(
    client, reliability_data, tmp_path
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

    assert not backup_dir.exists()