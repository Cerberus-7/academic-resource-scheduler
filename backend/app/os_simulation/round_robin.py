"""
Round Robin — used ONLY to break ties among requests that share the exact
same effective_priority after aging is applied. It rotates a cursor across
tied groups on successive processing passes so that no single tied request
is starved by always landing at the end of a stable sort.
"""
from dataclasses import dataclass
from app.os_simulation.priority_scheduler import QueueItem

_rr_cursor: dict[float, int] = {}  # effective_priority -> rotation offset (in-memory demo state)


def apply_round_robin_tiebreak(items: list[QueueItem]) -> list[QueueItem]:
    if not items:
        return items
    groups: dict[float, list[QueueItem]] = {}
    order_of_groups: list[float] = []
    for it in items:
        key = round(it.effective_priority, 6)
        if key not in groups:
            groups[key] = []
            order_of_groups.append(key)
        groups[key].append(it)

    final: list[QueueItem] = []
    for key in order_of_groups:
        group = groups[key]
        if len(group) > 1:
            offset = _rr_cursor.get(key, 0) % len(group)
            rotated = group[offset:] + group[:offset]
            _rr_cursor[key] = (offset + 1) % len(group)
            final.extend(rotated)
        else:
            final.extend(group)
    return final


def reset_round_robin_state():
    _rr_cursor.clear()
