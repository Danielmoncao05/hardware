// Updates, re-parents, or activates/deactivates a location (inventory.manage).
// Send parent_id = 0 to make it a top-level location; "" clears tipo/descricao.
// A new parent must be active and must not be the location itself or one of its descendants.
query "localizacoes/{localizacao_id}" verb=PATCH {
  api_group = "Inventory"
  auth = "user"

  input {
    int localizacao_id
    text? nome? filters=trim
    int? parent_id?
    text? tipo? filters=trim
    text? descricao? filters=trim
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get localizacoes {
      field_name = "id"
      field_value = $input.localizacao_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Location not found."
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

        var.update $updates {
          value = $updates|set:"nome":$input.nome
        }
      }
    }

    db.transaction {
      stack {
        conditional {
          if ($input.parent_id == 0) {
            var.update $updates {
              value = $updates|set:"parent_id":null
            }
          }

          elseif ($input.parent_id != null) {
            db.get localizacoes {
              field_name = "id"
              field_value = $input.parent_id
            } as $parent

            precondition ($parent != null && $parent.ativo == true) {
              error_type = "inputerror"
              error = "parent_id must reference an active location."
            }

            // Walk up from the new parent; reaching this location would create a cycle
            var $cursor {
              value = $input.parent_id
            }

            var $depth {
              value = 0
            }

            while ($cursor != null && $depth < 100) {
              each {
                precondition ($cursor != $input.localizacao_id) {
                  error_type = "inputerror"
                  error = "parent_id cannot be this location or one of its sub-locations."
                }

                db.get localizacoes {
                  field_name = "id"
                  field_value = $cursor
                  output = ["parent_id"]
                } as $node

                var.update $cursor {
                  value = $node.parent_id
                }

                math.add $depth {
                  value = 1
                }
              }
            }

            var.update $updates {
              value = $updates|set:"parent_id":$input.parent_id
            }
          }
        }

        conditional {
          if ($input.tipo != null) {
            var.update $updates {
              value = $updates|set:"tipo":($input.tipo == "" ? null : $input.tipo)
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

        db.patch localizacoes {
          field_name = "id"
          field_value = $input.localizacao_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "localizacao.updated"
            entidade   : "localizacoes"
            registro_id: $input.localizacao_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "qPbpr8Li57VYZQWs-LBID35pb4M"
}
