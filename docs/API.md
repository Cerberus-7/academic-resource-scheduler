# REST & WebSocket API

Generated from the FastAPI OpenAPI schema. Interactive docs: http://127.0.0.1:8000/docs

All endpoints except `POST /api/auth/login` and `GET /api/health` require `Authorization: Bearer <JWT>`.

Role restrictions are enforced server-side via `require_roles(...)` in `app/api/deps.py`.

## WebSocket

`ws://127.0.0.1:8000/ws?token=<JWT>` — server pushes JSON `{event, data}`. Events: `new_schedule_request`, `new_shift_request`, `shift_status_updated`, `new_discussion_message`, `timetable_updated`.


## analytics

| Method | Path | Summary |
|---|---|---|
| GET | `/api/analytics/audit-logs` | Audit Logs |
| GET | `/api/analytics/dashboard` | Dashboard |
| GET | `/api/analytics/scheduler-metrics` | Scheduler Metrics |
| GET | `/api/analytics/utilization` | Utilization |

## auth

| Method | Path | Summary |
|---|---|---|
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Me |

## availability

| Method | Path | Summary |
|---|---|---|
| GET | `/api/availability/search` | Search |

## backup

| Method | Path | Summary |
|---|---|---|
| GET | `/api/backup/export` | Export Backup |
| POST | `/api/backup/import` | Import Backup |

## banker-simulation

| Method | Path | Summary |
|---|---|---|
| POST | `/api/banker/add-process` | Add Process |
| POST | `/api/banker/add-resource` | Add Resource |
| GET | `/api/banker/history` | Get History |
| POST | `/api/banker/init` | Init |
| POST | `/api/banker/reduce-capacity` | Reduce Capacity |
| POST | `/api/banker/release` | Release Resources |
| POST | `/api/banker/request` | Request Resources |
| GET | `/api/banker/resource-types` | Resource Types |
| GET | `/api/banker/state` | Get State |

## courses

| Method | Path | Summary |
|---|---|---|
| GET | `/api/courses` | List Courses |
| POST | `/api/courses` | Create Course |
| GET | `/api/courses/sections` | List Sections |
| POST | `/api/courses/sections` | Create Section |
| GET | `/api/courses/sessions` | List Sessions |
| POST | `/api/courses/sessions` | Create Session |
| DELETE | `/api/courses/sessions/{session_id}` | Delete Session |

## faculty

| Method | Path | Summary |
|---|---|---|
| GET | `/api/faculty` | List Faculty |
| POST | `/api/faculty` | Create Faculty |
| GET | `/api/faculty/unavailability` | List Unavailability |
| POST | `/api/faculty/unavailability` | Create Unavailability |
| DELETE | `/api/faculty/unavailability/{row_id}` | Delete Unavailability |

## other

| Method | Path | Summary |
|---|---|---|
| GET | `/api/health` | Health |

## rescheduling

| Method | Path | Summary |
|---|---|---|
| POST | `/api/rescheduling/trigger` | Trigger |

## resources

| Method | Path | Summary |
|---|---|---|
| GET | `/api/resources` | List Resources |
| POST | `/api/resources` | Create Resource |
| GET | `/api/resources/facilities` | List Facilities |
| GET | `/api/resources/maintenance` | List Maintenance |
| POST | `/api/resources/maintenance` | Create Maintenance |
| DELETE | `/api/resources/maintenance/{maintenance_id}` | Delete Maintenance |
| DELETE | `/api/resources/{resource_id}` | Deactivate Resource |
| PUT | `/api/resources/{resource_id}` | Update Resource |

## schedule-requests

| Method | Path | Summary |
|---|---|---|
| GET | `/api/schedule-requests` | List Requests |
| POST | `/api/schedule-requests` | Create Request |
| POST | `/api/schedule-requests/process-all` | Process All |
| POST | `/api/schedule-requests/process-next` | Process Next |
| GET | `/api/schedule-requests/queue` | Get Queue |
| POST | `/api/schedule-requests/{request_id}/cancel` | Cancel Request |

## shift-requests

| Method | Path | Summary |
|---|---|---|
| GET | `/api/shift-requests` | List Shift Requests |
| POST | `/api/shift-requests` | Create Shift Request |
| GET | `/api/shift-requests/{shift_id}` | Get Shift Request |
| POST | `/api/shift-requests/{shift_id}/action` | Take Action |
| GET | `/api/shift-requests/{shift_id}/discussion` | Get Discussion |
| POST | `/api/shift-requests/{shift_id}/discussion` | Post Discussion |

## sync

| Method | Path | Summary |
|---|---|---|
| GET | `/api/sync/dashboard` | Sync Dashboard |
| POST | `/api/sync/emergency-override` | Emergency Override |

## timetable

| Method | Path | Summary |
|---|---|---|
| GET | `/api/timetable` | Get Timetable |
| POST | `/api/timetable/generate` | Generate |

## users

| Method | Path | Summary |
|---|---|---|
| GET | `/api/users` | List Users |
