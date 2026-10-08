// Lista o catálogo de componentes de hardware (operational.read).
query componentes verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    text? q? filters=trim
    enum? tipo? {
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

    db.query componentes {
      join = {
        fabricantes: {
          table: "fabricantes"
          type : "left"
          where: $db.componentes.fabricante_id == $db.fabricantes.id
        }
      }

      where = ($db.componentes.nome ilike $pattern || $db.componentes.numero_peca ilike $pattern) && $db.componentes.tipo ==? $input.tipo && $db.componentes.fabricante_id ==? $input.fabricante_id && $db.componentes.ativo ==? $only_active
      sort = {nome: "asc"}
      eval = {fabricante: $db.fabricantes.nome}
      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $items
  }

  response = $items
  guid = "Rb3PjXXY_4vFmauNqh47yaxTLDs"
}
