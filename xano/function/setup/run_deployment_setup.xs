// Single post-push setup step: seeds reference data, migrates existing accounts, then blanks credential
// material that the old quick-start endpoints wrote into audit events (setup/scrub_audit_credentials).
// After the schema push, login and every permission check require ativo = true and a role, which existing
// accounts only receive from the migration. Running seed and migration in one call keeps that lockout window to the
// time between the push and this command (see docs/operations.md, First deployment).
// Idempotent: each step only changes what is still missing.
function "setup/run_deployment_setup" {
  input {
  }

  stack {
    function.run "setup/seed_reference_data" as $seed

    precondition (($seed.divergencias|count) == 0) {
      error_type = "inputerror"
      error = "Role grants differ from the approved matrix; review seed output before migrating users."
    }

    function.run "setup/migrate_users" as $migration

    // Blank credential material that the old quick-start endpoints logged (events are kept)
    function.run "setup/scrub_audit_credentials" as $scrub
  }

  response = {seed: $seed, migration: $migration, scrub: $scrub}
  guid = "Z3G34T-NJuLX5EFkVNRH_k_Jb80"
}
