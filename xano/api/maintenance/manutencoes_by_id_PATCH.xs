// Edita uma manutenção aberta (planejada ou em andamento). Trocar o responsável exige
// maintenance.manage; o técnico atribuído pode editar data, descrição, checklist e recorrência.
// Registros concluídos e cancelados são histórico e não podem ser editados.
query "manutencoes/{manutencao_id}" verb=PATCH {
  api_group = "Maintenance"
  auth = "user"

  input {
    int manutencao_id
    date? data_planejada?
    text? descricao? filters=trim
    int? responsavel_id?
    json? checklist?
    int? intervalo_recorrencia_dias? filters=min:1
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
    } as $can_manage

    precondition ($before.status == "planned" || $before.status == "in_progress") {
      error_type = "inputerror"
      error = "Completed or canceled maintenance cannot be edited."
    }

    precondition ($input.descricao == null || $input.descricao != "") {
      error_type = "inputerror"
      error = "descricao cannot be blank."
    }

    precondition ($input.intervalo_recorrencia_dias == null || $before.tipo == "preventive") {
      error_type = "inputerror"
      error = "intervalo_recorrencia_dias applies only to preventive maintenance."
    }

    var $updates {
      value = {
        updated_at                : "now"
        data_planejada            : $input.data_planejada ?? $before.data_planejada
        descricao                 : $input.descricao ?? $before.descricao
        checklist                 : $input.checklist ?? $before.checklist
        intervalo_recorrencia_dias: $input.intervalo_recorrencia_dias ?? $before.intervalo_recorrencia_dias
      }
    }

    db.transaction {
      stack {
        conditional {
          if ($input.responsavel_id != null && $input.responsavel_id != $before.responsavel_id) {
            precondition ($can_manage) {
              error_type = "accessdenied"
              error = "Access denied."
            }

            function.run "hhm/require_assignable_user" {
              input = {user_id: $input.responsavel_id, area: "maintenance"}
            }

            var.update $updates {
              value = $updates|set:"responsavel_id":$input.responsavel_id
            }
          }
        }

        db.patch manutencoes {
          field_name = "id"
          field_value = $input.manutencao_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : $after.responsavel_id != $before.responsavel_id ? "manutencao.reassigned" : "manutencao.updated"
            entidade   : "manutencoes"
            registro_id: $input.manutencao_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "lItp8hnPwQM3RcXLOzBfpkvFnp8"
}
