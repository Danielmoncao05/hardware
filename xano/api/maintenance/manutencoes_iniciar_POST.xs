// planned -> in_progress. Optionally sets the equipment status to under_maintenance in the same
// transaction (audited as an equipment status change). Changing equipment status requires
// inventory.manage (decision 20): the assigned technician can start the work, but a request that also
// asks for the status change is refused as a whole when the user lacks that permission.
query "manutencoes/{manutencao_id}/iniciar" verb=POST {
  api_group = "Maintenance"
  auth = "user"

  input {
    int manutencao_id
    timestamp? iniciada_em?
    bool colocar_equipamento_em_manutencao?=false
  }

  stack {
    db.get manutencoes {
      field_name = "id"
      field_value = $input.manutencao_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Maintenance not found."
    }

    function.run "hhm/require_work_access" {
      input = {user_id: $auth.id, area: "maintenance", responsavel_id: $before.responsavel_id}
    }

    // Equipment status changes need inventory.manage, also when requested through maintenance
    conditional {
      if ($input.colocar_equipamento_em_manutencao) {
        function.run "hhm/require_permission" {
          input = {user_id: $auth.id, permission: "inventory.manage"}
        }
      }
    }

    precondition ($before.status == "planned") {
      error_type = "inputerror"
      error = "Only planned maintenance can be started."
    }

    var $iniciada_em {
      value = $input.iniciada_em ?? now
    }

    precondition ($iniciada_em <= now) {
      error_type = "inputerror"
      error = "iniciada_em cannot be in the future."
    }

    db.transaction {
      stack {
        db.edit manutencoes {
          field_name = "id"
          field_value = $input.manutencao_id
          data = {status: "in_progress", iniciada_em: $iniciada_em, updated_at: "now"}
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "manutencao.started"
            entidade   : "manutencoes"
            registro_id: $input.manutencao_id
            antes      : {status: $before.status}
            depois     : {status: "in_progress", iniciada_em: $iniciada_em}
          }
        }

        conditional {
          if ($input.colocar_equipamento_em_manutencao) {
            db.get equipamentos {
              field_name = "id"
              field_value = $before.equipamento_id
              output = ["id", "status"]
            } as $equip

            conditional {
              if ($equip.status != "under_maintenance") {
                function.run "hhm/set_equipment_status" {
                  input = {
                    equipamento_id: $before.equipamento_id
                    status        : "under_maintenance"
                    motivo        : "Maintenance #" ~ $input.manutencao_id ~ " started"
                    user_id       : $auth.id
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = $after
  guid = "bZwByZO6nr-hPqwSUmqShJsyE4o"
}
