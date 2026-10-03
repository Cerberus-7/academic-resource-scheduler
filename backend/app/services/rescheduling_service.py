from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.scheduling import TimetableAllocation, AllocationStatus
from app.models.requests import ShiftRequest, ShiftAlternative, ShiftReason, RequestStatus
from app.models.academic import Resource
from app.solver.cp_sat_scheduler import validate_placement_cp_sat, SLOTS_PER_DAY
from app.solver.objectives import disruption_score
from app.services.analytics_service import log_audit


def find_affected_allocations(db: Session, trigger: str, faculty_id: int | None = None,
                               resource_id: int | None = None, day_of_week: int | None = None) -> list[TimetableAllocation]:
    query = db.query(TimetableAllocation).filter(TimetableAllocation.status == AllocationStatus.ACTIVE)
    if faculty_id:
        query = query.filter(TimetableAllocation.faculty_id == faculty_id)
    if resource_id:
        query = query.filter(TimetableAllocation.resource_id == resource_id)
    if day_of_week is not None:
        query = query.filter(TimetableAllocation.day_of_week == day_of_week)
    return query.all()


def generate_minimal_disruption_alternatives(db: Session, allocation: TimetableAllocation, top_n: int = 3) -> list[dict]:
    """Search all (resource, day, start_slot) combos, CP-SAT-validate each,
    score by disruption, and return the top_n least-disruptive valid options."""
    resources = db.query(Resource).filter(
        Resource.is_active == True,  # noqa: E712
        Resource.capacity >= (allocation.section.student_count if allocation.section else 0),
    ).all()
    if allocation.resource and allocation.resource not in resources:
        resources.append(allocation.resource)

    candidates = []
    for r in resources:
        for day in range(6):
            for slot in range(0, SLOTS_PER_DAY - allocation.duration_hours + 1):
                if r.id == allocation.resource_id and day == allocation.day_of_week and slot == allocation.start_slot_index:
                    continue
                ok, msg = validate_placement_cp_sat(
                    db, resource_id=r.id, faculty_id=allocation.faculty_id, section_id=allocation.section_id,
                    day_of_week=day, start_slot_index=slot, duration_hours=allocation.duration_hours,
                    exclude_allocation_id=allocation.id,
                )
                if not ok:
                    continue
                score = disruption_score(
                    allocation.resource_id, r.id, allocation.day_of_week, day,
                    allocation.start_slot_index, slot, allocation.faculty_id, allocation.faculty_id,
                )
                candidates.append({"resource_id": r.id, "day_of_week": day, "start_slot_index": slot,
                                    "duration_hours": allocation.duration_hours, "score": score, "message": msg})
    candidates.sort(key=lambda c: c["score"])
    return candidates[:top_n]


def trigger_dynamic_reschedule(db: Session, actor_id: int, reason_code: ShiftReason, reason_text: str,
                                faculty_id: int | None = None, resource_id: int | None = None,
                                day_of_week: int | None = None) -> list[ShiftRequest]:
    """Entry point for admin-triggered disruptions (faculty absence, maintenance,
    equipment failure, room closure, cancellation, etc). For each affected
    active allocation, auto-creates a shift_request with CP-SAT-validated,
    minimal-disruption alternatives already attached, awaiting professor
    approval — nothing is moved automatically."""
    affected = find_affected_allocations(db, reason_code.value, faculty_id, resource_id, day_of_week)
    created = []
    for alloc in affected:
        shift = ShiftRequest(
            original_allocation_id=alloc.id, affected_faculty_id=alloc.faculty_id,
            requested_by_id=actor_id, reason_code=reason_code, reason_text=reason_text,
            base_priority=2, status=RequestStatus.PENDING,
            decision_deadline=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(shift)
        db.flush()
        alternatives = generate_minimal_disruption_alternatives(db, alloc)
        for alt in alternatives:
            db.add(ShiftAlternative(
                shift_request_id=shift.id, resource_id=alt["resource_id"], day_of_week=alt["day_of_week"],
                start_slot_index=alt["start_slot_index"], duration_hours=alt["duration_hours"],
                is_cp_sat_valid=True, validation_message=alt["message"],
            ))
        if alternatives:
            shift.status = RequestStatus.ALTERNATIVE_PROPOSED
        log_audit(db, actor_id, "AUTO_SHIFT_REQUEST_CREATED", "shift_request", shift.id,
                  f"Trigger={reason_code.value}. {len(alternatives)} CP-SAT-valid alternative(s) generated for allocation {alloc.id}.")
        created.append(shift)
    db.commit()
    for s in created:
        db.refresh(s)
    return created
