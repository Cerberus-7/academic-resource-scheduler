"""
Priority Scheduling + Aging.

IMPORTANT: this module ONLY decides the *order* in which pending
schedule_requests / shift_requests are handed to the CP-SAT-backed services
for placement. It never itself allocates a room/lab/faculty/time slot.
"""
from dataclasses import dataclass
from datetime import datetime
from app.os_simulation.aging_policy import effective_priority, waiting_seconds


@dataclass
class QueueItem:
    request_id: int
    request_kind: str  # "schedule_request" | "shift_request"
    base_priority: int
    arrival_time: datetime
    effective_priority: float = 0.0
    waiting_seconds: float = 0.0


def order_by_priority_with_aging(items: list[QueueItem], now: datetime | None = None) -> list[QueueItem]:
    now = now or datetime.utcnow()
    for item in items:
        item.effective_priority = effective_priority(item.base_priority, item.arrival_time, now)
        item.waiting_seconds = waiting_seconds(item.arrival_time, now)
    # Lower effective_priority number = served first. Ties -> earlier arrival first
    # (Round Robin is applied separately among exact ties, see round_robin.py)
    return sorted(items, key=lambda it: (it.effective_priority, it.arrival_time))
