"""Populate a LOCAL DEVELOPMENT database with demonstration data.

Creates demo teachers, students, classes, subjects, enrollments and a few
weeks of attendance so every dashboard has something to show.

Safe and repeatable:
- Existing users, classes and subjects are never modified or deleted.
- Rows that already exist (by username / name / unique key) are skipped.
- Passwords are hashed with the same Werkzeug function the app uses.

The demo password is generated on the first run and saved to
demo_credentials.txt (git-ignored). Later runs reuse it. Set the
DEMO_PASSWORD environment variable to choose your own instead.

Usage:
    python scripts/seed_demo_data.py [--database attendance.db]

Never run this against a production database.
"""

import argparse
import os
import random
import secrets
import sys
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
from app.db import get_db  # noqa: E402

CREDENTIALS_FILE = PROJECT_ROOT / "demo_credentials.txt"

ADMINS = ["demo.admin"]
TEACHERS = ["prof.mehta", "prof.iyer"]
# (username, typical chance of being present) — varied so some fall below 75%.
STUDENTS = [
    ("aarav", 0.95), ("diya", 0.85), ("kabir", 0.65), ("meera", 0.9),
    ("rohan", 0.7), ("sara", 0.92), ("vikram", 0.55), ("zoya", 0.82),
]

# class name -> [(subject name, teacher username)]
CLASSES = {
    "BSc Computer Science - Year 1": [
        ("Programming Fundamentals", "prof.mehta"),
        ("Discrete Mathematics", "prof.iyer"),
    ],
    "BSc Computer Science - Year 2": [
        ("Database Systems", "prof.mehta"),
        ("Software Engineering", "prof.iyer"),
    ],
}

# Which students study in which class.
CLASS_STUDENTS = {
    "BSc Computer Science - Year 1": ["aarav", "diya", "kabir", "meera"],
    "BSc Computer Science - Year 2": ["rohan", "sara", "vikram", "zoya"],
}

SESSIONS = 12  # most recent weekdays with attendance, ending yesterday


def demo_password():
    """Return the demo password from the environment, the saved file, or a new one."""
    if os.environ.get("DEMO_PASSWORD"):
        return os.environ["DEMO_PASSWORD"]

    if CREDENTIALS_FILE.exists():
        for line in CREDENTIALS_FILE.read_text().splitlines():
            if line.startswith("password:"):
                return line.split(":", 1)[1].strip()

    return "Demo-" + secrets.token_urlsafe(9)


def get_or_create_user(db, username, role, password, created):
    row = db.execute("SELECT id, role FROM users WHERE username = ?", (username,)).fetchone()

    if row is not None:
        if row["role"] != role:
            raise SystemExit(
                f"User '{username}' already exists with role '{row['role']}', "
                f"expected '{role}'. Rename it or remove it from the demo list."
            )
        return row["id"]

    cursor = db.execute(
        "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, ?, 1)",
        (username, generate_password_hash(password), role),
    )
    created.append(f"{role:<8} {username}")
    return cursor.lastrowid


def get_or_create(db, table, name, teacher_id):
    row = db.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()

    if row is not None:
        return row["id"], False

    cursor = db.execute(
        f"INSERT INTO {table} (name, teacher_id) VALUES (?, ?)", (name, teacher_id)
    )
    return cursor.lastrowid, True


def recent_weekdays(count):
    days = []
    day = date.today() - timedelta(days=1)
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return sorted(days)


def seed(database):
    app = create_app({"DATABASE": database})
    password = demo_password()
    created_users = []
    counts = {"classes": 0, "subjects": 0, "enrollments": 0, "attendance": 0}

    with app.app_context():
        db = get_db()

        for username in ADMINS:
            get_or_create_user(db, username, "admin", password, created_users)

        teacher_ids = {
            username: get_or_create_user(db, username, "teacher", password, created_users)
            for username in TEACHERS
        }
        student_ids = {
            username: get_or_create_user(db, username, "student", password, created_users)
            for username, _ in STUDENTS
        }
        presence = dict(STUDENTS)

        days = recent_weekdays(SESSIONS)

        for class_name, subjects in CLASSES.items():
            teacher_of_class = teacher_ids[subjects[0][1]]
            class_id, new = get_or_create(db, "classes", class_name, teacher_of_class)
            counts["classes"] += new

            for subject_name, teacher in subjects:
                subject_id, new = get_or_create(db, "subjects", subject_name, teacher_ids[teacher])
                counts["subjects"] += new

                db.execute(
                    "INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
                    (class_id, subject_id),
                )

                for student in CLASS_STUDENTS[class_name]:
                    student_id = student_ids[student]
                    cursor = db.execute(
                        "INSERT OR IGNORE INTO enrollments (student_id, class_id, subject_id) "
                        "VALUES (?, ?, ?)",
                        (student_id, class_id, subject_id),
                    )
                    counts["enrollments"] += cursor.rowcount

                    # Deterministic per student/subject so reruns produce the same data.
                    rng = random.Random(f"{student}|{subject_name}")
                    for day in days:
                        roll = rng.random()
                        if roll < presence[student]:
                            status = "Present"
                        elif roll < presence[student] + 0.05:
                            status = "Late"
                        else:
                            status = "Absent"

                        cursor = db.execute(
                            "INSERT OR IGNORE INTO attendance "
                            "(student_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?)",
                            (student_id, subject_id, day.isoformat(), status),
                        )
                        counts["attendance"] += cursor.rowcount

        db.commit()

    all_usernames = ADMINS + TEACHERS + [s for s, _ in STUDENTS]
    CREDENTIALS_FILE.write_text(
        "Local demo accounts (development only - do not commit)\n"
        f"password: {password}\n"
        "users:\n" + "".join(f"  {name}\n" for name in all_usernames)
    )

    print(f"Database: {database}")
    print(f"New users: {len(created_users)}")
    for line in created_users:
        print(f"  {line}")
    print(
        f"New classes: {counts['classes']}, subjects: {counts['subjects']}, "
        f"enrollments: {counts['enrollments']}, attendance records: {counts['attendance']}"
    )
    print(f"Demo password for newly created users: {password}")
    print(f"Saved to {CREDENTIALS_FILE.name} (git-ignored).")
    if len(created_users) < len(all_usernames):
        print("Note: users that already existed kept their existing passwords.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--database",
        default=str(PROJECT_ROOT / "attendance.db"),
        help="SQLite database file to populate (default: attendance.db)",
    )
    args = parser.parse_args()
    seed(args.database)


if __name__ == "__main__":
    main()
