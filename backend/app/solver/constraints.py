"""Helper predicates used while building the CP-SAT model.

These functions decide which (resource, day, start_slot) combinations are
even legal candidates for a course_session, based on capacity, resource type,
required facilities, faculty qualification/availability and maintenance
windows. The CP-SAT solver is still the final authority: these are used to
build the *candidate set* fed into the model, never to bypass NoOverlap /
capacity constraints inside the solver itself.
"""
from datetime import datetime, timedelta
from app.models.academic import Resource, ResourceType, Faculty, FacultyUnavailability, MaintenanceWindow
from app.models.scheduling import DAYS

SLOTS_PER_DAY = 8  # 9AM..5PM, 1-hour slots
WORK_DAYS = 6  # Mon-Sat


def slot_to_clock(slot_index: int) -> str:
    hour = 9 + slot_index
    return f"{hour:02d}:00"


def resource_matches_requirements(
    resource: Resource, required_type: str, min_capacity: int, required_facility_names: list[str]
) -> bool:
    if resource.resource_type.value != required_type:
        return False
    if resource.capacity < min_capacity:
        return False
    if not resource.is_active:
        return False
    have = {f.name for f in resource.facilities}
    for needed in required_facility_names:
        if needed and needed not in have:
            return False
    return True


def faculty_is_unavailable(
    faculty_id: int, day_of_week: int, start_slot: int, duration: int,
    unavailability_rows: list[FacultyUnavailability],
) -> bool:
    start_clock = slot_to_clock(start_slot)
    end_clock = slot_to_clock(start_slot + duration)
    for row in unavailability_rows:
        if row.faculty_id != faculty_id or row.day_of_week != day_of_week:
            continue
        if not (end_clock <= row.start_time or start_clock >= row.end_time):
            return True
    return False


def resource_under_maintenance(
    resource_id: int, day_of_week: int, start_slot: int, duration: int,
    maintenance_rows: list[MaintenanceWindow], week_anchor_monday: datetime,
) -> bool:
    """A maintenance window is stored as absolute datetimes; we map the
    candidate weekly slot onto the anchor week to check overlap."""
    slot_start = week_anchor_monday + timedelta(days=day_of_week, hours=9 + start_slot)
    slot_end = slot_start + timedelta(hours=duration)
    for mw in maintenance_rows:
        if mw.resource_id != resource_id:
            continue
        if not (slot_end <= mw.start_datetime or slot_start >= mw.end_datetime):
            return True
    return False
