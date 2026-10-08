# Spec Delta

## Purpose

Provide controlled, auditable access to operational equipment data and give authorized teams concise views and exports for inventory and maintenance planning.

## ADDED Requirements

### Requirement: Authenticate users and enforce role permissions
The system SHALL require an authenticated user for all non-public application data and SHALL enforce authorization on each protected operation. It SHALL support the roles `administrator`, `asset_manager`, `technician`, and `viewer`, with permissions for equipment and catalog management, maintenance and occurrence management, user and role administration, and read-only access. Administrators SHALL manage users, roles, and permissions; asset managers SHALL manage inventory and view operational data; technicians SHALL manage assigned maintenance and occurrences and view relevant equipment; viewers SHALL have read-only access. The system SHALL deny operations not granted to the user's role, including direct API requests, and SHALL NOT rely only on hiding interface controls.

#### Scenario: Deny unauthenticated access
- **WHEN** a user without a valid authenticated session requests protected equipment data
- **THEN** the system SHALL deny access and SHALL NOT return protected records

#### Scenario: Enforce a viewer's read-only role
- **WHEN** a viewer attempts to create, update, deactivate, or delete an equipment, maintenance, occurrence, user, or catalog record
- **THEN** the system SHALL deny the operation and preserve stored data

#### Scenario: Administrator manages user access
- **WHEN** an administrator creates or changes a user's role or enabled state
- **THEN** the system SHALL persist the access change and apply the new permission set on subsequent protected operations

#### Scenario: Signed-in user without permission for a screen
- **WHEN** a signed-in user opens a screen whose permission their role does not hold
- **THEN** the system SHALL show a no-access page that requires only a session, SHALL NOT show the protected data, and SHALL NOT redirect between protected screens in a loop

### Requirement: Provision accounts with temporary passwords
Accounts SHALL be created only by administrators; public sign-up SHALL be unavailable. An administrator SHALL set a temporary password when creating an account, and the account SHALL hold no permissions until its user replaces that password on first sign-in. Replacing a password SHALL require the current password and a new password that meets the password policy (at least 8 characters with letters and digits) and differs from the current one. Administrators SHALL NOT set or reset the password of an existing account by any means.

#### Scenario: Force a password change on first sign-in
- **WHEN** a user signs in with the temporary password an administrator set at account creation
- **THEN** the system SHALL require a new password before any other use and SHALL deny every protected operation until the change succeeds

#### Scenario: Administrator cannot set an existing user's password
- **WHEN** an administrator attempts to set or reset the password of an existing account
- **THEN** the system SHALL refuse and the account's password SHALL remain unchanged

### Requirement: Recover access through emailed reset links only
A user who forgets their password SHALL recover access only through a reset link sent by email through an external email service. A reset link SHALL be single use, SHALL be stored only as a hash, SHALL expire after 60 minutes, and SHALL be invalidated by any newer request. Completing a reset SHALL set the new password in one step and SHALL NOT create a session or grant access to any other operation; it SHALL also clear a pending temporary password. Requests for unknown or disabled accounts SHALL receive the same response as requests for active accounts.

#### Scenario: Reset a forgotten password
- **WHEN** a user follows a valid, unexpired, unused reset link and submits a new password that meets the policy
- **THEN** the system SHALL replace the password, mark the link used, and require a normal sign-in afterwards

#### Scenario: Reject an unusable reset link without revealing the account
- **WHEN** a reset is attempted with an invalid, expired, or already used link, or for an unknown or disabled account
- **THEN** the system SHALL refuse with the same response in every case and SHALL NOT disclose whether the account exists

### Requirement: Manage roles
Administrators SHALL be able to create roles, grant and revoke permissions on them, and activate or deactivate them; roles SHALL never be deleted. The `administrator` role SHALL NOT be deactivated and SHALL NOT lose the user-administration permission. A role still assigned to enabled users SHALL NOT be deactivated. Role changes SHALL be audited.

#### Scenario: Create a role and grant permissions
- **WHEN** an administrator creates a role and grants it permissions
- **THEN** the system SHALL persist the role and grants, record audit events, and apply the grants to users assigned that role

#### Scenario: Refuse unsafe role deactivation
- **WHEN** an administrator attempts to deactivate the `administrator` role or a role assigned to enabled users
- **THEN** the system SHALL refuse and leave the role active

### Requirement: Audit significant operational and access changes
The system SHALL record an audit event for authentication-relevant user changes and material create, update, status-change, and deactivation actions on equipment, catalogs, component assignments, maintenance, occurrences, and user permissions. Each event SHALL identify the acting user, action, affected record, and timestamp. Audit history SHALL be readable only by authorized users and SHALL not be editable through ordinary application workflows. Audit events SHALL NOT contain credential material such as password hashes or reset tokens; events recorded before this rule SHALL be kept, with only their credential values removed.

