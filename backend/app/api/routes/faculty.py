from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.models.academic import Faculty, Course
from app.schemas.academic import (
    FacultyCreate, FacultyOut, FacultyUnavailabilityCreate, FacultyUnavailabilityOut,
)
from app.models.academic import FacultyUnavailability
from app.api.deps import get_current_user, require_roles
from app.services.analytics_service import log_audit

router = APIRouter(prefix="/api/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyOut])
def list_faculty(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Faculty).all()


@router.post("", response_model=FacultyOut)
def create_faculty(payload: FacultyCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleName.ADMIN))):
    if db.query(Faculty).filter(Faculty.employee_code == payload.employee_code).first():
        raise HTTPException(400, "A faculty member with this employee code already exists.")
    courses = db.query(Course).filter(Course.id.in_(payload.qualified_course_ids)).all() if payload.qualified_course_ids else []
    faculty = Faculty(
        user_id=payload.user_id, employee_code=payload.employee_code, full_name=payload.full_name,
        department=payload.department, designation=payload.designation, qualified_courses=courses,
    )
    db.add(faculty)
    log_audit(db, user.id, "CREATE_FACULTY", "faculty", None, f"Created {payload.employee_code} - {payload.full_name}")
    db.commit()
    db.refresh(faculty)
    return faculty


@router.put("/{faculty_id}", response_model=FacultyOut)
def update_faculty(faculty_id: int, payload: FacultyCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleName.ADMIN))):
    faculty = db.query(Faculty).get(faculty_id)
    if not faculty:
        raise HTTPException(404, "Faculty not found.")
    if payload.employee_code != faculty.employee_code and db.query(Faculty).filter(Faculty.employee_code == payload.employee_code).first():
        raise HTTPException(400, "A faculty member with this employee code already exists.")
    faculty.employee_code = payload.employee_code
    faculty.full_name = payload.full_name
    faculty.department = payload.department
    faculty.designation = payload.designation
    if payload.user_id is not None:
        faculty.user_id = payload.user_id
    if payload.qualified_course_ids:
        faculty.qualified_courses = db.query(Course).filter(Course.id.in_(payload.qualified_course_ids)).all()
    log_audit(db, user.id, "UPDATE_FACULTY", "faculty", faculty.id, f"Updated {faculty.employee_code}")
    db.commit()
    db.refresh(faculty)
    return faculty


@router.get("/unavailability", response_model=list[FacultyUnavailabilityOut])
def list_unavailability(faculty_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(FacultyUnavailability)
    if faculty_id:
        query = query.filter(FacultyUnavailability.faculty_id == faculty_id)
    return query.all()


@router.post("/unavailability", response_model=FacultyUnavailabilityOut)
def create_unavailability(payload: FacultyUnavailabilityCreate, db: Session = Depends(get_db),
                           user: User = Depends(require_roles(RoleName.ADMIN, RoleName.PROFESSOR))):
    row = FacultyUnavailability(**payload.model_dump())
    db.add(row)
    log_audit(db, user.id, "MARK_FACULTY_UNAVAILABLE", "faculty", payload.faculty_id,
              f"Day {payload.day_of_week} {payload.start_time}-{payload.end_time}: {payload.reason}")
    db.commit()
    db.refresh(row)
    return row


@router.delete("/unavailability/{row_id}")
def delete_unavailability(row_id: int, db: Session = Depends(get_db),
                           user: User = Depends(require_roles(RoleName.ADMIN, RoleName.PROFESSOR))):
    row = db.query(FacultyUnavailability).get(row_id)
    if not row:
        raise HTTPException(404, "Not found.")
    db.delete(row)
    db.commit()
    return {"message": "Removed."}
