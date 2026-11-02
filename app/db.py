"""SQLite schema foundation; extend via reviewed migrations as features are built."""
import sqlite3
from flask import current_app, g

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK (role IN ('admin','teacher','student')),
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS classes (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 teacher_id INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS subjects (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 teacher_id INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS class_subjects (
 class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
 subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
 PRIMARY KEY (class_id, subject_id)
);
CREATE TABLE IF NOT EXISTS enrollments (
 student_id INTEGER NOT NULL REFERENCES users(id),
 class_id INTEGER NOT NULL REFERENCES classes(id),
 subject_id INTEGER NOT NULL REFERENCES subjects(id),
 PRIMARY KEY (student_id, class_id, subject_id)
);
CREATE TABLE IF NOT EXISTS attendance (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES users(id),
 subject_id INTEGER NOT NULL REFERENCES subjects(id),
 attendance_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK (status IN ('Present','Absent','Late')),
 UNIQUE (student_id, subject_id, attendance_date)
);
CREATE TABLE IF NOT EXISTS settings (
 key TEXT PRIMARY KEY,
 value TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attendance_subject_date ON attendance(subject_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_class ON enrollments(class_id, student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_subject ON enrollments(subject_id, student_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);
CREATE INDEX IF NOT EXISTS idx_subjects_teacher ON subjects(teacher_id);
CREATE INDEX IF NOT EXISTS idx_class_subjects_subject ON class_subjects(subject_id);
'''


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
        g.db.execute('PRAGMA synchronous = NORMAL')
        g.db.execute('PRAGMA cache_size = -64000')
        g.db.execute('PRAGMA temp_store = MEMORY')
    return g.db


def init_db(app):
    with app.app_context():
        connection = sqlite3.connect(app.config['DATABASE'])
        try:
            connection.executescript(SCHEMA)
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(classes)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'teacher_id' not in cols:
                connection.execute(
                    "ALTER TABLE classes ADD COLUMN teacher_id "
                    "INTEGER REFERENCES users(id)"
                )
            connection.execute('''
                CREATE TABLE IF NOT EXISTS class_subjects (
                    class_id INTEGER NOT NULL REFERENCES classes(id)
                        ON DELETE CASCADE,
                    subject_id INTEGER NOT NULL REFERENCES subjects(id)
                        ON DELETE CASCADE,
                    PRIMARY KEY (class_id, subject_id)
                )
            ''')
            connection.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_attendance_subject_date ON attendance(subject_id, attendance_date)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, attendance_date)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_enrollments_class ON enrollments(class_id, student_id)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_enrollments_subject ON enrollments(subject_id, student_id)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_subjects_teacher ON subjects(teacher_id)')
            connection.execute('CREATE INDEX IF NOT EXISTS idx_class_subjects_subject ON class_subjects(subject_id)')
            connection.commit()
        finally:
            connection.close()

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()
