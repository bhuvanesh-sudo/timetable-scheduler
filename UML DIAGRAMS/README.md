# Architectural Documentation: University Timetable Scheduling System



## 1. Architecture Rationale

The system architecture is designed with the following core principles:

1. **Decoupled Computation:** The scheduling algorithm (AI Solver) is computationally expensive (NP-Hard). Therefore, the architecture segregates the **Core Application Server** (Django) from the **AI Solver Engine** using an asynchronous job queue (RabbitMQ/Redis). This prevents HTTP request blocking during schedule generation.
2. **Role-Based Security:** A strict Role-Based Access Control (RBAC) mechanism is implemented via an API Gateway to ensure data integrity between System Administrators, Auditors (HODs), and Faculty.
3. **Scalability:** The use of stateless REST APIs and containerized microservices (Notification Service, PDF Engine) allows individual components to scale horizontally based on load.

## 2. UML Diagram Index

The architectural documentation is divided into the following five core diagrams:

| Diagram Type | Filename | Scope |
| --- | --- | --- |
| **Use Case** | `use-case_diagram.jpg` | Functional requirements and actor interactions. |
| **Architecture** | `architecture_diagram.jpg` | High-level system topology and technology stack. |
| **Activity** | `activity_diagram.jpg` | Logic flow for the scheduling algorithm and validation. |
| **Sequence** | `sequence_diagram.jpg` | Chronological object interaction and API lifecycle. |
| **Schema (ERD)** | `Schema Diagram.jpg` | Database normalization and entity relationships. |

---

## 3. Detailed Diagram Analysis

### 3.1. Use Case Diagram

**Artifact:** `use-case_diagram.jpg`

This diagram defines the functional boundaries of the system. It identifies three primary actors:

* **System Admin:** Possesses the highest privilege level, responsible for infrastructure configuration (Rooms, Blocks), bulk data ingestion, and triggering the AI generation process.
* **HOD (Auditor):** Functions as a compliance officer, approving constraints and monitoring faculty fatigue metrics.
* **Faculty:** End-users who interact with the system primarily to declare availability constraints.

**Key Design Note:** The *Generate Schedule* use case implements an "Include" relationship with *View Conflict Report* and an "Extend" relationship with *Manual Override*, indicating that manual intervention is an optional extension of the generation process.

### 3.2. Architecture Diagram

**Artifact:** `architecture_diagram.jpg`

This diagram illustrates the infrastructure topology. The system is divided into four distinct layers:

1. **Presentation Layer:** A ReactJS + Redux Single Page Application (SPA) serving three distinct dashboards based on user roles.
2. **Security Layer:** An API Gateway handling JWT authentication and SSO, forwarding requests to an RBAC Guard.
3. **Application Layer:**
* **Core Server (Django REST):** Orchestrates business logic.
* **Data Ingestion:** A Pandas/CSV parsing module for handling bulk uploads.
* **Worker Nodes:** Asynchronous services for PDF generation (ReportLab) and Email Notifications (Celery/SendGrid).


4. **Computation Layer:** The AI Constraint Solver, which operates independently to process Hard and Soft rules.

### 3.3. Activity Diagram

**Artifact:** `activity_diagram.jpg`

This diagram details the algorithmic flow of the scheduling process:

1. **Validation:** Input data undergoes strict validation. Invalid data triggers a loop back to the upload phase.
2. **Optimization Loop:** The "Network Assignment" phase executes the evolutionary algorithm:
* *Apply Hard Constraints:* Mandatory rules (e.g., room capacity, double-booking prevention).
* *Apply Soft Constraints:* Optimization rules (e.g., faculty preference, gap minimization).


3. **Convergence Check:** If the fitness score meets the threshold, the schedule is finalized. If not, the system triggers a manual resolution path or loops back for re-calculation.

### 3.4. Sequence Diagram

**Artifact:** `sequence_diagram.jpg`

This diagram captures the asynchronous nature of the schedule generation request, broken down into four phases:

1. **Phase 1 (Secure Data Upload):** Synchronous validation of uploaded CSV/JSON data.
2. **Phase 2 (Async Job Initiation):** The Core Server accepts the request, pushes a task to Redis, and immediately returns a `202 Accepted` status to the client to prevent timeouts.
3. **Phase 3 (Async Processing Loop):** The Frontend polls the server for status updates while the AI Engine constructs the timetable.
4. **Phase 4 (Result Rendering):** Upon completion, the final dataset is fetched and rendered.

### 3.5. Schema Diagram (ERD)

**Artifact:** `Schema Diagram.jpg`

The database schema is normalized to Third Normal Form (3NF). Key entities include:

* **User & Faculty_Profile:** Stores authentication and domain-specific attributes (max workload).
* **Schedule_Slot:** The central entity resolving the relationship between `Course_Assignment`, `Room`, and time slots.
* **Audit_Log:** A compliance table ensuring all changes to the schedule or constraints are immutable and traceable.
* **Compliance_Rule:** (Implied in attributes) Hard-coded constraints linked to Faculty Profiles.

---

