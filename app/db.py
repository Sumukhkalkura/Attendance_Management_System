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
 name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS subjects (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 teacher_id INTEGER REFERENCES users(id)
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
'''

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def init_db(app):
    with app.app_context():
        connection = sqlite3.connect(app.config['DATABASE'])
        try:
            connection.executescript(SCHEMA)
            connection.commit()
        finally:
            connection.close()

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()
