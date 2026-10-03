from sqlalchemy.orm import Session
from app.models.logs import AuditLog, SchedulerMetric
from app.models.requests import ScheduleRequest, ShiftRequest, RequestStatus
from app.models.scheduling import TimetableAllocation
from app.models.academic import Resource


def log_audit(db: Session, actor_id: int | None, action: str, entity_type: str, entity_id: int | None,
              details: str, is_override: bool = False):
    db.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id,
                     details=details, is_override=is_override))


def dashboard_kpis(db: Session) -> dict:
    total_allocations = db.query(TimetableAllocation).count()
    pending_schedule_requests = db.query(ScheduleRequest).filter(ScheduleRequest.status == RequestStatus.PENDING).count()
    pending_shift_requests = db.query(ShiftRequest).filter(
        ShiftRequest.status.in_([RequestStatus.PENDING, RequestStatus.UNDER_DISCUSSION, RequestStatus.ALTERNATIVE_PROPOSED])
    ).count()
    total_resources = db.query(Resource).count()
    active_resources = db.query(Resource).filter(Resource.is_active == True).count()  # noqa: E712
    return {
        "total_allocations": total_allocations,
        "pending_schedule_requests": pending_schedule_requests,
        "pending_shift_requests": pending_shift_requests,
        "total_resources": total_resources,
        "active_resources": active_resources,
    }


def resource_utilization(db: Session) -> list[dict]:
    resources = db.query(Resource).all()
    total_slots_per_week = 6 * 8
    out = []
    for r in resources:
        used = db.query(TimetableAllocation).filter(TimetableAllocation.resource_id == r.id).count()
        out.append({
            "resource_id": r.id, "name": r.name, "code": r.code,
            "utilization_percent": round(100 * used / total_slots_per_week, 1),
        })
    return out


def scheduler_metric_charts(db: Session) -> dict:
    metrics = db.query(SchedulerMetric).all()
    priority = [m for m in metrics if m.algorithm == "priority_aging"]
    rr = [m for m in metrics if m.algorithm == "round_robin"]

    def summarize(rows):
        if not rows:
            return {"avg_wait": 0, "max_wait": 0, "completion_rate": 0, "count": 0}
        completed = [r for r in rows if r.completed]
        return {
            "avg_wait": round(sum(r.wait_time_seconds for r in rows) / len(rows), 2),
            "max_wait": round(max(r.wait_time_seconds for r in rows), 2),
            "completion_rate": round(100 * len(completed) / len(rows), 1),
            "count": len(rows),
        }

    return {
        "priority_aging": summarize(priority),
        "round_robin": summarize(rr),
        "starvation_prevention": {
            "max_wait_without_aging_estimate": max((m.base_priority * 60 for m in metrics), default=0),
            "max_wait_with_aging_actual": round(max((m.wait_time_seconds for m in metrics), default=0), 2),
        },
    }
