from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base
from app.core import database as database_module
from app import models  # noqa: F401 registers all models on Base.metadata
from app.seed.seed_data import run_seed

from app.api.routes import (
    auth, resources, faculty, courses, timetable, availability,
    schedule_requests, shift_requests, rescheduling, banker, analytics,
    sync_dashboard, users, ws, backup,
)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=database_module.engine)
    run_seed()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resources.router)
app.include_router(faculty.router)
app.include_router(courses.router)
app.include_router(timetable.router)
app.include_router(availability.router)
app.include_router(schedule_requests.router)
app.include_router(shift_requests.router)
app.include_router(rescheduling.router)
app.include_router(banker.router)
app.include_router(analytics.router)
app.include_router(sync_dashboard.router)
app.include_router(backup.router)
app.include_router(ws.router)
