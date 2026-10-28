"""Reliable SQLite database backup utility.

Creates consistent database backups and verifies their integrity.
"""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def create_backup(database_path, backup_dir):
    """Create and verify a backup of a SQLite database.

    Args:
        database_path: Path to the original SQLite database.
        backup_dir: Directory in which the backup will be stored.

    Returns:
        Path to the successfully created backup.

    Raises:
        FileNotFoundError: If the original database does not exist.
        sqlite3.Error: If backup creation or verification fails.
    """

    source_path = Path(database_path).expanduser().resolve()
    destination_dir = Path(backup_dir).expanduser().resolve()

    # Never create an empty database accidentally.
    if not source_path.is_file():
        raise FileNotFoundError(
            f"Database file not found: {source_path}"
        )

    # Create the backup directory when necessary.
    destination_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename for each backup.
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    backup_path = destination_dir / (
        f"attendance_backup_{timestamp}.db"
    )

    try:
        # SQLite's backup API safely copies a live database.
        with sqlite3.connect(source_path) as source:
            with sqlite3.connect(backup_path) as destination:
                source.backup(destination)

                # Verify the integrity of the backup.
                result = destination.execute(
                    "PRAGMA integrity_check"
                ).fetchone()

                if result is None or result[0] != "ok":
                    raise sqlite3.DatabaseError(
                        "Backup integrity verification failed"
                    )

    except Exception:
        # Do not leave an incomplete backup behind.
        backup_path.unlink(missing_ok=True)
        raise

    print(f"Backup created successfully: {backup_path}")

    return backup_path


def main():
    """Read command-line arguments and create a backup."""

    parser = argparse.ArgumentParser(
        description=(
            "Create and verify an Attendance Management "
            "System SQLite database backup."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Path to the existing SQLite database",
    )

    parser.add_argument(
        "--backup-dir",
        default="backups",
        help="Directory where backups will be stored",
    )

    args = parser.parse_args()

    try:
        create_backup(
            database_path=args.database,
            backup_dir=args.backup_dir,
        )

    except (OSError, sqlite3.Error) as error:
        parser.exit(
            status=1,
            message=f"Backup failed: {error}\n",
        )


if __name__ == "__main__":
    main()