"""REST endpoint skeleton. Never expose unfinished routes as implemented."""
from flask import Blueprint, jsonify

api = Blueprint('api', __name__)

@api.get('/health')
def health():
    return jsonify(status='ok')

@api.post('/login')
def login():
    # TODO FR-01: validate input, verify hashed password, establish secure session,
    # enforce account status and roles; add error and timeout handling.
    return jsonify(error='FR-01 not implemented'), 501

@api.post('/logout')
def logout():
    # TODO FR-15: invalidate authenticated session.
    return jsonify(error='FR-15 not implemented'), 501

@api.post('/attendance')
def mark_attendance():
    # TODO FR-02/03: require assigned teacher, validate roster/date/status,
    # transactionally save records and prevent duplicate keys.
    return jsonify(error='FR-02/03 not implemented'), 501

@api.get('/attendance')
def view_attendance():
    # TODO FR-05: role-scoped attendance viewing with subject/date filters.
    return jsonify(error='FR-05 not implemented'), 501

@api.get('/attendance/percentage')
def attendance_percentage():
    # TODO FR-04: calculate from persisted records and document Late policy.
    return jsonify(error='FR-04 not implemented'), 501
