import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Enum, Text, DateTime, Table
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResourceType(str, enum.Enum):
    ROOM = "room"
    LAB = "lab"


faculty_qualifications = Table(
    "faculty_qualifications",
    Base.metadata,
    Column("faculty_id", ForeignKey("faculty.id"), primary_key=True),
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
)

resource_facilities = Table(
    "resource_facilities",
    Base.metadata,
    Column("resource_id", ForeignKey("resources.id"), primary_key=True),
    Column("facility_id", ForeignKey("facilities.id"), primary_key=True),
)


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    employee_code = Column(String(30), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    department = Column(String(120), default="")
    designation = Column(String(80), default="")

    user = relationship("User", back_populates="faculty_profile")
    qualified_courses = relationship(
        "Course", secondary=faculty_qualifications, back_populates="qualified_faculty"
    )
    unavailability = relationship("FacultyUnavailability", back_populates="faculty")


class FacultyUnavailability(Base):
    __tablename__ = "faculty_unavailability"

    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon ... 5=Sat
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)
    reason = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("Faculty", back_populates="unavailability")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)  # e.g. Projector, AC, Smart Board


class Resource(Base):
    """Unified table for Rooms and Labs (rooms/laboratories)."""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    code = Column(String(30), unique=True, nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)
    building = Column(String(80), default="")
    floor = Column(String(20), default="")
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, default="")

    facilities = relationship("Facility", secondary=resource_facilities)
    maintenance_windows = relationship("MaintenanceWindow", back_populates="resource")


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    reason = Column(String(255), default="")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="maintenance_windows")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    credits = Column(Integer, default=3)
    requires_lab = Column(Boolean, default=False)

    qualified_faculty = relationship(
        "Faculty", secondary=faculty_qualifications, back_populates="qualified_courses"
    )
    sections = relationship("StudentSection", back_populates="course")


class StudentSection(Base):
    __tablename__ = "student_sections"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)  # e.g. "CSE-3A"
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_count = Column(Integer, default=0)
    semester = Column(Integer, default=1)

    course = relationship("Course", back_populates="sections")
    sessions = relationship("CourseSession", back_populates="section")


class SessionType(str, enum.Enum):
    LECTURE = "lecture"
    LAB = "lab"
    TUTORIAL = "tutorial"


class CourseSession(Base):
    """A required weekly teaching unit that the CP-SAT solver must place."""
    __tablename__ = "course_sessions"

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("student_sections.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    session_type = Column(Enum(SessionType), default=SessionType.LECTURE)
    duration_hours = Column(Integer, default=1)  # 1 = lecture, 2 = lab
    sessions_per_week = Column(Integer, default=1)
    required_resource_type = Column(Enum(ResourceType), default=ResourceType.ROOM)
    required_facility_names = Column(String(255), default="")  # comma-separated

    section = relationship("StudentSection", back_populates="sessions")
    faculty = relationship("Faculty")
