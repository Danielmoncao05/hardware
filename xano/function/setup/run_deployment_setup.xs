// Passo único de setup após o push: cria os dados de referência, migra as contas existentes e depois apaga o material de credenciais
// que os endpoints antigos do quick-start gravaram nos eventos de auditoria (setup/scrub_audit_credentials).
// Depois do push do schema, o login e toda verificação de permissão exigem ativo = true e um perfil, que as contas
// existentes só recebem pela migração. Rodar seed e migração numa chamada só limita esse bloqueio ao
// tempo entre o push e este comando (ver docs/operations.md, Primeira implantação).
// Idempotente: cada passo só altera o que ainda falta.
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

    // Apaga o material de credenciais que os endpoints antigos do quick-start registraram (os eventos são mantidos)
    function.run "setup/scrub_audit_credentials" as $scrub
  }

  response = {seed: $seed, migration: $migration, scrub: $scrub}
  guid = "Z3G34T-NJuLX5EFkVNRH_k_Jb80"
}
