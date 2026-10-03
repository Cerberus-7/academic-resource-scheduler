"""
Synchronization primitives for the scheduling engine.

- `timetable_commit_lock` (threading.Lock): guards the read-check-commit
  critical section for any write to timetable_allocations (full generation,
  single-request placement, or shift application). Only one commit can be
  in-flight at a time, preventing lost-update races between concurrently
  submitted requests.
- `solver_job_semaphore` (threading.Semaphore): bounds how many CP-SAT solver
  jobs can run concurrently (default 3), so a burst of requests can't starve
  the server's CPU. It represents *worker capacity*, never a room or lab.
"""
import threading
import time
from collections import deque
from datetime import datetime
from app.core.config import settings

timetable_commit_lock = threading.Lock()
solver_job_semaphore = threading.Semaphore(settings.MAX_CONCURRENT_SOLVER_JOBS)

_activity_log = deque(maxlen=200)
_activity_lock = threading.Lock()
_active_workers = 0
_waiting_workers = 0
_lock_contention_events = 0
_state_lock = threading.Lock()


def _record(event: str, detail: str):
    with _activity_lock:
        _activity_log.append({
            "event": event, "detail": detail, "timestamp": datetime.utcnow().isoformat()
        })


def get_dashboard_snapshot() -> dict:
    with _state_lock:
        return {
            "active_workers": _active_workers,
            "waiting_workers": _waiting_workers,
            "lock_contention_events": _lock_contention_events,
            "max_concurrent_jobs": settings.MAX_CONCURRENT_SOLVER_JOBS,
            "recent_activity": list(_activity_log)[-30:][::-1],
        }


class SolverJobSlot:
    """Context manager acquiring a bounded semaphore slot for a solver job."""

    def __enter__(self):
        global _active_workers, _waiting_workers
        with _state_lock:
            _waiting_workers += 1
        _record("job_queued", "Waiting for a free solver worker slot")
        acquired = solver_job_semaphore.acquire(timeout=60)
        with _state_lock:
            _waiting_workers -= 1
            if acquired:
                _active_workers += 1
        if not acquired:
            _record("job_timeout", "Timed out waiting for a solver worker slot")
            raise TimeoutError("Timed out waiting for a free solver worker slot.")
        _record("job_started", "Solver worker slot acquired")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _active_workers
        solver_job_semaphore.release()
        with _state_lock:
            _active_workers -= 1
        _record("job_finished", "Solver worker slot released")
        return False


class CommitLock:
    """Context manager for the atomic read-check-commit critical section."""

    def __enter__(self):
        global _lock_contention_events
        acquired_immediately = timetable_commit_lock.acquire(blocking=False)
        if not acquired_immediately:
            with _state_lock:
                _lock_contention_events += 1
            _record("lock_contention", "Another commit was in progress — waited for lock")
            timetable_commit_lock.acquire(blocking=True)
        else:
            _record("lock_acquired", "Commit lock acquired immediately")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        timetable_commit_lock.release()
        _record("lock_released", "Commit lock released")
        return False
