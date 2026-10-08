# Spec Delta

## Purpose

Define the technical inventory and lifecycle records used to identify, locate, configure, and track hospital equipment without handling patient or clinical records.

## ADDED Requirements

### Requirement: Manage equipment reference catalogs
The system SHALL allow authorized users to create, view, update, and deactivate manufacturers, categories, and models. Each model SHALL reference exactly one manufacturer and one category; a manufacturer and category MAY each be referenced by multiple models. Categories SHALL support the supplied set: monitor multiparamétrico, ventilador pulmonar, bomba de infusão, desfibrilador, eletrocardiógrafo, máquina de anestesia, ultrassom, raio-X, tomógrafo, ressonância magnética, oxímetro, and aspirador hospitalar. Deactivation SHALL preserve historical references and prevent new assignments.

#### Scenario: Register model with its manufacturer and category
- **WHEN** an authorized user saves a model with a name, manufacturer, and category that exist
- **THEN** the system SHALL persist the model with both foreign-key relationships and make it available for equipment registration

#### Scenario: Reject missing or inactive model references
- **WHEN** a user attempts to save a model without a manufacturer or category, or using an inactive reference
- **THEN** the system SHALL reject the change and identify the invalid required relationship

### Requirement: Register and maintain equipment records
The system SHALL allow authorized users to register and update equipment with a name, unique asset number, manufacturer/model, location, and operational status. A model SHALL determine its manufacturer and category, and the system SHALL reject a conflicting separately supplied manufacturer or category. Serial number, manufacturing year, acquisition date, acquisition value, estimated useful life, and observations MAY be absent. When supplied, a serial number SHALL be unique among equipment records, manufacturing year SHALL be a valid calendar year, acquisition value SHALL be non-negative, and estimated useful life SHALL be positive. Acquisition date SHALL NOT be later than the current date. Equipment SHALL NOT be registered as `decommissioned`, and registering it as `out_of_service` SHALL require a reason. Decommissioning SHALL retain the equipment record and its maintenance and occurrence history.

#### Scenario: Register equipment with valid required fields
- **WHEN** an authorized user submits an equipment name, unused asset number, model, location, and allowed status
- **THEN** the system SHALL save the equipment and expose its derived category and manufacturer from the selected model

#### Scenario: Reject a duplicate asset number or serial number
- **WHEN** a user submits an asset number already in use, or a non-empty serial number already assigned to another equipment record
- **THEN** the system SHALL reject the save without changing either equipment record

#### Scenario: Preserve equipment history during decommissioning
- **WHEN** an authorized user decommissions equipment with existing maintenance or occurrences
- **THEN** the system SHALL retain the equipment and its related history and exclude it from active-equipment views by default

### Requirement: Manage locations and operational equipment status
The system SHALL allow authorized users to maintain locations and SHALL allow each equipment record to reference one active location. The system SHALL provide the statuses `operational`, `under_maintenance`, `out_of_service`, and `decommissioned`; a status change SHALL be authorized, persisted, and included in the equipment's audit history. Changing equipment status SHALL require the inventory-management permission, including when the change is requested while starting or completing maintenance. A reason SHALL be required, and recorded in the audit history, whenever equipment becomes `out_of_service` or `decommissioned`, by any path. Decommissioning SHALL be final: decommissioned equipment SHALL NOT change status, move, be edited, or have components installed or removed, and SHALL remain readable with its full history. Inactive locations SHALL remain visible on historical records but SHALL NOT be selectable for new or moved equipment. Location filters SHALL match only the selected location, not its sub-locations.

#### Scenario: Move equipment to an active location
- **WHEN** an authorized user selects an active location for equipment
- **THEN** the system SHALL update the current location and retain the change in the audit history

#### Scenario: Prevent assigning an inactive location
- **WHEN** a user attempts to register or move equipment to an inactive location
- **THEN** the system SHALL reject the operation and preserve the existing location

#### Scenario: Set equipment under maintenance
- **WHEN** an authorized user records an active maintenance operation for equipment
- **THEN** the system SHALL allow the equipment status to be set to `under_maintenance` and SHALL show that status consistently in inventory and dashboards

#### Scenario: Require a reason for out of service or decommissioning
- **WHEN** a user registers equipment as `out_of_service`, changes its status to `out_of_service` or `decommissioned`, or completes maintenance leaving it `out_of_service`, without a reason
- **THEN** the system SHALL reject the operation and preserve the current status

#### Scenario: Decommissioning is final
- **WHEN** a user attempts to change the status of, move, edit, or change components of decommissioned equipment
- **THEN** the system SHALL reject the operation and keep the record and its history unchanged

#### Scenario: Status change through maintenance requires inventory permission
- **WHEN** a user without the inventory-management permission starts or completes maintenance and asks to change the equipment status
- **THEN** the system SHALL reject the whole request, leaving both the maintenance record and the equipment status unchanged

### Requirement: Catalog and assign hardware components
The system SHALL allow authorized users to catalog hardware components by name and type, with optional manufacturer, model, part or serial identifier, specifications, and notes. Supported component types SHALL include processor, memory RAM, storage, motherboard, power supply, sensors, displays, batteries, electronic modules, communication boards, and other components. An equipment record SHALL support zero or more component assignments, and a component catalog record SHALL be assignable to zero or more equipment records. Each assignment SHALL identify its equipment and component and MAY record a slot or sequence, quantity, installation date, removal date, and notes. Historical assignments SHALL remain queryable after removal.

#### Scenario: Assign and remove components
- **WHEN** an authorized user assigns a catalog component to equipment and later records its removal
- **THEN** the system SHALL preserve the equipment-component relationship and installation/removal details in the equipment's technical history

#### Scenario: Reject invalid component assignment
- **WHEN** a user attempts an assignment with a missing equipment or component, or a non-positive quantity
- **THEN** the system SHALL reject it and SHALL NOT create a dangling relationship

### Requirement: Keep inventory data technical and non-clinical
The system SHALL collect and display technical and operational equipment information only. It SHALL NOT provide medical diagnosis, patient charts, patient identifiers, clinical observations, or patient-related fields in equipment, component, location, maintenance, occurrence, dashboard, or report workflows. User-entered occurrence descriptions SHALL be framed as equipment symptoms or operational observations and SHALL not be used to make clinical decisions.

#### Scenario: Record a technical equipment observation
- **WHEN** a user records a malfunction description using equipment and maintenance fields
- **THEN** the system SHALL associate the observation only with equipment operations and SHALL NOT create or infer a patient or diagnosis record

#### Scenario: Attempt to use an out-of-scope clinical workflow
- **WHEN** a user looks for patient records or diagnosis functionality
- **THEN** the system SHALL provide no such workflow, entity, or report in the equipment-management system
