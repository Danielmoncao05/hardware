# Proposal

## Why

Hospitals, clinics, and maintenance teams need a shared operational record of medical equipment, its technical configuration and location, current status, service history, and reported issues. This change defines a focused equipment-management application so teams can coordinate asset lifecycle and maintenance without turning the system into a clinical record or diagnostic product.

## What Changes

- Define an equipment inventory covering manufacturers, categories, models, equipment, hardware components, equipment-component assignments, locations, and equipment status.
- Define preventive and corrective maintenance, occurrences, and an auditable maintenance history linked to equipment and responsible users.
- Define user roles and permissions, operational dashboards, and reports for equipment and maintenance.
- Specify a normalized relational data model, validation and referential-integrity rules, primary user flows, and the application structure.
- Explicitly exclude medical diagnosis, patient records, and patient clinical information.

## Capabilities

### New Capabilities

- `equipment-inventory`: Manage equipment, manufacturers, categories, models, hardware components, component assignments, locations, and operational status.
- `maintenance-operations`: Schedule and record preventive and corrective maintenance, capture equipment occurrences, and consult service history.
- `access-and-reporting`: Manage user access and permissions and provide operational dashboards and reports.

### Modified Capabilities

None.

## Impact

- Adds requirements and architecture for the existing Reflex application scaffold in `hardware/`.
- Defines the intended Xano-backed API and relational persistence; current Xano exports include starter user and event-log tables, authentication endpoints, and role-related examples, but do not yet contain the requested equipment domain.
- Introduces no implementation code or dependency changes in this proposal phase.
- Requires keeping equipment data separate from patient and clinical data throughout the UI, API, persistence, and reporting surfaces.
