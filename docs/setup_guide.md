# 🚀 M3 Timetable Project Setup Guide

Follow these exact steps after cloning the repository to get the system running on your local machine.

## 💻 Terminal Commands

### 🔌 Terminal 1: Backend Server
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Setup environment variables
cp .env.example .env
# (Note: Update backend/.env with the Secrets provided below)

# Initialize Databases
python3 manage.py migrate
python3 manage.py migrate --database=audit_db

# Import Datasets & Setup Users
python3 manage.py import_data --clear
python3 manage.py setup_standard_users

# Run the server
python3 manage.py runserver
```

### ⚙️ Terminal 2: Celery Worker
```bash
# Navigate to backend and activate venv
cd backend
source venv/bin/activate

# Start the background task worker
celery -A timetable_project worker --loglevel=ERROR
```

### 🎨 Terminal 3: Frontend Web App
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env
# (Note: Update frontend/.env with the Google Client ID provided below)

# Run the development server
npm run dev
```

---

## 🔑 Default Login Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` |
| **HOD** | `hod` | `hod123` |
| **Faculty** | `T001` (up to `T086`) | `faculty123` |

---

## 🛡️ Required Secrets (.env)

**Backend Settings (`backend/.env`):**
- **Gmail**: `m3amrita@gmail.com`
- **SMTP Password**: `m3password`
- **Google Client ID**: `501564234185-nn61nqv9vukrbgajpqgq6tdo3o3bh70v.apps.googleusercontent.com`

**Frontend Settings (`frontend/.env`):**
- **Vite Google Client ID**: `501564234185-nn61nqv9vukrbgajpqgq6tdo3o3bh70v.apps.googleusercontent.com`
