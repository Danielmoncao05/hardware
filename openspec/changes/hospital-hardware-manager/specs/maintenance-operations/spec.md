# Spec Delta

## Purpose

Enable maintenance teams to plan and document preventive and corrective service, report operational occurrences, and retrieve a trustworthy equipment service history.

## ADDED Requirements

### Requirement: Schedule preventive maintenance
The system SHALL allow authorized users to schedule preventive maintenance for equipment with a planned date, maintenance description or checklist, and responsible user. A schedule MAY include a recurrence interval; when recurring work is completed, the system SHALL suggest the next planned date (planned date plus the interval) and SHALL NOT schedule it automatically. The responsible user SHALL be an enabled user whose role can work on maintenance. The system SHALL identify upcoming and overdue preventive work using the planned date and current maintenance status; due work (upcoming and overdue) SHALL mean planned preventive maintenance only, with the same definition in maintenance lists, the dashboard, and reports. The next-maintenance date shown for equipment SHALL be derived from its earliest future planned preventive maintenance and SHALL NOT be stored as an independently editable copy.

#### Scenario: Schedule preventive maintenance
- **WHEN** an authorized user schedules preventive maintenance with a valid equipment item, planned date, and responsible user
- **THEN** the system SHALL create a planned maintenance record linked to that equipment and expose it in the maintenance calendar and due-work views

#### Scenario: Identify upcoming and overdue work
- **WHEN** a user views maintenance due dates
- **THEN** the system SHALL distinguish upcoming work from overdue planned work using the planned date and exclude completed or canceled records

#### Scenario: Due work excludes corrective maintenance
- **WHEN** planned corrective and planned preventive maintenance are both dated before today
- **THEN** only the preventive record SHALL appear as overdue, identically in the maintenance list, the dashboard, and the overdue report

#### Scenario: Recurrence suggests without scheduling
- **WHEN** an authorized user completes preventive maintenance that has a recurrence interval
- **THEN** the system SHALL return the suggested next planned date and SHALL NOT create a new maintenance record

#### Scenario: Reject an assignee who cannot work on the area
- **WHEN** a user assigns maintenance or an occurrence to a user whose role cannot work on that area
- **THEN** the system SHALL reject the assignment and keep the current responsible user

### Requirement: Record corrective and preventive maintenance
The system SHALL allow authorized users to track maintenance through `planned`, `in_progress`, `completed`, and `canceled` states, with a maintenance type of `preventive` or `corrective`. A maintenance record SHALL reference one equipment item and SHALL retain its planned date, actual start/completion dates, work performed, outcome, responsible user, and optional occurrence relationship as applicable. Completing maintenance SHALL require a completion date and work summary; canceling SHALL require a cancellation reason. Completed and canceled maintenance records SHALL remain in history. Corrective maintenance MAY reference the occurrence that prompted the work. Users limited to assigned work SHALL change only maintenance assigned to them.

#### Scenario: Complete maintenance with service details
- **WHEN** an authorized user completes a maintenance record and supplies a completion date and work summary
- **THEN** the system SHALL retain the completion details in the equipment history and update the equipment's derived last-maintenance date

#### Scenario: Reject incomplete completion or cancellation
- **WHEN** a user attempts to complete maintenance without a completion date or work summary, or cancel it without a reason
- **THEN** the system SHALL reject the transition and preserve the current maintenance state

#### Scenario: Maintain history after cancellation
- **WHEN** a user cancels planned maintenance with a reason
- **THEN** the system SHALL retain the canceled record and reason and SHALL exclude the record from future due-work calculations

### Requirement: Register and resolve equipment occurrences
The system SHALL allow authorized users to create an occurrence linked to one equipment item with a reported date, technical description, and severity. A reporter SHALL be recorded, and assignment to a responsible user, resolution date, resolution summary, and related maintenance MAY be recorded. Occurrence states SHALL include `open`, `in_progress`, `resolved`, and `canceled`. Resolution SHALL require a resolution date and summary; cancellation SHALL require a reason. Occurrences SHALL remain available in the equipment history after resolution or cancellation. A responsible user SHALL be an enabled user whose role can work on occurrences. From an open or in-progress occurrence, an authorized user SHALL be able to open a corrective maintenance form pre-filled with the corrective type and the occurrence's equipment, with the occurrence linked automatically.

#### Scenario: Report equipment occurrence
- **WHEN** an authorized user reports an issue with valid equipment, date, technical description, and severity
- **THEN** the system SHALL create an open occurrence associated with the equipment and reporting user

#### Scenario: Resolve occurrence with outcome
- **WHEN** an authorized user resolves an occurrence and records the resolution date and summary
- **THEN** the system SHALL retain the resolution details and show the occurrence as resolved in the equipment history

#### Scenario: Reject incomplete resolution
- **WHEN** a user attempts to resolve an occurrence without a resolution date or summary
- **THEN** the system SHALL reject the state change and keep the occurrence open or in progress

#### Scenario: Open corrective maintenance from an occurrence
- **WHEN** an authorized user chooses to open corrective maintenance from an open occurrence and saves the form
- **THEN** the system SHALL create corrective maintenance for the occurrence's equipment, linked to that occurrence, without the user entering the type, equipment, or occurrence

### Requirement: Provide complete equipment maintenance history
The system SHALL provide a chronological (oldest first) equipment history containing maintenance records, occurrences, and component installation/removal events, with dates, types, states, responsible users, and recorded summaries where applicable. The system SHALL derive the last-maintenance date from the most recent completed maintenance record and SHALL show no date when there is no completed maintenance. History SHALL remain available for decommissioned equipment and SHALL not be altered by deleting a catalog entry or user. Maintenance that has not started SHALL be dated in the history by its planned calendar date.

#### Scenario: Review equipment history
- **WHEN** an authorized user opens the history for equipment
- **THEN** the system SHALL show its maintenance, occurrence, and component-change events in chronological order, including completed and canceled records

#### Scenario: Derive maintenance dates
- **WHEN** an authorized user views equipment with completed and planned maintenance
- **THEN** the system SHALL show the latest completed date as last maintenance and the earliest future planned preventive date as next maintenance
