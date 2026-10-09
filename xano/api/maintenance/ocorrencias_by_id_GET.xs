// Detalhe da ocorrência com os nomes de quem relatou e do responsável e a manutenção corretiva vinculada
// (operational.read).
query "ocorrencias/{ocorrencia_id}" verb=GET {
  api_group = "Maintenance"
  auth = "user"

  input {
    int ocorrencia_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    db.get ocorrencias {
      field_name = "id"
      field_value = $input.ocorrencia_id
    } as $item

    precondition ($item != null) {
      error_type = "notfound"
      error = "Occurrence not found."
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $item.equipamento_id
      output = ["id", "nome", "numero_patrimonio", "status", "localizacao_id"]
    } as $equip

    db.get user {
      field_name = "id"
      field_value = $item.relatada_por
      output = ["id", "name"]
    } as $relator

    // Responsável é opcional: db.get com field_value nulo falha ("Missing param: field_value")
    var $responsavel {
      value = null
    }

    conditional {
      if ($item.responsavel_id != null) {
        db.get user {
          field_name = "id"
          field_value = $item.responsavel_id
          output = ["id", "name"]
        } as $resp

        var.update $responsavel {
          value = $resp
        }
      }
    }

    db.query manutencoes {
      where = $db.manutencoes.ocorrencia_id == $input.ocorrencia_id
      sort = {data_planejada: "asc"}
      output = ["id", "tipo", "status", "data_planejada", "concluida_em", "responsavel_id", "descricao"]
      return = {type: "list"}
    } as $manutencoes
  }

  response = $item
    |set:"equipamento":$equip
    |set:"relatada_por_nome":$relator.name
    |set:"responsavel":$responsavel.name
    |set:"manutencoes":$manutencoes
    guid = "vMpwCcX0idCZ-U5kKE99w6VtGK8"
}
