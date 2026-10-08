// Updates or activates/deactivates a manufacturer (inventory.manage). Send "" to clear an optional field.
// Deactivation keeps every historical reference and blocks new models/components from using it.
query "fabricantes/{fabricante_id}" verb=PATCH {
  api_group = "Inventory"
  auth = "user"

  input {
    int fabricante_id
    text? nome? filters=trim
    text? site? filters=trim
    text? contato_suporte? filters=trim
    text? observacoes? filters=trim
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get fabricantes {
      field_name = "id"
      field_value = $input.fabricante_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Manufacturer not found."
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

        db.query fabricantes {
          where = $db.fabricantes.nome == $input.nome && $db.fabricantes.id != $input.fabricante_id
          return = {type: "exists"}
        } as $taken

        precondition ($taken == false) {
          error_type = "inputerror"
          error = "nome: a manufacturer with this name already exists."
        }

        var.update $updates {
          value = $updates|set:"nome":$input.nome
        }
      }
    }

    conditional {
      if ($input.site != null) {
        var.update $updates {
          value = $updates|set:"site":($input.site == "" ? null : $input.site)
        }
      }
    }

    conditional {
      if ($input.contato_suporte != null) {
        var.update $updates {
          value = $updates|set:"contato_suporte":($input.contato_suporte == "" ? null : $input.contato_suporte)
        }
      }
    }

    conditional {
      if ($input.observacoes != null) {
        var.update $updates {
          value = $updates|set:"observacoes":($input.observacoes == "" ? null : $input.observacoes)
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
        db.patch fabricantes {
          field_name = "id"
          field_value = $input.fabricante_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "fabricante.updated"
            entidade   : "fabricantes"
            registro_id: $input.fabricante_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "zJ7fHrkRVjxlJoFq9z9mIsUMNag"
}
