from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.schemas.banker import (
    BankerInitRequest, BankerStateOut, BankerRequestOp, BankerReleaseOp,
    BankerAddProcess, BankerAddResource, BankerReduceCapacity, RESOURCE_TYPES,
)
from app.api.deps import require_roles, get_current_user
from app.services import banker_service

router = APIRouter(prefix="/api/banker", tags=["banker-simulation"])


@router.get("/resource-types")
def resource_types():
    return {"resource_types": RESOURCE_TYPES, "note": "Operating Systems Resource Safety Simulation — Separate from Final Timetable Allocation"}


@router.get("/state", response_model=BankerStateOut)
def get_state(user: User = Depends(get_current_user)):
    return banker_service.get_state()


@router.post("/init", response_model=BankerStateOut)
def init(payload: BankerInitRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    if len(payload.total_resources) != len(RESOURCE_TYPES):
        raise HTTPException(400, f"total_resources must have exactly {len(RESOURCE_TYPES)} values: {RESOURCE_TYPES}")
    return banker_service.init_state(db, payload.total_resources, payload.processes, payload.allocation)


@router.post("/request", response_model=BankerStateOut)
def request_resources(payload: BankerRequestOp, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return banker_service.request(db, payload.process_name, payload.request_vector)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/release", response_model=BankerStateOut)
def release_resources(payload: BankerReleaseOp, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return banker_service.release(db, payload.process_name, payload.release_vector)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/add-process", response_model=BankerStateOut)
def add_process(payload: BankerAddProcess, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    try:
        return banker_service.add_process(db, payload.process_name, payload.max_demand)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/add-resource", response_model=BankerStateOut)
def add_resource(payload: BankerAddResource, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    try:
        return banker_service.add_resource_capacity(db, payload.resource_index, payload.additional_units)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/reduce-capacity", response_model=BankerStateOut)
def reduce_capacity(payload: BankerReduceCapacity, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    try:
        return banker_service.reduce_resource_capacity(db, payload.resource_index, payload.reduced_units, payload.reason)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/history")
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = banker_service.history(db)
    return [{"id": r.id, "event": r.event, "is_safe": r.is_safe, "safe_sequence": r.safe_sequence,
             "available": r.available, "created_at": r.created_at.isoformat()} for r in rows]
