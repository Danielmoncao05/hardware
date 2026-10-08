// Lista as localizações com o nome da localização superior (operational.read). As inativas ficam ocultas, a menos que
// include_inactive seja true; os registros históricos continuam mostrando-as pelos próprios joins.
query localizacoes verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    text? q? filters=trim
    int? parent_id?
    bool include_inactive?=false
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    var $pattern {
      value = "%" ~ ($input.q ?? "") ~ "%"
    }

    var $only_active {
      value = null
    }

    conditional {
      if ($input.include_inactive == false) {
        var.update $only_active {
          value = true
        }
      }
    }

    db.query localizacoes {
      where = $db.localizacoes.nome ilike $pattern && $db.localizacoes.parent_id ==? $input.parent_id && $db.localizacoes.ativo ==? $only_active
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $items

    // Os nomes das superiores vêm da mesma lista, mais uma busca para as superiores que não estão nela
    var $result {
      value = []
    }

    foreach ($items) {
      each as $loc {
        var $parent_nome {
          value = null
        }

        conditional {
          if ($loc.parent_id != null) {
            db.get localizacoes {
              field_name = "id"
              field_value = $loc.parent_id
              output = ["nome"]
            } as $parent

            var.update $parent_nome {
              value = $parent.nome
            }
          }
        }

        var.update $result {
          value = $result|push:($loc|set:"parent":$parent_nome)
        }
      }
    }
  }

  response = $result
  guid = "dvssoBJEJ0iKDbJpT8mZzUposvU"
}
