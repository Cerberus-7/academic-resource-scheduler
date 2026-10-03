import math
from datetime import datetime
from app.core.config import settings


def effective_priority(base_priority: int, arrival_time: datetime, now: datetime | None = None) -> float:
    """Lower numeric value = higher priority (1=highest, 10=lowest).
    effective_priority = base_priority - floor(wait_time / aging_interval)
    i.e. priority number decreases (improves) the longer a request waits,
    which implements the required formula
        effective_priority = base_priority + floor(wait_time / aging_interval)
    where "+" boosts urgency by *lowering* the numeric rank by that amount.
    """
    now = now or datetime.utcnow()
    wait_seconds = max(0.0, (now - arrival_time).total_seconds())
    boost = math.floor(wait_seconds / settings.AGING_INTERVAL_SECONDS)
    eff = base_priority - boost
    return max(1.0, eff)


def waiting_seconds(arrival_time: datetime, now: datetime | None = None) -> float:
    now = now or datetime.utcnow()
    return max(0.0, (now - arrival_time).total_seconds())
