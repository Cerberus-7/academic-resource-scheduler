# Changelog

## Security & repository hygiene
- Removed the hardcoded JWT signing key from `backend/app/core/config.py`.
  `SECRET_KEY` is now required and loaded from the environment or `backend/.env`;
  startup fails fast on a missing, placeholder, or short (<32 chars) key.
- Added `backend/.env.example` (placeholders only) and ignore rules for `.env` files.
- `.gitignore` now also covers `*.tsbuildinfo`, local databases, virtualenvs, and
  editor folders; removed the stray `frontend/tsconfig.tsbuildinfo` build artifact.
- Tests use a test-only key via `backend/conftest.py`.
- `docker-compose.yml` loads `backend/.env`; added `.dockerignore` files so secrets
  and local artifacts are not baked into images.

## Earlier updates

### 1. Table UX: search, sort, pagination (spec requirement)
- New reusable `frontend/src/components/DataTable.tsx` (search box, clickable
  sortable headers, pagination) with its own test suite (5 tests).
- Retrofitted onto: Rooms & Labs, Maintenance Windows, Faculty, Faculty
  Unavailability, Courses, Sections, Weekly Sessions, Request Queue history,
  Audit Log, My Requests, and Shift Requests — replacing the old plain
  `<Table>` markup on every one of those pages.

### 2. Inline editing
- New backend endpoints: `PUT /api/faculty/{id}`, `PUT /api/courses/{id}`,
  `PUT /api/courses/sections/{id}` (Resources already had `PUT /api/resources/{id}`).
- Admin UI: Rooms & Labs, Faculty, Courses, and Sections now have an Edit
  (pencil) action that opens the same dialog pre-filled, instead of
  create-only forms.
- **Bug found and fixed in the process:** the faculty edit form doesn't
  expose `user_id`, so saving an edit was silently unlinking the faculty
  member's login account. Fixed by only updating `user_id` when explicitly
  provided, with a regression test (`test_editing_faculty_does_not_unlink_user_account`).

### 3. Concurrency / load test for the Lock + Semaphore layer
- New `backend/app/tests/test_concurrency_and_ws.py`:
  - Fires 5 concurrent full-timetable-generation requests and asserts the
    result is still exactly one clean, non-overlapping timetable.
  - Directly drives `CommitLock` from 6 threads with an artificial overlap
    window and asserts only one thread is ever inside the critical section,
    and that contention is recorded on the sync dashboard.
  - Directly drives `SolverJobSlot` with more threads than the configured
    semaphore limit and asserts active-worker count never exceeds it.
  - Confirms a real (sequential) generation call shows up in the dashboard's
    activity feed end-to-end.
- **Bug found and fixed in the process:** `app/main.py`, `app/seed/seed_data.py`,
  and `app/services/backup_service.py` all imported `engine` *by value* at
  module load time (`from app.core.database import engine`). This is latent
  but harmless in normal single-process use (the engine never changes), yet
  it broke test isolation and is generally fragile — fixed by referencing
  `database_module.engine` dynamically instead, so these modules always see
  the current engine.

### 4. WebSocket automated tests
- `test_websocket_connects_and_receives_broadcast`: connects with a valid
  JWT, submits a schedule request, and asserts the `new_schedule_request`
  event arrives over the socket with the right payload.
- `test_websocket_rejects_invalid_token`: an invalid token is refused.

### 5. Bundle size / code-splitting
- Every page component is now loaded via `React.lazy()` behind a
  `<Suspense>` spinner per role-app, instead of one eager bundle.
- Main JS chunk: **1,044 KB → 522 KB** (gzip 310 KB → 170 KB); page code and
  the Recharts chart library now load on demand only when a page that needs
  them is actually visited.

### Not done (honest status)
- **Screenshots** (`docs/screenshots/`): this sandboxed build environment has
  no working headless browser (apt package fetch 404s on required
  dependencies; the available `chromium-browser` is a non-functional snap
  stub), so real screenshots could not be captured here. Run the app
  locally and add your own — the folder is ready for them.

### Test totals after this update
- Backend: **19 passing** (`pytest -q`) — up from 12.
- Frontend: **11 passing** (`npm test`) — up from 0.
