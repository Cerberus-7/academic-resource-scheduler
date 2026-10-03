from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.academic import Course, StudentSection, CourseSession
from app.schemas.academic import (
    CourseCreate, CourseOut, StudentSectionCreate, StudentSectionOut, CourseSessionCreate, CourseSessionOut,
)
from app.api.deps import get_current_user, require_roles
from app.services.analytics_service import log_audit

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Course).all()


@router.post("", response_model=CourseOut)
def create_course(payload: CourseCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    if db.query(Course).filter(Course.code == payload.code).first():
        raise HTTPException(400, "A course with this code already exists.")
    course = Course(**payload.model_dump())
    db.add(course)
    log_audit(db, user.id, "CREATE_COURSE", "course", None, f"{payload.code} - {payload.name}")
    db.commit()
    db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404, "Course not found.")
    if payload.code != course.code and db.query(Course).filter(Course.code == payload.code).first():
        raise HTTPException(400, "A course with this code already exists.")
    for k, v in payload.model_dump().items():
        setattr(course, k, v)
    log_audit(db, user.id, "UPDATE_COURSE", "course", course.id, f"{course.code} - {course.name}")
    db.commit()
    db.refresh(course)
    return course


@router.get("/sections", response_model=list[StudentSectionOut])
def list_sections(course_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(StudentSection)
    if course_id:
        query = query.filter(StudentSection.course_id == course_id)
    return query.all()


@router.post("/sections", response_model=StudentSectionOut)
def create_section(payload: StudentSectionCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    section = StudentSection(**payload.model_dump())
    db.add(section)
    log_audit(db, user.id, "CREATE_SECTION", "student_section", None, payload.name)
    db.commit()
    db.refresh(section)
    return section


@router.put("/sections/{section_id}", response_model=StudentSectionOut)
def update_section(section_id: int, payload: StudentSectionCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    section = db.query(StudentSection).get(section_id)
    if not section:
        raise HTTPException(404, "Section not found.")
    for k, v in payload.model_dump().items():
        setattr(section, k, v)
    log_audit(db, user.id, "UPDATE_SECTION", "student_section", section.id, section.name)
    db.commit()
    db.refresh(section)
    return section


@router.get("/sessions", response_model=list[CourseSessionOut])
def list_sessions(section_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(CourseSession)
    if section_id:
        query = query.filter(CourseSession.section_id == section_id)
    return query.all()


@router.post("/sessions", response_model=CourseSessionOut)
def create_session(payload: CourseSessionCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    session = CourseSession(**payload.model_dump())
    db.add(session)
    log_audit(db, user.id, "CREATE_COURSE_SESSION", "course_session", None,
              f"section={payload.section_id} faculty={payload.faculty_id}")
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    session = db.query(CourseSession).get(session_id)
    if not session:
        raise HTTPException(404, "Not found.")
    db.delete(session)
    db.commit()
    return {"message": "Removed."}