#### Scenario: Record equipment status change
- **WHEN** an authorized user changes an equipment status
- **THEN** the system SHALL record the actor, equipment, previous and new status, and timestamp

#### Scenario: Preserve an auditable maintenance change
- **WHEN** a user changes maintenance state or records its completion
- **THEN** the system SHALL add an audit event that identifies the actor, maintenance record, action, and timestamp

#### Scenario: Keep credentials out of audit history
- **WHEN** an authorized user reads audit events, including events recorded before this rule
- **THEN** no event SHALL contain a password hash or reset token, and no historical event SHALL have been deleted

### Requirement: Provide an operational dashboard
The system SHALL provide an authenticated dashboard summarizing active equipment totals by status and category, upcoming and overdue preventive maintenance, open occurrences by severity and status, and recent maintenance activity. Dashboard values SHALL be derived from persisted equipment and maintenance records and SHALL respect the user's read permissions and currently selected filters.

#### Scenario: View operational summary
- **WHEN** an authorized user opens the dashboard
- **THEN** the system SHALL show current status/category totals, due and overdue work, open occurrence counts, and recent maintenance activity from the available records

#### Scenario: Filter dashboard by location
- **WHEN** an authorized user selects a location filter
- **THEN** the system SHALL recalculate equipment and related operational summaries for that location without including unrelated records

#### Scenario: Location filter excludes sub-locations
- **WHEN** an authorized user filters by a location that has sub-locations
- **THEN** the system SHALL include only equipment assigned directly to the selected location, in the dashboard, lists, and reports alike

### Requirement: Generate operational reports
The system SHALL allow authorized users to view and filter reports for equipment inventory, status and location, upcoming or overdue maintenance, maintenance history, and open or resolved occurrences. Reports SHALL provide on-screen results and a downloadable CSV export using the same filters and authorized data scope. Report columns SHALL contain only equipment-management, maintenance, occurrence, and user attribution fields and SHALL NOT contain patient or clinical data.

#### Scenario: Filter and export an equipment report
- **WHEN** an authorized user filters an equipment report by category, location, or status and requests CSV export
- **THEN** the system SHALL export only records matching the filters and the user's read permissions

#### Scenario: Export overdue maintenance report
- **WHEN** an authorized user requests an overdue-maintenance report for a selected date range
- **THEN** the system SHALL return planned preventive maintenance that is overdue and not completed or canceled, with the associated equipment and location

### Requirement: Isolate each deployment's institutional data
Each deployment SHALL serve one institution, and all equipment, reference catalogs, maintenance, occurrence, user, audit, dashboard, and report data SHALL remain confined to that deployment. The system SHALL not expose or combine data from another institution through application routes, API operations, searches, exports, or background processing.

#### Scenario: Query records within a deployment
- **WHEN** an authenticated user searches or exports records in an installation
- **THEN** the system SHALL return only records persisted for that installation

#### Scenario: Prevent cross-deployment data access
- **WHEN** a request supplies an identifier that belongs to data outside the active deployment
- **THEN** the system SHALL return no cross-deployment data and SHALL not disclose whether the external record exists

### Requirement: Protect service availability and user data
The system SHALL protect credentials and authenticated sessions using the selected platform's supported secure mechanisms, SHALL use encrypted transport for browser-to-service communication, and SHALL avoid exposing secrets in client-visible state or logs. Standard filtered list views SHALL target a response time of no more than 2 seconds at the 95th percentile for an installation with up to 10,000 equipment records under nominal load. The application SHALL remain usable on desktop and tablet viewports and SHALL provide labeled controls and keyboard-operable primary workflows.

#### Scenario: Load an inventory list within the target
- **WHEN** a user loads a standard paginated and filtered inventory view under nominal load with up to 10,000 equipment records
- **THEN** the system SHALL return the view within 2 seconds at the 95th percentile

#### Scenario: Use a primary workflow with keyboard navigation
- **WHEN** a user navigates an equipment or maintenance form using a keyboard
- **THEN** the system SHALL expose labeled controls in a logical focus order and allow submission and validation without requiring pointer input

### Requirement: Use one institution timezone for times
Times entered in forms and times displayed SHALL use the institution's configured timezone, regardless of the timezone of the user's browser. Calendar dates, such as planned maintenance dates and acquisition dates, SHALL be shown as entered and SHALL NOT be shifted by timezone conversion.

#### Scenario: Enter and view a completion time
- **WHEN** a user records a maintenance completion time and later views it, from a browser set to any timezone
- **THEN** the system SHALL display the same wall-clock time that was entered, in the institution's timezone, and planned dates SHALL show the same calendar day that was scheduled
