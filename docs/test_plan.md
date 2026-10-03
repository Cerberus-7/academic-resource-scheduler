# Test Plan

## Automated backend tests (`backend/app/tests/test_core_flows.py`, run with `pytest -q`)

| # | Test | Verifies |
|---|------|----------|
| 1 | test_health | API boots and responds |
| 2 | test_login_success / failure | JWT login, bad password → 401 |
| 3 | test_generate_timetable | CP-SAT returns a feasible timetable and stores allocations |
| 4 | test_no_double_booking_in_generated_timetable | No room or faculty is booked twice in the same slot (NoOverlap holds) |
| 5 | test_banker_safe_state | Classical Banker safety check on a safe initial state |
| 6 | test_banker_rejects_unsafe_request | Over-need request is rejected, state unchanged |
| 7 | test_availability_search | Search returns resources with availability windows |
| 8 | test_schedule_request_and_queue_processing | Priority queue picks a request; CP-SAT places it |
| 9 | test_backup_export_and_import_roundtrip | JSON export → import restores every table; login still works |
| 10 | test_backup_import_rejects_invalid_json | Bad upload → 400, no data loss |
| 11 | test_role_based_access_denied_for_student | RBAC: student cannot generate timetable (403) |

## Automated frontend tests (`frontend`, run with `npm test`)
StatusChip colour mapping, KpiCard rendering, TimetableGrid placement of multi-hour sessions.

## Manual acceptance checklist
1. Log in as each of the 4 demo roles; confirm each sees only its own sidebar.
2. Admin → Timetable Generator → generate; open Weekly Timetable and confirm no overlaps.
3. Professor → Find Room/Lab → search; Request Extra Class → submit.
4. Admin → Request Queue → Process Next; confirm status becomes `applied` and the allocation appears.
5. Admin → add a maintenance window on a busy room; trigger rescheduling; professor sees a shift request with CP-SAT-validated alternatives, discusses, approves; timetable updates.
6. Admin → OS Simulation → initialise, request/release, add process, reduce capacity; unsafe requests are rejected.
7. Admin → Sync Dashboard shows semaphore/lock activity while generating.
8. Admin → Backup & Restore → download, then restore; data intact.

## Known gaps
No load/concurrency stress test; WebSocket delivery is verified manually only.
