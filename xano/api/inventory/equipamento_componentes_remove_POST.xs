// Records the removal of an installed component (inventory.manage). The assignment row is kept with
// removido_em so installation/removal history stays queryable; it is never deleted.
query "equipamentos/{equipamento_id}/componentes/{atribuicao_id}/remover" verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    int equipamento_id
    int atribuicao_id
    timestamp? removido_em?
    text? observacoes? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get equipamento_componentes {
      field_name = "id"
      field_value = $input.atribuicao_id
    } as $before

    precondition ($before != null && $before.equipamento_id == $input.equipamento_id) {
      error_type = "notfound"
      error = "Component assignment not found on this equipment."
    }

    precondition ($before.removido_em == null) {
      error_type = "inputerror"
      error = "This component has already been removed."
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
      output = ["id", "status"]
    } as $equip

    // Decommissioned equipment is kept read-only as history (same rule as install/move/status)
    precondition ($equip.status != "decommissioned") {
      error_type = "inputerror"
      error = "Components of decommissioned equipment cannot be changed."
    }

    var $removido_em {
      value = $input.removido_em ?? now
    }

    precondition ($before.instalado_em == null || $removido_em >= $before.instalado_em) {
      error_type = "inputerror"
      error = "removido_em cannot be earlier than the installation date."
    }

    var $updates {
      value = {removido_em: $removido_em, updated_at: "now"}
    }

    conditional {
      if ($input.observacoes != null && $input.observacoes != "") {
        var.update $updates {
          value = $updates|set:"observacoes":$input.observacoes
        }
      }
    }

    db.transaction {
      stack {
        db.patch equipamento_componentes {
          field_name = "id"
          field_value = $input.atribuicao_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "componente.removed"
            entidade   : "equipamento_componentes"
            registro_id: $input.atribuicao_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "ISNsxBiGfgPsZd-jbXzg2-14k80"
}
