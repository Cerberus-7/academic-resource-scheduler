from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.requests import ShiftReason
from app.schemas.requests import ShiftRequestOut
from app.api.deps import require_roles
from app.services.rescheduling_service import trigger_dynamic_reschedule
from app.websocket.manager import manager

router = APIRouter(prefix="/api/rescheduling", tags=["rescheduling"])


class TriggerPayload(BaseModel):
    reason_code: ShiftReason
    reason_text: str = ""
    faculty_id: int | None = None
    resource_id: int | None = None
    day_of_week: int | None = None


@router.post("/trigger", response_model=list[ShiftRequestOut])
async def trigger(payload: TriggerPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    shifts = trigger_dynamic_reschedule(
        db, user.id, payload.reason_code, payload.reason_text,
        payload.faculty_id, payload.resource_id, payload.day_of_week,
    )
    for s in shifts:
        await manager.send_to_user(s.affected_faculty_id, "new_shift_request", {"id": s.id, "auto_generated": True})
    return shifts
