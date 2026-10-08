// Creates a model (inventory.manage). Requires an existing, active manufacturer and category, and a
// name unique within that manufacturer and category. References are checked here because the
// datastore does not enforce them (validation.md #1).
query modelos verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    text nome filters=trim|min:1
    int fabricante_id
    int categoria_id
    text? codigo? filters=trim
    text? observacoes? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.transaction {
      stack {
        db.get fabricantes {
          field_name = "id"
          field_value = $input.fabricante_id
        } as $fabricante

        precondition ($fabricante != null && $fabricante.ativo == true) {
          error_type = "inputerror"
          error = "fabricante_id must reference an active manufacturer."
        }

        db.get categorias {
          field_name = "id"
          field_value = $input.categoria_id
        } as $categoria

        precondition ($categoria != null && $categoria.ativo == true) {
          error_type = "inputerror"
          error = "categoria_id must reference an active category."
        }

        db.query modelos {
          where = $db.modelos.fabricante_id == $input.fabricante_id && $db.modelos.categoria_id == $input.categoria_id && $db.modelos.nome == $input.nome
          return = {type: "exists"}
        } as $exists

        precondition ($exists == false) {
          error_type = "inputerror"
          error = "nome: this manufacturer already has a model with this name in this category."
        }

        db.add modelos {
          data = {
            nome         : $input.nome
            fabricante_id: $input.fabricante_id
            categoria_id : $input.categoria_id
            codigo       : $input.codigo
            observacoes  : $input.observacoes
            ativo        : true
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "modelo.created"
            entidade   : "modelos"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item|set:"fabricante":$fabricante.nome|set:"categoria":$categoria.nome
  guid = "pjrVbAaJs2g_CNIT8A1B2pHkqjs"
}
