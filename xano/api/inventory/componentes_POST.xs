// Adiciona um componente de hardware ao catálogo (inventory.manage). O fabricante, se informado, precisa estar ativo.
query componentes verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    text nome filters=trim|min:1
    enum tipo {
      values = [
        "processor"
        "memory_ram"
        "storage"
        "motherboard"
        "power_supply"
        "sensor"
        "display"
        "battery"
        "electronic_module"
        "communication_board"
        "other"
      ]
    }

    int? fabricante_id?
    text? modelo_componente? filters=trim
    text? numero_peca? filters=trim
    text? especificacoes? filters=trim
    text? observacoes? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.transaction {
      stack {
        conditional {
          if ($input.fabricante_id != null) {
            db.get fabricantes {
              field_name = "id"
              field_value = $input.fabricante_id
            } as $fabricante

            precondition ($fabricante != null && $fabricante.ativo == true) {
              error_type = "inputerror"
              error = "fabricante_id must reference an active manufacturer."
            }
          }
        }

        db.add componentes {
          data = {
            nome             : $input.nome
            tipo             : $input.tipo
            fabricante_id    : $input.fabricante_id
            modelo_componente: $input.modelo_componente
            numero_peca      : $input.numero_peca
            especificacoes   : $input.especificacoes
            observacoes      : $input.observacoes
            ativo            : true
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "componente.created"
            entidade   : "componentes"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item
  guid = "10BrreM169bVEvVbfy_gywA6g7M"
}
