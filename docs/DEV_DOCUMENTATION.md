# Developer Setup & Contribution Guide

## 1. Prerequisites
- Python 3.12+
- Node.js 20.x
- PostgreSQL 15+ (For local DB override)
- Redis 5.0+ (For Async Celery Scheduling)

## 2. Backend Setup (Django)

1. Navigate to backend: `cd backend`
2. Create virtual environment: `python3 -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure `.env`:
   * Copy `.env.example` -> `.env`
   * Add Database credentials, `SECRET_KEY`, and `GOOGLE_CLIENT_ID`
5. Migrate database: `python manage.py migrate`
6. (Optional) Load sample data: `python manage.py import_data`
7. Start Server: `python manage.py runserver`

## 3. Background Queue Setup (Celery & Redis)

M3's timetable generation runs asynchronously to prevent HTTP timeouts.
1. Ensure `redis-server` is running locally on port 6379.
2. In a new terminal, activate the venv and start Celery:
   `celery -A timetable_project worker -l INFO`

## 4. Frontend Setup (React/Vite)

1. Navigate to frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Configure `.env`:
   * Provide `VITE_GOOGLE_CLIENT_ID` matching the backend setting.
4. Start dev server: `npm run dev`

## 5. Automated CI/CD
This project utilizes GitHub Actions (see `.github/workflows/main.yml`).
All Pull Requests to `main` and `dev` will trigger:
1. Pytest suite validation (algorithm, logic, views)
2. Frontend lint checks & production build simulations.

To run tests locally: `pytest tests/` in the `/backend` directory.
