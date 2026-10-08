// Creates a manufacturer (inventory.manage). Names are unique.
query fabricantes verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    text nome filters=trim|min:1
    text? site? filters=trim
    text? contato_suporte? filters=trim
    text? observacoes? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.has fabricantes {
      field_name = "nome"
      field_value = $input.nome
    } as $exists

    precondition ($exists == false) {
      error_type = "inputerror"
      error = "nome: a manufacturer with this name already exists."
    }

    db.transaction {
      stack {
        db.add fabricantes {
          data = {
            nome           : $input.nome
            site           : $input.site
            contato_suporte: $input.contato_suporte
            observacoes    : $input.observacoes
            ativo          : true
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "fabricante.created"
            entidade   : "fabricantes"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item
  guid = "lDa5P74GI65DYtwCHNGywroumXs"
}
