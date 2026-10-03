from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON, Float, Boolean
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), default="")
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, default="")
    is_override = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class BankerSimulationState(Base):
    """Snapshot / log entries for the classical + dynamic Banker's algorithm module.
    Purely an OS-education simulation over abstract resource units — never used
    to make final room/time allocation decisions."""
    __tablename__ = "banker_simulation_states"

    id = Column(Integer, primary_key=True)
    snapshot_label = Column(String(100), default="")
    resource_types = Column(JSON, default=list)     # ["lecture_room_units", ...]
    available = Column(JSON, default=list)          # list[int]
    max_matrix = Column(JSON, default=dict)         # {process_name: [int,...]}
    allocation_matrix = Column(JSON, default=dict)  # {process_name: [int,...]}
    is_safe = Column(Boolean, default=True)
    safe_sequence = Column(JSON, default=list)
    event = Column(String(120), default="")  # e.g. "request", "release", "add_process"
    created_at = Column(DateTime, default=datetime.utcnow)


class SchedulerMetric(Base):
    """Per-request OS scheduling metric snapshot for analytics/charts."""
    __tablename__ = "scheduler_metrics"

    id = Column(Integer, primary_key=True)
    schedule_request_id = Column(Integer, ForeignKey("schedule_requests.id"), nullable=True)
    shift_request_id = Column(Integer, ForeignKey("shift_requests.id"), nullable=True)
    algorithm = Column(String(30), default="priority_aging")  # priority_aging | round_robin
    base_priority = Column(Integer, default=5)
    effective_priority = Column(Float, default=5)
    wait_time_seconds = Column(Float, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
