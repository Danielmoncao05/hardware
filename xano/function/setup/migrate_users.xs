// Migração única das contas do quick-start para o novo modelo de perfis (rodar depois de setup/seed_reference_data).
// admin -> administrator; member ou sem perfil -> viewer (menor privilégio). As contas continuam habilitadas,
// nada é apagado e event_log não é alterado. Só usuários sem role_id são alterados, então rodar de
// novo nunca desfaz uma reatribuição feita depois por um administrador.
// Devolve todas as contas migradas para um administrador revisar as atribuições de viewer antes de entrar em produção.
function "setup/migrate_users" {
  input {
  }

  stack {
    db.get roles {
      field_name = "nome"
      field_value = "administrator"
    } as $administrator

    db.get roles {
      field_name = "nome"
      field_value = "viewer"
    } as $viewer

    precondition ($administrator != null && $viewer != null) {
      error_type = "inputerror"
      error = "Run setup/seed_reference_data before migrating users."
    }

    db.query user {
      where = $db.user.role_id == null
      output = ["id", "name", "email", "role", "ativo"]
      return = {type: "list"}
    } as $pending

    var $migrated {
      value = []
    }

    db.transaction {
      stack {
        foreach ($pending) {
          each as $u {
            var $novo_role {
              value = $viewer
            }

            conditional {
              if ($u.role == "admin") {
                var.update $novo_role {
                  value = $administrator
                }
              }
            }

            var $ativo {
              value = $u.ativo
            }

            conditional {
              if ($ativo == null) {
                var.update $ativo {
                  value = true
                }
              }
            }

            db.edit user {
              field_name = "id"
              field_value = $u.id
              data = {role_id: $novo_role.id, ativo: $ativo, updated_at: "now"}
            }

            function.run "hhm/audit" {
              input = {
                user_id    : null
                action     : "user.role_migrated"
                entidade   : "user"
                registro_id: $u.id
                antes      : {role: $u.role, role_id: null, ativo: $u.ativo}
                depois     : {role_id: $novo_role.id, role: $novo_role.nome, ativo: $ativo}
              }
            }

            var.update $migrated {
              value = $migrated|push:{
                id          : $u.id
                email       : $u.email
                legacy_role : $u.role
                novo_role   : $novo_role.nome
                needs_review: $novo_role.nome == "viewer"
              }
            }
          }
        }
      }
    }

    db.query user {
      return = {type: "count"}
    } as $total_users

    db.query user {
      where = $db.user.role_id == null
      return = {type: "count"}
    } as $without_role
  }

  response = {
    total_users : $total_users
    migrated    : $migrated
    without_role: $without_role
  }
  guid = "c71SuAF2vb3s4s2eRySpeYOkD_M"
}
