// Updates or activates/deactivates a catalog component (inventory.manage). Send "" to clear an optional
// text field and fabricante_id = 0 to remove the manufacturer. Deactivated components stay on existing
// assignments but cannot be newly assigned.
query "componentes/{componente_id}" verb=PATCH {
  api_group = "Inventory"
  auth = "user"

  input {
    int componente_id
    text? nome? filters=trim
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
    text? modelo_componente? filters=trim
    text? numero_peca? filters=trim
    text? especificacoes? filters=trim
    text? observacoes? filters=trim
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get componentes {
      field_name = "id"
      field_value = $input.componente_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Component not found."
    }

    precondition ($input.nome == null || $input.nome != "") {
      error_type = "inputerror"
      error = "nome cannot be blank."
    }

    var $updates {
      value = {
        updated_at: "now"
        nome      : $input.nome ?? $before.nome
        tipo      : $input.tipo ?? $before.tipo
        ativo     : $input.ativo ?? $before.ativo
      }
    }

    db.transaction {
      stack {
        conditional {
          if ($input.fabricante_id == 0) {
            var.update $updates {
              value = $updates|set:"fabricante_id":null
            }
          }

          elseif ($input.fabricante_id != null) {
            db.get fabricantes {
              field_name = "id"
              field_value = $input.fabricante_id
            } as $fabricante

            precondition ($fabricante != null && $fabricante.ativo == true) {
              error_type = "inputerror"
              error = "fabricante_id must reference an active manufacturer."
            }

            var.update $updates {
              value = $updates|set:"fabricante_id":$input.fabricante_id
            }
          }
        }

        conditional {
          if ($input.modelo_componente != null) {
            var.update $updates {
              value = $updates|set:"modelo_componente":($input.modelo_componente == "" ? null : $input.modelo_componente)
            }
          }
        }

        conditional {
          if ($input.numero_peca != null) {
            var.update $updates {
              value = $updates|set:"numero_peca":($input.numero_peca == "" ? null : $input.numero_peca)
            }
          }
        }

        conditional {
          if ($input.especificacoes != null) {
            var.update $updates {
              value = $updates|set:"especificacoes":($input.especificacoes == "" ? null : $input.especificacoes)
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

        db.patch componentes {
          field_name = "id"
          field_value = $input.componente_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "componente.updated"
            entidade   : "componentes"
            registro_id: $input.componente_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "zRq45PYhVQGZzXFcznFxWrmnITY"
}
