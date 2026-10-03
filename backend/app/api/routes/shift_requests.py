from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.requests import ShiftRequest, DiscussionMessage
from app.schemas.requests import (
    ShiftRequestCreate, ShiftRequestOut, ApprovalActionRequest, DiscussionMessageCreate, DiscussionMessageOut,
)
from app.api.deps import get_current_user, require_roles
from app.services import approval_service
from app.websocket.manager import manager

router = APIRouter(prefix="/api/shift-requests", tags=["shift-requests"])


@router.post("", response_model=ShiftRequestOut)
async def create_shift_request(payload: ShiftRequestCreate, db: Session = Depends(get_db),
                                user: User = Depends(require_roles(RoleName.ADMIN, RoleName.EVENT_COORDINATOR))):
    try:
        shift = approval_service.create_shift_request(db, user.id, payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await manager.send_to_user(shift.affected_faculty_id, "new_shift_request", {"id": shift.id})
    return shift


@router.get("", response_model=list[ShiftRequestOut])
def list_shift_requests(faculty_id: int | None = None, status: str | None = None,
                         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(ShiftRequest)
    if faculty_id:
        query = query.filter(ShiftRequest.affected_faculty_id == faculty_id)
    if status:
        query = query.filter(ShiftRequest.status == status)
    return query.order_by(ShiftRequest.arrival_time.desc()).all()


@router.get("/{shift_id}", response_model=ShiftRequestOut)
def get_shift_request(shift_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shift = db.query(ShiftRequest).get(shift_id)
    if not shift:
        raise HTTPException(404, "Not found.")
    return shift


@router.post("/{shift_id}/action")
async def take_action(shift_id: int, payload: ApprovalActionRequest, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    try:
        result = approval_service.professor_action(
            db, user.id, shift_id, payload.action, payload.alternative_id, payload.new_alternative, payload.comment,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    await manager.broadcast_all("shift_status_updated", {"shift_id": shift_id, "status": str(result["status"])})
    return result


@router.get("/{shift_id}/discussion", response_model=list[DiscussionMessageOut])
def get_discussion(shift_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(DiscussionMessage).filter(DiscussionMessage.shift_request_id == shift_id).order_by(DiscussionMessage.created_at).all()
    return [DiscussionMessageOut(id=r.id, shift_request_id=r.shift_request_id, sender_id=r.sender_id,
                                  sender_name=r.sender.full_name if r.sender else None, message=r.message,
                                  created_at=r.created_at) for r in rows]


@router.post("/{shift_id}/discussion", response_model=DiscussionMessageOut)
async def post_discussion(shift_id: int, payload: DiscussionMessageCreate, db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    try:
        msg = approval_service.add_discussion_message(db, user.id, shift_id, payload.message)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await manager.broadcast_all("new_discussion_message", {"shift_id": shift_id, "message": payload.message, "sender": user.full_name})
    return DiscussionMessageOut(id=msg.id, shift_request_id=msg.shift_request_id, sender_id=msg.sender_id,
                                 sender_name=user.full_name, message=msg.message, created_at=msg.created_at)
