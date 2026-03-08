# M3 Timetable System - User Guide

## 1. Introduction
Welcome to the Faculty Workload Optimization & Timetable Scheduling System. The platform supports three primary user roles:
- **System Administrator:** Full access to trigger schedules, manage all data, drag-and-drop slots, and publish releases.
- **Head of Department (HOD):** Dashboard access to view department constraints, submit Teacher Change Requests for admin approval, and view Analytics.
- **Faculty:** Read-only access to view their personalized `My Timetable`, receive publication notifications, and download PDF schedules.

## 2. Authentication
Log in via the portal using either standard credentials provided by the Admin, or click **"Sign In with Google"**. If your university email matches an existing faculty record, your account will automatically be aliased to your permissions.

## 3. Administrator Workflows

### 3.1 Data Ingestion
1. Navigate to the **Data Management** tab.
2. Ensure you have the CSV files formatted precisely as expected: `courses.csv`, `teachers1.csv`, `rooms.csv`, `sections.csv`, and constraint `mappings.csv`.
3. Click "Import Data" to bulk-load the database.

### 3.2 Generating a Schedule
1. Go to the "Generate Schedule" page.
2. Enter a descriptive Name and Select the Semester/Year.
3. Click **Generate**. The process will run asynchronously to satisfy lab continuity and theory distribution rules without freezing your browser.

### 3.3 Visual Overrides (Drag & Drop)
If you spot an edge-case aesthetic issue:
1. Open the Master Timetable Grid.
2. Click and Hold any class block. Valid destination slots will glow **Green**, while slots producing clashes will glow **Red** (hovering over Red reveals a tooltip explaining *why* it clashes).
3. Drop the block in a Green slot to lock the change.

### 3.4 Publishing & Rollover
*   **Publishing:** From the grid, click "Publish Schedule". This solidifies the timetable, saves a system snapshot, and automatically blasts Emails to all faculty utilizing the SendGrid integration.
*   **Rollover:** From the Admin Dashboard, click "Reset Semester" at the end of the academic year to neatly drop current schedule instances while retaining core faculty/course data.
