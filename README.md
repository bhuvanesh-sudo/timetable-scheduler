# M3 Timetable Scheduling and Faculty Workload Optimization System

**Sprint 1 Deliverable** | Medium Complexity Project  
**Team 10** | Software Engineering Capstone Project

---

## 📋 Project Overview

The M3 Timetable Scheduling System is an intelligent scheduling and academic workload optimization platform that automatically generates conflict-free institutional timetables while respecting real-world constraints. The system uses constraint programming algorithms to create optimal schedules considering faculty availability, room allocation, section requirements, and workload distribution.

### Key Features (Sprint 1 - 50% Implementation)

✅ **Automated Schedule Generation** - Constraint-based algorithm with backtracking  
✅ **Data Management** - CRUD operations for teachers, courses, rooms, and sections  
✅ **Timetable Visualization** - Interactive grid view with filtering  
✅ **Workload Analytics** - Faculty workload distribution and room utilization  
✅ **Conflict Detection** - Automatic conflict logging and reporting  
✅ **Real Campus Data** - Imported from actual institutional datasets  

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                 │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │Dashboard │   Data   │ Generate │ Timetable│ Analytics│  │
│  │          │   Mgmt   │ Schedule │   View   │          │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                           ↕ REST API                        │
│                     (axios, JSON)                           │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (Django + Django REST Framework)       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Core API (CRUD)  │  Scheduler API (Generation)      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Scheduling Algorithm (Constraint Programming)       │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Data Models (Teachers, Courses, Rooms, Sections)    │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↕                                 │
│                    SQLite Database                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.0.1
- **API**: Django REST Framework 3.14.0
- **Database**: SQLite (Sprint 1), PostgreSQL (Sprint 2)
- **Language**: Python 3.13.5

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 7.3.1
- **HTTP Client**: Axios
- **Routing**: React Router DOM
- **Styling**: Custom CSS (Professional Design System)

### Testing
- **Backend**: pytest, pytest-django, pytest-cov
- **Frontend**: Vitest, React Testing Library (Sprint 2)

---

## 📊 Database Schema

### Core Models
- **Teacher**: Faculty information with max hours per week
- **Course**: Course details with theory/lab flags, weekly slots
- **Room**: Room information with type (CLASSROOM/LAB)
- **TimeSlot**: Time slot definitions (40 slots per week)
- **Section**: Class sections with year, semester, department
- **TeacherCourseMapping**: Many-to-many relationship

### Scheduling Models
- **Schedule**: Main schedule container with status tracking
- **ScheduleEntry**: Individual class assignments
- **Constraint**: Configurable scheduling rules
- **ConflictLog**: Conflict tracking during generation

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.13+
- Node.js 18+
- npm 10+

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Import campus data
python manage.py import_data --clear

# Start development server
python manage.py runserver 8000
```

Backend will be available at: `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## 📁 Project Structure

```
SE/
├── backend/
│   ├── core/                    # Core data models and API
│   │   ├── models.py           # Data models
│   │   ├── serializers.py      # DRF serializers
│   │   ├── views.py            # API ViewSets
│   │   ├── urls.py             # API routes
│   │   └── management/
│   │       └── commands/
│   │           └── import_data.py  # CSV import script
│   ├── scheduler/               # Scheduling algorithm
│   │   ├── algorithm.py        # Core scheduling logic
│   │   ├── constraints.py      # Constraint validation
│   │   ├── views.py            # Scheduler API views
│   │   └── urls.py             # Scheduler routes
│   ├── timetable_project/       # Django project settings
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── pages/              # React pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── DataManagement.jsx
│   │   │   ├── GenerateSchedule.jsx
│   │   │   ├── ViewTimetable.jsx
│   │   │   └── Analytics.jsx
│   │   ├── services/
│   │   │   └── api.js          # API service layer
│   │   ├── App.jsx             # Main app component
│   │   └── index.css           # Professional CSS
│   ├── package.json
│   └── vite.config.js
├── Datasets/                    # Real campus data (CSV files)
│   ├── teachers1.csv
│   ├── teachers2.csv
│   ├── courses.csv
│   ├── elective_courses.csv
│   ├── rooms.csv
│   ├── timeslots.csv
│   ├── classes_odd.csv
│   ├── classes_even.csv
│   ├── teacher_course_map1.csv
│   └── teacher_course_map2.csv
└── README.md
```

---

## 🎯 API Endpoints

