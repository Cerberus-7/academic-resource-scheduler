from typing import Optional
from pydantic import BaseModel
from app.models.academic import ResourceType, SessionType


class FacultyBase(BaseModel):
    employee_code: str
    full_name: str
    department: str = ""
    designation: str = ""


class FacultyCreate(FacultyBase):
    user_id: Optional[int] = None
    qualified_course_ids: list[int] = []


class FacultyOut(FacultyBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class FacultyUnavailabilityCreate(BaseModel):
    faculty_id: int
    day_of_week: int
    start_time: str
    end_time: str
    reason: str = ""


class FacultyUnavailabilityOut(FacultyUnavailabilityCreate):
    id: int

    class Config:
        from_attributes = True


class FacilityOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ResourceBase(BaseModel):
    name: str
    code: str
    resource_type: ResourceType
    building: str = ""
    floor: str = ""
    capacity: int
    is_active: bool = True
    notes: str = ""


class ResourceCreate(ResourceBase):
    facility_names: list[str] = []


class ResourceOut(ResourceBase):
    id: int
    facilities: list[FacilityOut] = []

    class Config:
        from_attributes = True


class MaintenanceWindowCreate(BaseModel):
    resource_id: int
    start_datetime: str  # ISO format
    end_datetime: str
    reason: str = ""


class MaintenanceWindowOut(BaseModel):
    id: int
    resource_id: int
    start_datetime: str
    end_datetime: str
    reason: str

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    code: str
    name: str
    credits: int = 3
    requires_lab: bool = False


class CourseCreate(CourseBase):
    pass


class CourseOut(CourseBase):
    id: int

    class Config:
        from_attributes = True


class StudentSectionBase(BaseModel):
    name: str
    course_id: int
    student_count: int = 0
    semester: int = 1


class StudentSectionCreate(StudentSectionBase):
    pass


class StudentSectionOut(StudentSectionBase):
    id: int

    class Config:
        from_attributes = True


class CourseSessionCreate(BaseModel):
    section_id: int
    faculty_id: int
    session_type: SessionType = SessionType.LECTURE
    duration_hours: int = 1
    sessions_per_week: int = 1
    required_resource_type: ResourceType = ResourceType.ROOM
    required_facility_names: str = ""


class CourseSessionOut(CourseSessionCreate):
    id: int

    class Config:
        from_attributes = True
