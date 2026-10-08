# Xano Constraint Validation (task 1.1)

## Setup

- **Date:** 2026-10-08
- **Target:** workspace 149197 ("Matheus's Workspace"), branch `v1` (live), instance `x8ki-letl-twmt.n7.xano.io`, Xano CLI 1.3.3.
- **Why live:** the sandbox and tenant environments are not available on the Free plan (`Access Denied. Not supported with Free plan`). Branches do not isolate tables.
- **Method:** pushed the temporary objects `zz_probe_parent`, `zz_probe_child` (tables) and `zz_probe/run_checks` (function), all tagged `zz_probe`, and ran `xano function run "zz_probe/run_checks"`. Each case runs `db.add`/`db.edit`/`db.del` inside `try_catch` and records whether the datastore accepted or rejected it. The final table rows were read back to confirm what was stored.
- **Cleanup:** delete the three `zz_probe*` objects in the Xano dashboard. They are not part of the domain schema.

## Results

| # | Constraint used by the domain schema | Probe case | Observed | Verdict |
|---|---|---|---|---|
| 1 | FK rejects a nonexistent reference (`table = "x"` field) | insert child with `parent_id = 999999999` | accepted, row stored | **Not enforced by the datastore** |
| 2 | FK restricts deleting a referenced row | delete a parent that has a child | accepted, child left dangling | **Not enforced by the datastore** |
| 3 | Unique single column (`btree|unique`): `numero_patrimonio`, `fabricantes.nome`, `usuarios.email`, ... | duplicate asset number; duplicate parent name | rejected | Enforced |
| 4 | Unique only when filled in (`numero_serie`) | duplicate `"S-1"` | rejected | Enforced |
| 5 | Multiple missing serials allowed | two rows with `numero_serie = null` | both accepted | Enforced (NULLs are distinct) |
| 6 | Empty-string serial treated as missing | two rows with `numero_serie = ""` | second rejected | **Only works for `null`**: `""` is a real value |
| 7 | Composite unique (`modelos` (`fabricante_id`, `categoria_id`, `nome`); `role_permissions` (`role_id`, `permission_id`)) | duplicate (`parent_id`, `chave_a`, `chave_b`) | rejected | Enforced |
| 8 | Positive quantity (`filters=min:1`) on insert | `quantidade` 0 and -3 | rejected | Enforced |
| 9 | Positive quantity on update | `db.edit` to `quantidade = 0` | rejected | Enforced |
| 10 | Non-negative value (`filters=min:0` on nullable decimal) | `valor = -1` | rejected | Enforced |
| 11 | Enum domain (status, type, severity) | `status = "bogus"` | rejected | Enforced |
| 12 | Required column given `null` | `numero_patrimonio = null` | rejected | Enforced |
| 13 | Required column omitted | insert without `numero_patrimonio` | accepted, stored as `""` | **Not enforced**: omitted text defaults to empty string |
| 14 | Transactions roll back (`db.transaction`) | insert then `throw` inside a transaction | 0 rows left | Enforced |
| 15 | Composite primary key (`role_permissions`) | not probed | Xano requires an `int id` (or `uuid`) primary key on every table ([tables reference](https://cdn.jsdelivr.net/npm/@xano/developer-mcp/dist/xanoscript_docs/tables.md)) | **Not supported** |
| 16 | B-tree indexes on FK, date, and status columns | `btree` index on `parent_id` | created by the push | Supported |

`$error` was `null` inside `catch` for every rejected case, so the API cannot rely on the datastore's error text. Endpoints must check uniqueness and validity themselves to return field-specific messages, and treat the database constraint as a safety net.

## Consequences for the design

1. **Foreign keys (#1, #2):** every write that sets a reference must check that the target row exists and, where required, is active, inside the same `db.transaction`. Physical deletes of referenced rows must be blocked in the API. The existing rule "deactivate, don't delete" covers catalogs and users.
2. **Optional unique serial (#6):** the API normalizes an empty or blank `numero_serie` to `null` before writing.
3. **Required text (#13):** the API rejects missing or blank required text fields. The datastore stores `""` instead.
4. **`role_permissions` (#15):** use a surrogate `id` primary key plus a unique index on (`role_id`, `permission_id`). Uniqueness of the grant is still enforced by the datastore (#7).
5. Unique, composite unique, `min:` filters, enums, null-on-required, and transactions are enforced by the datastore and can be used as designed.
