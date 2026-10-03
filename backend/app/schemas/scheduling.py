from typing import Optional
from pydantic import BaseModel
from app.models.scheduling import AllocationStatus


class TimeSlotOut(BaseModel):
    id: int
    day_of_week: int
    start_time: str
    end_time: str
    slot_index: int

    class Config:
        from_attributes = True


class TimetableAllocationOut(BaseModel):
    id: int
    course_session_id: Optional[int] = None
    resource_id: int
    resource_name: str
    resource_code: str
    faculty_id: Optional[int] = None
    faculty_name: str
    section_id: Optional[int] = None
    section_name: str
    course_code: str
    course_name: str
    day_of_week: int
    start_slot_index: int
    duration_hours: int
    status: AllocationStatus
    version: int

    class Config:
        from_attributes = True


class GenerateTimetableRequest(BaseModel):
    clear_existing: bool = True
    max_solve_seconds: int = 30


class GenerateTimetableResponse(BaseModel):
    success: bool
    message: str
    allocations_created: int
    solve_status: str
    solve_time_seconds: float


class AvailabilitySearchParams(BaseModel):
    resource_type: Optional[str] = None  # room | lab
    day_of_week: int
    start_time: str
    duration_hours: int = 1
    min_capacity: int = 0
    facility_names: list[str] = []
    building: Optional[str] = None


class AvailabilityResult(BaseModel):
    resource_id: int
    name: str
    code: str
    resource_type: str
    capacity: int
    building: str
    facilities: list[str]
    is_suitable: bool
    available_from: str
    available_until: str
    max_continuous_hours: int
    next_booking: Optional[str] = None
    status: str  # "available" | "occupied" | "maintenance"
