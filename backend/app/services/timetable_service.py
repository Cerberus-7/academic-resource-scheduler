from sqlalchemy.orm import Session, joinedload
from app.models.scheduling import TimetableAllocation, AllocationStatus
from app.solver.cp_sat_scheduler import generate_timetable
from app.services.sync_service import SolverJobSlot, CommitLock
from app.services.analytics_service import log_audit


def run_full_generation(db: Session, actor_id: int, clear_existing: bool, max_solve_seconds: int):
    with SolverJobSlot():
        result = generate_timetable(db, max_solve_seconds=max_solve_seconds)

    if not result.success:
        return result

    with CommitLock():
        if clear_existing:
            db.query(TimetableAllocation).delete()
            db.flush()
        for alloc in result.allocations:
            db.add(TimetableAllocation(**alloc, status=AllocationStatus.ACTIVE, generated_by="cp_sat"))
        log_audit(db, actor_id, "GENERATE_TIMETABLE", "timetable", None,
                  f"Generated {len(result.allocations)} allocations via CP-SAT ({result.status_name}).")
        db.commit()
    return result


def list_allocations(db: Session, section_id=None, faculty_id=None, resource_id=None, day_of_week=None, course_id=None):
    query = db.query(TimetableAllocation).options(
        joinedload(TimetableAllocation.resource),
        joinedload(TimetableAllocation.faculty),
        joinedload(TimetableAllocation.section),
        joinedload(TimetableAllocation.course_session),
    ).filter(TimetableAllocation.status == AllocationStatus.ACTIVE)

    if section_id:
        query = query.filter(TimetableAllocation.section_id == section_id)
    if faculty_id:
        query = query.filter(TimetableAllocation.faculty_id == faculty_id)
    if resource_id:
        query = query.filter(TimetableAllocation.resource_id == resource_id)
    if day_of_week is not None:
        query = query.filter(TimetableAllocation.day_of_week == day_of_week)

    allocations = query.all()
    if course_id:
        allocations = [a for a in allocations if a.section and a.section.course_id == course_id]

    out = []
    for a in allocations:
        out.append({
            "id": a.id, "course_session_id": a.course_session_id, "resource_id": a.resource_id,
            "resource_name": a.resource.name if a.resource else "", "resource_code": a.resource.code if a.resource else "",
            "faculty_id": a.faculty_id, "faculty_name": a.faculty.full_name if a.faculty else "",
            "section_id": a.section_id, "section_name": a.section.name if a.section else "",
            "course_code": a.section.course.code if a.section and a.section.course else "",
            "course_name": a.section.course.name if a.section and a.section.course else "",
            "day_of_week": a.day_of_week, "start_slot_index": a.start_slot_index,
            "duration_hours": a.duration_hours, "status": a.status, "version": a.version,
        })
    return out
