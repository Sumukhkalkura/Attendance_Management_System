"""Automated tests for FR-08: Class and Subject Management.

Covers:
- Class creation with name validation and duplicate prevention (409)
- Class listing and individual class retrieval
- Class updating (PUT/PATCH) with uniqueness enforcement
- Teacher assignment to classes
- Subject creation with name validation, optional teacher, and duplicate prevention (409)
- Subject listing and individual subject retrieval
- Subject updating (PUT/PATCH) with uniqueness enforcement
- Teacher assignment to subjects (PUT/PATCH /subjects/<id>/teacher)
- Active teacher validation (rejects student or inactive teacher with 400)
- Associating subjects with classes (POST/GET/DELETE /classes/<id>/subjects)
- Filtering subjects by class_id
- Role-Based Access Control (RBAC): Unauthenticated (401), Teacher (403), Student (403), Admin (allowed)
"""

from uuid import uuid4
from werkzeug.security import generate_password_hash
from app.db import get_db


def unique_name(prefix="fr08"):
    return f"{prefix}_{uuid4().hex[:12]}"


def insert_user(client, role, active=1):
    username = unique_name(role)
    with client.application.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, role, active) "
            "VALUES (?, ?, ?, ?)",
            (username, generate_password_hash("TestPassword123!"), role, active),
        )
        db.commit()
        return cursor.lastrowid


def login_as(client, role="admin"):
    user_id = insert_user(client, role)
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id
    return user_id


# =====================================================================
# Class Management Tests
# =====================================================================

def test_admin_can_create_class(client):
    """Administrator can successfully create a new class."""
    login_as(client)
    name = unique_name("class")
    response = client.post("/api/classes", json={"name": name})
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Class created successfully"
    assert data["class_info"]["name"] == name
    assert "id" in data["class_info"]


def test_admin_can_create_class_with_assigned_teacher(client):
    """Administrator can create a class with a teacher assigned."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    name = unique_name("class")
    response = client.post(
        "/api/classes",
        json={"name": name, "teacher_id": teacher_id},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["class_info"]["teacher_id"] == teacher_id


def test_admin_can_list_classes(client):
    """Administrator can list all classes."""
    login_as(client)
    name = unique_name("class")
    client.post("/api/classes", json={"name": name})

    response = client.get("/api/classes")
    assert response.status_code == 200
    classes = response.get_json()["classes"]
    assert any(c["name"] == name for c in classes)


def test_admin_can_get_single_class(client):
    """Administrator can retrieve a specific class by ID."""
    login_as(client)
    name = unique_name("class")
    created = client.post("/api/classes", json={"name": name})
    class_id = created.get_json()["class_info"]["id"]

    response = client.get(f"/api/classes/{class_id}")
    assert response.status_code == 200
    assert response.get_json()["class_info"]["name"] == name


def test_get_nonexistent_class_returns_404(client):
    """Retrieving a non-existent class returns 404."""
    login_as(client)
    response = client.get("/api/classes/999999")
    assert response.status_code == 404


def test_admin_can_update_class(client):
    """Administrator can update class details."""
    login_as(client)
    created = client.post("/api/classes", json={"name": unique_name("class")})
    class_id = created.get_json()["class_info"]["id"]

    updated_name = unique_name("updated_class")
    response = client.put(
        f"/api/classes/{class_id}",
        json={"name": updated_name},
    )
    assert response.status_code == 200
    assert response.get_json()["class_info"]["name"] == updated_name


def test_admin_can_update_class_unassign_teacher(client):
    """Administrator can unassign a teacher from a class by setting teacher_id to None."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    created = client.post(
        "/api/classes",
        json={"name": unique_name("class"), "teacher_id": teacher_id},
    )
    class_id = created.get_json()["class_info"]["id"]
    assert created.get_json()["class_info"]["teacher_id"] == teacher_id

    response = client.put(
        f"/api/classes/{class_id}",
        json={"teacher_id": None},
    )
    assert response.status_code == 200
    assert response.get_json()["class_info"]["teacher_id"] is None

    fetch = client.get(f"/api/classes/{class_id}")
    assert fetch.get_json()["class_info"]["teacher_id"] is None


