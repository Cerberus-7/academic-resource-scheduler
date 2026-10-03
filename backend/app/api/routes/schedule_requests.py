from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.requests import ScheduleRequest
from app.schemas.requests import ScheduleRequestCreate, ScheduleRequestOut
from app.api.deps import get_current_user, require_roles
from app.services import request_queue_service
from app.services.analytics_service import log_audit
from app.websocket.manager import manager

router = APIRouter(prefix="/api/schedule-requests", tags=["schedule-requests"])


@router.post("", response_model=ScheduleRequestOut)
async def create_request(payload: ScheduleRequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    req = ScheduleRequest(**payload.model_dump(), requested_by_id=user.id)
    db.add(req)
    log_audit(db, user.id, "CREATE_SCHEDULE_REQUEST", "schedule_request", None, payload.title or payload.request_type.value)
    db.commit()
    db.refresh(req)
    await manager.broadcast_to_role("admin", "new_schedule_request", {"id": req.id, "title": req.title, "type": req.request_type.value})
    return req


@router.get("", response_model=list[ScheduleRequestOut])
def list_requests(mine_only: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ordered = request_queue_service.get_ordered_pending_queue(db)
    pending_ids = {o["id"] for o in ordered}
    pending_by_id = {o["id"]: o for o in ordered}
    query = db.query(ScheduleRequest)
    if mine_only:
        query = query.filter(ScheduleRequest.requested_by_id == user.id)
    all_reqs = query.order_by(ScheduleRequest.arrival_time.desc()).all()
    out = []
    for r in all_reqs:
        extra = pending_by_id.get(r.id, {})
        out.append(ScheduleRequestOut(
            id=r.id, request_type=r.request_type, requested_by_id=r.requested_by_id, title=r.title,
            reason=r.reason, duration_hours=r.duration_hours, required_resource_type=r.required_resource_type,
            base_priority=r.base_priority, arrival_time=r.arrival_time, status=r.status,
            failure_reason=r.failure_reason, assigned_allocation_id=r.assigned_allocation_id,
            effective_priority=extra.get("effective_priority"), waiting_seconds=extra.get("waiting_seconds"),
        ))
    return out


@router.get("/queue", response_model=list[ScheduleRequestOut])
def get_queue(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    ordered = request_queue_service.get_ordered_pending_queue(db)
    return [ScheduleRequestOut(**o) for o in ordered]


@router.post("/process-next")
async def process_next(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    result = request_queue_service.process_next_in_queue(db, user.id)
    if result.get("processed"):
        await manager.broadcast_all("timetable_updated", {"message": "A queued request was processed."})
    return result


@router.post("/process-all")
async def process_all(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    results = request_queue_service.process_all_pending(db, user.id)
    await manager.broadcast_all("timetable_updated", {"message": f"Processed {len(results)} queued request(s)."})
    return results


@router.post("/{request_id}/cancel")
def cancel_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    req = db.query(ScheduleRequest).get(request_id)
    if not req:
        raise HTTPException(404, "Request not found.")
    if req.requested_by_id != user.id and user.role.name != RoleName.ADMIN:
        raise HTTPException(403, "Not allowed to cancel this request.")
    from app.models.requests import RequestStatus
    req.status = RequestStatus.CANCELLED
    log_audit(db, user.id, "CANCEL_SCHEDULE_REQUEST", "schedule_request", req.id, "")
    db.commit()
    return {"message": "Request cancelled."}
