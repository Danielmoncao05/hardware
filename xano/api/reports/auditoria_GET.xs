// Audit log (audit.read, administrators only). Read-only: no endpoint edits or deletes audit events.
// Filter by actor, action, affected entity/record, and date range.
query auditoria verb=GET {
  api_group = "Reports"
  auth = "user"

  input {
    int? user_id?
    text? action? filters=trim
    text? entidade? filters=trim
    int? registro_id?
    timestamp? de?
    timestamp? ate?
    int page?=1 filters=min:1
    int per_page?=50 filters=min:1|max:200
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "audit.read"}
    }

    // JSON containment has no null-safe form, so build the metadata filter only from given values
    var $meta {
      value = {}
    }

    conditional {
      if ($input.entidade != null && $input.entidade != "") {
        var.update $meta {
          value = $meta|set:"entidade":$input.entidade
        }
      }
    }

    conditional {
      if ($input.registro_id != null) {
        var.update $meta {
          value = $meta|set:"registro_id":$input.registro_id
        }
      }
    }

    var $action {
      value = $input.action == "" ? null : $input.action
    }

    // Apply the metadata containment only when an entity/record filter is given: "metadata @> {}" would
    // silently drop every event whose metadata is null (e.g. events logged without details).
    var $items {
      value = null
    }

    conditional {
      if (($meta|keys|count) > 0) {
        db.query event_log {
          join = {
            user: {
              table: "user"
              type : "left"
              where: $db.event_log.user_id == $db.user.id
            }
          }

          where = $db.event_log.user_id ==? $input.user_id && $db.event_log.action ==? $action && $db.event_log.metadata @> $meta && $db.event_log.created_at >=? $input.de && $db.event_log.created_at <=? $input.ate
          sort = {created_at: "desc"}
          eval = {ator: $db.user.name}
          return = {
            type  : "list"
            paging: {page: $input.page, per_page: $input.per_page, totals: true}
          }
        } as $result

        var.update $items {
          value = $result
        }
      }

      else {
        db.query event_log {
          join = {
            user: {
              table: "user"
              type : "left"
              where: $db.event_log.user_id == $db.user.id
            }
          }

          where = $db.event_log.user_id ==? $input.user_id && $db.event_log.action ==? $action && $db.event_log.created_at >=? $input.de && $db.event_log.created_at <=? $input.ate
          sort = {created_at: "desc"}
          eval = {ator: $db.user.name}
          return = {
            type  : "list"
            paging: {page: $input.page, per_page: $input.per_page, totals: true}
          }
        } as $result

        var.update $items {
          value = $result
        }
      }
    }
  }

  response = $items
  guid = "QpBBmSzt5uTWTtV2ihQB-yVfuMQ"
}