def test_admin_can_assign_teacher_to_class(client):
    """Administrator can assign a teacher to a class."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    created = client.post("/api/classes", json={"name": unique_name("class")})
    class_id = created.get_json()["class_info"]["id"]

    response = client.put(
        f"/api/classes/{class_id}/teacher",
        json={"teacher_id": teacher_id},
    )
    assert response.status_code == 200
    assert response.get_json()["teacher_id"] == teacher_id

    # Verify retrieval reflects assigned teacher
    fetch = client.get(f"/api/classes/{class_id}")
    assert fetch.get_json()["class_info"]["teacher_id"] == teacher_id


def test_assign_teacher_to_class_rejects_student_and_inactive(client):
    """Assigning student or inactive teacher to class returns 400."""
    login_as(client)
    created = client.post("/api/classes", json={"name": unique_name("class")})
    class_id = created.get_json()["class_info"]["id"]

    student_id = insert_user(client, "student")
    assert client.put(f"/api/classes/{class_id}/teacher", json={"teacher_id": student_id}).status_code == 400

    inactive_teacher_id = insert_user(client, "teacher", active=0)
    assert client.put(f"/api/classes/{class_id}/teacher", json={"teacher_id": inactive_teacher_id}).status_code == 400

    assert client.put(f"/api/classes/{class_id}/teacher", json={"teacher_id": 999999}).status_code == 400
    assert client.put(f"/api/classes/{class_id}/teacher", json={"teacher_id": "not-int"}).status_code == 400


def test_assign_teacher_to_class_invalid_class_returns_404(client):
    """Assigning a teacher to a non-existent class returns 404."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    resp = client.put("/api/classes/999999/teacher", json={"teacher_id": teacher_id})
    assert resp.status_code == 404


def test_blank_class_name_rejected(client):
    """Empty or whitespace class name returns 400 Bad Request."""
    login_as(client)
    assert client.post("/api/classes", json={"name": ""}).status_code == 400
    assert client.post("/api/classes", json={"name": "   "}).status_code == 400
    assert client.post("/api/classes", json={}).status_code == 400
    assert client.post("/api/classes", json={"name": 12345}).status_code == 400
    assert client.post("/api/classes", data="invalid json", content_type="application/json").status_code == 400


def test_update_class_invalid_payloads(client):
    """Updating a class with invalid payloads returns 400."""
    login_as(client)
    created = client.post("/api/classes", json={"name": unique_name("class")})
    class_id = created.get_json()["class_info"]["id"]

    # Empty payload
    assert client.put(f"/api/classes/{class_id}", json={}).status_code == 400
    # Disallowed fields
    assert client.put(f"/api/classes/{class_id}", json={"unknown": "val"}).status_code == 400
    # Blank name
    assert client.put(f"/api/classes/{class_id}", json={"name": "  "}).status_code == 400
    # Non-integer teacher_id
    assert client.put(f"/api/classes/{class_id}", json={"teacher_id": "invalid"}).status_code == 400
    # Inactive teacher
    inactive_id = insert_user(client, "teacher", active=0)
    assert client.put(f"/api/classes/{class_id}", json={"teacher_id": inactive_id}).status_code == 400
    # Non-existent teacher
    assert client.put(f"/api/classes/{class_id}", json={"teacher_id": 999999}).status_code == 400


def test_duplicate_class_name_rejected(client):
    """Duplicate class name returns 409 Conflict."""
    login_as(client)
    name = unique_name("class")
    first = client.post("/api/classes", json={"name": name})
    assert first.status_code == 201
    second = client.post("/api/classes", json={"name": name})
    assert second.status_code == 409


def test_update_class_duplicate_name_rejected(client):
    """Updating a class to another existing class name returns 409 Conflict."""
    login_as(client)
    name1 = unique_name("class1")
    name2 = unique_name("class2")
    c1 = client.post("/api/classes", json={"name": name1}).get_json()["class_info"]["id"]
    client.post("/api/classes", json={"name": name2})

    response = client.put(f"/api/classes/{c1}", json={"name": name2})
    assert response.status_code == 409


