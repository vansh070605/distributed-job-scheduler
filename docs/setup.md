# Quick Start & Setup Guide

This document describes how to boot up and run the Distributed Job Scheduler locally and inside containers.

## Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose v2](https://docs.docker.com/compose/)
- [Python 3.11+](https://www.python.org/) (if running locally without Docker)
- [Node.js 18+](https://nodejs.org/) (if running frontend locally without Docker)

---

## 1. Single Command Docker Deployment

The repository is fully containerized. You can launch all backend, database, broker, scheduler, worker, and frontend services with a single command:

```bash
docker compose up --build
```

### Exposed Port Access:
- **FastAPI API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **SaaS Dashboard (React Client)**: [http://localhost:5173](http://localhost:5173)
- **PostgreSQL Database**: Port `5432`
- **Redis Server**: Port `6379`

---

## 2. Bootstrapping Your Test Environment

When you access the UI dashboard at [http://localhost:5173](http://localhost:5173) for the first time:
1. Register a new user account (e.g. `admin@scheduler.io` / `admin123`).
2. Log in with your credentials.
3. The dashboard will detect that you have no active organization or projects. Click the **Bootstrap Test Environment** button.
4. This automatically initializes:
   - Default Organization
   - Default Project
   - `default-queue` (mapped under the project with concurrency = 5)
5. You can now submit jobs directly via the **Jobs** tab.

---

## 3. Local Development Run

If you want to run services individually for debugging:

### Start Postgres & Redis dependencies:
```bash
docker compose up postgres redis -d
```

### Running Backend API:
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows: .\venv\Scripts\activate
# Unix: source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Running Celery Worker:
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### Running Celery Beat:
```bash
cd backend
celery -A app.workers.celery_app beat --loglevel=info
```

### Running React Frontend:
```bash
cd frontend
npm install
npm run dev
```
