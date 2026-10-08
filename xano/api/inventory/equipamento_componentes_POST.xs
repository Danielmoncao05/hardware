// Installs a catalog component on equipment (inventory.manage). The same component may be installed
// several times (each assignment has its own id, e.g. one per slot). Quantity must be positive;
// equipment and component must exist, and the component must be active.
query "equipamentos/{equipamento_id}/componentes" verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    int equipamento_id
    int componente_id
    int quantidade?=1
    text? slot? filters=trim
    text? numero_serie_instalado? filters=trim
    timestamp? instalado_em?
    text? observacoes? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    precondition ($input.quantidade > 0) {
      error_type = "inputerror"
      error = "quantidade must be greater than zero."
    }

    db.transaction {
      stack {
        db.get equipamentos {
          field_name = "id"
          field_value = $input.equipamento_id
          output = ["id", "status"]
        } as $equip

        precondition ($equip != null) {
          error_type = "inputerror"
          error = "equipamento_id must reference existing equipment."
        }

        precondition ($equip.status != "decommissioned") {
          error_type = "inputerror"
          error = "Components cannot be installed on decommissioned equipment."
        }

        db.get componentes {
          field_name = "id"
          field_value = $input.componente_id
        } as $componente

        precondition ($componente != null && $componente.ativo == true) {
          error_type = "inputerror"
          error = "componente_id must reference an active catalog component."
        }

        db.add equipamento_componentes {
          data = {
            equipamento_id        : $input.equipamento_id
            componente_id         : $input.componente_id
            quantidade            : $input.quantidade
            slot                  : $input.slot
            numero_serie_instalado: $input.numero_serie_instalado
            instalado_em          : $input.instalado_em ?? "now"
            observacoes           : $input.observacoes
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "componente.installed"
            entidade   : "equipamento_componentes"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item|set:"componente":$componente.nome|set:"tipo":$componente.tipo
  guid = "HHxuBQqIHFEv4XwRbm0BKRj9zk0"
}
