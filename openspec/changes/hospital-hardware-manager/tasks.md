# Tasks

## 1. Data foundation and migration

- [x] 1.1 Verify Xano support for the proposed foreign keys, unique constraints, transactions, and indexes; record a validation result for every constraint used by the domain schema.
- [ ] 1.2 Create the relational tables, primary/foreign keys, constraints, and indexes from `design.md`; verify schema checks reject invalid references, duplicate asset numbers, duplicate non-empty serial numbers, and invalid quantities.
- [ ] 1.3 Seed the 12 equipment categories, component types, roles, permissions, and role grants; verify each required value exists exactly once and role grants match the approved matrix.
- [ ] 1.4 Extend the existing user and event-log model; migrate `admin` to `administrator` and `member` to `viewer`, disable public signup, and verify the migration preserves accounts and audit history without granting unintended privileges.

## 2. Authentication, authorization, and audit

- [ ] 2.1 Implement authenticated account provisioning (with a temporary password), disablement, and recovery flows (single-step `reset/confirm`; the session-based `reset/magic-link-login` and `reset/update_password` disabled); verify public signup is unavailable and disabled users cannot authenticate or recover access.
- [ ] 2.2 Enforce role permissions in every protected API operation; verify unauthenticated requests and each denied role/action combination return an authorization error without changing or disclosing protected data.
- [ ] 2.3 Record audit events for material inventory, component, maintenance, occurrence, location, status, and permission changes; verify actor, action, affected record, timestamp, and status before/after details are retained.

## 3. Equipment inventory

- [ ] 3.1 Implement manufacturer, category, model, and location management with activation/deactivation; verify required relationships, unique model constraints, and inactive-reference rejection.
- [ ] 3.2 Implement equipment list, create/edit, detail, move, status-change, and decommission workflows; verify required and optional fields, server-side validation, derived category/manufacturer, uniqueness, and history retention.
- [ ] 3.3 Implement the component catalog and equipment-component assignment/removal workflows; verify the N:N relationship, positive quantity rule, repeat component slots, and retained installation/removal history.

## 4. Maintenance and occurrences

- [ ] 4.1 Implement preventive scheduling, recurrence metadata, assignment, due/overdue views, and maintenance state transitions; verify completion/cancellation requirements and exclusion of completed/canceled work from due lists.
- [ ] 4.2 Implement corrective maintenance and occurrence reporting, assignment, resolution, cancellation, and linkage; verify required technical description, severity, reporter, resolution details, and occurrence-to-maintenance relationship.
- [ ] 4.3 Implement the chronological equipment history and derived last/next maintenance dates; verify completed and canceled records remain visible and dates are calculated from source maintenance records rather than stored copies.

## 5. Dashboard and reports

- [ ] 5.1 Implement the authenticated operational dashboard with status/category totals, location filtering, due/overdue preventive work, open occurrences, and recent service activity; verify totals against fixture records for each filter.
- [ ] 5.2 Implement filtered inventory, maintenance, and occurrence reports with CSV export; verify exported rows match on-screen filters, permissions, and allowed non-clinical columns.

## 6. Quality, accessibility, and release readiness

- [ ] 6.1 Implement the screens and navigation specified in `design.md`; verify primary workflows are usable on desktop and tablet and forms have accessible labels, logical keyboard focus, and visible validation errors.
- [ ] 6.2 Measure standard filtered inventory-list response time with 10,000 equipment records under nominal load; verify p95 is at or below 2 seconds and record the test setup and result.
- [ ] 6.3 Run cross-capability integration tests for referential integrity, role enforcement, audit coverage, maintenance/history calculations, and the absence of patient/clinical fields or workflows; verify all scenarios in the capability specs pass.
- [ ] 6.4 Document production hosting, backup/retention, recovery objectives, deployment, and rollback procedures; verify a recovery and rollback rehearsal preserves existing users, equipment, and service history.

## 7. Review decisions and added scope

- [ ] 7.1 Implement role creation, permission grant/revoke, and activation/deactivation; verify the `administrator` role and roles held by enabled users cannot be deactivated, `users.manage` cannot be revoked from `administrator`, and every change is audited.
- [ ] 7.2 Implement temporary passwords on account creation and the first-login change (`auth/change_password`); verify the account holds no permissions until the change, the change requires the current password and the password policy, and administrators cannot set or reset an existing user's password by any means.
- [ ] 7.3 Implement email-only password recovery through the shared email function and `reset/confirm`; verify links are single use, hashed, expire after 60 minutes, create no session, return identical responses for unknown, disabled, and invalid cases, and that recovery fails closed until `HHM_APP_URL`, `RESEND_API_KEY`, and `HHM_EMAIL_FROM` are configured.
- [ ] 7.4 Implement the audit credential cleanup (`setup/scrub_audit_credentials`); verify no audit event contains a password hash or reset token afterwards and no event was deleted.
- [ ] 7.5 Enforce the confirmed equipment rules; verify a reason is required for `out_of_service` and `decommissioned` on every path, decommissioning is final, and equipment status changes made while starting or completing maintenance require `inventory.manage`.
- [ ] 7.6 Implement preventive-only due work, recurrence as a suggestion, the assignee permission rule, and corrective maintenance pre-filled from an occurrence; verify the overdue definition matches across list, dashboard, and report, completion creates no new record, unqualified assignees are rejected, and the occurrence link is set automatically.
- [ ] 7.7 Implement the frontend behaviors: no-access page and guards, catalog editing, oldest-first history, and display in the institution timezone; verify guards never loop, inactive references are not cleared on edit, and planned dates are not timezone-shifted.
- [ ] 7.8 Implement the single post-push setup step (`setup/run_deployment_setup`: seed, migration, audit cleanup) and the maintenance-window procedure in `docs/operations.md`; verify it is idempotent, refuses divergent role grants, and leaves no account without a role.
