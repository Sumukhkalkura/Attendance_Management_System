"""O-01 probe (Deliverable 3, Phase 3). Uses a temporary database only.

Question: does POST /api/enrollments accept a subject that is not linked to
the chosen class (no class_subjects row), and what happens downstream?
Run: .venv/bin/python docs/evidence/phase3/o01_enrollment_probe.py
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from werkzeug.security import generate_password_hash  # noqa: E402

from app import create_app  # noqa: E402

PW = "ProbePass01!"
tmp = Path(tempfile.mkdtemp()) / "o01_probe.db"
app = create_app({"TESTING": True, "DATABASE": str(tmp), "SECRET_KEY": "o01-probe"})
with sqlite3.connect(tmp) as c:
    h = generate_password_hash(PW)
    ids = {u: c.execute("INSERT INTO users (username,password_hash,role,active) VALUES (?,?,?,1)", (u, h, r)).lastrowid
           for u, r in [("admin1", "admin"), ("teacher1", "teacher"), ("stud1", "student")]}
    cse_a = c.execute("INSERT INTO classes (name) VALUES ('CSE-A')").lastrowid
    cse_b = c.execute("INSERT INTO classes (name) VALUES ('CSE-B')").lastrowid
    dbms = c.execute("INSERT INTO subjects (name, teacher_id) VALUES ('DBMS', ?)", (ids["teacher1"],)).lastrowid
    c.execute("INSERT INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (cse_a, dbms))
    c.commit()

admin = app.test_client()
admin.post("/api/login", json={"username": "admin1", "password": PW})
print("Setup: DBMS is linked to CSE-A only (class_subjects). CSE-B has no subjects.")
r = admin.post("/api/enrollments", json={"student_id": ids["stud1"], "class_id": cse_b, "subject_id": dbms})
print("POST /api/enrollments stud1 -> CSE-B / DBMS:", r.status_code, r.get_json())
with sqlite3.connect(tmp) as c:
    print("enrollments rows:", c.execute("SELECT student_id, class_id, subject_id FROM enrollments").fetchall())
    print("class_subjects rows:", c.execute("SELECT class_id, subject_id FROM class_subjects").fetchall())
r = admin.get(f"/api/classes/{cse_b}/subjects")
print(f"GET /api/classes/{cse_b}/subjects:", r.status_code, r.get_json())
teacher = app.test_client()
teacher.post("/api/login", json={"username": "teacher1", "password": PW})
r = teacher.get(f"/api/roster?class_id={cse_b}&subject_id={dbms}")
print(f"teacher GET /api/roster?class_id={cse_b}&subject_id={dbms}:", r.status_code, r.get_json())
