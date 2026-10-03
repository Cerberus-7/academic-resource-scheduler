import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DB = "/tmp/test_academic_scheduler.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"


@pytest.fixture(scope="module")
def client():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    from app.core import config as config_module
    config_module.settings.DATABASE_URL = f"sqlite:///{TEST_DB}"
    from app.core.database import engine
    engine.dispose()
    import sqlalchemy
    new_engine = sqlalchemy.create_engine(config_module.settings.DATABASE_URL, connect_args={"check_same_thread": False})
    from app.core import database as database_module
    database_module.engine = new_engine
    database_module.SessionLocal.configure(bind=new_engine)

    from app.main import app
    with TestClient(app) as c:
        yield c
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def admin_token(client):
    r = client.post("/api/auth/login", json={"email": "admin@college.edu", "password": "Admin@123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_login_success(client):
    r = client.post("/api/auth/login", json={"email": "admin@college.edu", "password": "Admin@123"})
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"


def test_login_failure(client):
    r = client.post("/api/auth/login", json={"email": "admin@college.edu", "password": "wrong"})
    assert r.status_code == 401


def test_generate_timetable(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/timetable/generate", json={"clear_existing": True, "max_solve_seconds": 20}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["allocations_created"] > 0


def test_no_double_booking_in_generated_timetable(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    allocations = client.get("/api/timetable", headers=h).json()
    seen_resource_slots = set()
    seen_faculty_slots = set()
    for a in allocations:
        for offset in range(a["duration_hours"]):
            r_key = (a["resource_id"], a["day_of_week"], a["start_slot_index"] + offset)
            f_key = (a["faculty_id"], a["day_of_week"], a["start_slot_index"] + offset)
            assert r_key not in seen_resource_slots, f"Room double-booked: {r_key}"
            assert f_key not in seen_faculty_slots, f"Faculty double-booked: {f_key}"
            seen_resource_slots.add(r_key)
            seen_faculty_slots.add(f_key)


def test_banker_safe_state(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/banker/init", headers=h, json={
        "total_resources": [10, 5, 8, 4, 3],
        "processes": {"P1": [4, 2, 3, 1, 1], "P2": [3, 1, 2, 2, 1]},
        "allocation": {"P1": [2, 1, 1, 0, 0], "P2": [1, 0, 1, 1, 0]},
    })
    assert r.status_code == 200
    assert r.json()["is_safe"] is True


def test_banker_rejects_unsafe_request(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/banker/request", headers=h, json={"process_name": "P1", "request_vector": [100, 0, 0, 0, 0]})
    # Banker service reports rejection in the response body (200) rather than
    # a client error, since this is a normal/expected simulation outcome.
    assert r.status_code == 200
    body = r.json()
    assert "exceeds" in body["message"] or "unsafe" in body["message"].lower()


def test_availability_search(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/availability/search", headers=h, params={
        "day_of_week": 5, "start_time": "09:00", "duration_hours": 1, "min_capacity": 10,
    })
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_schedule_request_and_queue_processing(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/schedule-requests", headers=h, json={
        "request_type": "extra_class", "section_id": 1, "faculty_id": 1, "title": "Extra Class",
        "reason": "test", "duration_hours": 1, "required_resource_type": "room", "base_priority": 1,
    })
    assert r.status_code == 200
    r2 = client.post("/api/schedule-requests/process-next", headers=h)
    assert r2.status_code == 200
    assert r2.json()["processed"] is True


def test_backup_export_and_import_roundtrip(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/backup/export", headers=h)
    assert r.status_code == 200
    backup = r.json()
    assert "tables" in backup
    assert backup["tables"]["users"], "Expected seeded users in export"
    original_allocation_count = len(backup["tables"]["timetable_allocations"])

    import io
    files = {"file": ("backup.json", io.BytesIO(r.content), "application/json")}
    r2 = client.post("/api/backup/import", headers=h, files=files, params={"clear_existing": True})
    assert r2.status_code == 200
    counts = r2.json()["row_counts"]
    assert counts["timetable_allocations"] == original_allocation_count
    assert counts["users"] == len(backup["tables"]["users"])

    # Data must be usable again immediately after restore (re-login, re-list)
    r3 = client.post("/api/auth/login", json={"email": "admin@college.edu", "password": "Admin@123"})
    assert r3.status_code == 200
    r4 = client.get("/api/timetable", headers=h)
    assert len(r4.json()) == original_allocation_count


def test_backup_import_rejects_invalid_json(client):
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    import io
    files = {"file": ("bad.json", io.BytesIO(b"not json"), "application/json")}
    r = client.post("/api/backup/import", headers=h, files=files)
    assert r.status_code == 400


def test_editing_faculty_does_not_unlink_user_account(client):
    """Regression test: the admin faculty-edit form doesn't expose user_id,
    so PUT /api/faculty/{id} must never null out an existing login link
    just because the payload omitted it."""
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    faculty_list = client.get("/api/faculty", headers=h).json()
    linked = next(f for f in faculty_list if f["user_id"] is not None)

    r = client.put(f"/api/faculty/{linked['id']}", headers=h, json={
        "employee_code": linked["employee_code"], "full_name": linked["full_name"] + " (edited)",
        "department": linked["department"], "designation": linked["designation"], "qualified_course_ids": [],
    })
    assert r.status_code == 200
    assert r.json()["user_id"] == linked["user_id"], "Edit must not unlink the faculty member's user account"


def test_role_based_access_denied_for_student(client):
    r = client.post("/api/auth/login", json={"email": "student@college.edu", "password": "Student@123"})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r2 = client.post("/api/timetable/generate", json={"clear_existing": True}, headers=h)
    assert r2.status_code == 403
