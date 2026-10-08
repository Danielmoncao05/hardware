# Design

## Context

See `proposal.md` for motivation and the three capability specs for observable behavior and acceptance scenarios. The repository currently contains a Reflex starter screen and Xano quick-start exports for users, authentication, role checks, and an event log; it has no equipment-domain implementation. The selected scope is one deployment per institution, using Reflex for the application and Xano for authenticated APIs and relational persistence.

## Goals / Non-Goals

**Goals:**

- Establish a normalized relational model for equipment, catalogs, component assignments, locations, maintenance, occurrences, users, permissions, and audit events.
- Keep business rules and authorization enforced at the API/data boundary, not only in the UI.
- Provide an implementable path from the existing starter without changing the selected platform.
- Keep operational equipment data distinct from patient and clinical information.

**Non-Goals:**

- Multi-tenant data partitioning within one deployment; each institution receives a separate deployment.
- Clinical workflows, patient records, medical diagnosis, telemetry collection, or device control.
- Integrations with hospital information systems, procurement, finance, or external maintenance vendors in this initial scope.
- Hard deletion of records that have operational history.

## Decisions

### Application architecture

- **Frontend:** Use the existing Reflex Python application for authenticated screens, navigation, forms, filters, and dashboard/report presentation.
- **API and persistence:** Use Xano endpoint groups as the API boundary and Xano's relational data store for the application tables. Keep authoritative validation, relationship checks, role checks, and state transitions in API operations. The frontend SHALL call those operations rather than directly manipulating persistence.
- **Authentication:** Extend the existing Xano authentication model. Disable public signup for production use; administrators provision and disable accounts. Keep credentials in the authentication mechanism, never in general application tables or client-visible state.
- **Alternatives considered:** A separate custom API and relational database could provide portability, but it would duplicate the Xano starter already present. A browser-to-database design would expose credentials and weaken centralized authorization, so it is not selected.

### Relational schema and keys

Tables use a generated, immutable `id` primary key. Xano requires this key on every table, so `role_permissions` also has an `id` key, and its (`role_id`, `permission_id`) pair is protected by a unique index instead of a composite primary key (see `validation.md`). The `equipamento_componentes` associative table uses its own generated `id` so the same component catalog entry can have multiple installed instances on one equipment item. Foreign keys use restrictive deletion semantics for records with history; reference data is deactivated instead of physically deleted. Required columns are non-null. Optional columns are nullable. Timestamps are stored consistently in UTC and presented in the institution's timezone (`HHM_TIMEZONE`), the same zone used to interpret times entered in forms.

