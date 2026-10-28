"""Install, inspect, and remove the daily SQLite backup cron job."""

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


CRON_MARKER = "# Attendance Management System NFR-03 daily backup"


def validate_time(schedule_time):
    """Validate a daily schedule expressed as HH:MM."""

    try:
        hour_text, minute_text = schedule_time.split(":")
        hour = int(hour_text)
        minute = int(minute_text)
    except (ValueError, AttributeError):
        raise ValueError(
            "Time must use HH:MM format, for example 02:00."
        ) from None

    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(
            "Time must be between 00:00 and 23:59."
        )

    return hour, minute


def build_cron_entry(
    project_root,
    python_executable,
    schedule_time="02:00",
):
    """Build a cron entry using absolute paths."""

    hour, minute = validate_time(schedule_time)

    root = Path(project_root).expanduser().resolve()
    python_path = Path(python_executable).expanduser().resolve()

    backup_script = root / "scripts" / "backup_db.py"
    database_path = root / "attendance.db"
    backup_dir = root / "backups"
    log_path = root / "backup.log"

    command = (
        f"{shlex.quote(str(python_path))} "
        f"{shlex.quote(str(backup_script))} "
        f"--database {shlex.quote(str(database_path))} "
        f"--backup-dir {shlex.quote(str(backup_dir))} "
        f">> {shlex.quote(str(log_path))} 2>&1"
    )

    return (
        f"{minute} {hour} * * * "
        f"{command} {CRON_MARKER}"
    )


def replace_managed_entry(existing_crontab, new_entry):
    """Replace our managed entry without changing unrelated jobs."""

    unrelated_entries = [
        line
        for line in existing_crontab.splitlines()
        if CRON_MARKER not in line
    ]

    unrelated_entries.append(new_entry)

    return "\n".join(unrelated_entries).rstrip() + "\n"


def remove_managed_entry(existing_crontab):
    """Remove our managed entry and preserve unrelated jobs."""

    unrelated_entries = [
        line
        for line in existing_crontab.splitlines()
        if CRON_MARKER not in line
    ]

    return "\n".join(unrelated_entries).rstrip() + (
        "\n" if unrelated_entries else ""
    )


def read_crontab():
    """Read the current user's crontab."""

    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        return result.stdout

    if "no crontab for" in result.stderr.lower():
        return ""

    raise RuntimeError(
        f"Unable to read crontab: {result.stderr.strip()}"
    )


def install_crontab(content):
    """Install the supplied crontab contents."""

    subprocess.run(
        ["crontab", "-"],
        input=content,
        text=True,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Manage daily backups for the Attendance Management System."
        )
    )

    actions = parser.add_mutually_exclusive_group(required=True)

    actions.add_argument(
        "--install",
        action="store_true",
        help="Install or update the daily backup job.",
    )

    actions.add_argument(
        "--remove",
        action="store_true",
        help="Remove the daily backup job.",
    )

    actions.add_argument(
        "--show",
        action="store_true",
        help="Display the proposed cron entry without installing it.",
    )

    parser.add_argument(
        "--time",
        default="02:00",
        help="Daily backup time in HH:MM format; default: 02:00.",
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    try:
        if args.show or args.install:
            entry = build_cron_entry(
                project_root=project_root,
                python_executable=sys.executable,
                schedule_time=args.time,
            )

            if args.show:
                print(entry)
                return

            existing = read_crontab()
            updated = replace_managed_entry(existing, entry)
            install_crontab(updated)

            print("Daily backup schedule installed.")
            print(entry)
            return

        if args.remove:
            existing = read_crontab()
            updated = remove_managed_entry(existing)

            if updated == existing:
                print("No managed NFR-03 backup schedule was found.")
                return

            install_crontab(updated)
            print("Daily backup schedule removed.")

    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(
            status=1,
            message=f"Scheduling failed: {error}\n",
        )


if __name__ == "__main__":
    main()