# Operations: hosting, deployment, backup, recovery, rollback

Runbook for one institution's deployment of the equipment-management application
(Reflex frontend + Xano API/database). One deployment = one institution's data.

## 1. Decisions still open (owner: project lead)

These are deployment decisions from `design.md` → Open Questions. Recommended values are proposals,
not commitments; record the agreed value and date here before production.

| Decision | Recommendation | Agreed value |
|---|---|---|
| Xano plan | A paid plan with a non-live branch, sandbox/tenant environments, and managed backups. The Free plan used during development has no sandbox, so every test touches live data (see `openspec/changes/hospital-hardware-manager/validation.md`). | _TBD_ |
| Frontend hosting | Reflex Cloud, or any container host running `reflex run --env prod` behind HTTPS, in the same region as the Xano instance. | _TBD_ |
| Recovery point objective (RPO) | ≤ 24 h (daily backups); ≤ 1 h if the plan offers point-in-time recovery. | _TBD_ |
| Recovery time objective (RTO) | ≤ 4 h during business hours. | _TBD_ |
| Backup retention | Daily backups kept 30 days, plus monthly backups kept 12 months. | _TBD_ |
| Audit log retention | Same as the equipment records (never purged by the application). | _TBD_ |
| Email provider for password reset | Decided: an external email service. XanoScript's `util.send_email` supports only `resend` besides the owner-only `xano` provider, so the code uses Resend: create the account, verify the sender domain, and set the variables in section 2. A plain SMTP server would need a relay in front of it. | Resend (2026-10-08) |

## 2. Environments and configuration

| Setting | Where | Purpose |
|---|---|---|
| `HHM_APP_URL` | Xano environment variable | Production URL of the frontend, used in password-reset links (`/reset-password` page). |
| `RESEND_API_KEY` | Xano environment variable (secret) | Email service API key for reset and welcome emails. |
| `HHM_EMAIL_FROM` | Xano environment variable | Sender address on a domain verified in the email service. |

Password recovery fails closed: until these three are set, `reset/request-reset-link` returns an error for
every request (it never reveals whether an email exists) and no email is sent.
| `XANO_BASE_URL` | Frontend environment | Xano instance URL. |
| `XANO_*_GROUP` | Frontend environment (optional) | API group canonicals; defaults match `xano/api/*/api_group.xs`. |
| `HHM_TIMEZONE` | Frontend environment | Institution timezone for entered/displayed times (default `America/Sao_Paulo`). |

The frontend holds the Xano auth token only in backend (server) state; nothing secret is sent to the
browser. Serve the frontend over HTTPS only; Xano endpoints are HTTPS by default.

**Session state and scaling.** Reflex keeps that state in the app process's memory by default. With a
single process, a restart only logs everyone out. To run more than one process or worker (or to survive
restarts), configure Redis for Reflex state (`REFLEX_REDIS_URL`, i.e. `redis_url` in `rxconfig.py`);
otherwise users are logged out whenever a request reaches a different process.

## 3. First deployment

**Maintenance window.** Between the push (step 4) and the setup command (step 6), every existing
account is locked out: login and all permission checks require `ativo = true` and a role, which only the
migration assigns. Announce a short window and run steps 4–6 back to back.