### Core Data APIs
- `GET/POST /api/teachers/` - Teacher CRUD
- `GET/POST /api/courses/` - Course CRUD
- `GET/POST /api/rooms/` - Room CRUD
- `GET/POST /api/sections/` - Section CRUD
- `GET /api/timeslots/` - Time slots (read-only)
- `GET/POST /api/schedules/` - Schedule management

### Scheduler APIs
- `POST /api/scheduler/generate` - Trigger schedule generation
- `GET /api/scheduler/analytics/workload?schedule_id=X` - Faculty workload
- `GET /api/scheduler/analytics/rooms?schedule_id=X` - Room utilization
- `GET /api/scheduler/timetable?schedule_id=X&section=Y` - Timetable view

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest --cov=core --cov=scheduler --cov-report=html
```

### Running the System
1. Start backend: `cd backend && source venv/bin/activate && python manage.py runserver`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:5173`

---

## 👥 Team Roles (Team 10)

| Name | Role | Responsibilities |
|------|------|------------------|
| **Vamsi (505)** | Backend Engineer | Data models, API development, scheduling algorithm |
| **Bhuvanesh (544)** | Frontend Engineer | React components, UI/UX design, API integration |
| **Akshitha (555)** | Frontend/Backend | Scheduling algorithm, frontend support |
| **Kanishthika (520)** | Test Engineer | Unit testing, integration testing, test documentation |
| **Karthikeyan (539)** | DevOps Engineer | Git setup (Sprint 1), CI/CD (Sprint 2) |

---

## 📈 Sprint 1 Deliverables

✅ **Codebase** - Complete backend and frontend implementation  
✅ **50% Functionality** - Core features operational  
✅ **Data Import** - 86 teachers, 165 courses, 44 rooms, 32 sections  
✅ **Scheduling Algorithm** - Constraint-based with backtracking  
✅ **API Documentation** - All endpoints documented  
✅ **Professional UI** - Clean, modern design  
✅ **Testing Framework** - pytest setup with test cases  
✅ **Git Repository** - Proper branching and commits  
✅ **README** - Comprehensive documentation  

### Pending for Sprint 2
- Cloud deployment (AWS/Azure/GCP)
- CI/CD pipeline (GitHub Actions)
- Advanced features (drag-and-drop, email notifications)
- PostgreSQL migration
- Enhanced testing coverage
- UML diagrams (Use Case, Class, Sequence, Activity)
- Architecture diagram

---

## 📊 Current Data Statistics

- **Teachers**: 86 faculty members
- **Courses**: 165 courses (theory + lab + electives)
- **Rooms**: 44 rooms (classrooms + labs)
- **Time Slots**: 40 slots per week (8 slots/day × 5 days)
- **Sections**: 32 class sections
- **Teacher-Course Mappings**: 924 assignments

---

## 🔍 Scheduling Algorithm

### Approach: Greedy with Backtracking

**Constraints Validated:**
1. ✅ Faculty availability (no double-booking)
2. ✅ Room availability (no double-booking)
3. ✅ Section availability (no double-booking)
4. ✅ Room type matching (Lab courses → Lab rooms)
5. ✅ Maximum 4 continuous hours per faculty
6. ✅ Faculty weekly hour limits

**Quality Scoring:**
- Conflict penalty: -5 points per unresolved conflict
- Workload balance: Penalty for high variance
- Score range: 0-100

---

## 🎨 UI Design Philosophy

- **Professional**: Clean, modern design without AI-generated look
- **Responsive**: Works on desktop and mobile
- **Accessible**: Clear typography and color contrast
- **Intuitive**: Easy navigation and clear information hierarchy
- **Fast**: Optimized performance with minimal loading times

---

## 📝 Code Comments

All code includes comprehensive comments as required for Sprint 1 evaluation:
- Function/method documentation
- Complex logic explanations
- API endpoint descriptions
- Algorithm step-by-step comments

---

## 🔗 Links

- **Backend API**: http://localhost:8000/api/
- **Frontend**: http://localhost:5173/
- **Django Admin**: http://localhost:8000/admin/

---

## 📄 License

This project is developed as part of the Software Engineering Capstone course.

---

## 🙏 Acknowledgments

- Real campus data provided by the institution
- Django and React communities for excellent documentation
- Team 10 for collaborative development

---

**Last Updated**: February 7, 2026  
**Sprint**: 1 of 2  
**Status**: ✅ 50% Implementation Complete
