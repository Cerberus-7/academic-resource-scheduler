"""
OR-Tools CP-SAT timetable scheduler.

ARCHITECTURE RULE (enforced throughout the project):
CP-SAT is the ONLY final authority for timetable generation, room/lab/faculty
allocation and rescheduling. Priority Scheduling / Aging / Round Robin (see
app/os_simulation) only decide *ordering* of pending requests; they never
place a request onto the timetable themselves. Every placement — whether from
full generation or from a single shift-alternative proposal — is validated
here before being committed.
"""
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.models.academic import Resource, ResourceType, Faculty, FacultyUnavailability, MaintenanceWindow, CourseSession
from app.models.scheduling import TimetableAllocation, AllocationStatus
from app.solver.constraints import resource_matches_requirements, slot_to_clock, SLOTS_PER_DAY, WORK_DAYS

SLOT_DURATION_HOURS = 1


def _current_week_monday() -> datetime:
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def _allowed_starts(duration: int) -> list[int]:
    """Combined day*SLOTS_PER_DAY+slot values where a session of `duration`
    hours can start without running past the 9AM-5PM day boundary."""
    allowed = []
    for day in range(WORK_DAYS):
        for slot in range(0, SLOTS_PER_DAY - duration + 1):
            allowed.append(day * SLOTS_PER_DAY + slot)
    return allowed


def decode_combined(value: int) -> tuple[int, int]:
    return value // SLOTS_PER_DAY, value % SLOTS_PER_DAY


def encode_combined(day: int, slot: int) -> int:
    return day * SLOTS_PER_DAY + slot


class TimetableGenerationResult:
    def __init__(self, success, message, allocations, status_name, solve_time):
        self.success = success
        self.message = message
        self.allocations = allocations  # list of dicts
        self.status_name = status_name
        self.solve_time = solve_time


def generate_timetable(db: Session, max_solve_seconds: int = 30) -> TimetableGenerationResult:
    sessions = db.query(CourseSession).all()
    if not sessions:
        return TimetableGenerationResult(False, "No course sessions defined. Add courses/sections/sessions first.", [], "NO_INPUT", 0.0)

    resources = db.query(Resource).filter(Resource.is_active == True).all()  # noqa: E712
    unavailability_rows = db.query(FacultyUnavailability).all()
    maintenance_rows = db.query(MaintenanceWindow).all()
    anchor_monday = _current_week_monday()

    model = cp_model.CpModel()

    # Expand sessions_per_week into individual occurrences
    occurrences = []
    for s in sessions:
        for occ_idx in range(max(1, s.sessions_per_week)):
            occurrences.append({"session": s, "occ_idx": occ_idx})

    if not occurrences:
        return TimetableGenerationResult(False, "No session occurrences to schedule.", [], "NO_INPUT", 0.0)

    occ_vars = []  # per occurrence: dict with start var, interval, candidates
    resource_intervals: dict[int, list] = {r.id: [] for r in resources}
    faculty_intervals: dict[int, list] = {}
    section_intervals: dict[int, list] = {}

    for i, occ in enumerate(occurrences):
        session: CourseSession = occ["session"]
        duration = session.duration_hours
        allowed = _allowed_starts(duration)
        if not allowed:
            return TimetableGenerationResult(False, f"Session {session.id} duration {duration}h does not fit in any slot.", [], "INFEASIBLE_INPUT", 0.0)

        start_var = model.NewIntVarFromDomain(cp_model.Domain.FromValues(allowed), f"start_{i}")
        end_var = model.NewIntVar(0, WORK_DAYS * SLOTS_PER_DAY, f"end_{i}")
        model.Add(end_var == start_var + duration)
        interval = model.NewIntervalVar(start_var, duration, end_var, f"interval_{i}")

        # Exclude faculty-unavailable combined slots (unconditional — faculty fixed per session)
        for day in range(WORK_DAYS):
            for slot in range(0, SLOTS_PER_DAY - duration + 1):
                clock_start = slot_to_clock(slot)
                clock_end = slot_to_clock(slot + duration)
                blocked = False
                for row in unavailability_rows:
                    if row.faculty_id != session.faculty_id or row.day_of_week != day:
                        continue
                    if not (clock_end <= row.start_time or clock_start >= row.end_time):
                        blocked = True
                        break
                if blocked:
                    model.Add(start_var != encode_combined(day, slot))

        # Candidate resources matching type/capacity/facilities
        required_facilities = [f for f in (session.required_facility_names or "").split(",") if f]
        min_capacity = session.section.student_count if session.section else 0
        candidates = [
            r for r in resources
            if resource_matches_requirements(r, session.required_resource_type.value, min_capacity, required_facilities)
        ]
        if not candidates:
            return TimetableGenerationResult(
                False,
                f"No suitable {session.required_resource_type.value} found for session {session.id} "
                f"(section {session.section.name if session.section else '?'}, needs capacity>={min_capacity}, facilities={required_facilities}).",
                [], "INFEASIBLE_INPUT", 0.0,
            )

        presence_lits = []
        for r in candidates:
            presence = model.NewBoolVar(f"presence_{i}_{r.id}")
            opt_interval = model.NewOptionalIntervalVar(start_var, duration, end_var, presence, f"opt_{i}_{r.id}")
            # Exclude maintenance-blocked slots for this resource when this resource is chosen
            for day in range(WORK_DAYS):
                for slot in range(0, SLOTS_PER_DAY - duration + 1):
                    slot_start_dt = anchor_monday + timedelta(days=day, hours=9 + slot)
                    slot_end_dt = slot_start_dt + timedelta(hours=duration)
                    blocked = any(
                        mw.resource_id == r.id and not (slot_end_dt <= mw.start_datetime or slot_start_dt >= mw.end_datetime)
                        for mw in maintenance_rows
                    )
                    if blocked:
                        model.Add(start_var != encode_combined(day, slot)).OnlyEnforceIf(presence)
            resource_intervals[r.id].append(opt_interval)
            presence_lits.append(presence)

        model.AddExactlyOne(presence_lits)

        faculty_intervals.setdefault(session.faculty_id, []).append(interval)
        section_intervals.setdefault(session.section_id, []).append(interval)

        occ_vars.append({
            "session": session, "start_var": start_var, "duration": duration,
            "candidates": candidates, "presence_by_resource": dict(zip((r.id for r in candidates), presence_lits)),
        })

    for r_id, intervals in resource_intervals.items():
        if intervals:
            model.AddNoOverlap(intervals)
    for f_id, intervals in faculty_intervals.items():
        model.AddNoOverlap(intervals)
    for sec_id, intervals in section_intervals.items():
        model.AddNoOverlap(intervals)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_solve_seconds
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return TimetableGenerationResult(
            False,
            "CP-SAT could not find a feasible timetable with the current courses, faculty, and rooms. "
            "Try adding more rooms/labs, relaxing facility requirements, or reducing sessions.",
            [], status_name, solver.WallTime(),
        )

    results = []
    for ov in occ_vars:
        start_val = solver.Value(ov["start_var"])
        day, slot = decode_combined(start_val)
        chosen_resource_id = None
        for r_id, presence in ov["presence_by_resource"].items():
            if solver.Value(presence) == 1:
                chosen_resource_id = r_id
                break
        results.append({
            "course_session_id": ov["session"].id,
            "faculty_id": ov["session"].faculty_id,
            "section_id": ov["session"].section_id,
            "resource_id": chosen_resource_id,
            "day_of_week": day,
            "start_slot_index": slot,
            "duration_hours": ov["duration"],
        })

    return TimetableGenerationResult(True, "Timetable generated successfully.", results, status_name, solver.WallTime())


