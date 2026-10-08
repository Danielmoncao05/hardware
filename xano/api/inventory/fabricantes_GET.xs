// Lista os fabricantes (operational.read). Os inativos ficam ocultos, a menos que include_inactive seja true.
query fabricantes verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    text? q? filters=trim
    bool include_inactive?=false
    int page?=1 filters=min:1
    int per_page?=50 filters=min:1|max:200
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

    db.query fabricantes {
      where = $db.fabricantes.nome ilike $pattern && $db.fabricantes.ativo ==? $only_active
      sort = {nome: "asc"}
      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $items
  }

  response = $items
  guid = "gNU-j4JXUuaXLhVri8oibWNwtIQ"
}
