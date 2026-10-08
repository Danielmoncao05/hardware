// Cria uma categoria de equipamento (inventory.manage). Os nomes são únicos.
query categorias verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    text nome filters=trim|min:1
    text? descricao? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.has categorias {
      field_name = "nome"
      field_value = $input.nome
    } as $exists

    precondition ($exists == false) {
      error_type = "inputerror"
      error = "nome: a category with this name already exists."
    }

    db.transaction {
      stack {
        db.add categorias {
          data = {nome: $input.nome, descricao: $input.descricao, ativo: true}
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "categoria.created"
            entidade   : "categorias"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item
  guid = "uhfxm5rNwezCjopq5PI3Z0_X1gM"
}
