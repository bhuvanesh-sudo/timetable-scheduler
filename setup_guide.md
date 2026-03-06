# M3 Timetable System - Teammate Setup Guide 🚀

To get this project running on your device after cloning, follow these two command sequences:

### 1. Backend (Terminal 1)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# Create your .env file from the example
cp timetable_project/.env.example timetable_project/.env
# IMPORTANT: Open timetable_project/.env and add your Gmail App Password & Google Client ID!

# Setup Database & Standard Users
python manage.py migrate
python manage.py import_data          # Link CSV data
python manage.py setup_standard_users # Reset/Create dev logins
python manage.py runserver
```

### 2. Frontend (Terminal 2)
```bash
cd frontend
npm install

# Create your .env file
cp .env.example .env
# IMPORTANT: Open .env and add your VITE_GOOGLE_CLIENT_ID!

npm run dev
```

---

### 🔑 Default Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` |
| **HOD** | `hod` | `hod123` |
| **Faculty** | `T001` (up to `T086`) | `faculty123` |

> [!TIP]
> **Faculty Login**: Use the Teacher ID (e.g., `T001`) as the username. The system handles the "Welcome [Full Name]" logic automatically!
