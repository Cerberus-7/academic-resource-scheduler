# Architecture

## Layers

```
frontend/  React 18 + TS + Vite + MUI + React Query + Recharts
   ↓ REST (axios) + WebSocket
backend/app/
   api/routes/      FastAPI route handlers (thin — delegate to services)
   services/         Business logic orchestration (transactions, logging)
   solver/            OR-Tools CP-SAT — sole authority for placements
   os_simulation/    Priority/Aging/RoundRobin (ordering only) + Banker's Algorithm
   websocket/         Connection manager for live notifications
   models/            SQLAlchemy ORM models (SQLite)
   schemas/           Pydantic request/response contracts
   seed/               Demo data
```

## The three scheduling layers, and why they don't overlap

1. **CP-SAT (`solver/cp_sat_scheduler.py`)** — the only component allowed to
   decide *where* (room/lab/day/time/faculty) something goes. Used for full
   timetable generation and for validating every single shift alternative
   before it can be shown or approved.
2. **OS Scheduling (`os_simulation/priority_scheduler.py`, `aging_policy.py`,
   `round_robin.py`)** — decides *which pending request goes next* into the
   CP-SAT-backed placement search. It never touches a room/time/faculty
   directly.
3. **Banker's Algorithm (`os_simulation/banker_classic.py`,
   `banker_dynamic.py`)** — a standalone OS-safety teaching simulation over
   abstract resource units (`lecture_room_units`, `computer_lab_units`,
   `faculty_slot_units`, `projector_units`, `special_equipment_units`). It is
   never consulted by the real timetable engine.

## Concurrency

`services/sync_service.py` exposes:
- `CommitLock` — wraps `threading.Lock` around the read-check-commit section
  of every timetable write (full generation, ad-hoc request placement, shift
  application).
- `SolverJobSlot` — wraps `threading.Semaphore(MAX_CONCURRENT_SOLVER_JOBS)`
  around every CP-SAT invocation, so a burst of requests can't overload the
  server. It represents worker capacity only — never a room or lab.

Both publish a live in-memory activity log surfaced on the admin Sync
Dashboard page and polled every 2 seconds.

## Data flow: a shift request

1. Admin/coordinator (or an automatic disruption trigger) creates a
   `ShiftRequest` against an existing `TimetableAllocation`.
2. Suggested `ShiftAlternative`s are generated and *each one* is validated
   through `validate_placement_cp_sat()` before being shown — invalid ones
   are visibly marked and cannot be approved.
3. The affected professor discusses (via WebSocket-backed `DiscussionMessage`s),
   approves an alternative, rejects, or proposes their own (which is itself
   re-validated by CP-SAT).
4. On approval, `approval_service.apply_shift()` re-validates once more, then
   commits atomically inside `CommitLock`: the original allocation is marked
   `moved` and a new `active` allocation is created.

## Emergency override

`api/routes/sync_dashboard.py::emergency_override` lets an admin force-apply
an already-CP-SAT-valid alternative without waiting for professor approval,
for the configured emergency-demo scenario only. It still requires a
justification string and is unconditionally written to `audit_logs` with
`is_override=True`.
