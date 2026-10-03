from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.academic import Resource, Facility, MaintenanceWindow
from app.schemas.academic import ResourceCreate, ResourceOut, MaintenanceWindowCreate, MaintenanceWindowOut, FacilityOut
from app.api.deps import get_current_user, require_roles
from app.services.analytics_service import log_audit

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("", response_model=list[ResourceOut])
def list_resources(resource_type: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Resource)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    return query.all()


@router.get("/facilities", response_model=list[FacilityOut])
def list_facilities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Facility).all()


@router.post("", response_model=ResourceOut)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(RoleName.ADMIN))):
    if db.query(Resource).filter(Resource.code == payload.code).first():
        raise HTTPException(400, "A resource with this code already exists.")
    facilities = []
    for name in payload.facility_names:
        f = db.query(Facility).filter(Facility.name == name).first()
        if not f:
            f = Facility(name=name)
            db.add(f)
            db.flush()
        facilities.append(f)
    resource = Resource(**payload.model_dump(exclude={"facility_names"}), facilities=facilities)
    db.add(resource)
    log_audit(db, user.id, "CREATE_RESOURCE", "resource", None, f"Created {payload.code} - {payload.name}")
    db.commit()
    db.refresh(resource)
    return resource


@router.put("/{resource_id}", response_model=ResourceOut)
def update_resource(resource_id: int, payload: ResourceCreate, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(RoleName.ADMIN))):
    resource = db.query(Resource).get(resource_id)
    if not resource:
        raise HTTPException(404, "Resource not found.")
    for k, v in payload.model_dump(exclude={"facility_names"}).items():
        setattr(resource, k, v)
    facilities = []
    for name in payload.facility_names:
        f = db.query(Facility).filter(Facility.name == name).first()
        if not f:
            f = Facility(name=name)
            db.add(f)
            db.flush()
        facilities.append(f)
    resource.facilities = facilities
    log_audit(db, user.id, "UPDATE_RESOURCE", "resource", resource.id, f"Updated {resource.code}")
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}")
def deactivate_resource(resource_id: int, db: Session = Depends(get_db),
                         user: User = Depends(require_roles(RoleName.ADMIN))):
    resource = db.query(Resource).get(resource_id)
    if not resource:
        raise HTTPException(404, "Resource not found.")
    resource.is_active = False
    log_audit(db, user.id, "DEACTIVATE_RESOURCE", "resource", resource.id, f"Deactivated {resource.code}")
    db.commit()
    return {"message": "Resource deactivated."}


@router.get("/maintenance", response_model=list[MaintenanceWindowOut])
def list_maintenance(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(MaintenanceWindow).all()
    return [MaintenanceWindowOut(id=r.id, resource_id=r.resource_id, start_datetime=r.start_datetime.isoformat(),
                                  end_datetime=r.end_datetime.isoformat(), reason=r.reason) for r in rows]


@router.post("/maintenance", response_model=MaintenanceWindowOut)
def create_maintenance(payload: MaintenanceWindowCreate, db: Session = Depends(get_db),
                        user: User = Depends(require_roles(RoleName.ADMIN))):
    resource = db.query(Resource).get(payload.resource_id)
    if not resource:
        raise HTTPException(404, "Resource not found.")
    mw = MaintenanceWindow(
        resource_id=payload.resource_id, start_datetime=datetime.fromisoformat(payload.start_datetime),
        end_datetime=datetime.fromisoformat(payload.end_datetime), reason=payload.reason, created_by_id=user.id,
    )
    db.add(mw)
    log_audit(db, user.id, "CREATE_MAINTENANCE_WINDOW", "resource", resource.id,
              f"{payload.start_datetime} to {payload.end_datetime}: {payload.reason}")
    db.commit()
    db.refresh(mw)
    return MaintenanceWindowOut(id=mw.id, resource_id=mw.resource_id, start_datetime=mw.start_datetime.isoformat(),
                                 end_datetime=mw.end_datetime.isoformat(), reason=mw.reason)


@router.delete("/maintenance/{maintenance_id}")
def delete_maintenance(maintenance_id: int, db: Session = Depends(get_db),
                        user: User = Depends(require_roles(RoleName.ADMIN))):
    mw = db.query(MaintenanceWindow).get(maintenance_id)
    if not mw:
        raise HTTPException(404, "Maintenance window not found.")
    db.delete(mw)
    log_audit(db, user.id, "DELETE_MAINTENANCE_WINDOW", "resource", mw.resource_id, "Maintenance window removed.")
    db.commit()
    return {"message": "Maintenance window removed."}
