// planned/in_progress -> canceled. A reason is required; the record stays in history and leaves the
// due-work views.
query "manutencoes/{manutencao_id}/cancelar" verb=POST {
  api_group = "Maintenance"
  auth = "user"

  input {
    int manutencao_id
    text motivo_cancelamento filters=trim
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

    precondition ($before.status == "planned" || $before.status == "in_progress") {
      error_type = "inputerror"
      error = "Only planned or in-progress maintenance can be canceled."
    }

    precondition ($input.motivo_cancelamento != "") {
      error_type = "inputerror"
      error = "motivo_cancelamento is required to cancel maintenance."
    }

    db.transaction {
      stack {
        db.edit manutencoes {
          field_name = "id"
          field_value = $input.manutencao_id
          data = {status: "canceled", motivo_cancelamento: $input.motivo_cancelamento, updated_at: "now"}
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "manutencao.canceled"
            entidade   : "manutencoes"
            registro_id: $input.manutencao_id
            antes      : {status: $before.status}
            depois     : {status: "canceled", motivo_cancelamento: $input.motivo_cancelamento}
          }
        }
      }
    }
  }

  response = $after
  guid = "cPpj42gV9OPLaGE_MeGn9UABUb8"
}
