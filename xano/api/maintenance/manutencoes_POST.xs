// Agenda manutenção preventiva ou registra corretiva no estado "planned".
// maintenance.manage pode criar qualquer registro. Um técnico (maintenance.manage_assigned) pode criar
// manutenção corretiva para uma ocorrência atribuída a ele, com ele mesmo como responsável.
// O equipamento precisa existir e não estar descomissionado; o responsável precisa estar habilitado e poder atuar
// em manutenções (maintenance.manage ou maintenance.manage_assigned);
// uma ocorrência vinculada precisa ser do mesmo equipamento, e só manutenção corretiva pode ter vínculo.
query manutencoes verb=POST {
  api_group = "Maintenance"
  auth = "user"

  input {
    int equipamento_id
    enum tipo {
      values = ["preventive", "corrective"]
    }

    date data_planejada
    text descricao filters=trim
    int responsavel_id
    json? checklist?
    int? intervalo_recorrencia_dias? filters=min:1
    int? ocorrencia_id?
  }

  stack {
    precondition ($input.descricao != "") {
      error_type = "inputerror"
      error = "descricao is required."
    }

    precondition ($input.intervalo_recorrencia_dias == null || $input.tipo == "preventive") {
      error_type = "inputerror"
      error = "intervalo_recorrencia_dias applies only to preventive maintenance."
    }

    precondition ($input.ocorrencia_id == null || $input.tipo == "corrective") {
      error_type = "inputerror"
      error = "Only corrective maintenance can be linked to an occurrence."
    }

    function.run "hhm/has_permission" {
      input = {user_id: $auth.id, permission: "maintenance.manage"}
    } as $can_manage

    conditional {
      if ($can_manage == false) {
        function.run "hhm/require_permission" {
          input = {user_id: $auth.id, permission: "maintenance.manage_assigned"}
        }

        precondition ($input.tipo == "corrective" && $input.ocorrencia_id != null && $input.responsavel_id == $auth.id) {
          error_type = "accessdenied"
          error = "Access denied."
        }
      }
    }

    db.transaction {
      stack {
        db.get equipamentos {
          field_name = "id"
          field_value = $input.equipamento_id
          output = ["id", "nome", "status"]
        } as $equip

        precondition ($equip != null && $equip.status != "decommissioned") {
          error_type = "inputerror"
          error = "equipamento_id must reference equipment that is not decommissioned."
        }

        function.run "hhm/require_assignable_user" {
          input = {user_id: $input.responsavel_id, area: "maintenance"}
        } as $responsavel

        conditional {
          if ($input.ocorrencia_id != null) {
            db.get ocorrencias {
              field_name = "id"
              field_value = $input.ocorrencia_id
            } as $ocorrencia

            precondition ($ocorrencia != null && $ocorrencia.equipamento_id == $input.equipamento_id) {
              error_type = "inputerror"
              error = "ocorrencia_id must reference an occurrence of the same equipment."
            }

            precondition ($can_manage || $ocorrencia.responsavel_id == $auth.id) {
              error_type = "accessdenied"
              error = "Access denied."
            }
          }
        }

        db.add manutencoes {
          data = {
            equipamento_id            : $input.equipamento_id
            tipo                      : $input.tipo
            data_planejada            : $input.data_planejada
            descricao                 : $input.descricao
            status                    : "planned"
            responsavel_id            : $input.responsavel_id
            criado_por                : $auth.id
            checklist                 : $input.checklist
            intervalo_recorrencia_dias: $input.intervalo_recorrencia_dias
            ocorrencia_id             : $input.ocorrencia_id
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "manutencao.created"
            entidade   : "manutencoes"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item|set:"equipamento":$equip.nome|set:"responsavel":$responsavel.name
  guid = "FLu0yZaYvF504g-nxZPiMMAXsp4"
}
