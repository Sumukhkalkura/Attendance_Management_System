"""Runnable foundation checks; these are not proof Sprint 1 is complete."""
import sqlite3
from app import create_app


def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json()['application'] == 'Attendance Management System'


def test_health(client):
    assert client.get('/api/health').get_json() == {'status': 'ok'}


def test_database_schema(tmp_path):
    path = tmp_path / 'schema.db'
    create_app({'TESTING': True, 'DATABASE': str(path)})
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'users', 'classes', 'subjects', 'enrollments', 'attendance'} <= tables


def test_duplicate_attendance_prevented(tmp_path):
    path = tmp_path / 'schema.db'
    create_app({'TESTING': True, 'DATABASE': str(path)})
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO users(username,password_hash,role) VALUES ('s1','test-placeholder','student')")
        db.execute("INSERT INTO subjects(name) VALUES ('DBMS')")
        db.execute("INSERT INTO attendance(student_id,subject_id,attendance_date,status) VALUES (1,1,'2026-10-24','Present')")
        try:
            db.execute("INSERT INTO attendance(student_id,subject_id,attendance_date,status) VALUES (1,1,'2026-10-24','Absent')")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError('Duplicate attendance was allowed')


def test_unimplemented_endpoints_are_explicit(client):
    assert client.post('/api/login').status_code == 501
    assert client.post('/api/logout').status_code == 501
    assert client.post('/api/attendance').status_code == 501
    assert client.get('/api/attendance').status_code == 501
    assert client.get('/api/attendance/percentage').status_code == 501