def test_nonexistent_class_returns_404(client):
    """Updating a non-existent class returns 404."""
    login_as(client)
    response = client.put(
        "/api/classes/987654321",
        json={"name": unique_name("class")},
    )
    assert response.status_code == 404


# =====================================================================
# Subject Management Tests
# =====================================================================

def test_admin_can_create_subject(client):
    """Administrator can successfully create a new subject."""
    login_as(client)
    name = unique_name("subject")
    response = client.post("/api/subjects", json={"name": name})
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Subject created successfully"
    assert data["subject"]["name"] == name
    assert "id" in data["subject"]


def test_admin_can_create_subject_with_assigned_teacher(client):
    """Administrator can create a subject with an assigned teacher."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    name = unique_name("subject")
    response = client.post(
        "/api/subjects",
        json={"name": name, "teacher_id": teacher_id},
    )
    assert response.status_code == 201
    assert response.get_json()["subject"]["teacher_id"] == teacher_id


def test_admin_can_list_subjects(client):
    """Administrator can list all subjects."""
    login_as(client)
    name = unique_name("subject")
    client.post("/api/subjects", json={"name": name})

    response = client.get("/api/subjects")
    assert response.status_code == 200
    subjects = response.get_json()["subjects"]
    assert any(s["name"] == name for s in subjects)


def test_admin_can_get_single_subject(client):
    """Administrator can retrieve a specific subject by ID."""
    login_as(client)
    name = unique_name("subject")
    created = client.post("/api/subjects", json={"name": name})
    subject_id = created.get_json()["subject"]["id"]

    response = client.get(f"/api/subjects/{subject_id}")
    assert response.status_code == 200
    assert response.get_json()["subject"]["name"] == name


def test_get_nonexistent_subject_returns_404(client):
    """Retrieving a non-existent subject returns 404."""
    login_as(client)
    response = client.get("/api/subjects/999999")
    assert response.status_code == 404


def test_admin_can_update_subject(client):
    """Administrator can update subject details."""
    login_as(client)
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    updated_name = unique_name("updated_subject")
    response = client.put(
        f"/api/subjects/{subject_id}",
        json={"name": updated_name},
    )
    assert response.status_code == 200
    assert response.get_json()["subject"]["name"] == updated_name


def test_admin_can_update_subject_unassign_teacher(client):
    """Administrator can unassign a teacher from a subject by setting teacher_id to None."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    created = client.post(
        "/api/subjects",
        json={"name": unique_name("subject"), "teacher_id": teacher_id},
    )
    subject_id = created.get_json()["subject"]["id"]
    assert created.get_json()["subject"]["teacher_id"] == teacher_id

    response = client.put(
        f"/api/subjects/{subject_id}",
        json={"teacher_id": None},
    )
    assert response.status_code == 200
    assert response.get_json()["subject"]["teacher_id"] is None

    fetch = client.get(f"/api/subjects/{subject_id}")
    assert fetch.get_json()["subject"]["teacher_id"] is None


def test_admin_can_update_subject_associate_class(client):
    """Updating a subject with class_id establishes class-subject association."""
    login_as(client)
    cls_id = client.post("/api/classes", json={"name": unique_name("class")}).get_json()["class_info"]["id"]
    subj_id = client.post("/api/subjects", json={"name": unique_name("subject")}).get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subj_id}",
        json={"class_id": cls_id},
    )
    assert response.status_code == 200

    # Verify association was created
    class_subjects_resp = client.get(f"/api/classes/{cls_id}/subjects")
    assert class_subjects_resp.status_code == 200
    assert any(s["id"] == subj_id for s in class_subjects_resp.get_json()["subjects"])


