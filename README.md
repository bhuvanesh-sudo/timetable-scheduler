# M3 Timetable Scheduling and Faculty Workload Optimization System

**Sprint 2 Ready** | Professional Academic Scheduling Platform
**Team 10** | Software Engineering Capstone Project

---

## 📋 Project Overview

The M3 Timetable Scheduling System is an intelligent scheduling platform that automatically generates conflict-free institutional timetables. The system uses constraint programming algorithms to create optimal schedules considering faculty availability, room allocation, section requirements, and workload distribution.

## 🏗️ System Architecture

The project follows a modern decoupled architecture:
- **Frontend**: React + Vite (Custom Professional Design System)
- **Backend**: Django + Django REST Framework
- **Database**: SQLite (Main) + Separate Audit Database

---

## 🚀 Getting Started (Terminal Setup)

Follow these steps to get the system running in your local environment.

### 1. Terminal 1: Backend & Worker
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Sync Environment
cp .env.example .env

# Database & Data Setup
python manage.py migrate
python manage.py migrate --database=audit_db
python manage.py import_data --clear
python manage.py setup_standard_users

# Run Background Worker (Ensure Redis is running)
celery -A timetable_project worker --loglevel=ERROR

# Run Backend Server
python manage.py runserver
```

### 2. Terminal 2: Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Credentials Quick Reference

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` |
| **HOD** | `hod` | `hod123` |
| **Faculty** | `T001` to `T086` | `faculty123` |

**Central Institution Email**: `m3amrita@gmail.com`

---

## 👥 Team 10
- **Vamsi (505)** - Backend & Algorithm
- **Bhuvanesh (544)** - Frontend & UI/UX
- **Akshitha (555)** - Algorithm & Support
- **Kanishthika (520)** - Quality Assurance
- **Karthikeyan (539)** - DevOps & Structure

---
**Status**: 100% Ready for Distribution
