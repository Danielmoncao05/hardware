// Atualiza uma ocorrência aberta ou em andamento: descrição e severidade (gestor ou técnico
// atribuído) e atribuição do responsável (somente occurrence.manage).
// Envie responsavel_id = 0 para remover a atribuição. Ocorrências resolvidas e canceladas são histórico.
query "ocorrencias/{ocorrencia_id}" verb=PATCH {
  api_group = "Maintenance"
  auth = "user"

  input {
    int ocorrencia_id
    text? descricao_tecnica? filters=trim
    enum? severidade? {
      values = ["low", "medium", "high", "critical"]
    }

    int? responsavel_id?
  }

  stack {
    db.get ocorrencias {
      field_name = "id"
      field_value = $input.ocorrencia_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Occurrence not found."
    }

    function.run "hhm/require_work_access" {
      input = {user_id: $auth.id, area: "occurrence", responsavel_id: $before.responsavel_id}
    } as $can_manage

    precondition ($before.status == "open" || $before.status == "in_progress") {
      error_type = "inputerror"
      error = "Resolved or canceled occurrences cannot be edited."
    }

    precondition ($input.descricao_tecnica == null || $input.descricao_tecnica != "") {
      error_type = "inputerror"
      error = "descricao_tecnica cannot be blank."
    }

    var $updates {
      value = {
        updated_at       : "now"
        descricao_tecnica: $input.descricao_tecnica ?? $before.descricao_tecnica
        severidade       : $input.severidade ?? $before.severidade
      }
    }

    db.transaction {
      stack {
        conditional {
          if ($input.responsavel_id != null) {
            precondition ($can_manage) {
              error_type = "accessdenied"
              error = "Access denied."
            }

            conditional {
              if ($input.responsavel_id == 0) {
                var.update $updates {
                  value = $updates|set:"responsavel_id":null
                }
              }

              else {
                function.run "hhm/require_assignable_user" {
                  input = {user_id: $input.responsavel_id, area: "occurrence"}
                }

                var.update $updates {
                  value = $updates|set:"responsavel_id":$input.responsavel_id
                }
              }
            }
          }
        }

        db.patch ocorrencias {
          field_name = "id"
          field_value = $input.ocorrencia_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : $after.responsavel_id != $before.responsavel_id ? "ocorrencia.assigned" : "ocorrencia.updated"
            entidade   : "ocorrencias"
            registro_id: $input.ocorrencia_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "E4oaZ-tU5SFlijy-aHGNZMzqQFc"
}
