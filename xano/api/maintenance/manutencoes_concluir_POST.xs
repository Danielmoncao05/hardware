// planned/in_progress -> completed. Requires a completion date (not in the future, not before the start)
// and a work summary; otherwise the state is left unchanged. Optionally sets the equipment status
// afterwards (e.g. back to operational). For recurring preventive work, the response includes the
// suggested next planned date (data_planejada + interval); scheduling it is a separate POST manutencoes.
// Setting the equipment status (status_equipamento) requires inventory.manage (decision 20); without it
// the whole request is refused, so nothing is half-applied. Setting it to out_of_service requires
// motivo_status, the same reason rule as the status endpoint.
query "manutencoes/{manutencao_id}/concluir" verb=POST {
  api_group = "Maintenance"
  auth = "user"

  input {
    int manutencao_id
    timestamp concluida_em
    text resumo_execucao filters=trim
    json? checklist?
    enum? status_equipamento? {
      values = ["operational", "out_of_service"]
    }

    text? motivo_status? filters=trim
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
      if ($input.status_equipamento != null) {
        function.run "hhm/require_permission" {
          input = {user_id: $auth.id, permission: "inventory.manage"}
        }
      }
    }

    precondition ($before.status == "planned" || $before.status == "in_progress") {
      error_type = "inputerror"
      error = "Only planned or in-progress maintenance can be completed."
    }

    precondition ($input.status_equipamento != "out_of_service" || ($input.motivo_status != null && $input.motivo_status != "")) {
      error_type = "inputerror"
      error = "motivo_status is required to take the equipment out of service."
    }

    precondition ($input.resumo_execucao != "") {
      error_type = "inputerror"
      error = "resumo_execucao is required to complete maintenance."
    }

    precondition ($input.concluida_em <= now) {
      error_type = "inputerror"
      error = "concluida_em cannot be in the future."
    }

    precondition ($before.iniciada_em == null || $input.concluida_em >= $before.iniciada_em) {
      error_type = "inputerror"
      error = "concluida_em cannot be earlier than the start date."
    }

    db.transaction {
      stack {
        db.edit manutencoes {
          field_name = "id"
          field_value = $input.manutencao_id
          data = {
            status         : "completed"
            concluida_em   : $input.concluida_em
            resumo_execucao: $input.resumo_execucao
            checklist      : $input.checklist ?? $before.checklist
            iniciada_em    : $before.iniciada_em ?? $input.concluida_em
            updated_at     : "now"
          }
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "manutencao.completed"
            entidade   : "manutencoes"
            registro_id: $input.manutencao_id
            antes      : {status: $before.status}
            depois     : {status: "completed", concluida_em: $input.concluida_em, resumo_execucao: $input.resumo_execucao}
          }
        }

        conditional {
          if ($input.status_equipamento != null) {
            db.get equipamentos {
              field_name = "id"
              field_value = $before.equipamento_id
              output = ["id", "status"]
            } as $equip

            conditional {
              if ($equip.status != $input.status_equipamento) {
                function.run "hhm/set_equipment_status" {
                  input = {
                    equipamento_id: $before.equipamento_id
                    status        : $input.status_equipamento
                    motivo        : $input.motivo_status ?? ("Maintenance #" ~ $input.manutencao_id ~ " completed")
                    user_id       : $auth.id
                  }
                }
              }
            }
          }
        }
      }
    }

    var $proxima_sugerida {
      value = null
    }

    conditional {
      if ($before.tipo == "preventive" && $before.intervalo_recorrencia_dias != null) {
        var.update $proxima_sugerida {
          value = $before.data_planejada|to_timestamp|transform_timestamp:("+" ~ $before.intervalo_recorrencia_dias ~ " days")|format_timestamp:"Y-m-d":"UTC"
        }
      }
    }
  }

  response = $after|set:"proxima_data_sugerida":$proxima_sugerida
  guid = "6cxjXiTb5LvQ520nkwl5-6SRBho"
}