def test_admin_can_assign_teacher(client):
    """Administrator can assign a teacher to a subject."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": teacher_id},
    )
    assert response.status_code == 200
    assert response.get_json()["teacher_id"] == teacher_id

    # Verify retrieval reflects assigned teacher
    fetch = client.get(f"/api/subjects/{subject_id}")
    assert fetch.get_json()["subject"]["teacher_id"] == teacher_id


def test_blank_subject_name_rejected(client):
    """Empty or whitespace subject name returns 400 Bad Request."""
    login_as(client)
    assert client.post("/api/subjects", json={"name": ""}).status_code == 400
    assert client.post("/api/subjects", json={"name": "   "}).status_code == 400
    assert client.post("/api/subjects", json={}).status_code == 400
    assert client.post("/api/subjects", json={"name": 12345}).status_code == 400
    assert client.post("/api/subjects", data="invalid json", content_type="application/json").status_code == 400


def test_subject_creation_invalid_payloads(client):
    """Creating a subject with invalid payload or relationships returns appropriate errors."""
    login_as(client)
    # Non-existent class
    assert client.post("/api/subjects", json={"name": unique_name("s"), "class_id": 999999}).status_code == 404
    # Non-existent teacher
    assert client.post("/api/subjects", json={"name": unique_name("s"), "teacher_id": 999999}).status_code == 400
    # Inactive teacher
    inactive_id = insert_user(client, "teacher", active=0)
    assert client.post("/api/subjects", json={"name": unique_name("s"), "teacher_id": inactive_id}).status_code == 400
    # Student as teacher
    student_id = insert_user(client, "student")
    assert client.post("/api/subjects", json={"name": unique_name("s"), "teacher_id": student_id}).status_code == 400


def test_update_subject_invalid_payloads(client):
    """Updating a subject with invalid payloads returns 400 or 404."""
    login_as(client)
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    # Empty payload
    assert client.put(f"/api/subjects/{subject_id}", json={}).status_code == 400
    # Disallowed fields
    assert client.put(f"/api/subjects/{subject_id}", json={"unknown": "val"}).status_code == 400
    # Blank name
    assert client.put(f"/api/subjects/{subject_id}", json={"name": "  "}).status_code == 400
    # Non-integer teacher_id
    assert client.put(f"/api/subjects/{subject_id}", json={"teacher_id": "invalid"}).status_code == 400
    # Non-existent teacher_id
    assert client.put(f"/api/subjects/{subject_id}", json={"teacher_id": 999999}).status_code == 400
    # Inactive teacher
    inactive_id = insert_user(client, "teacher", active=0)
    assert client.put(f"/api/subjects/{subject_id}", json={"teacher_id": inactive_id}).status_code == 400
    # Non-existent class_id
    assert client.put(f"/api/subjects/{subject_id}", json={"class_id": 999999}).status_code == 404


def test_assign_teacher_to_subject_invalid_subject_returns_404(client):
    """Assigning a teacher to a non-existent subject returns 404."""
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    resp = client.put("/api/subjects/999999/teacher", json={"teacher_id": teacher_id})
    assert resp.status_code == 404


def test_nonexistent_teacher_id_rejected(client):
    """Assigning a non-existent teacher ID returns 400."""
    login_as(client)
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": 999999},
    )
    assert response.status_code == 400


def test_duplicate_subject_name_rejected(client):
    """Duplicate subject name returns 409 Conflict."""
    login_as(client)
    name = unique_name("subject")
    first = client.post("/api/subjects", json={"name": name})
    assert first.status_code == 201
    second = client.post("/api/subjects", json={"name": name})
    assert second.status_code == 409


def test_update_subject_duplicate_name_rejected(client):
    """Updating a subject to an existing name returns 409 Conflict."""
    login_as(client)
    name1 = unique_name("subject1")
    name2 = unique_name("subject2")
    s1 = client.post("/api/subjects", json={"name": name1}).get_json()["subject"]["id"]
    client.post("/api/subjects", json={"name": name2})

    response = client.put(f"/api/subjects/{s1}", json={"name": name2})
    assert response.status_code == 409


def test_nonexistent_subject_returns_404(client):
    """Updating a non-existent subject returns 404."""
    login_as(client)
    response = client.put(
        "/api/subjects/987654321",
        json={"name": unique_name("subject")},
    )
    assert response.status_code == 404


def test_student_cannot_be_assigned_as_teacher(client):
    """Assigning a student account as teacher returns 400 Bad Request."""
    login_as(client)
    student_id = insert_user(client, "student")
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": student_id},
    )
    assert response.status_code == 400


def test_inactive_teacher_cannot_be_assigned(client):
    """Assigning an inactive teacher returns 400 Bad Request."""
    login_as(client)
    teacher_id = insert_user(client, "teacher", active=0)
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": teacher_id},
    )
    assert response.status_code == 400


def test_invalid_teacher_id_type_rejected(client):
    """Non-integer teacher_id returns 400 Bad Request."""
    login_as(client)
    created = client.post("/api/subjects", json={"name": unique_name("subject")})
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": "not-an-id"},
    )
    assert response.status_code == 400
    assert client.put(f"/api/subjects/{subject_id}/teacher", json={"teacher_id": True}).status_code == 400
    assert client.put(f"/api/subjects/{subject_id}/teacher", data="not json", content_type="application/json").status_code == 400


# =====================================================================
# Class-Subject Association Tests
# =====================================================================

def test_admin_can_associate_subject_with_class(client):
    """Administrator can associate a subject with a class."""
    login_as(client)
    cls = client.post("/api/classes", json={"name": unique_name("class")}).get_json()["class_info"]["id"]
    subj = client.post("/api/subjects", json={"name": unique_name("subject")}).get_json()["subject"]["id"]

    assoc_resp = client.post(f"/api/classes/{cls}/subjects", json={"subject_id": subj})
    assert assoc_resp.status_code == 201

    # Duplicate association returns 409
    dup_resp = client.post(f"/api/classes/{cls}/subjects", json={"subject_id": subj})
    assert dup_resp.status_code == 409

    # List subjects in class
    list_resp = client.get(f"/api/classes/{cls}/subjects")
    assert list_resp.status_code == 200
    subject_ids = [s["id"] for s in list_resp.get_json()["subjects"]]
    assert subj in subject_ids

    # Dissociate subject from class
    del_resp = client.delete(f"/api/classes/{cls}/subjects/{subj}")
    assert del_resp.status_code == 200

    # Verify removal
    list_after = client.get(f"/api/classes/{cls}/subjects")
    assert subj not in [s["id"] for s in list_after.get_json()["subjects"]]


def test_create_subject_with_class_id_associates_automatically(client):
    """Creating a subject with class_id automatically establishes association."""
    login_as(client)
    cls_id = client.post("/api/classes", json={"name": unique_name("class")}).get_json()["class_info"]["id"]
    name = unique_name("subj_with_class")

    resp = client.post("/api/subjects", json={"name": name, "class_id": cls_id})
    assert resp.status_code == 201
    subj_id = resp.get_json()["subject"]["id"]

    # Filter subjects by class_id
    filtered = client.get(f"/api/subjects?class_id={cls_id}")
    assert filtered.status_code == 200
    assert any(s["id"] == subj_id for s in filtered.get_json()["subjects"])


def test_associate_subject_invalid_ids(client):
    """Invalid class or subject IDs return appropriate errors."""
    login_as(client)
    cls_id = client.post("/api/classes", json={"name": unique_name("class")}).get_json()["class_info"]["id"]

    # Non-existent subject
    resp = client.post(f"/api/classes/{cls_id}/subjects", json={"subject_id": 999999})
    assert resp.status_code == 404

    # Non-existent class
    resp2 = client.post("/api/classes/999999/subjects", json={"subject_id": 1})
    assert resp2.status_code == 404

    # Non-integer or invalid payload
    assert client.post(f"/api/classes/{cls_id}/subjects", json={"subject_id": "invalid"}).status_code == 400
    assert client.post(f"/api/classes/{cls_id}/subjects", json={"subject_id": True}).status_code == 400
    assert client.post(f"/api/classes/{cls_id}/subjects", data="not json", content_type="application/json").status_code == 400


def test_dissociate_subject_invalid_ids(client):
    """Dissociating with non-existent class or subject returns 404."""
    login_as(client)
    cls_id = client.post("/api/classes", json={"name": unique_name("class")}).get_json()["class_info"]["id"]
    subj_id = client.post("/api/subjects", json={"name": unique_name("subject")}).get_json()["subject"]["id"]

    assert client.delete(f"/api/classes/999999/subjects/{subj_id}").status_code == 404
    assert client.delete(f"/api/classes/{cls_id}/subjects/999999").status_code == 404
    assert client.get("/api/classes/999999/subjects").status_code == 404


# =====================================================================
# Role-Based Access Control (RBAC) Tests
# =====================================================================

def test_unauthenticated_access_is_denied(client):
    """Unauthenticated access to class and subject endpoints returns 401."""
    assert client.get("/api/classes").status_code == 401
    assert client.post("/api/classes", json={"name": "test"}).status_code == 401
    assert client.get("/api/classes/1").status_code == 401
    assert client.put("/api/classes/1", json={"name": "test"}).status_code == 401
    assert client.put("/api/classes/1/teacher", json={"teacher_id": 1}).status_code == 401
    assert client.get("/api/classes/1/subjects").status_code == 401
    assert client.post("/api/classes/1/subjects", json={"subject_id": 1}).status_code == 401
    assert client.delete("/api/classes/1/subjects/1").status_code == 401

    assert client.get("/api/subjects").status_code == 401
    assert client.post("/api/subjects", json={"name": "test"}).status_code == 401
    assert client.get("/api/subjects/1").status_code == 401
    assert client.put("/api/subjects/1", json={"name": "test"}).status_code == 401
    assert client.put("/api/subjects/1/teacher", json={"teacher_id": 1}).status_code == 401


def test_teacher_access_is_denied(client):
    """Teachers cannot create, update, or list via admin class/subject endpoints."""
    login_as(client, "teacher")
    assert client.get("/api/classes").status_code == 403
    assert client.post("/api/classes", json={"name": "test"}).status_code == 403
    assert client.get("/api/classes/1").status_code == 403
    assert client.put("/api/classes/1", json={"name": "test"}).status_code == 403
    assert client.put("/api/classes/1/teacher", json={"teacher_id": 1}).status_code == 403
    assert client.get("/api/classes/1/subjects").status_code == 403
    assert client.post("/api/classes/1/subjects", json={"subject_id": 1}).status_code == 403
    assert client.delete("/api/classes/1/subjects/1").status_code == 403

    assert client.get("/api/subjects").status_code == 403
    assert client.post("/api/subjects", json={"name": "test"}).status_code == 403
    assert client.get("/api/subjects/1").status_code == 403
    assert client.put("/api/subjects/1", json={"name": "test"}).status_code == 403
    assert client.put("/api/subjects/1/teacher", json={"teacher_id": 1}).status_code == 403


def test_student_access_is_denied(client):
    """Students cannot access class/subject management endpoints."""
    login_as(client, "student")
    assert client.get("/api/classes").status_code == 403
    assert client.post("/api/classes", json={"name": "test"}).status_code == 403
    assert client.get("/api/classes/1").status_code == 403
    assert client.put("/api/classes/1", json={"name": "test"}).status_code == 403
    assert client.put("/api/classes/1/teacher", json={"teacher_id": 1}).status_code == 403
    assert client.get("/api/classes/1/subjects").status_code == 403
    assert client.post("/api/classes/1/subjects", json={"subject_id": 1}).status_code == 403
    assert client.delete("/api/classes/1/subjects/1").status_code == 403

    assert client.get("/api/subjects").status_code == 403
    assert client.post("/api/subjects", json={"name": "test"}).status_code == 403
    assert client.get("/api/subjects/1").status_code == 403
    assert client.put("/api/subjects/1", json={"name": "test"}).status_code == 403
    assert client.put("/api/subjects/1/teacher", json={"teacher_id": 1}).status_code == 403


def test_assigned_teacher_visibility_in_teacher_routes(client):
    """Assigned teachers can see their assigned subjects via teacher helper routes."""
    # 1. Admin creates teacher, class, and subject, and assigns teacher
    login_as(client, "admin")
    teacher_id = insert_user(client, "teacher")
    subject_name = unique_name("subj_assigned")
    subj_resp = client.post(
        "/api/subjects",
        json={"name": subject_name, "teacher_id": teacher_id},
    )
    assert subj_resp.status_code == 201

    # 2. Login as that teacher
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = teacher_id

    # 3. Call /api/teacher/subjects
    resp = client.get("/api/teacher/subjects")
    assert resp.status_code == 200
    subjects = resp.get_json()["subjects"]
    assert any(s["name"] == subject_name and s["teacher_id"] == teacher_id for s in subjects)
