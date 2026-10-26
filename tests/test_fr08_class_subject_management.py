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


def test_admin_can_create_class(client):
    login_as(client)
    response = client.post(
        "/api/classes",
        json={"name": unique_name("class")},
    )
    assert response.status_code == 201


def test_admin_can_list_classes(client):
    login_as(client)
    response = client.get("/api/classes")
    assert response.status_code == 200
    assert "classes" in response.get_json()


def test_admin_can_update_class(client):
    login_as(client)
    created = client.post(
        "/api/classes",
        json={"name": unique_name("class")},
    )
    assert created.status_code == 201
    class_id = created.get_json()["class_info"]["id"]

    response = client.put(
        f"/api/classes/{class_id}",
        json={"name": unique_name("updated_class")},
    )
    assert response.status_code == 200


def test_admin_can_create_subject(client):
    login_as(client)
    response = client.post(
        "/api/subjects",
        json={"name": unique_name("subject")},
    )
    assert response.status_code == 201


def test_admin_can_list_subjects(client):
    login_as(client)
    response = client.get("/api/subjects")
    assert response.status_code == 200
    assert "subjects" in response.get_json()


def test_admin_can_update_subject(client):
    login_as(client)
    created = client.post(
        "/api/subjects",
        json={"name": unique_name("subject")},
    )
    assert created.status_code == 201
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}",
        json={"name": unique_name("updated_subject")},
    )
    assert response.status_code == 200


def test_admin_can_assign_teacher(client):
    login_as(client)
    teacher_id = insert_user(client, "teacher")
    created = client.post(
        "/api/subjects",
        json={"name": unique_name("subject")},
    )
    assert created.status_code == 201
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": teacher_id},
    )
    assert response.status_code == 200


def test_blank_class_name_rejected(client):
    login_as(client)
    response = client.post("/api/classes", json={"name": " "})
    assert response.status_code == 400


def test_blank_subject_name_rejected(client):
    login_as(client)
    response = client.post("/api/subjects", json={"name": " "})
    assert response.status_code == 400


def test_duplicate_class_name_rejected(client):
    login_as(client)
    name = unique_name("class")
    first = client.post("/api/classes", json={"name": name})
    second = client.post("/api/classes", json={"name": name})
    assert first.status_code == 201
    assert second.status_code == 409


def test_duplicate_subject_name_rejected(client):
    login_as(client)
    name = unique_name("subject")
    first = client.post("/api/subjects", json={"name": name})
    second = client.post("/api/subjects", json={"name": name})
    assert first.status_code == 201
    assert second.status_code == 409


def test_nonexistent_class_returns_404(client):
    login_as(client)
    response = client.put(
        "/api/classes/987654321",
        json={"name": unique_name("class")},
    )
    assert response.status_code == 404


def test_nonexistent_subject_returns_404(client):
    login_as(client)
    response = client.put(
        "/api/subjects/987654321",
        json={"name": unique_name("subject")},
    )
    assert response.status_code == 404


def test_student_cannot_be_assigned_as_teacher(client):
    login_as(client)
    student_id = insert_user(client, "student")
    created = client.post(
        "/api/subjects",
        json={"name": unique_name("subject")},
    )
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": student_id},
    )
    assert response.status_code == 400


def test_inactive_teacher_cannot_be_assigned(client):
    login_as(client)
    teacher_id = insert_user(client, "teacher", active=0)
    created = client.post(
        "/api/subjects",
        json={"name": unique_name("subject")},
    )
    subject_id = created.get_json()["subject"]["id"]

    response = client.put(
        f"/api/subjects/{subject_id}/teacher",
        json={"teacher_id": teacher_id},
    )
    assert response.status_code == 400


def test_unauthenticated_access_is_denied(client):
    assert client.get("/api/classes").status_code == 401
    assert client.get("/api/subjects").status_code == 401


def test_teacher_access_is_denied(client):
    login_as(client, "teacher")
    assert client.get("/api/classes").status_code == 403
    assert client.get("/api/subjects").status_code == 403


def test_student_access_is_denied(client):
    login_as(client, "student")
    assert client.get("/api/classes").status_code == 403
    assert client.get("/api/subjects").status_code == 403