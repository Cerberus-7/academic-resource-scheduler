import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


class TimeSlot(Base):
    """Fixed discrete 1-hour slots, e.g. Mon 09:00-10:00."""
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon .. 5=Sat
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)    # "10:00"
    slot_index = Column(Integer, nullable=False)     # 0..7 within the day


class AllocationStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    MOVED = "moved"


class TimetableAllocation(Base):
    """A concrete committed placement of a course_session onto a resource/time/day."""
    __tablename__ = "timetable_allocations"

    id = Column(Integer, primary_key=True)
    course_session_id = Column(Integer, ForeignKey("course_sessions.id"), nullable=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    section_id = Column(Integer, ForeignKey("student_sections.id"), nullable=True)
    day_of_week = Column(Integer, nullable=False)
    start_slot_index = Column(Integer, nullable=False)
    duration_hours = Column(Integer, default=1)
    status = Column(Enum(AllocationStatus), default=AllocationStatus.ACTIVE)
    version = Column(Integer, default=1)  # for optimistic concurrency in sync_service
    generated_by = Column(String(30), default="cp_sat")  # cp_sat | manual | ad_hoc_request
    title = Column(String(150), default="")  # used for ad-hoc events/extra-classes without a course_session
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course_session = relationship("CourseSession")
    resource = relationship("Resource")
    faculty = relationship("Faculty")
    section = relationship("StudentSection")


class AvailabilityWindow(Base):
    """Optional recurring availability override for a resource or faculty.
    If absent, default working hours (Mon-Sat 09:00-17:00) apply."""
    __tablename__ = "availability_windows"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(20), nullable=False)  # "resource" | "faculty"
    entity_id = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    is_available = Column(Boolean, default=True)
