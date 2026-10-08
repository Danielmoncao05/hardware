// Aplica uma transição de status do equipamento e audita o status anterior/novo. Quem chama verifica as permissões.
// Usada pelo endpoint de status e pelas transições de manutenção que colocam o equipamento em manutenção.
// Não abre transação própria: todo chamador a executa dentro do seu único db.transaction, então a troca de
// status, o evento de auditoria e as gravações do próprio chamador são confirmados ou desfeitos juntos.
function "hhm/set_equipment_status" {
  input {
    int equipamento_id
    text status
    text? motivo?
    int user_id
  }

  stack {
    precondition (["operational", "under_maintenance", "out_of_service", "decommissioned"]|some:$$ == $input.status) {
      error_type = "inputerror"
      error = "status is not a valid equipment status."
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Equipment not found."
    }

    precondition ($before.status != $input.status) {
      error_type = "inputerror"
      error = "The equipment already has this status."
    }

    precondition ($before.status != "decommissioned") {
      error_type = "inputerror"
      error = "Decommissioned equipment cannot change status."
    }

    precondition (($input.status != "decommissioned" && $input.status != "out_of_service") || ($input.motivo != null && $input.motivo != "")) {
      error_type = "inputerror"
      error = "motivo is required to decommission or take equipment out of service."
    }

    db.edit equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
      data = {status: $input.status, updated_at: "now"}
    } as $after

    function.run "hhm/audit" {
      input = {
        user_id    : $input.user_id
        action     : $input.status == "decommissioned" ? "equipamento.decommissioned" : "equipamento.status_changed"
        entidade   : "equipamentos"
        registro_id: $input.equipamento_id
        antes      : {status: $before.status}
        depois     : {status: $input.status, motivo: $input.motivo}
      }
    }
  }

  response = $after
  guid = "CTI851pnEeYD2u52jiSLiIKT5_s"
}
