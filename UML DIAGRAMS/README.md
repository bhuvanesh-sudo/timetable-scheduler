Here is a comprehensive, production-grade README documentation for the University Timetable Scheduling System’s architectural artifacts.

---

# Architectural Documentation: University Timetable Scheduling System


## 1. Project Overview

The **University Timetable Scheduling System** is an enterprise-grade web application designed to automate the complex logistical challenge of academic scheduling. The system utilizes a constraint-satisfaction AI engine to generate conflict-free timetables based on resource availability, faculty constraints, and curriculum requirements.

This repository contains the architectural blueprints and Unified Modeling Language (UML) diagrams that define the system's structure, behavior, and data interactions. These artifacts serve as the primary reference for backend engineers, frontend developers, and system architects.

## 2. Architecture Rationale

The system architecture is designed with the following core principles:

1. **Decoupled Computation:** The scheduling algorithm (AI Solver) is computationally expensive (NP-Hard). Therefore, the architecture segregates the **Core Application Server** (Django) from the **AI Solver Engine** using an asynchronous job queue (RabbitMQ/Redis). This prevents HTTP request blocking during schedule generation.
2. **Role-Based Security:** A strict Role-Based Access Control (RBAC) mechanism is implemented via an API Gateway to ensure data integrity between System Administrators, Auditors (HODs), and Faculty.
3. **Scalability:** The use of stateless REST APIs and containerized microservices (Notification Service, PDF Engine) allows individual components to scale horizontally based on load.

## 3. UML Diagram Index

The architectural documentation is divided into the following five core diagrams:

| Diagram Type | Filename | Scope |
| --- | --- | --- |
| **Use Case** | `use-case_diagram.jpg` | Functional requirements and actor interactions. |
| **Architecture** | `architecture_diagram.jpg` | High-level system topology and technology stack. |
| **Activity** | `activity_diagram.jpg` | Logic flow for the scheduling algorithm and validation. |
| **Sequence** | `sequence_diagram.jpg` | Chronological object interaction and API lifecycle. |
| **Schema (ERD)** | `Schema Diagram.jpg` | Database normalization and entity relationships. |

---

## 4. Detailed Diagram Analysis

### 4.1. Use Case Diagram

**Artifact:** `use-case_diagram.jpg`

This diagram defines the functional boundaries of the system. It identifies three primary actors:

* **System Admin:** Possesses the highest privilege level, responsible for infrastructure configuration (Rooms, Blocks), bulk data ingestion, and triggering the AI generation process.
* **HOD (Auditor):** Functions as a compliance officer, approving constraints and monitoring faculty fatigue metrics.
* **Faculty:** End-users who interact with the system primarily to declare availability constraints.

**Key Design Note:** The *Generate Schedule* use case implements an "Include" relationship with *View Conflict Report* and an "Extend" relationship with *Manual Override*, indicating that manual intervention is an optional extension of the generation process.

### 4.2. Architecture Diagram

**Artifact:** `architecture_diagram.jpg`

This diagram illustrates the infrastructure topology. The system is divided into four distinct layers:

1. **Presentation Layer:** A ReactJS + Redux Single Page Application (SPA) serving three distinct dashboards based on user roles.
2. **Security Layer:** An API Gateway handling JWT authentication and SSO, forwarding requests to an RBAC Guard.
3. **Application Layer:**
* **Core Server (Django REST):** Orchestrates business logic.
* **Data Ingestion:** A Pandas/CSV parsing module for handling bulk uploads.
* **Worker Nodes:** Asynchronous services for PDF generation (ReportLab) and Email Notifications (Celery/SendGrid).


4. **Computation Layer:** The AI Constraint Solver, which operates independently to process Hard and Soft rules.

### 4.3. Activity Diagram

**Artifact:** `activity_diagram.jpg`

This diagram details the algorithmic flow of the scheduling process:

1. **Validation:** Input data undergoes strict validation. Invalid data triggers a loop back to the upload phase.
2. **Optimization Loop:** The "Network Assignment" phase executes the evolutionary algorithm:
* *Apply Hard Constraints:* Mandatory rules (e.g., room capacity, double-booking prevention).
* *Apply Soft Constraints:* Optimization rules (e.g., faculty preference, gap minimization).