def validate_placement_cp_sat(
    db: Session, resource_id: int, faculty_id: int, section_id: int,
    day_of_week: int, start_slot_index: int, duration_hours: int,
    exclude_allocation_id: int | None = None,
) -> tuple[bool, str]:
    """CP-SAT feasibility check for a single proposed placement (used to
    validate shift-request alternatives before they can be approved/applied).
    Builds a tiny model: the proposed interval plus all other *active*
    committed allocations that share the same resource, faculty, or section,
    and checks NoOverlap holds."""
    resource = db.query(Resource).get(resource_id)
    if resource is None or not resource.is_active:
        return False, "Resource does not exist or is inactive."
    if start_slot_index < 0 or start_slot_index + duration_hours > SLOTS_PER_DAY:
        return False, "Proposed time does not fit within working hours (09:00-17:00)."
    if resource.capacity <= 0:
        return False, "Resource has no capacity configured."

    query = db.query(TimetableAllocation).filter(TimetableAllocation.status == AllocationStatus.ACTIVE)
    if exclude_allocation_id:
        query = query.filter(TimetableAllocation.id != exclude_allocation_id)
    others = query.filter(
        (TimetableAllocation.resource_id == resource_id)
        | (TimetableAllocation.faculty_id == faculty_id)
        | (TimetableAllocation.section_id == section_id)
    ).all()

    model = cp_model.CpModel()
    proposed_start = day_of_week * SLOTS_PER_DAY + start_slot_index
    proposed_end = proposed_start + duration_hours
    proposed_interval = model.NewIntervalVar(
        model.NewConstant(proposed_start), duration_hours, model.NewConstant(proposed_end), "proposed"
    )

    resource_group, faculty_group, section_group = [proposed_interval], [], []
    if faculty_id is not None:
        faculty_group.append(proposed_interval)
    section_group.append(proposed_interval)

    for idx, alloc in enumerate(others):
        a_start = alloc.day_of_week * SLOTS_PER_DAY + alloc.start_slot_index
        a_end = a_start + alloc.duration_hours
        iv = model.NewIntervalVar(model.NewConstant(a_start), alloc.duration_hours, model.NewConstant(a_end), f"existing_{idx}")
        if alloc.resource_id == resource_id:
            resource_group.append(iv)
        if alloc.faculty_id == faculty_id:
            faculty_group.append(iv)
        if alloc.section_id == section_id:
            section_group.append(iv)

    if len(resource_group) > 1:
        model.AddNoOverlap(resource_group)
    if len(faculty_group) > 1:
        model.AddNoOverlap(faculty_group)
    if len(section_group) > 1:
        model.AddNoOverlap(section_group)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return True, "Alternative validated by CP-SAT: no conflicts with room, faculty, or section."
    return False, "CP-SAT detected a conflict (room, faculty, or section already booked at this time)."
