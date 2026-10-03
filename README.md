# Academic Resource Scheduling & Dynamic Rescheduling System

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-4285F4)

A full-stack web application for scheduling classrooms, labs, and faculty, and for
rescheduling them dynamically when requests and conflicts arise. Built as an
Operating Systems course project, it applies classic OS concepts (priority scheduling
with aging, round robin, mutual exclusion, bounded concurrency, and the Banker's
Algorithm) to a realistic university-administration problem.

The project runs **entirely locally**: no paid APIs, no cloud database, and no external
accounts are required.

## Table of Contents

- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Demo Accounts](#demo-accounts)
- [Running Tests](#running-tests)
- [Docker (Optional)](#docker-optional)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Security Notes](#security-notes)
- [Known Limitations](#known-limitations)

## Key Features

- **Authentication & RBAC**: JWT-based login with four roles (Administrator, Professor,
  Event Coordinator, Student).
- **Resource management**: CRUD for rooms, labs, faculty, courses, sections, and weekly
  sessions, with search, sorting, pagination, and inline editing.
- **Automated timetable generation**: constraint-based scheduling with OR-Tools CP-SAT
  that guarantees no room, lab, or faculty double-booking, plus a weekly grid UI.
- **Availability search**: find free rooms and labs by time slot, capacity, and facilities.
- **Request workflow**: extra-class and event requests are queued by priority + aging +
  round robin, then resolved by the solver.
- **Dynamic rescheduling**: shift-request approval workflow with a discussion thread and
  live WebSocket notifications.
- **Concurrency dashboard**: live view of lock contention and solver-slot usage.
- **Banker's Algorithm simulation**: classical and dynamic variants as an interactive
  educational tool.
- **Analytics & audit logs**: usage insights and a searchable audit trail.
- **Backup & restore**: export/import the whole database as JSON from the admin UI
  (transactional import with rollback on failure).

## Architecture

| Concern | Approach |
|---|---|
| Timetable generation, allocation, rescheduling | **OR-Tools CP-SAT** is the sole authority (`backend/app/solver/`). |
| Request ordering | **Priority Scheduling + Aging + Round Robin** (`backend/app/os_simulation/`) decide only *which request is handed to the solver next*; they never place anything on the timetable. |
| Atomic timetable writes | `threading.Lock` guards the read-check-commit critical section. |
| Bounded solver concurrency | `threading.Semaphore` caps simultaneous CP-SAT jobs (`backend/app/services/sync_service.py`). |
| Banker's Algorithm | A separate educational simulation over abstract resource units. It is never used to approve real allocations. |
| Live updates | FastAPI WebSockets. |

See [`docs/architecture.md`](docs/architecture.md) for a deeper walkthrough.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite, OR-Tools CP-SAT, python-jose (JWT),
  passlib/bcrypt, WebSockets, pytest
- **Frontend:** React 18, TypeScript, Vite, Material UI, React Router, Axios,
  TanStack Query, Recharts, Vitest

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/academic-resource-scheduler.git
cd academic-resource-scheduler
```

### 2. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows (PowerShell):  venv\Scripts\Activate.ps1
# Windows (cmd):         venv\Scripts\activate.bat
# macOS / Linux:         source venv/bin/activate

pip install -r requirements.txt

# Create your local environment file and set SECRET_KEY (see Configuration)
cp .env.example .env          # Windows: copy .env.example .env

uvicorn app.main:app --reload
```

The API is served at <http://127.0.0.1:8000> with interactive docs at
<http://127.0.0.1:8000/docs>. On first launch the application creates a local SQLite
database (`backend/app.db`) and seeds demo data.

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` and `/ws` to the backend on port 8000
(see `frontend/vite.config.ts`), so no extra CORS setup is needed for local development.

### Troubleshooting

`requirements.txt` pins version ranges so `pip` can choose releases with prebuilt wheels
for your Python version. If installation fails:

1. Upgrade pip: `python -m pip install --upgrade pip`.
2. Use Python 3.11 or 3.12, which have the widest wheel coverage.
3. You should never need a Rust or C toolchain. If `pip` starts compiling packages,
   re-check that you are using this project's `requirements.txt`.

To reset the database, stop the backend, delete `backend/app.db`, and start it again.

## Configuration

Configuration is read from environment variables or from `backend/.env`. The `.env` file
is git-ignored; `backend/.env.example` documents the available settings.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | none | Secret used to sign JWTs. Must be random and at least 32 characters. The app refuses to start without it. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `720` | JWT lifetime in minutes. |
| `DATABASE_URL` | No | `sqlite:///<backend>/app.db` | SQLAlchemy database URL. |

Generate a strong key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

> **Never commit `.env`.** Only `.env.example` (placeholders) belongs in version control.

## Demo Accounts

On first startup the database is seeded with **fictional, local-only** accounts for
demonstration purposes:

| Role | Email | Password |
|---|---|---|
| Administrator | admin@college.edu | Admin@123 |
| Professor | professor@college.edu | Prof@123 |
| Event Coordinator | coordinator@college.edu | Coord@123 |
| Student | student@college.edu | Student@123 |

These credentials are for development only. Remove or change them before any real
deployment.

## Running Tests

```bash
# Backend (from backend/, virtual environment active): 19 tests
pytest -q

# Frontend (from frontend/): 11 tests
npm test
```

The backend suite uses an isolated temporary database and a test-only `SECRET_KEY`
(`backend/conftest.py`), so it does not need your `.env`.

## Docker (Optional)

```bash
cp backend/.env.example backend/.env   # then set SECRET_KEY
docker compose up --build
```

This starts the backend on port 8000 and the frontend on port 5173.

## Project Structure

```text
academic-resource-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers and dependencies
│   │   ├── core/           # Settings, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic and concurrency primitives
│   │   ├── solver/         # OR-Tools CP-SAT scheduler
│   │   ├── os_simulation/  # Priority/aging/RR queue, Banker's Algorithm
│   │   ├── websocket/      # Live notification manager
│   │   ├── seed/           # Demo data
│   │   └── tests/          # pytest suite
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/                # React + TypeScript application
├── docs/                   # Architecture, API, schema, test plan
├── docker-compose.yml
└── CHANGELOG.md
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md): layers, scheduling separation, concurrency, shift flow
- [`docs/API.md`](docs/API.md): REST endpoints and WebSocket events
- [`docs/database_schema.md`](docs/database_schema.md): database tables
- [`docs/test_plan.md`](docs/test_plan.md): automated tests and manual acceptance checklist
- [`CHANGELOG.md`](CHANGELOG.md): notable changes

## Security Notes

- The JWT signing key is **never** stored in source control; it is loaded from the
  environment or `backend/.env`.
- If a secret is ever committed by mistake, rotate it immediately. Removing it in a later
  commit does not remove it from Git history.
- The frontend currently stores the access token in `localStorage`. This is acceptable for
  a local/demo deployment; consider httpOnly cookies for production use.

## Known Limitations

- Designed for local/demo use: SQLite, a single process, and seeded demo accounts.
- The `docs/screenshots/` folder is empty. Screenshots of the UI have not been added yet.