3. **Convergence Check:** If the fitness score meets the threshold, the schedule is finalized. If not, the system triggers a manual resolution path or loops back for re-calculation.

### 4.4. Sequence Diagram

**Artifact:** `sequence_diagram.jpg`

This diagram captures the asynchronous nature of the schedule generation request, broken down into four phases:

1. **Phase 1 (Secure Data Upload):** Synchronous validation of uploaded CSV/JSON data.
2. **Phase 2 (Async Job Initiation):** The Core Server accepts the request, pushes a task to Redis, and immediately returns a `202 Accepted` status to the client to prevent timeouts.
3. **Phase 3 (Async Processing Loop):** The Frontend polls the server for status updates while the AI Engine constructs the timetable.
4. **Phase 4 (Result Rendering):** Upon completion, the final dataset is fetched and rendered.

### 4.5. Schema Diagram (ERD)

**Artifact:** `Schema Diagram.jpg`

The database schema is normalized to Third Normal Form (3NF). Key entities include:

* **User & Faculty_Profile:** Stores authentication and domain-specific attributes (max workload).
* **Schedule_Slot:** The central entity resolving the relationship between `Course_Assignment`, `Room`, and time slots.
* **Audit_Log:** A compliance table ensuring all changes to the schedule or constraints are immutable and traceable.
* **Compliance_Rule:** (Implied in attributes) Hard-coded constraints linked to Faculty Profiles.

---

## 5. Assumptions and Design Constraints

### 5.1. Assumptions

* **Data Integrity:** It is assumed that bulk data uploaded by the System Admin follows the strict template definitions provided in the `templates/` directory.
* **Single-Tenant Execution:** The AI Solver is currently optimized for processing one major scheduling batch per department at a time.
* **Network Reliability:** External SMTP services (SendGrid) are assumed to be available for critical notifications.

### 5.2. Design Constraints

* **Optimization Timeout:** The AI Solver has a hard execution cap of 15 minutes. If convergence is not reached, the system returns the "best found" solution with a conflict report.
* **Browser Compatibility:** The Interactive Dashboard (React) requires WebGL support for rendering large schedule grids.
* **Database Locking:** To prevent race conditions, the `Schedule_Slot` table implements row-level locking during the "Manual Override" phase.

## 6. Methodology

The system design follows **Domain-Driven Design (DDD)** principles. The complexity of the "Scheduling" domain is isolated from the "User Management" domain.

* **Development Lifecycle:** Agile/Scrum.
* **Diagramming Standard:** UML 2.5.
* **Architectural Pattern:** Event-Driven Microservices (Hybrid).

## 7. Versioning Approach

This documentation tracks the software versioning.

* **Major Version (1.x):** Significant architectural changes (e.g., changing the AI Solver engine or Database).
* **Minor Version (x.1):** Addition of new actors or modules (e.g., adding a Student Portal).
* **Patch Version (x.x.1):** Corrections to field names or logic flow corrections in diagrams.

## 8. Naming Conventions

To ensure consistency across diagrams and code:

* **Classes/Entities:** PascalCase (e.g., `CourseAssignment`, `FacultyProfile`).
* **Database Tables:** snake_case (e.g., `audit_log`, `schedule_slot`).
* **API Endpoints:** kebab-case (e.g., `/api/v1/generate-schedule`).
* **Functions/Methods:** camelCase (e.g., `calculateFitness()`, `validateToken()`).

## 9. Maintenance and Tools

### 9.1. Tools Used

The diagrams were generated using the following enterprise modeling tools:

* **Structural & Behavioral Diagrams:** PlantUML / Lucidchart.
* **Schema Design:** DbSchema / MySQL Workbench.

### 9.2. How to Regenerate

1. Source files for these diagrams are located in `docs/uml_source/`.
2. Edit the source files using the appropriate tool.
3. Export high-resolution JPG/PNG files.
4. Update this README to reflect changes in logic or structure.

## 10. Best Practices for Extension

When extending the system, adhering to the following practices is mandatory:

1. **Schema First:** Do not modify the database layer without first updating the Schema Diagram and validating normalization.
2. **Async by Default:** Any new feature involving heavy computation (e.g., generating analytics reports) must follow the asynchronous pattern defined in the Sequence Diagram.
3. **Auditability:** New write-operations must trigger an entry in the `Audit_Log` table as defined in the Schema.