"""Sprint 1 acceptance-test checklist derived from the SRS/Test Plan.

Implement these tests as the corresponding endpoints are completed.
The skip markers are intentional: they must be removed before claiming
that the respective requirement is verified.
"""
import pytest

@pytest.mark.skip(reason='FR-01 pending: valid/invalid/blank login, role restrictions, timeout')
def test_fr01_authentication(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-07/08/09 pending: admin user/class/subject/enrollment workflows')
def test_admin_management(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-02 pending: Present/Absent/Late, date validation, assigned teacher')
def test_fr02_attendance_marking(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-03 pending: update, persistence, duplicate protection, permissions')
def test_fr03_record_management(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-04 pending: 100%, 50%, zero records, late policy, filters')
def test_fr04_percentages(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-05 pending: student/teacher scopes, filters, empty results')
def test_fr05_viewing(client):
    raise NotImplementedError

@pytest.mark.skip(reason='FR-15 pending: logout revokes access')
def test_fr15_logout(client):
    raise NotImplementedError

@pytest.mark.skip(reason='NFR-01 pending: permissions, session protection, HTTPS deployment')
def test_nfr01_security(client):
    raise NotImplementedError

@pytest.mark.skip(reason='NFR-03 pending: backup creation, restore, failure recovery')
def test_nfr03_reliability(client):
    raise NotImplementedError
