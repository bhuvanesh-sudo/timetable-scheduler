# UML Diagrams for M3 Timetable System

This document contains textual representations of the required UML diagrams for Sprint 1. These diagrams should be created in StarUML for the final submission.

---

## 1. Use Case Diagram

### Actors
- **Admin**: System administrator
- **HOD**: Head of Department
- **Faculty**: Teaching staff
- **Student**: Students

### Use Cases

#### Admin Use Cases
- Manage Teachers (CRUD)
- Manage Courses (CRUD)
- Manage Rooms (CRUD)
- Manage Sections (CRUD)
- Import Data from CSV
- Generate Schedule
- View All Timetables
- View Analytics
- Resolve Conflicts

#### HOD Use Cases
- View Department Timetable
- View Faculty Workload
- Generate Department Schedule
- View Analytics
- Request Schedule Changes

#### Faculty Use Cases
- View Personal Timetable
- View Assigned Courses
- View Room Assignments
- Check Workload

#### Student Use Cases
- View Section Timetable
- View Course Schedule
- Check Room Locations

### Relationships
- Admin **includes** all use cases
- HOD **extends** Admin for department-specific operations
- Faculty **uses** View Personal Timetable
- Student **uses** View Section Timetable
- Generate Schedule **includes** Validate Constraints
- Generate Schedule **includes** Detect Conflicts

---

## 2. Class Diagram

### Core Classes

```
┌─────────────────────┐
│     Teacher         │
├─────────────────────┤
│ - teacher_id: str   │
│ - teacher_name: str │
│ - email: str        │
│ - department: str   │
│ - max_hours: int    │
├─────────────────────┤
│ + __str__()         │
│ + validate()        │
└─────────────────────┘
         │
         │ *
         │
         ▼
┌─────────────────────┐
│TeacherCourseMapping │
├─────────────────────┤
│ - teacher: FK       │
│ - course: FK        │
│ - preference: int   │
└─────────────────────┘
         │
         │ *
         │
         ▼
┌─────────────────────┐
│      Course         │
├─────────────────────┤
│ - course_id: str    │
│ - course_name: str  │
│ - year: int         │
│ - semester: str     │
│ - credits: int      │
│ - is_lab: bool      │
│ - weekly_slots: int │
├─────────────────────┤
│ + __str__()         │
│ + validate()        │
└─────────────────────┘

┌─────────────────────┐
│       Room          │
├─────────────────────┤
│ - room_id: str      │
│ - block: str        │
│ - floor: int        │
│ - room_type: enum   │
├─────────────────────┤
│ + __str__()         │
│ + is_available()    │
└─────────────────────┘

┌─────────────────────┐
│     TimeSlot        │
├─────────────────────┤
│ - slot_id: str      │
│ - day: str          │
│ - slot_number: int  │
│ - start_time: time  │
│ - end_time: time    │
├─────────────────────┤
│ + __str__()         │
└─────────────────────┘

┌─────────────────────┐
│      Section        │
├─────────────────────┤
│ - class_id: str     │
│ - year: int         │
│ - section: str      │
│ - sem: str          │
│ - department: str   │
├─────────────────────┤
│ + __str__()         │
└─────────────────────┘

┌─────────────────────┐
│     Schedule        │
├─────────────────────┤
│ - schedule_id: int  │
│ - name: str         │
│ - semester: str     │
│ - year: int         │
│ - status: enum      │
│ - quality_score: fl │
├─────────────────────┤
│ + generate()        │
│ + calculate_score() │
└─────────────────────┘
         │
         │ 1
         │
         ▼ *
┌─────────────────────┐
│   ScheduleEntry     │
├─────────────────────┤
│ - schedule: FK      │
│ - section: FK       │
│ - course: FK        │
│ - teacher: FK       │
│ - room: FK          │
│ - timeslot: FK      │
│ - is_lab: bool      │
├─────────────────────┤
│ + validate()        │
└─────────────────────┘
```

### Algorithm Classes

```
┌──────────────────────────┐
│  TimetableScheduler      │
├──────────────────────────┤
│ - schedule: Schedule     │
│ - validator: Validator   │
│ - conflicts: list        │
├──────────────────────────┤
│ + generate()             │
│ + schedule_section()     │
│ + find_suitable_room()   │
│ + log_conflict()         │
└──────────────────────────┘
            │
            │ uses
            ▼
┌──────────────────────────┐
│  ConstraintValidator     │
├──────────────────────────┤
│ - schedule: Schedule     │
│ - entries: QuerySet      │
├──────────────────────────┤
│ + validate_faculty()     │
│ + validate_room()        │
│ + validate_section()     │
│ + validate_room_type()   │
│ + validate_hours()       │
│ + validate_all()         │
└──────────────────────────┘
```

---

## 3. Sequence Diagram - Schedule Generation Flow

