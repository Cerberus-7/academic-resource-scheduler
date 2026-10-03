from datetime import datetime
from sqlalchemy.orm import Session
from app.models.requests import ScheduleRequest, RequestStatus
from app.models.scheduling import TimetableAllocation, AllocationStatus
from app.models.logs import SchedulerMetric
from app.os_simulation.priority_scheduler import QueueItem, order_by_priority_with_aging
from app.os_simulation.round_robin import apply_round_robin_tiebreak
from app.os_simulation.aging_policy import effective_priority, waiting_seconds
from app.solver.cp_sat_scheduler import validate_placement_cp_sat, SLOTS_PER_DAY
from app.services.availability_service import search_availability
from app.services.sync_service import SolverJobSlot, CommitLock
from app.services.analytics_service import log_audit


def get_ordered_pending_queue(db: Session) -> list[dict]:
    pending = db.query(ScheduleRequest).filter(ScheduleRequest.status == RequestStatus.PENDING).all()
    items = [
        QueueItem(request_id=p.id, request_kind="schedule_request", base_priority=p.base_priority, arrival_time=p.arrival_time)
        for p in pending
    ]
    ordered = order_by_priority_with_aging(items)
    ordered = apply_round_robin_tiebreak(ordered)
    by_id = {p.id: p for p in pending}
    result = []
    for it in ordered:
        req = by_id[it.request_id]
        result.append({
            "id": req.id, "request_type": req.request_type, "requested_by_id": req.requested_by_id,
            "title": req.title, "reason": req.reason, "duration_hours": req.duration_hours,
            "required_resource_type": req.required_resource_type, "base_priority": req.base_priority,
            "arrival_time": req.arrival_time, "status": req.status, "failure_reason": req.failure_reason,
            "assigned_allocation_id": req.assigned_allocation_id,
            "effective_priority": it.effective_priority, "waiting_seconds": it.waiting_seconds,
        })
    return result


def _find_best_slot(db: Session, req: ScheduleRequest):
    """Search across candidate days/times for the first CP-SAT-valid slot,
    preferring the professor's preferred day/time if given."""
    candidate_days = [req.preferred_day_of_week] if req.preferred_day_of_week is not None else list(range(6))
    facility_names = [f for f in (req.required_facility_names or "").split(",") if f]

    for day in candidate_days:
        start_slots = [req.preferred_start_slot_index] if req.preferred_start_slot_index is not None else list(range(0, SLOTS_PER_DAY - req.duration_hours + 1))
        for start_slot in start_slots:
            if start_slot is None or start_slot + req.duration_hours > SLOTS_PER_DAY:
                continue
            start_time = f"{9 + start_slot:02d}:00"
            options = search_availability(
                db, resource_type=req.required_resource_type, day_of_week=day, start_time=start_time,
                duration_hours=req.duration_hours, min_capacity=req.student_count,
                facility_names=facility_names, building=None,
            )
            suitable = [o for o in options if o["is_suitable"]]
            if not suitable:
                continue
            best = suitable[0]
            ok, msg = validate_placement_cp_sat(
                db, resource_id=best["resource_id"], faculty_id=req.faculty_id, section_id=req.section_id,
                day_of_week=day, start_slot_index=start_slot, duration_hours=req.duration_hours,
            )
            if ok:
                return day, start_slot, best["resource_id"], msg
    return None


def process_next_in_queue(db: Session, actor_id: int | None) -> dict:
    """Pop the highest-priority (aged, RR-tiebroken) pending request and try
    to place it via CP-SAT. Priority/Aging/RR only pick WHICH request goes
    next — CP-SAT alone decides WHERE (or whether) it fits."""
    ordered = get_ordered_pending_queue(db)
    if not ordered:
        return {"processed": False, "message": "No pending requests in queue."}

    top = ordered[0]
    req = db.query(ScheduleRequest).get(top["id"])
    req.started_processing_at = datetime.utcnow()

    with SolverJobSlot():
        placement = _find_best_slot(db, req)

    metric_algo = "round_robin" if sum(1 for o in ordered if o["effective_priority"] == top["effective_priority"]) > 1 else "priority_aging"
    wait = waiting_seconds(req.arrival_time)

    if placement is None:
        req.status = RequestStatus.FAILED
        req.failure_reason = "No CP-SAT-valid room/lab/time slot found for this request."
        req.completed_at = datetime.utcnow()
        db.add(SchedulerMetric(schedule_request_id=req.id, algorithm=metric_algo, base_priority=req.base_priority,
                                effective_priority=top["effective_priority"], wait_time_seconds=wait, completed=False))
        log_audit(db, actor_id, "REQUEST_FAILED", "schedule_request", req.id, req.failure_reason)
        db.commit()
        return {"processed": True, "success": False, "request_id": req.id, "message": req.failure_reason}

    day, start_slot, resource_id, validation_msg = placement
    with CommitLock():
        alloc = TimetableAllocation(
            resource_id=resource_id, faculty_id=req.faculty_id, section_id=req.section_id,
            day_of_week=day, start_slot_index=start_slot, duration_hours=req.duration_hours,
            status=AllocationStatus.ACTIVE, generated_by="ad_hoc_request",
            title=req.title or req.request_type.value,
        )
        db.add(alloc)
        db.flush()
        req.status = RequestStatus.APPLIED
        req.assigned_allocation_id = alloc.id
        req.completed_at = datetime.utcnow()
        db.add(SchedulerMetric(schedule_request_id=req.id, algorithm=metric_algo, base_priority=req.base_priority,
                                effective_priority=top["effective_priority"], wait_time_seconds=wait, completed=True))
        log_audit(db, actor_id, "REQUEST_APPLIED", "schedule_request", req.id,
                  f"Placed on resource {resource_id}, day {day}, slot {start_slot}. {validation_msg}")
        db.commit()

    return {"processed": True, "success": True, "request_id": req.id, "allocation_id": alloc.id, "message": validation_msg}


def process_all_pending(db: Session, actor_id: int | None) -> list[dict]:
    results = []
    while True:
        pending_count = db.query(ScheduleRequest).filter(ScheduleRequest.status == RequestStatus.PENDING).count()
        if pending_count == 0:
            break
        results.append(process_next_in_queue(db, actor_id))
    return results
