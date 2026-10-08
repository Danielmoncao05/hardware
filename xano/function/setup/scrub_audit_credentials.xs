// Limpeza única do material de credenciais nos eventos históricos de auditoria (decisão 4).
// Antes da correção desta mudança, os endpoints de login, cadastro, auth/me, magic-link login e redefinição
// de senha do quick-start gravavam o registro inteiro do usuário em event_log.metadata, inclusive o hash da senha e
// o hash do token de redefinição. Esta função mantém todos os eventos (ação, autor, data e o
// restante da metadata) e só troca esses dois valores por null. Idempotente; registra o próprio evento de auditoria.
function "setup/scrub_audit_credentials" {
  input {
  }

  stack {
    var $scrubbed_ids {
      value = []
    }

    // Uma leitura sem paginação: roda uma única vez, só sobre os eventos de autenticação do quick-start
    db.query event_log {
      where = $db.event_log.action in ["login", "signup", "get_auth_user", "login_for_password_reset", "reset_password"]
      sort = {id: "asc"}
      output = ["id", "metadata"]
      return = {type: "list"}
    } as $eventos

    foreach ($eventos) {
      each as $ev {
        var $meta {
          value = $ev.metadata
        }

        var $changed {
          value = false
        }

        conditional {
          if ($meta != null && ($meta|has:"password") && $meta.password != null) {
            var.update $meta {
              value = $meta|set:"password":null
            }

            var.update $changed {
              value = true
            }
          }
        }

        conditional {
          if ($meta != null && ($meta|has:"password_reset") && $meta.password_reset != null && $meta.password_reset.token != null) {
            var.update $meta {
              value = $meta|set:"password_reset":($meta.password_reset|set:"token":null)
            }

            var.update $changed {
              value = true
            }
          }
        }

        conditional {
          if ($changed) {
            db.edit event_log {
              field_name = "id"
              field_value = $ev.id
              data = {metadata: $meta}
            }

            var.update $scrubbed_ids {
              value = $scrubbed_ids|push:$ev.id
            }
          }
        }
      }
    }

    conditional {
      if (($scrubbed_ids|count) > 0) {
        function.run "hhm/audit" {
          input = {
            user_id    : null
            action     : "audit.credentials_scrubbed"
            entidade   : "event_log"
            registro_id: null
            depois     : {eventos: $scrubbed_ids|count, primeiro_id: $scrubbed_ids|first, ultimo_id: $scrubbed_ids|last, campos: ["password", "password_reset.token"]}
          }
        }
      }
    }
  }

  response = {eventos_corrigidos: $scrubbed_ids|count}
  guid = "xiMvcswZC7uBkwtzBNqcRJcsw3o"
}
