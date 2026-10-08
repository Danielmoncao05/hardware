// Log de auditoria (audit.read, só administradores). Somente leitura: nenhum endpoint edita ou apaga eventos de auditoria.
// Filtros por autor, ação, entidade/registro afetado e período.
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

    // A comparação de contenção em JSON não tem forma segura para null, então o filtro de metadata é montado só com os valores informados
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

    // Só aplica a contenção de metadata quando há filtro de entidade/registro: "metadata @> {}" descartaria
    // silenciosamente todo evento com metadata nula (ex.: eventos registrados sem detalhes).
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
