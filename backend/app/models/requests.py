import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Enum, DateTime, Text, Float, Boolean
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class RequestType(str, enum.Enum):
    EXTRA_CLASS = "extra_class"
    MAKEUP_CLASS = "makeup_class"
    LAB_SESSION = "lab_session"
    TUTORIAL = "tutorial"
    REMEDIAL_CLASS = "remedial_class"
    DOUBT_CLEARING = "doubt_clearing"
    PROJECT_DISCUSSION = "project_discussion"
    GUEST_LECTURE = "guest_lecture"
    SEMINAR = "seminar"
    WORKSHOP = "workshop"
    HACKATHON = "hackathon"
    CODING_COMPETITION = "coding_competition"
    PLACEMENT_TRAINING = "placement_training"
    EXAMINATION = "examination"
    VIVA_VOCE = "viva_voce"
    DEPARTMENT_MEETING = "department_meeting"
    ORIENTATION = "orientation"
    PROJECT_PRESENTATION = "project_presentation"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_DISCUSSION = "under_discussion"
    ALTERNATIVE_PROPOSED = "alternative_proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    APPLIED = "applied"
    FAILED = "failed"


class ScheduleRequest(Base):
    """A request/process fed into the OS scheduling simulation (priority+aging+RR)."""
    __tablename__ = "schedule_requests"

    id = Column(Integer, primary_key=True)
    request_type = Column(Enum(RequestType), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    section_id = Column(Integer, ForeignKey("student_sections.id"), nullable=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    title = Column(String(150), default="")
    reason = Column(Text, default="")
    student_count = Column(Integer, default=0)
    duration_hours = Column(Integer, default=1)
    required_resource_type = Column(String(10), default="room")  # room | lab
    required_facility_names = Column(String(255), default="")
    preferred_day_of_week = Column(Integer, nullable=True)
    preferred_start_slot_index = Column(Integer, nullable=True)

    base_priority = Column(Integer, default=5)  # 1 (highest) .. 10 (lowest)
    arrival_time = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    started_processing_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assigned_allocation_id = Column(Integer, ForeignKey("timetable_allocations.id"), nullable=True)
    failure_reason = Column(String(255), default="")

    requested_by = relationship("User")


class ShiftReason(str, enum.Enum):
    FACULTY_ABSENCE = "faculty_absence"
    ROOM_MAINTENANCE = "room_maintenance"
    LAB_MAINTENANCE = "lab_maintenance"
    EQUIPMENT_FAILURE = "equipment_failure"
    ROOM_CLOSURE = "room_closure"
    NEW_SECTION = "new_course_section"
    EVENT_REQUEST = "event_request"
    CANCELLATION = "cancellation"
    OTHER = "other"


class ShiftRequest(Base):
    """A request to move/postpone an existing timetable_allocation."""
    __tablename__ = "shift_requests"

    id = Column(Integer, primary_key=True)
    original_allocation_id = Column(Integer, ForeignKey("timetable_allocations.id"), nullable=False)
    affected_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason_code = Column(Enum(ShiftReason), default=ShiftReason.OTHER)
    reason_text = Column(Text, default="")
    base_priority = Column(Integer, default=5)
    arrival_time = Column(DateTime, default=datetime.utcnow)
    decision_deadline = Column(DateTime, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    final_decision = Column(String(20), default="")  # approved | rejected | applied | failed
    linked_schedule_request_id = Column(Integer, ForeignKey("schedule_requests.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    original_allocation = relationship("TimetableAllocation")
    affected_faculty = relationship("Faculty")
    requested_by = relationship("User")
    alternatives = relationship("ShiftAlternative", back_populates="shift_request")
    discussion_messages = relationship("DiscussionMessage", back_populates="shift_request")


class ShiftAlternative(Base):
    """A candidate new day/time/resource, CP-SAT-validated before shown to the professor."""
    __tablename__ = "shift_alternatives"

    id = Column(Integer, primary_key=True)
    shift_request_id = Column(Integer, ForeignKey("shift_requests.id"), nullable=False)
    proposed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_slot_index = Column(Integer, nullable=False)
    duration_hours = Column(Integer, default=1)
    is_cp_sat_valid = Column(Boolean, default=False)
    validation_message = Column(String(255), default="")
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    shift_request = relationship("ShiftRequest", back_populates="alternatives")
    resource = relationship("Resource")


class ApprovalResponse(Base):
    __tablename__ = "approval_responses"

    id = Column(Integer, primary_key=True)
    shift_request_id = Column(Integer, ForeignKey("shift_requests.id"), nullable=False)
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)  # approve | reject | propose_alternative
    alternative_id = Column(Integer, ForeignKey("shift_alternatives.id"), nullable=True)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    shift_request = relationship("ShiftRequest")


class DiscussionMessage(Base):
    __tablename__ = "discussion_messages"

    id = Column(Integer, primary_key=True)
    shift_request_id = Column(Integer, ForeignKey("shift_requests.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    shift_request = relationship("ShiftRequest", back_populates="discussion_messages")
    sender = relationship("User")
