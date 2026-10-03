from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.scheduling import AvailabilityResult
from app.api.deps import get_current_user
from app.services.availability_service import search_availability

router = APIRouter(prefix="/api/availability", tags=["availability"])


@router.get("/search", response_model=list[AvailabilityResult])
def search(
    day_of_week: int, start_time: str, duration_hours: int = 1, min_capacity: int = 0,
    resource_type: str | None = None, facility_names: str = "", building: str | None = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    names = [f for f in facility_names.split(",") if f]
    return search_availability(db, resource_type, day_of_week, start_time, duration_hours, min_capacity, names, building)