```
Admin -> API: POST /api/scheduler/generate
API -> SchedulerView: trigger_generation()
SchedulerView -> Schedule: create(name, semester, year)
Schedule --> SchedulerView: schedule_id
SchedulerView -> TimetableScheduler: new(schedule)
TimetableScheduler -> Database: get_sections()
Database --> TimetableScheduler: sections[]

loop for each section
    TimetableScheduler -> Database: get_courses(section)
    Database --> TimetableScheduler: courses[]
    
    loop for each course
        TimetableScheduler -> Database: get_teachers(course)
        Database --> TimetableScheduler: teachers[]
        
        loop for each timeslot
            TimetableScheduler -> ConstraintValidator: validate_all()
            ConstraintValidator -> Database: check_conflicts()
            Database --> ConstraintValidator: conflict_status
            ConstraintValidator --> TimetableScheduler: is_valid
            
            alt is_valid
                TimetableScheduler -> Database: create_entry()
                Database --> TimetableScheduler: success
            else has_conflict
                TimetableScheduler -> ConflictLog: log_conflict()
            end
        end
    end
end

TimetableScheduler -> Schedule: calculate_quality()
Schedule --> TimetableScheduler: quality_score
TimetableScheduler --> SchedulerView: result
SchedulerView --> API: response
API --> Admin: schedule_data
```

---

## 4. Activity Diagram - Admin Workflow

```
[Start]
   │
   ▼
[Login to System]
   │
   ▼
[View Dashboard]
   │
   ├──────────────┬──────────────┬──────────────┐
   │              │              │              │
   ▼              ▼              ▼              ▼
[Manage Data] [Generate]   [View Timetable] [Analytics]
   │           Schedule         │              │
   │              │              │              │
   ▼              ▼              ▼              ▼
[Select Tab]  [Configure]   [Select Filter] [Select Schedule]
   │           Parameters       │              │
   ▼              │              ▼              ▼
[View/Edit]      ▼          [View Grid]    [View Charts]
   │        [Click Generate]    │              │
   ▼              │              ▼              ▼
[Save Changes]   ▼          [Export PDF]   [Download Report]
   │        [Processing...]     │              │
   │              │              │              │
   │              ▼              │              │
   │        {Schedule Ready?}    │              │
   │         /        \          │              │
   │       Yes        No         │              │
   │        │          │         │              │
   │        │          ▼         │              │
   │        │    [View Conflicts]│              │
   │        │          │         │              │
   │        │          ▼         │              │
   │        │    [Resolve]       │              │
   │        │          │         │              │
   │        ▼          │         │              │
   │    [Success]      │         │              │
   │        │          │         │              │
   └────────┴──────────┴─────────┴──────────────┘
                       │
                       ▼
                   [Logout]
                       │
                       ▼
                    [End]
```

---

## 5. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │         React Frontend (Port 5173)               │  │
│  │  ┌────────┬────────┬────────┬────────┬────────┐  │  │
│  │  │Dashboard│  Data  │Generate│Timetable│Analytics│ │  │
│  │  └────────┴────────┴────────┴────────┴────────┘  │  │
│  │              Axios HTTP Client                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │ REST API (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Django REST Framework (Port 8000)           │  │
│  │  ┌────────────────┬──────────────────────────┐  │  │
│  │  │  Core API      │  Scheduler API           │  │  │
│  │  │  (ViewSets)    │  (Function Views)        │  │  │
│  │  └────────────────┴──────────────────────────┘  │  │
│  │              Serializers & Validators            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Scheduling Algorithm                      │  │
│  │  ┌────────────────┬──────────────────────────┐  │  │
│  │  │TimetableScheduler│ ConstraintValidator    │  │  │
│  │  │(Greedy+Backtrack)│ (6 Core Constraints)   │  │  │
│  │  └────────────────┴──────────────────────────┘  │  │
│  │         Quality Scoring & Conflict Detection     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Django ORM Models                    │  │
│  │  Teacher │ Course │ Room │ TimeSlot │ Section    │  │
│  │  Schedule │ ScheduleEntry │ Constraint │ Conflict │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │           SQLite Database (Sprint 1)              │  │
│  │        PostgreSQL (Planned for Sprint 2)          │  │
│  │                                                    │  │
│  │  1,300+ Records: Teachers, Courses, Rooms, etc.  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Notes

These diagrams should be created in **StarUML** with proper formatting:

1. **Use Case Diagram**: Show all actors on the left, use cases in the center, with include/extend relationships
2. **Class Diagram**: Show all classes with attributes, methods, and relationships (associations, inheritance, composition)
3. **Sequence Diagram**: Show the complete flow of schedule generation with all interactions
4. **Activity Diagram**: Show the admin workflow with decision points and parallel activities

**Tools Required**: StarUML 5.0+

**Export Format**: PNG/PDF for documentation

---

**Created**: February 7, 2026  
**Sprint**: 1  
**Team**: Team 10
