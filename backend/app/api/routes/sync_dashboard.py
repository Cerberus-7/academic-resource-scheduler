from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.requests import ShiftRequest, RequestStatus
from app.api.deps import require_roles
from app.services.sync_service import get_dashboard_snapshot
from app.services.approval_service import apply_shift
from app.services.analytics_service import log_audit

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.get("/dashboard")
def sync_dashboard(user: User = Depends(require_roles(RoleName.ADMIN))):
    return get_dashboard_snapshot()


class OverridePayload(BaseModel):
    shift_request_id: int
    alternative_id: int
    justification: str


@router.post("/emergency-override")
def emergency_override(payload: OverridePayload, db: Session = Depends(get_db),
                        user: User = Depends(require_roles(RoleName.ADMIN))):
    """Configured emergency-demo override workflow: an admin can force-apply a
    shift's alternative even if approvals are incomplete. Every use is
    mandatorily written to the audit log with is_override=True, per spec —
    CP-SAT re-validation still applies; only the human-approval step is skipped."""
    from app.models.requests import ShiftAlternative
    shift = db.query(ShiftRequest).get(payload.shift_request_id)
    alt = db.query(ShiftAlternative).get(payload.alternative_id)
    if not shift or not alt or alt.shift_request_id != shift.id:
        raise HTTPException(404, "Shift request or alternative not found.")
    if not payload.justification.strip():
        raise HTTPException(400, "A justification is mandatory for emergency overrides.")
    if not alt.is_cp_sat_valid:
        raise HTTPException(400, "This alternative failed CP-SAT validation and cannot be applied even via override.")

    ok, msg = apply_shift(db, shift, alt, user.id)
    log_audit(db, user.id, "EMERGENCY_OVERRIDE", "shift_request", shift.id,
              f"Justification: {payload.justification}. Result: {msg}", is_override=True)
    db.commit()
    return {"success": ok, "message": msg}
