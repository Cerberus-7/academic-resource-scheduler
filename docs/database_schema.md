# Database Schema (SQLite)

Generated from the SQLAlchemy models in `backend/app/models/`. SQLite is the primary database; JSON export/import is backup-only.

> **Design note:** rooms and laboratories share one `resources` table, distinguished by `resource_type` (`room` | `lab`). This lets CP-SAT treat them uniformly in NoOverlap constraints.


## `availability_windows`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| entity_type | VARCHAR(20) | no |  |
| entity_id | INTEGER | no |  |
| day_of_week | INTEGER | no |  |
| start_time | VARCHAR(5) | no |  |
| end_time | VARCHAR(5) | no |  |
| is_available | BOOLEAN | yes |  |

## `banker_simulation_states`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| snapshot_label | VARCHAR(100) | yes |  |
| resource_types | JSON | yes |  |
| available | JSON | yes |  |
| max_matrix | JSON | yes |  |
| allocation_matrix | JSON | yes |  |
| is_safe | BOOLEAN | yes |  |
| safe_sequence | JSON | yes |  |
| event | VARCHAR(120) | yes |  |
| created_at | DATETIME | yes |  |

## `courses`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| code | VARCHAR(30) | no | unique |
| name | VARCHAR(150) | no |  |
| credits | INTEGER | yes |  |
| requires_lab | BOOLEAN | yes |  |

## `facilities`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| name | VARCHAR(80) | no | unique |

## `resources`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| name | VARCHAR(80) | no |  |
| code | VARCHAR(30) | no | unique |
| resource_type | VARCHAR(4) | no |  |
| building | VARCHAR(80) | yes |  |
| floor | VARCHAR(20) | yes |  |
| capacity | INTEGER | no |  |
| is_active | BOOLEAN | yes |  |
| notes | TEXT | yes |  |

## `roles`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| name | VARCHAR(17) | no | unique |
| description | VARCHAR(255) | yes |  |

## `time_slots`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| day_of_week | INTEGER | no |  |
| start_time | VARCHAR(5) | no |  |
| end_time | VARCHAR(5) | no |  |
| slot_index | INTEGER | no |  |

## `resource_facilities`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| resource_id | INTEGER | no | PK, FK → resources.id |
| facility_id | INTEGER | no | PK, FK → facilities.id |

## `student_sections`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| name | VARCHAR(50) | no |  |
| course_id | INTEGER | no | FK → courses.id |
| student_count | INTEGER | yes |  |
| semester | INTEGER | yes |  |

## `users`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| full_name | VARCHAR(120) | no |  |
| email | VARCHAR(120) | no | unique |
| hashed_password | VARCHAR(255) | no |  |
| role_id | INTEGER | no | FK → roles.id |
| is_active | BOOLEAN | yes |  |
| created_at | DATETIME | yes |  |

## `audit_logs`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| actor_id | INTEGER | yes | FK → users.id |
| action | VARCHAR(100) | no |  |
| entity_type | VARCHAR(50) | yes |  |
| entity_id | INTEGER | yes |  |
| details | TEXT | yes |  |
| is_override | BOOLEAN | yes |  |
| created_at | DATETIME | yes |  |

## `faculty`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| user_id | INTEGER | yes | FK → users.id, unique |
| employee_code | VARCHAR(30) | no | unique |
| full_name | VARCHAR(120) | no |  |
| department | VARCHAR(120) | yes |  |
| designation | VARCHAR(80) | yes |  |

## `maintenance_windows`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| resource_id | INTEGER | no | FK → resources.id |
| start_datetime | DATETIME | no |  |
| end_datetime | DATETIME | no |  |
| reason | VARCHAR(255) | yes |  |
| created_by_id | INTEGER | yes | FK → users.id |
| created_at | DATETIME | yes |  |

## `course_sessions`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| section_id | INTEGER | no | FK → student_sections.id |
| faculty_id | INTEGER | no | FK → faculty.id |
| session_type | VARCHAR(8) | yes |  |
| duration_hours | INTEGER | yes |  |
| sessions_per_week | INTEGER | yes |  |
| required_resource_type | VARCHAR(4) | yes |  |
| required_facility_names | VARCHAR(255) | yes |  |

## `faculty_qualifications`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| faculty_id | INTEGER | no | PK, FK → faculty.id |
| course_id | INTEGER | no | PK, FK → courses.id |

