// Updates or activates/deactivates a category (inventory.manage). Send "" to clear descricao.
query "categorias/{categoria_id}" verb=PATCH {
  api_group = "Inventory"
  auth = "user"

  input {
    int categoria_id
    text? nome? filters=trim
    text? descricao? filters=trim
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get categorias {
      field_name = "id"
      field_value = $input.categoria_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Category not found."
    }

    var $updates {
      value = {updated_at: "now"}
    }

    conditional {
      if ($input.nome != null) {
        precondition ($input.nome != "") {
          error_type = "inputerror"
          error = "nome cannot be blank."
        }

        db.query categorias {
          where = $db.categorias.nome == $input.nome && $db.categorias.id != $input.categoria_id
          return = {type: "exists"}
        } as $taken

        precondition ($taken == false) {
          error_type = "inputerror"
          error = "nome: a category with this name already exists."
        }

        var.update $updates {
          value = $updates|set:"nome":$input.nome
        }
      }
    }

    conditional {
      if ($input.descricao != null) {
        var.update $updates {
          value = $updates|set:"descricao":($input.descricao == "" ? null : $input.descricao)
        }
      }
    }

    conditional {
      if ($input.ativo != null) {
        var.update $updates {
          value = $updates|set:"ativo":$input.ativo
        }
      }
    }

    db.transaction {
      stack {
        db.patch categorias {
          field_name = "id"
          field_value = $input.categoria_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "categoria.updated"
            entidade   : "categorias"
            registro_id: $input.categoria_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "DO070dyni_ivcBGNI2fBE6GIPFQ"
}
