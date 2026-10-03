from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.schemas.scheduling import GenerateTimetableRequest, GenerateTimetableResponse, TimetableAllocationOut
from app.api.deps import get_current_user, require_roles
from app.services import timetable_service
from app.websocket.manager import manager

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


@router.post("/generate", response_model=GenerateTimetableResponse)
async def generate(payload: GenerateTimetableRequest, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleName.ADMIN))):
    result = timetable_service.run_full_generation(db, user.id, payload.clear_existing, payload.max_solve_seconds)
    await manager.broadcast_all("timetable_updated", {"success": result.success, "message": result.message})
    return GenerateTimetableResponse(
        success=result.success, message=result.message, allocations_created=len(result.allocations),
        solve_status=result.status_name, solve_time_seconds=round(result.solve_time, 3),
    )


@router.get("", response_model=list[TimetableAllocationOut])
def get_timetable(section_id: int | None = None, faculty_id: int | None = None, resource_id: int | None = None,
                   day_of_week: int | None = None, course_id: int | None = None,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return timetable_service.list_allocations(db, section_id, faculty_id, resource_id, day_of_week, course_id)
