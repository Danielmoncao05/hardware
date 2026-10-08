// Move o equipamento para outra localização ativa (inventory.manage) e audita a localização anterior e a nova.
query "equipamentos/{equipamento_id}/mover" verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    int equipamento_id
    int localizacao_id
    text? observacao? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Equipment not found."
    }

    precondition ($before.status != "decommissioned") {
      error_type = "inputerror"
      error = "Decommissioned equipment cannot be moved."
    }

    precondition ($input.localizacao_id != $before.localizacao_id) {
      error_type = "inputerror"
      error = "The equipment is already at this location."
    }

    db.transaction {
      stack {
        function.run "hhm/require_active_location" {
          input = {localizacao_id: $input.localizacao_id}
        } as $loc

        db.edit equipamentos {
          field_name = "id"
          field_value = $input.equipamento_id
          data = {localizacao_id: $input.localizacao_id, updated_at: "now"}
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "equipamento.moved"
            entidade   : "equipamentos"
            registro_id: $input.equipamento_id
            antes      : {localizacao_id: $before.localizacao_id}
            depois     : {localizacao_id: $input.localizacao_id, observacao: $input.observacao}
          }
        }
      }
    }
  }

  response = $after|set:"localizacao":$loc.nome
  guid = "13IGPaHoA5Seb843PqKnUarPNuA"
}
