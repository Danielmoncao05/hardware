// Atualiza ou ativa/desativa um modelo (inventory.manage). Um fabricante ou categoria alterado
// precisa estar ativo; a combinação (fabricante, categoria, nome) precisa continuar única.
// O equipamento deriva fabricante/categoria do modelo, então uma mudança aqui se reflete em todos os
// equipamentos deste modelo e é registrada no log de auditoria.
query "modelos/{modelo_id}" verb=PATCH {
  api_group = "Inventory"
  auth = "user"

  input {
    int modelo_id
    text? nome? filters=trim
    int? fabricante_id?
    int? categoria_id?
    text? codigo? filters=trim
    text? observacoes? filters=trim
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get modelos {
      field_name = "id"
      field_value = $input.modelo_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Model not found."
    }

    precondition ($input.nome == null || $input.nome != "") {
      error_type = "inputerror"
      error = "nome cannot be blank."
    }

    var $nome {
      value = $input.nome ?? $before.nome
    }

    var $fabricante_id {
      value = $input.fabricante_id ?? $before.fabricante_id
    }

    var $categoria_id {
      value = $input.categoria_id ?? $before.categoria_id
    }

    db.transaction {
      stack {
        conditional {
          if ($input.fabricante_id != null && $input.fabricante_id != $before.fabricante_id) {
            db.get fabricantes {
              field_name = "id"
              field_value = $input.fabricante_id
            } as $fabricante

            precondition ($fabricante != null && $fabricante.ativo == true) {
              error_type = "inputerror"
              error = "fabricante_id must reference an active manufacturer."
            }
          }
        }

        conditional {
          if ($input.categoria_id != null && $input.categoria_id != $before.categoria_id) {
            db.get categorias {
              field_name = "id"
              field_value = $input.categoria_id
            } as $categoria

            precondition ($categoria != null && $categoria.ativo == true) {
              error_type = "inputerror"
              error = "categoria_id must reference an active category."
            }
          }
        }

        db.query modelos {
          where = $db.modelos.fabricante_id == $fabricante_id && $db.modelos.categoria_id == $categoria_id && $db.modelos.nome == $nome && $db.modelos.id != $input.modelo_id
          return = {type: "exists"}
        } as $taken

        precondition ($taken == false) {
          error_type = "inputerror"
          error = "nome: this manufacturer already has a model with this name in this category."
        }

        var $updates {
          value = {
            updated_at   : "now"
            nome         : $nome
            fabricante_id: $fabricante_id
            categoria_id : $categoria_id
          }
        }

        conditional {
          if ($input.codigo != null) {
            var.update $updates {
              value = $updates|set:"codigo":($input.codigo == "" ? null : $input.codigo)
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

        db.patch modelos {
          field_name = "id"
          field_value = $input.modelo_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "modelo.updated"
            entidade   : "modelos"
            registro_id: $input.modelo_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "sMWYCTPD5YTeGSbaer1fDZQZldI"
}
