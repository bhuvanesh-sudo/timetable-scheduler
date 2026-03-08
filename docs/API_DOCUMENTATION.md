# M3 System API Documentation

## Authentication Endpoints (`/api/auth/`)
All secure endpoints require a Bearer JWT token in the `Authorization` header.

*   `POST /api/auth/token/` - Obtain Access & Refresh Tokens (Login)
*   `POST /api/auth/token/refresh/` - Refresh Access Token
*   `POST /api/auth/google/` - Google OAuth Sign-In (Creates alias User if needed)
*   `GET  /api/auth/me/` - Get currently logged-in user details
*   `GET  /api/auth/users/` - List all registered system users (Admin Only)

## Core Data Endpoints (`/api/`)
These endpoints provide basic CRUD functionality for the underlying master data.
*Role requirements generally mandate Admin/HOD for writes.*

*   `/api/teachers/` - Manage Faculty
    *   *Filters: `?department=CSE`*
*   `/api/courses/` - Manage Courses & Electives
    *   *Filters: `?year=1`, `?semester=Odd`*
*   `/api/rooms/` - Manage Classrooms/Labs
    *   *Filters: `?type=LAB` or `?type=CLASSROOM`*
*   `/api/sections/` - Manage Student Batches (e.g. CSE1A)
*   `/api/timeslots/` - Grid definitions
*   `/api/teacher-course-mappings/` - Manage Who-Teaches-What constraints
*   `/api/schedules/` - Retrieve Master Schedules
*   `/api/change-requests/` - HOD request workflows for assigning subjects
    *   *Custom Actions: `.../approve/`, `.../reject/`, `.../pending_count/`*
*   `/api/audit-logs/` - Retrieve system activity history

## Scheduler Engine & Analytics (`/api/scheduler/`)

*   `POST /api/scheduler/generate`
    *   Triggers the automated AI constraint-satisfaction algorithm in the background via **Celery**.
    *   Returns: `202 Accepted`
*   `GET  /api/scheduler/timetable`
    *   Get schedule instances. *Query Params: `schedule_id`, `section`, `teacher`*
*   `GET  /api/scheduler/my-schedule`
    *   Auto-filters timetable for the currently logged-in faculty token.
*   `GET  /api/scheduler/analytics/workload`
    *   Retrieve teacher hour-utilization stats.
*   `GET  /api/scheduler/analytics/rooms`
    *   Retrieve spatial utilization stats.
*   `POST /api/scheduler/move-entry`
    *   (Admin) Perform Drag-and-Drop. Requires optimistic lock `last_modified` timestamp.
*   `GET  /api/scheduler/validate-move`
    *   Real-time conflict pre-flight check without committing.
*   `POST /api/scheduler/publish/<int:schedule_id>/`
    *   Publish schedule, save snapshot variation, and send Notifications/Emails to affected faculty.

## System Resilience (`/api/system/`)
*   `POST /api/system/backups/create/` - Create a `.sql` Postgres snapshot
*   `POST /api/system/restore/<filename>/` - Restore from snapshot
*   `POST /api/system/reset-semester/` - End-of-year rollover data wipe