1. **Announce** the maintenance window to current users.
2. **Snapshot.** Take a backup/export of the Xano workspace (dashboard backup, or `xano workspace pull` into a dated folder outside the repo) and record its identifier.
3. **Dry run.** From `xano/`: `xano workspace push -d . --dry-run`. Confirm the preview only creates the domain tables, functions, and API groups, and updates the auth endpoints, `user`, and `event_log`. It must show no deletes.
4. **Push.** Run `xano workspace push -d .`. The push is additive and wrapped in a transaction by default; do not use `--no-transaction`, `--truncate`, `--sync --delete`, or `--records`.
5. **Set `HHM_APP_URL`, `RESEND_API_KEY` and `HHM_EMAIL_FROM`** in the Xano environment.
6. **Seed and migrate, immediately:** `xano function run "setup/run_deployment_setup"`. It seeds reference data (expect `categorias: 12, roles: 4, permissions: 10, role_permissions: 21, divergencias: []`), refuses to continue if the role grants differ from the approved matrix, then migrates accounts: every former `admin` becomes `administrator`, every other account becomes `viewer` with `needs_review: true`. Confirm `without_role: 0`. Finally it blanks the password hash and hashed reset token that the old quick-start endpoints wrote into audit events (events are kept, see `scrub.eventos_corrigidos`).
7. **Review accounts:** an administrator reviews and reassigns the `needs_review` accounts in **Usuários e perfis** before go-live.
   Accounts that existed before this release keep their passwords. New accounts are created with a temporary
   password, delivered to the user over a separate secure channel, and must be changed on first login.
   Administrators cannot reset existing passwords; users who forget theirs use **Esqueci minha senha**.
8. **Verify:** run `pytest tests/test_no_clinical_data.py`. Against a test deployment (not production), also run `pytest tests/test_api_integration.py` and `python tests/perf/inventory_list_p95.py`, and record the results in `validation.md`.
9. **Deploy the frontend:** `pip install -r requirements.txt`, then `reflex run --env prod` (or the host's equivalent), with the environment from section 2.
10. **Smoke test** with one account per role: login, dashboard, equipment list, a denied action as viewer; create one new account and confirm the first login forces a password change. End the maintenance window.

The legacy quick-start function `Quick Start/enforce_role` was removed from the local sources; an additive
push does not delete it from the workspace, so delete it in the Xano dashboard (nothing calls it).

## 4. Routine releases

1. Back up (section 3, step 2).
2. Run `xano workspace push --dry-run` and review it. Any `DELETE` or field type change needs explicit approval and a forward-repair plan.
3. Push the backend first, then deploy the frontend (the API stays backward compatible within a release).
4. Run the smoke test; check `reflex.log` and Xano request history for errors.

## 5. Backup

- Managed backups per the plan chosen in section 1, on the agreed schedule and retention.
- After each release, and at least monthly, pull a logical export of the workspace definitions (`xano workspace pull`) into versioned storage outside the application host.
- Backups contain operational equipment data, user names/emails, and audit history. Store them encrypted, with administrator-only access.

## 6. Recovery (data loss or corruption)

1. Disable user access: set the API groups `Inventory`, `Maintenance`, `Reports`, `Users` to `active = false`, or stop the frontend.
2. Identify the last good backup within the RPO.
3. Restore it into a **non-live** environment first (tenant/branch, per plan) and verify record counts for `user`, `equipamentos`, `manutencoes`, `ocorrencias`, `event_log`, and a sample equipment history.
4. Promote/restore to live, re-enable access, and record the incident, data-loss window, and timings against the RPO/RTO.

## 7. Rollback (bad release)

Rollback never drops tables or deletes records.

1. Disable the new routes/endpoints (API groups `active = false`, or redeploy the previous frontend).
2. Restore the previous function/endpoint definitions from the pre-release snapshot (`xano workspace pull` folder or dashboard backup).
3. If records were created under the new schema, keep them and apply a **forward-repair** change instead of restoring a data snapshot over them.
4. Re-enable access and re-run the smoke test.

## 8. Recovery and rollback rehearsal (required before production)

Run in a non-live environment with production-like data and record the result:

| Step | Check | Result |
|---|---|---|
| Restore the latest backup | Counts of users, equipment, maintenance, occurrences, and audit events equal the source | _pending_ |
| Equipment history | 3 sampled equipment show identical history and last/next maintenance dates | _pending_ |
| Logins | One account per role can log in; a disabled account cannot | _pending_ |
| Rollback | After deploying a test change and rolling back, all of the above still hold and no rows were lost | _pending_ |
| Timing | Restore time measured against the RTO | _pending_ |
