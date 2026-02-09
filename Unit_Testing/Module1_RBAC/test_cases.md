# Test Cases for Module 1 - RBAC (Modular)

## 1. User Authentication & Profile (`test_user_auth.py`)

| Test Case ID | Feature | Objective | Input (User Role) | Expected Outcome |
|--------------|---------|-----------|-------------------|------------------|
| TC_RBAC_UA_001 | IsAdmin | Verify Admin access logic | ADMIN | Granted |
| TC_RBAC_UA_002 | IsHODOrAdmin | Verify HOD access logic | HOD | Granted |
| TC_RBAC_UA_003 | Profile Access | Verify user can see own profile | Any | 200 OK |
| TC_RBAC_UA_004 | Admin Listing | Verify Admin-only user listing | ADMIN | 200 OK |
| TC_RBAC_UA_005 | Admin Listing | Block unauthorized listing | HOD/FACULTY | 403 Forbidden |
| TC_RBAC_UA_006 | Protection | Block deletion of protected users | ADMIN | 403 Forbidden |

## 2. Resource Permissions (`test_resource_permissions.py`)

| Test Case ID | Resource | Objective | Action | Role | Expected Outcome |
|--------------|----------|-----------|--------|------|------------------|
| TC_RBAC_RP_001 | Teacher | View all teachers | GET | FACULTY | 200 OK |
| TC_RBAC_RP_002 | Teacher | Block teacher creation | POST | FACULTY | 403 Forbidden |
| TC_RBAC_RP_003 | Course | View all courses | GET | FACULTY | 200 OK |
| TC_RBAC_RP_004 | Room | Block room creation | POST | FACULTY | 403 Forbidden |

## 3. Change Requests (`test_change_requests.py`)

| Test Case ID | Feature | Objective | Role | Expected Outcome |
|--------------|---------|-----------|------|------------------|
| TC_RBAC_CR_001 | Request View | HOD sees only their own requests | HOD | Filtered List |
| TC_RBAC_CR_002 | Request View | Admin sees all requests | ADMIN | Full List |
| TC_RBAC_CR_003 | Approval | Block HOD from approving requests | HOD | 403 Forbidden |

## 4. System Governance (`test_governance.py`)

| Test Case ID | Feature | Objective | Role | Expected Outcome |
|--------------|---------|-----------|------|------------------|
| TC_RBAC_GV_001 | Audit Logs | Restrict access to Admins/HODs | FACULTY | 403/404 |
| TC_RBAC_GV_002 | Audit Logs | Allow HOD access to logs | HOD | 200 OK |
| TC_RBAC_GV_003 | Constraints | Restrict constraint creation to Admin | HOD | 403 Forbidden |
| TC_RBAC_GV_004 | Constraints | Allow Admin to create constraints | ADMIN | 201 Created |
