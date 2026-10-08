// Lista os modelos com os nomes do fabricante e da categoria (operational.read).
query modelos verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    text? q? filters=trim
    int? fabricante_id?
    int? categoria_id?
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

    db.query modelos {
      join = {
        fabricantes: {
          table: "fabricantes"
          where: $db.modelos.fabricante_id == $db.fabricantes.id
        }
        categorias: {
          table: "categorias"
          where: $db.modelos.categoria_id == $db.categorias.id
        }
      }

      where = $db.modelos.nome ilike $pattern && $db.modelos.fabricante_id ==? $input.fabricante_id && $db.modelos.categoria_id ==? $input.categoria_id && $db.modelos.ativo ==? $only_active
      sort = {nome: "asc"}
      eval = {
        fabricante: $db.fabricantes.nome
        categoria : $db.categorias.nome
      }

      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $items
  }

  response = $items
  guid = "RNGnfESS7CvDyVt4hv1WTMf2CYo"
}
