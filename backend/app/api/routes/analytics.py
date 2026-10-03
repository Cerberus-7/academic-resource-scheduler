from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.logs import AuditLog
from app.api.deps import get_current_user, require_roles
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return analytics_service.dashboard_kpis(db)


@router.get("/utilization")
def utilization(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return analytics_service.resource_utilization(db)


@router.get("/scheduler-metrics")
def scheduler_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return analytics_service.scheduler_metric_charts(db)


@router.get("/audit-logs")
def audit_logs(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [{"id": r.id, "actor_id": r.actor_id, "action": r.action, "entity_type": r.entity_type,
             "entity_id": r.entity_id, "details": r.details, "is_override": r.is_override,
             "created_at": r.created_at.isoformat()} for r in rows]