| Table | Primary key | Required fields | Optional fields and relationships |
|---|---|---|---|
| `fabricantes` | `id` | `nome` (unique) | `site`, `contato_suporte`, `observacoes`, `ativo`, timestamps |
| `categorias` | `id` | `nome` (unique) | `descricao`, `ativo`, timestamps. Seed the 12 categories specified in `equipment-inventory/spec.md`. |
| `modelos` | `id` | `nome`, `fabricante_id` FK, `categoria_id` FK | `codigo`, `observacoes`, `ativo`, timestamps. Unique (`fabricante_id`, `categoria_id`, `nome`). |
| `localizacoes` | `id` | `nome` | `parent_id` self-FK nullable for a location hierarchy, `tipo`, `descricao`, `ativo`, timestamps. |
| `equipamentos` | `id` | `nome`, `numero_patrimonio` (unique), `modelo_id` FK, `localizacao_id` FK, `status` | `numero_serie` (unique when present), `ano_fabricacao`, `data_aquisicao`, `valor_aquisicao`, `vida_util_anos`, `observacoes`, `criado_por` FK, timestamps. Manufacturer and category are derived through `modelos`, not duplicated. |
| `componentes` | `id` | `nome`, `tipo` | `fabricante_id` nullable FK, `modelo_componente`, `numero_peca`, `especificacoes`, `observacoes`, `ativo`, timestamps. `tipo` is constrained to processor, memory RAM, storage, motherboard, power supply, sensors, displays, batteries, electronic modules, communication boards, and other. |
| `equipamento_componentes` | `id` | `equipamento_id` FK, `componente_id` FK, `quantidade` (> 0) | `slot`, `numero_serie_instalado`, `instalado_em`, `removido_em`, `observacoes`, timestamps. A surrogate key permits several instances of the same catalog component on one equipment item. |
| `ocorrencias` | `id` | `equipamento_id` FK, `relatada_em`, `descricao_tecnica`, `severidade`, `status`, `relatada_por` FK | `responsavel_id` FK, `resolvida_em`, `resumo_resolucao`, `motivo_cancelamento`, timestamps. |
| `manutencoes` | `id` | `equipamento_id` FK, `tipo`, `data_planejada`, `descricao`, `status`, `responsavel_id` FK, `criado_por` FK | `iniciada_em`, `concluida_em`, `resumo_execucao`, `checklist`, `motivo_cancelamento`, `intervalo_recorrencia_dias`, `ocorrencia_id` FK, timestamps. |
| `user` (existing Xano auth table, extended) | `id` | `name`, `email` (unique), `role_id` FK, `ativo` | Authentication-managed credential fields and timestamps; the legacy `role` enum is kept only for migration. Retain disabled accounts referenced by historical records. |
| `roles` | `id` | `nome` (unique) | `descricao`, `ativo`, timestamps. Seed `administrator`, `asset_manager`, `technician`, `viewer`. |
| `permissions` | `id` | `chave` (unique), `descricao` | Timestamps. Permissions correspond to the protected read, create, update, deactivate, maintenance, occurrence, report, audit, and user-administration operations. |
| `role_permissions` | `id`; unique (`role_id`, `permission_id`), both FKs | Both keys | Timestamps. The unique index prevents duplicate role-permission grants. |
| `event_log` | `id` | `action`, `created_at` | `user_id` FK, `metadata` for structured before/after details and affected-record identifiers. Extend the existing Xano event-log table for audit use; restrict editing to trusted server operations. `action` is required by every writer (`hhm/audit` and the quick-start `log_event` both take it as a required input); the column itself stays nullable because the existing quick-start table already holds rows and a stricter column would put the additive schema push at risk (`validation.md` #13 shows omitted text would otherwise be stored as `""`). |

**Relationships and referential integrity**

- `fabricantes` 1:N `modelos`; `categorias` 1:N `modelos`; `modelos` 1:N `equipamentos`.
- `localizacoes` 1:N `equipamentos`; `localizacoes` 1:N child locations through nullable `parent_id`.
- `equipamentos` N:N `componentes` through `equipamento_componentes`; each assignment has its own key and installation/removal history.
- `equipamentos` 1:N `manutencoes` and 1:N `ocorrencias`; one occurrence MAY be referenced by multiple corrective maintenance records.
- `user` 1:N created, reported, assigned, and audited records. `roles` N:N `permissions` through `role_permissions`, and `roles` 1:N `user`.
- Model, location, component, user, and role foreign keys SHALL be validated by the API. Xano's datastore does not enforce references: it accepts nonexistent IDs and allows deleting referenced rows (`validation.md` #1, #2). Every write that sets a reference therefore checks that the target exists and, where required, is active, within the same `db.transaction`, and the API blocks physical deletion of referenced rows. Unique indexes, composite unique indexes, `min:` filters, enums, and non-null checks are enforced by the datastore. The API still checks them first to return field-specific errors, because the datastore's rejection carries no error detail.
- The API normalizes blank optional unique values (such as `numero_serie`) to `null` before writing, and rejects missing or blank required text, which the datastore would otherwise store as `""` (`validation.md` #6, #13). Do not cascade-delete equipment or history. Deactivate catalog records; disable users. Reject deleting referenced rows, except where a record has no references and deletion is explicitly permitted by an administrator.

### Domain and lifecycle rules

- `equipamentos.status`: `operational`, `under_maintenance`, `out_of_service`, `decommissioned`. Decommissioned equipment is retained and omitted from active lists by default.
- `manutencoes.tipo`: `preventive` or `corrective`; status: `planned`, `in_progress`, `completed`, `canceled`. Completion requires a completion date and work summary; cancellation requires a reason. Preventive planned work has a planned date and responsible user.
- `ocorrencias.severidade`: `low`, `medium`, `high`, `critical`; status: `open`, `in_progress`, `resolved`, `canceled`. Resolution requires a date and summary; cancellation requires a reason.
- Model category and manufacturer are authoritative; clients do not independently persist a conflicting category or manufacturer on equipment.
- Asset number is mandatory and unique. Serial number is optional and unique when supplied. Value is non-negative; useful life is positive; manufacturing year is valid; acquisition date cannot be in the future.
- Component assignment quantity is positive. Installation/removal timestamps are preserved; removal is recorded rather than deleting the assignment.
- Last maintenance is a read-time derived value: the latest completion date among completed maintenance. Next maintenance is derived as the earliest future planned preventive date. These values are never independently edited on an equipment row.
- Changing equipment status, location, role, maintenance state, or occurrence state is an authorized state transition that adds an audit event. Store core domain facts in relational columns; reserve `event_log.metadata` for audit details, not as a substitute for domain tables.
- One deployment contains data for one institution. Do not add a tenant key unless the deployment model changes through a separately specified change.
- Confirmed rules (review decisions, 2026-10-08):
  - A reason is required whenever equipment becomes `out_of_service` or `decommissioned`, through any path (registration, the status action, or completing maintenance), and it is recorded in the audit event.
  - Decommissioning is final: decommissioned equipment cannot change status, move, be edited, or have components installed or removed. It remains readable with its full history.
  - A preventive recurrence interval only suggests the next planned date when the work is completed; it never schedules maintenance automatically.
  - Location filters (lists, dashboard, reports) match the selected location only, not its sub-locations.
- Due work ("upcoming"/"overdue") means planned preventive maintenance, identically in the dashboard, maintenance lists, and reports.
- Equipment history is shown oldest first (chronological order).
- Timestamps are entered and displayed in one institution timezone (`HHM_TIMEZONE`), independent of the browser's zone. Calendar dates (planned dates, acquisition date) are never timezone-converted.

### Authorization and privacy

Use RBAC with least privilege and enforce permissions server-side for every API operation. The initial role matrix is:

| Operation | Administrator | Asset manager | Technician | Viewer |
|---|---:|---:|---:|---:|
| Read equipment, catalogs, locations, maintenance, occurrences | Yes | Yes | Yes | Yes |
| Manage equipment and catalogs | Yes | Yes | No | No |
| Create/update maintenance and occurrences | Yes | Yes | Assigned/relevant work | No |
| Manage users, roles, and permissions | Yes | No | No | No |
| Read dashboard and operational reports | Yes | Yes | Yes | Yes |
| Read audit log | Yes | No | No | No |

The matrix is a starting role policy; permissions SHALL be represented as explicit grants so they can be refined without embedding role-name checks throughout the application. Existing `admin` users map to `administrator`. Existing `member` users map initially to `viewer` (least privilege) and administrators review/reassign them before operational use. Disable public signup; do not automatically grant privileged access to existing accounts.

Do not add patient-related columns, screens, endpoints, analytics, or exports. Form copy and occurrence fields refer to technical equipment behavior only. Use encrypted transport, platform-supported password/session protection, server-side authorization, paginated queries, and audit access controls. The 2-second p95 list-view target and nominal-load scope are defined in `access-and-reporting/spec.md`.

- Equipment status changes require `inventory.manage`, including when requested while starting or completing maintenance; a technician without it can transition the maintenance record but not the equipment status.
- Responsible users for maintenance or occurrences must be enabled and hold the area's `manage` or `manage_assigned` permission.
- Password recovery uses single-use, hashed, 60-minute reset links sent through an external email service (Resend via `util.send_email`; configured with `RESEND_API_KEY`, `HHM_EMAIL_FROM`, `HHM_APP_URL`). A reset link never creates a session: `reset/confirm` verifies the token and sets the new password in one step, so the link can only change that account's password. The quick-start `reset/magic-link-login` (which returned a full session) and `reset/update_password` (which changed the password of any signed-in session without the current one) are disabled. Administrators provision accounts with a temporary password; the account is flagged `deve_trocar_senha` and holds no permissions until the user replaces that password on first login (`auth/change_password`, which requires the current password). Administrators cannot set or reset an existing user's password; a forgotten password is recovered only through the email reset flow, and completing it also clears a pending temporary password.
- Audit events written by the quick-start endpoints before this change contained the password hash and the hashed reset token. They are kept for historical integrity and only those two values are blanked (`setup/scrub_audit_credentials`); no audit event is deleted.

### Screens and navigation

1. **Login / account recovery:** authenticated entry; no public account creation.
2. **Dashboard:** status/category summary, upcoming and overdue maintenance, open occurrences, recent service activity; filter by location and relevant time range.
3. **Equipment list:** searchable, paginated inventory; filters for category, manufacturer/model, location, and status; actions gated by permissions.
4. **Equipment detail:** overview and derived maintenance dates, component assignments, occurrence list, and chronological history; edit/move/status actions when permitted.
5. **Equipment create/edit:** required asset identity, model, location, and status; optional serial/acquisition/useful-life/observations; model supplies manufacturer/category.
6. **Catalogs and locations:** manufacturers, categories, models, component catalog, and hierarchical locations with create, edit, and activate/deactivate actions.
7. **Maintenance:** calendar and list views for planned/upcoming/overdue work; create, assign, start, complete, or cancel forms with transition validation.
8. **Occurrences:** open/in-progress/resolved/canceled queues; report, assign, resolve, cancel, and open a corrective maintenance form pre-filled from the occurrence and linked to it automatically.
9. **Users and roles:** administrator-only user provisioning, enable/disable, and role/permission management.
10. **Reports and audit:** filtered inventory, status/location, due maintenance, maintenance history, occurrences, and administrator-only audit views; filtered operational reports may export CSV.

## Risks / Trade-offs

- [Existing Xano user roles (`admin`/`member`) do not match the new role set] → Migrate `admin` to `administrator`, default `member` to `viewer`, and require administrator review before launch.
- [The existing public signup endpoint could create unmanaged accounts] → Disable it for the production application and provision users through administrator-only operations.
- [Derived dates and dashboard counts can become expensive as histories grow] → Use indexed foreign keys and date/status columns, paginate lists, and optimize measured queries while preserving the relational source of truth.
- [Free-text occurrence notes could contain patient information despite the product boundary] → Keep fields explicitly technical, do not create patient fields, warn users in the UI, restrict exports, and define operational retention/access policy before production.
- [Changing roles or deactivating reference data can affect access and historical display] → Preserve referenced rows, use active flags, validate changes in the API, and retain audit events.
- [Xano's native relational capabilities and export schema need validation against every planned constraint] → Verify unique constraints, FK behavior, transactions, and index support in the target Xano workspace before implementation; report any unsupported invariant rather than silently weakening it.

## Migration Plan

1. Confirm Xano relational constraints and authentication behavior against the proposed schema before changing production data.
2. Create the reference catalogs, roles, permissions, and role grants; seed the 12 equipment categories and role definitions.
3. Extend the existing user and event-log schema; map existing `admin` to `administrator` and `member` to `viewer`, then require administrator review.
4. Create remaining domain tables and indexes, validate foreign keys and uniqueness, and keep new workflows unavailable until the schema is ready.
5. Deploy API validation and authorization, then the Reflex screens; verify role-denial cases and non-clinical data boundaries before enabling user access.
6. Rollback by disabling the new application routes and endpoints and restoring the previous deployment/schema snapshot. Do not drop tables or erase data during rollback; use a forward repair migration if records were created under the new schema.

## Open Questions

- Production hosting, backup retention, and recovery-time objectives remain deployment decisions; settle them before production rollout without changing the initial domain model.
