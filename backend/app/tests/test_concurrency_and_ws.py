"""
Tests for the concurrency layer (threading.Lock + threading.Semaphore) and
the WebSocket live-notification channel. Separate module from
test_core_flows.py so it can run against its own isolated SQLite file.
"""
import os
import sys
import threading
import time

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DB = "/tmp/test_concurrency.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"


@pytest.fixture(scope="module")
def client():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    from app.core import config as config_module
    config_module.settings.DATABASE_URL = f"sqlite:///{TEST_DB}"
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


def test_concurrent_timetable_generations_do_not_corrupt_state(client):
    """Fire several full-timetable-generation requests at once. The
    threading.Lock around the commit section must serialize the actual
    writes, so the end result is always exactly one clean, non-overlapping
    timetable — never a partial or duplicated one — no matter how many
    requests raced to get there."""
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}

    results = []
    lock = threading.Lock()

    def fire():
        r = client.post("/api/timetable/generate", json={"clear_existing": True, "max_solve_seconds": 15}, headers=h)
        with lock:
            results.append(r.status_code)

    threads = [threading.Thread(target=fire) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert all(code == 200 for code in results), f"Some concurrent generations failed: {results}"

    allocations = client.get("/api/timetable", headers=h).json()
    seen_resource_slots = set()
    seen_faculty_slots = set()
    for a in allocations:
        for offset in range(a["duration_hours"]):
            r_key = (a["resource_id"], a["day_of_week"], a["start_slot_index"] + offset)
            f_key = (a["faculty_id"], a["day_of_week"], a["start_slot_index"] + offset)
            assert r_key not in seen_resource_slots, f"Concurrent writes corrupted state: room double-booked {r_key}"
            assert f_key not in seen_faculty_slots, f"Concurrent writes corrupted state: faculty double-booked {f_key}"
            seen_resource_slots.add(r_key)
            seen_faculty_slots.add(f_key)


def test_lock_serializes_concurrent_commits_and_is_reported(client):
    """Directly exercises CommitLock with threads that intentionally hold the
    lock for a short, overlapping window, so contention is deterministic
    rather than timing-dependent. Confirms: (a) the lock actually serializes
    access — no two threads are ever inside the critical section at once —
    and (b) at least one contention event is recorded on the dashboard."""
    from app.services.sync_service import CommitLock, get_dashboard_snapshot

    concurrent_inside = 0
    max_concurrent_inside = 0
    state_lock = threading.Lock()

    def worker():
        nonlocal concurrent_inside, max_concurrent_inside
        with CommitLock():
            with state_lock:
                concurrent_inside += 1
                max_concurrent_inside = max(max_concurrent_inside, concurrent_inside)
            time.sleep(0.15)
            with state_lock:
                concurrent_inside -= 1

    before = get_dashboard_snapshot()["lock_contention_events"]
    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    after = get_dashboard_snapshot()["lock_contention_events"]

    assert max_concurrent_inside == 1, "CommitLock failed to serialize concurrent commits"
    assert after > before, "Expected at least one lock-contention event to be recorded"


def test_sync_dashboard_reflects_real_generation_activity(client):
    """A real (sequential) generation call should still show up in the
    dashboard's recent-activity feed, confirming the two layers are wired
    together end-to-end (not just unit-testable in isolation)."""
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/timetable/generate", json={"clear_existing": True, "max_solve_seconds": 15}, headers=h)
    assert r.status_code == 200

    snapshot = client.get("/api/sync/dashboard", headers=h).json()
    assert snapshot["max_concurrent_jobs"] >= 1
    events = [a["event"] for a in snapshot["recent_activity"]]
    assert "job_started" in events and "job_finished" in events
    assert "lock_acquired" in events or "lock_contention" in events


def test_semaphore_bounds_concurrent_solver_jobs(client):
    """Directly exercises SolverJobSlot: launching more jobs than the
    configured semaphore limit must still complete all of them (later ones
    simply wait), and the dashboard must never report more active workers
    than the configured maximum at any single observation."""
    from app.services.sync_service import SolverJobSlot, get_dashboard_snapshot
    from app.core.config import settings

    observed_max_active = 0
    lock = threading.Lock()

    def worker():
        nonlocal observed_max_active
        with SolverJobSlot():
            with lock:
                snap = get_dashboard_snapshot()
                observed_max_active = max(observed_max_active, snap["active_workers"])
            time.sleep(0.2)

    threads = [threading.Thread(target=worker) for _ in range(settings.MAX_CONCURRENT_SOLVER_JOBS + 3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert observed_max_active <= settings.MAX_CONCURRENT_SOLVER_JOBS


def test_websocket_connects_and_receives_broadcast(client):
    """A WebSocket client with a valid token can connect, and a schedule
    request submission broadcasts a notification to admins over it."""
    token = admin_token(client)
    h = {"Authorization": f"Bearer {token}"}

    with client.websocket_connect(f"/ws?token={token}") as ws:
        r = client.post("/api/schedule-requests", headers=h, json={
            "request_type": "extra_class", "title": "WS test class",
            "reason": "testing websocket broadcast", "duration_hours": 1,
            "required_resource_type": "room", "base_priority": 5,
        })
        assert r.status_code == 200
        message = ws.receive_json(mode="text")
        assert message["event"] == "new_schedule_request"
        assert message["data"]["title"] == "WS test class"


def test_websocket_rejects_invalid_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=not-a-real-token"):
            pass
