from datetime import datetime
from sqlalchemy.orm import Session
from app.models.requests import ShiftRequest, ShiftAlternative, ApprovalResponse, RequestStatus, DiscussionMessage
from app.models.scheduling import TimetableAllocation, AllocationStatus
from app.solver.cp_sat_scheduler import validate_placement_cp_sat
from app.services.sync_service import CommitLock
from app.services.analytics_service import log_audit


def create_shift_request(db: Session, actor_id: int, payload) -> ShiftRequest:
    original = db.query(TimetableAllocation).get(payload.original_allocation_id)
    if original is None:
        raise ValueError("Original allocation not found.")

    shift = ShiftRequest(
        original_allocation_id=original.id,
        affected_faculty_id=original.faculty_id,
        requested_by_id=actor_id,
        reason_code=payload.reason_code,
        reason_text=payload.reason_text,
        base_priority=payload.base_priority,
        decision_deadline=payload.decision_deadline,
        status=RequestStatus.PENDING,
    )
    db.add(shift)
    db.flush()

    for alt in payload.suggested_alternatives:
        ok, msg = validate_placement_cp_sat(
            db, resource_id=alt.resource_id, faculty_id=original.faculty_id, section_id=original.section_id,
            day_of_week=alt.day_of_week, start_slot_index=alt.start_slot_index, duration_hours=alt.duration_hours,
            exclude_allocation_id=original.id,
        )
        db.add(ShiftAlternative(
            shift_request_id=shift.id, proposed_by_id=actor_id, resource_id=alt.resource_id,
            day_of_week=alt.day_of_week, start_slot_index=alt.start_slot_index, duration_hours=alt.duration_hours,
            is_cp_sat_valid=ok, validation_message=msg,
        ))
    if payload.suggested_alternatives:
        shift.status = RequestStatus.ALTERNATIVE_PROPOSED

    log_audit(db, actor_id, "CREATE_SHIFT_REQUEST", "shift_request", shift.id,
              f"Reason: {payload.reason_code}. {len(payload.suggested_alternatives)} alternative(s) proposed.")
    db.commit()
    db.refresh(shift)
    return shift


def add_discussion_message(db: Session, actor_id: int, shift_request_id: int, message: str) -> DiscussionMessage:
    shift = db.query(ShiftRequest).get(shift_request_id)
    if shift is None:
        raise ValueError("Shift request not found.")
    if shift.status == RequestStatus.PENDING:
        shift.status = RequestStatus.UNDER_DISCUSSION
    msg = DiscussionMessage(shift_request_id=shift_request_id, sender_id=actor_id, message=message)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def apply_shift(db: Session, shift: ShiftRequest, alternative: ShiftAlternative, actor_id: int | None):
    """Final CP-SAT re-validation + atomic commit of an approved shift."""
    original = db.query(TimetableAllocation).get(shift.original_allocation_id)
    ok, msg = validate_placement_cp_sat(
        db, resource_id=alternative.resource_id, faculty_id=original.faculty_id, section_id=original.section_id,
        day_of_week=alternative.day_of_week, start_slot_index=alternative.start_slot_index,
        duration_hours=alternative.duration_hours, exclude_allocation_id=original.id,
    )
    if not ok:
        shift.status = RequestStatus.FAILED
        shift.final_decision = "failed"
        log_audit(db, actor_id, "SHIFT_APPLY_FAILED", "shift_request", shift.id, msg)
        db.commit()
        return False, msg

    with CommitLock():
        original.status = AllocationStatus.MOVED
        db.add(TimetableAllocation(
            course_session_id=original.course_session_id, resource_id=alternative.resource_id,
            faculty_id=original.faculty_id, section_id=original.section_id,
            day_of_week=alternative.day_of_week, start_slot_index=alternative.start_slot_index,
            duration_hours=alternative.duration_hours, status=AllocationStatus.ACTIVE,
            generated_by="shift_applied", title=original.title,
        ))
        alternative.is_selected = True
        shift.status = RequestStatus.APPLIED
        shift.final_decision = "applied"
        log_audit(db, actor_id, "SHIFT_APPLIED", "shift_request", shift.id,
                  f"Moved allocation {original.id} to resource {alternative.resource_id}, "
                  f"day {alternative.day_of_week}, slot {alternative.start_slot_index}.")
        db.commit()
    return True, "Shift applied and committed to timetable."


def professor_action(db: Session, actor_id: int, shift_request_id: int, action: str,
                      alternative_id: int | None, new_alternative, comment: str):
    shift = db.query(ShiftRequest).get(shift_request_id)
    if shift is None:
        raise ValueError("Shift request not found.")

    db.add(ApprovalResponse(shift_request_id=shift.id, responder_id=actor_id, action=action,
                             alternative_id=alternative_id, comment=comment))

    if action == "reject":
        shift.status = RequestStatus.REJECTED
        shift.final_decision = "rejected"
        log_audit(db, actor_id, "SHIFT_REJECTED", "shift_request", shift.id, comment)
        db.commit()
        return {"status": shift.status, "message": "Shift request rejected."}

    if action == "approve":
        if not alternative_id:
            raise ValueError("alternative_id is required to approve a shift.")
        alt = db.query(ShiftAlternative).get(alternative_id)
        if alt is None or alt.shift_request_id != shift.id:
            raise ValueError("Alternative not found for this shift request.")
        if not alt.is_cp_sat_valid:
            raise ValueError("This alternative failed CP-SAT validation and cannot be approved.")
        ok, msg = apply_shift(db, shift, alt, actor_id)
        return {"status": shift.status, "message": msg}

    if action == "propose_alternative":
        if not new_alternative:
            raise ValueError("new_alternative payload is required.")
        original = db.query(TimetableAllocation).get(shift.original_allocation_id)
        ok, msg = validate_placement_cp_sat(
            db, resource_id=new_alternative.resource_id, faculty_id=original.faculty_id,
            section_id=original.section_id, day_of_week=new_alternative.day_of_week,
            start_slot_index=new_alternative.start_slot_index, duration_hours=new_alternative.duration_hours,
            exclude_allocation_id=original.id,
        )
        alt = ShiftAlternative(
            shift_request_id=shift.id, proposed_by_id=actor_id, resource_id=new_alternative.resource_id,
            day_of_week=new_alternative.day_of_week, start_slot_index=new_alternative.start_slot_index,
            duration_hours=new_alternative.duration_hours, is_cp_sat_valid=ok, validation_message=msg,
        )
        db.add(alt)
        shift.status = RequestStatus.ALTERNATIVE_PROPOSED
        log_audit(db, actor_id, "SHIFT_ALTERNATIVE_PROPOSED", "shift_request", shift.id, msg)
        db.commit()
        return {"status": shift.status, "message": msg, "cp_sat_valid": ok}

    raise ValueError(f"Unknown action '{action}'.")