## `faculty_unavailability`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| faculty_id | INTEGER | no | FK → faculty.id |
| day_of_week | INTEGER | no |  |
| start_time | VARCHAR(5) | no |  |
| end_time | VARCHAR(5) | no |  |
| reason | VARCHAR(255) | yes |  |
| created_at | DATETIME | yes |  |

## `timetable_allocations`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| course_session_id | INTEGER | yes | FK → course_sessions.id |
| resource_id | INTEGER | no | FK → resources.id |
| faculty_id | INTEGER | yes | FK → faculty.id |
| section_id | INTEGER | yes | FK → student_sections.id |
| day_of_week | INTEGER | no |  |
| start_slot_index | INTEGER | no |  |
| duration_hours | INTEGER | yes |  |
| status | VARCHAR(9) | yes |  |
| version | INTEGER | yes |  |
| generated_by | VARCHAR(30) | yes |  |
| title | VARCHAR(150) | yes |  |
| created_at | DATETIME | yes |  |
| updated_at | DATETIME | yes |  |

## `schedule_requests`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| request_type | VARCHAR(20) | no |  |
| requested_by_id | INTEGER | no | FK → users.id |
| course_id | INTEGER | yes | FK → courses.id |
| section_id | INTEGER | yes | FK → student_sections.id |
| faculty_id | INTEGER | yes | FK → faculty.id |
| title | VARCHAR(150) | yes |  |
| reason | TEXT | yes |  |
| student_count | INTEGER | yes |  |
| duration_hours | INTEGER | yes |  |
| required_resource_type | VARCHAR(10) | yes |  |
| required_facility_names | VARCHAR(255) | yes |  |
| preferred_day_of_week | INTEGER | yes |  |
| preferred_start_slot_index | INTEGER | yes |  |
| base_priority | INTEGER | yes |  |
| arrival_time | DATETIME | yes |  |
| status | VARCHAR(20) | yes |  |
| started_processing_at | DATETIME | yes |  |
| completed_at | DATETIME | yes |  |
| assigned_allocation_id | INTEGER | yes | FK → timetable_allocations.id |
| failure_reason | VARCHAR(255) | yes |  |

## `shift_requests`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| original_allocation_id | INTEGER | no | FK → timetable_allocations.id |
| affected_faculty_id | INTEGER | no | FK → faculty.id |
| requested_by_id | INTEGER | no | FK → users.id |
| reason_code | VARCHAR(17) | yes |  |
| reason_text | TEXT | yes |  |
| base_priority | INTEGER | yes |  |
| arrival_time | DATETIME | yes |  |
| decision_deadline | DATETIME | yes |  |
| status | VARCHAR(20) | yes |  |
| final_decision | VARCHAR(20) | yes |  |
| linked_schedule_request_id | INTEGER | yes | FK → schedule_requests.id |
| created_at | DATETIME | yes |  |
| updated_at | DATETIME | yes |  |

## `discussion_messages`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| shift_request_id | INTEGER | no | FK → shift_requests.id |
| sender_id | INTEGER | no | FK → users.id |
| message | TEXT | no |  |
| created_at | DATETIME | yes |  |

## `scheduler_metrics`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| schedule_request_id | INTEGER | yes | FK → schedule_requests.id |
| shift_request_id | INTEGER | yes | FK → shift_requests.id |
| algorithm | VARCHAR(30) | yes |  |
| base_priority | INTEGER | yes |  |
| effective_priority | FLOAT | yes |  |
| wait_time_seconds | FLOAT | yes |  |
| completed | BOOLEAN | yes |  |
| created_at | DATETIME | yes |  |

## `shift_alternatives`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| shift_request_id | INTEGER | no | FK → shift_requests.id |
| proposed_by_id | INTEGER | yes | FK → users.id |
| resource_id | INTEGER | no | FK → resources.id |
| day_of_week | INTEGER | no |  |
| start_slot_index | INTEGER | no |  |
| duration_hours | INTEGER | yes |  |
| is_cp_sat_valid | BOOLEAN | yes |  |
| validation_message | VARCHAR(255) | yes |  |
| is_selected | BOOLEAN | yes |  |
| created_at | DATETIME | yes |  |

## `approval_responses`

| Column | Type | Nullable | Key / FK |
|---|---|---|---|
| id | INTEGER | no | PK |
| shift_request_id | INTEGER | no | FK → shift_requests.id |
| responder_id | INTEGER | no | FK → users.id |
| action | VARCHAR(20) | no |  |
| alternative_id | INTEGER | yes | FK → shift_alternatives.id |
| comment | TEXT | yes |  |
| created_at | DATETIME | yes |  |
