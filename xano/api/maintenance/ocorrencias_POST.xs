// Registra uma ocorrência de equipamento (occurrence.report). Cria como "open", com quem chama como relator.
// descricao_tecnica descreve só o comportamento do equipamento: nada de informações de pacientes ou clínicas.
// Atribuir um responsável no cadastro exige occurrence.manage.
query ocorrencias verb=POST {
  api_group = "Maintenance"
  auth = "user"

  input {
    int equipamento_id
    text descricao_tecnica filters=trim
    enum severidade {
      values = ["low", "medium", "high", "critical"]
    }

    timestamp? relatada_em?
    int? responsavel_id?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "occurrence.report"}
    }

    precondition ($input.descricao_tecnica != "") {
      error_type = "inputerror"
      error = "descricao_tecnica is required."
    }

    var $relatada_em {
      value = $input.relatada_em ?? now
    }

    // Só valida a data informada pelo cliente: o padrão (now) nunca está no futuro (ver manutencoes_iniciar_POST)
    precondition ($input.relatada_em == null || $input.relatada_em <= now) {
      error_type = "inputerror"
      error = "relatada_em cannot be in the future."
    }

    conditional {
      if ($input.responsavel_id != null) {
        function.run "hhm/require_permission" {
          input = {user_id: $auth.id, permission: "occurrence.manage"}
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

        conditional {
          if ($input.responsavel_id != null) {
            function.run "hhm/require_assignable_user" {
              input = {user_id: $input.responsavel_id, area: "occurrence"}
            }
          }
        }

        db.add ocorrencias {
          data = {
            equipamento_id   : $input.equipamento_id
            relatada_em      : $relatada_em
            descricao_tecnica: $input.descricao_tecnica
            severidade       : $input.severidade
            status           : "open"
            relatada_por     : $auth.id
            responsavel_id   : $input.responsavel_id
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "ocorrencia.reported"
            entidade   : "ocorrencias"
            registro_id: $item.id
            depois     : $item
          }
        }
      }
    }
  }

  response = $item|set:"equipamento":$equip.nome
  guid = "eCnJpCE1_9JOwkXFHC0tl56wu9E"
}
