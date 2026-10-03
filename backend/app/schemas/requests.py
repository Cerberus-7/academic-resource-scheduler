from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.requests import RequestType, RequestStatus, ShiftReason


class ScheduleRequestCreate(BaseModel):
    request_type: RequestType
    course_id: Optional[int] = None
    section_id: Optional[int] = None
    faculty_id: Optional[int] = None
    title: str = ""
    reason: str = ""
    student_count: int = 0
    duration_hours: int = 1
    required_resource_type: str = "room"
    required_facility_names: str = ""
    preferred_day_of_week: Optional[int] = None
    preferred_start_slot_index: Optional[int] = None
    base_priority: int = 5


class ScheduleRequestOut(BaseModel):
    id: int
    request_type: RequestType
    requested_by_id: int
    title: str
    reason: str
    duration_hours: int
    required_resource_type: str
    base_priority: int
    arrival_time: datetime
    status: RequestStatus
    failure_reason: str
    assigned_allocation_id: Optional[int] = None
    effective_priority: Optional[float] = None
    waiting_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class ShiftAlternativeCreate(BaseModel):
    resource_id: int
    day_of_week: int
    start_slot_index: int
    duration_hours: int = 1


class ShiftAlternativeOut(BaseModel):
    id: int
    shift_request_id: int
    resource_id: int
    day_of_week: int
    start_slot_index: int
    duration_hours: int
    is_cp_sat_valid: bool
    validation_message: str
    is_selected: bool

    class Config:
        from_attributes = True


class ShiftRequestCreate(BaseModel):
    original_allocation_id: int
    reason_code: ShiftReason = ShiftReason.OTHER
    reason_text: str = ""
    base_priority: int = 5
    decision_deadline: Optional[datetime] = None
    suggested_alternatives: list[ShiftAlternativeCreate] = []


class ShiftRequestOut(BaseModel):
    id: int
    original_allocation_id: int
    affected_faculty_id: int
    requested_by_id: int
    reason_code: ShiftReason
    reason_text: str
    base_priority: int
    arrival_time: datetime
    decision_deadline: Optional[datetime] = None
    status: RequestStatus
    final_decision: str
    alternatives: list[ShiftAlternativeOut] = []

    class Config:
        from_attributes = True


class ApprovalActionRequest(BaseModel):
    action: str  # approve | reject | propose_alternative
    alternative_id: Optional[int] = None
    new_alternative: Optional[ShiftAlternativeCreate] = None
    comment: str = ""


class DiscussionMessageCreate(BaseModel):
    message: str


class DiscussionMessageOut(BaseModel):
    id: int
    shift_request_id: int
    sender_id: int
    sender_name: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
