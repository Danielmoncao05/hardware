// Lista as categorias de equipamento (operational.read). As inativas ficam ocultas, a menos que include_inactive seja true.
query categorias verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    bool include_inactive?=false
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
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

    db.query categorias {
      where = $db.categorias.ativo ==? $only_active
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $items
  }

  response = $items
  guid = "ndYGt3jZ4OKUDNnU9DxeUN2xlUk"
}
