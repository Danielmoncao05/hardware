// One-time cleanup of credential material in historical audit events (decision 4).
// Before the fix in this change, the quick-start login, signup, auth/me, magic-link login and password
// reset endpoints logged the whole user record as event_log.metadata, including the password hash and
// the hashed password-reset token. This function keeps every event (action, actor, timestamp and the
// remaining metadata) and only sets those two values to null. Idempotent; records its own audit event.
function "setup/scrub_audit_credentials" {
  input {
  }

  stack {
    var $scrubbed_ids {
      value = []
    }

    // One unpaginated read: this runs once, over the quick-start auth events only
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
