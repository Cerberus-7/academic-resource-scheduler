from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.academic import Resource, MaintenanceWindow
from app.models.scheduling import TimetableAllocation, AllocationStatus
from app.solver.constraints import SLOTS_PER_DAY, slot_to_clock


def _current_week_monday() -> datetime:
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def search_availability(
    db: Session, resource_type: str | None, day_of_week: int, start_time: str,
    duration_hours: int, min_capacity: int, facility_names: list[str], building: str | None,
):
    start_slot = int(start_time.split(":")[0]) - 9
    end_slot = start_slot + duration_hours

    query = db.query(Resource).filter(Resource.is_active == True)  # noqa: E712
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if building:
        query = query.filter(Resource.building == building)
    resources = query.all()

    allocations = db.query(TimetableAllocation).filter(
        TimetableAllocation.status == AllocationStatus.ACTIVE,
        TimetableAllocation.day_of_week == day_of_week,
    ).all()
    maintenance_rows = db.query(MaintenanceWindow).all()
    anchor_monday = _current_week_monday()
    day_start_dt = anchor_monday + timedelta(days=day_of_week)

    results = []
    for r in resources:
        r_facility_names = {f.name for f in r.facilities}
        occupied_slots = sorted(
            (a.start_slot_index, a.start_slot_index + a.duration_hours)
            for a in allocations if a.resource_id == r.id
        )
        for mw in maintenance_rows:
            if mw.resource_id != r.id:
                continue
            mw_day_start = day_start_dt + timedelta(hours=9)
            mw_day_end = day_start_dt + timedelta(hours=17)
            overlap_start = max(mw.start_datetime, mw_day_start)
            overlap_end = min(mw.end_datetime, mw_day_end)
            if overlap_start < overlap_end:
                occupied_slots.append((
                    int((overlap_start - mw_day_start).total_seconds() // 3600),
                    int((overlap_end - mw_day_start).total_seconds() // 3600),
                ))
        occupied_slots.sort()

        # Compute free gaps across the 8 slots (0..8)
        free_gaps = []
        cursor = 0
        for s, e in occupied_slots:
            if s > cursor:
                free_gaps.append((cursor, s))
            cursor = max(cursor, e)
        if cursor < SLOTS_PER_DAY:
            free_gaps.append((cursor, SLOTS_PER_DAY))

        is_requested_slot_free = any(gs <= start_slot and end_slot <= ge for gs, ge in free_gaps)
        max_continuous = max((ge - gs for gs, ge in free_gaps), default=0)
        current_gap = next(((gs, ge) for gs, ge in free_gaps if gs <= start_slot < ge), None)
        available_from = slot_to_clock(current_gap[0]) if current_gap else "-"
        available_until = slot_to_clock(current_gap[1]) if current_gap else "-"
        next_booking = None
        upcoming = [s for s, _ in occupied_slots if s >= start_slot]
        if upcoming:
            next_booking = slot_to_clock(min(upcoming))

        meets_capacity = r.capacity >= min_capacity
        meets_facilities = all(f in r_facility_names for f in facility_names if f)
        is_suitable = is_requested_slot_free and meets_capacity and meets_facilities

        is_under_maintenance_now = any(
            gs <= start_slot < ge for gs, ge in [
                (int((max(mw.start_datetime, day_start_dt + timedelta(hours=9)) - (day_start_dt + timedelta(hours=9))).total_seconds() // 3600),
                 int((min(mw.end_datetime, day_start_dt + timedelta(hours=17)) - (day_start_dt + timedelta(hours=9))).total_seconds() // 3600))
                for mw in maintenance_rows if mw.resource_id == r.id
                and mw.start_datetime < day_start_dt + timedelta(hours=17)
                and mw.end_datetime > day_start_dt + timedelta(hours=9)
            ]
        )
        status = "maintenance" if is_under_maintenance_now else ("available" if is_requested_slot_free else "occupied")

        results.append({
            "resource_id": r.id, "name": r.name, "code": r.code, "resource_type": r.resource_type.value,
            "capacity": r.capacity, "building": r.building, "facilities": sorted(r_facility_names),
            "is_suitable": is_suitable, "available_from": available_from, "available_until": available_until,
            "max_continuous_hours": max_continuous, "next_booking": next_booking, "status": status,
        })

    results.sort(key=lambda r: (not r["is_suitable"], -r["max_continuous_hours"]))
    return results
