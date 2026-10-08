// Cria uma localização (inventory.manage). A localização superior, se informada, precisa existir e estar ativa.
query localizacoes verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    text nome filters=trim|min:1
    int? parent_id?
    text? tipo? filters=trim
    text? descricao? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.transaction {
      stack {
        conditional {
          if ($input.parent_id != null) {
            db.get localizacoes {
              field_name = "id"
              field_value = $input.parent_id
            } as $parent

            precondition ($parent != null && $parent.ativo == true) {
              error_type = "inputerror"
              error = "parent_id must reference an active location."
            }
          }
        }

        db.add localizacoes {
          data = {
            nome     : $input.nome
            parent_id: $input.parent_id
            tipo     : $input.tipo
            descricao: $input.descricao
            ativo    : true
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "localizacao.created"
            entidade   : "localizacoes"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item
  guid = "mhTsTpnJ9AACdFe2r4WF5i94kIg"
}
