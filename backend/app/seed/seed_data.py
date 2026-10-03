from app.core.database import SessionLocal, Base
from app.core import database as database_module
from app.core.security import hash_password
from app.models.user import User, Role, RoleName
from app.models.academic import Faculty, Facility, Resource, ResourceType, Course, StudentSection, CourseSession, SessionType
from app.models.scheduling import TimeSlot
from app import models  # noqa: F401 ensures all models are registered on Base.metadata


def run_seed():
    Base.metadata.create_all(bind=database_module.engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded — skipping.")
            return

        roles = {name: Role(name=name, description=name.value.replace("_", " ").title()) for name in RoleName}
        db.add_all(roles.values())
        db.flush()

        # Time slots: Mon-Sat, 9AM-5PM, 1-hour periods
        for day in range(6):
            for slot in range(8):
                db.add(TimeSlot(day_of_week=day, start_time=f"{9+slot:02d}:00", end_time=f"{10+slot:02d}:00", slot_index=slot))

        # Facilities
        facility_names = ["Projector", "Smart Board", "AC", "Computers", "Speaker System", "Whiteboard"]
        facilities = {name: Facility(name=name) for name in facility_names}
        db.add_all(facilities.values())
        db.flush()

        # Users (demo login accounts)
        # DEMO ONLY: fictional accounts with throwaway passwords for local development.
        # Never reuse real credentials here, and change/remove these before any real deployment.
        admin_user = User(full_name="Admin User", email="admin@college.edu", hashed_password=hash_password("Admin@123"), role_id=roles[RoleName.ADMIN].id)
        prof_user = User(full_name="Dr. Asha Verma", email="professor@college.edu", hashed_password=hash_password("Prof@123"), role_id=roles[RoleName.PROFESSOR].id)
        coord_user = User(full_name="Rahul Mehta", email="coordinator@college.edu", hashed_password=hash_password("Coord@123"), role_id=roles[RoleName.EVENT_COORDINATOR].id)
        student_user = User(full_name="Student Viewer", email="student@college.edu", hashed_password=hash_password("Student@123"), role_id=roles[RoleName.STUDENT].id)
        db.add_all([admin_user, prof_user, coord_user, student_user])
        db.flush()

        # Faculty
        f1 = Faculty(user_id=prof_user.id, employee_code="FAC001", full_name="Dr. Asha Verma", department="CSE", designation="Associate Professor")
        f2 = Faculty(employee_code="FAC002", full_name="Dr. Kunal Rao", department="CSE", designation="Assistant Professor")
        f3 = Faculty(employee_code="FAC003", full_name="Dr. Priya Nair", department="CSE", designation="Professor")
        f4 = Faculty(employee_code="FAC004", full_name="Dr. Sameer Iyer", department="CSE", designation="Assistant Professor")
        db.add_all([f1, f2, f3, f4])
        db.flush()

        # Rooms and Labs
        rooms = [
            Resource(name="Room 101", code="R101", resource_type=ResourceType.ROOM, building="Main Block", floor="1", capacity=70,
                     facilities=[facilities["Projector"], facilities["AC"], facilities["Whiteboard"]]),
            Resource(name="Room 102", code="R102", resource_type=ResourceType.ROOM, building="Main Block", floor="1", capacity=60,
                     facilities=[facilities["Projector"], facilities["Whiteboard"]]),
            Resource(name="Room 201", code="R201", resource_type=ResourceType.ROOM, building="Main Block", floor="2", capacity=80,
                     facilities=[facilities["Smart Board"], facilities["AC"], facilities["Speaker System"]]),
            Resource(name="Seminar Hall", code="SH01", resource_type=ResourceType.ROOM, building="Admin Block", floor="G", capacity=150,
                     facilities=[facilities["Smart Board"], facilities["AC"], facilities["Speaker System"], facilities["Projector"]]),
            Resource(name="Computer Lab 1", code="L101", resource_type=ResourceType.LAB, building="Tech Block", floor="1", capacity=70,
                     facilities=[facilities["Computers"], facilities["AC"], facilities["Projector"]]),
            Resource(name="Computer Lab 2", code="L102", resource_type=ResourceType.LAB, building="Tech Block", floor="1", capacity=70,
                     facilities=[facilities["Computers"], facilities["AC"]]),
            Resource(name="Electronics Lab", code="L201", resource_type=ResourceType.LAB, building="Tech Block", floor="2", capacity=35,
                     facilities=[facilities["Computers"]]),
        ]
        db.add_all(rooms)
        db.flush()

        # Courses
        courses = [
            Course(code="CS301", name="Operating Systems", credits=4, requires_lab=True),
            Course(code="CS302", name="Database Management Systems", credits=4, requires_lab=True),
            Course(code="CS303", name="Computer Networks", credits=3, requires_lab=False),
            Course(code="CS304", name="Software Engineering", credits=3, requires_lab=False),
            Course(code="CS305", name="Web Technologies", credits=3, requires_lab=True),
        ]
        db.add_all(courses)
        db.flush()
        f1.qualified_courses = [courses[0], courses[4]]
        f2.qualified_courses = [courses[1], courses[4]]
        f3.qualified_courses = [courses[2]]
        f4.qualified_courses = [courses[3], courses[0]]

        # Sections
        sections = [
            StudentSection(name="CSE-3A", course_id=courses[0].id, student_count=65, semester=3),
            StudentSection(name="CSE-3B", course_id=courses[1].id, student_count=58, semester=3),
            StudentSection(name="CSE-5A", course_id=courses[2].id, student_count=70, semester=5),
            StudentSection(name="CSE-5B", course_id=courses[3].id, student_count=55, semester=5),
            StudentSection(name="CSE-3A-DB", course_id=courses[1].id, student_count=65, semester=3),
        ]
        db.add_all(sections)
        db.flush()

        # Course sessions (weekly teaching units the CP-SAT solver must place)
        sessions = [
            CourseSession(section_id=sections[0].id, faculty_id=f1.id, session_type=SessionType.LECTURE,
                          duration_hours=1, sessions_per_week=3, required_resource_type=ResourceType.ROOM,
                          required_facility_names="Projector"),
            CourseSession(section_id=sections[0].id, faculty_id=f1.id, session_type=SessionType.LAB,
                          duration_hours=2, sessions_per_week=1, required_resource_type=ResourceType.LAB,
                          required_facility_names="Computers"),
            CourseSession(section_id=sections[1].id, faculty_id=f2.id, session_type=SessionType.LECTURE,
                          duration_hours=1, sessions_per_week=3, required_resource_type=ResourceType.ROOM),
            CourseSession(section_id=sections[1].id, faculty_id=f2.id, session_type=SessionType.LAB,
                          duration_hours=2, sessions_per_week=1, required_resource_type=ResourceType.LAB,
                          required_facility_names="Computers"),
            CourseSession(section_id=sections[2].id, faculty_id=f3.id, session_type=SessionType.LECTURE,
                          duration_hours=1, sessions_per_week=3, required_resource_type=ResourceType.ROOM),
            CourseSession(section_id=sections[3].id, faculty_id=f4.id, session_type=SessionType.LECTURE,
                          duration_hours=1, sessions_per_week=2, required_resource_type=ResourceType.ROOM),
            CourseSession(section_id=sections[4].id, faculty_id=f2.id, session_type=SessionType.TUTORIAL,
                          duration_hours=1, sessions_per_week=1, required_resource_type=ResourceType.ROOM),
        ]
        db.add_all(sessions)

        db.commit()
        print("Seed data created successfully.")
        print("Demo logins:")
        print("  Admin:             admin@college.edu / Admin@123")
        print("  Professor:         professor@college.edu / Prof@123")
        print("  Event Coordinator: coordinator@college.edu / Coord@123")
        print("  Student:           student@college.edu / Student@123")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
