// Occurrence queues (operational.read): filter by status, severity, equipment, location, responsible,
// and reported-date range. abertas = true lists open and in-progress occurrences only.
query ocorrencias verb=GET {
  api_group = "Maintenance"
  auth = "user"

  input {
    enum? status? {
      values = ["open", "in_progress", "resolved", "canceled"]
    }

    bool abertas?=false
    enum? severidade? {
      values = ["low", "medium", "high", "critical"]
    }

    int? equipamento_id?
    int? localizacao_id?
    int? responsavel_id?
    bool minhas?=false
    timestamp? de?
    timestamp? ate?
    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    var $responsavel {
      value = $input.responsavel_id
    }

    conditional {
      if ($input.minhas) {
        var.update $responsavel {
          value = $auth.id
        }
      }
    }

    // abertas excludes the two closed states
    var $excluir_1 {
      value = null
    }

    var $excluir_2 {
      value = null
    }

    conditional {
      if ($input.abertas) {
        var.update $excluir_1 {
          value = "resolved"
        }

        var.update $excluir_2 {
          value = "canceled"
        }
      }
    }

    db.query ocorrencias {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.ocorrencias.equipamento_id == $db.equipamentos.id
        }
        localizacoes: {
          table: "localizacoes"
          where: $db.equipamentos.localizacao_id == $db.localizacoes.id
        }
      }

      where = $db.ocorrencias.status ==? $input.status && $db.ocorrencias.status !=? $excluir_1 && $db.ocorrencias.status !=? $excluir_2 && $db.ocorrencias.severidade ==? $input.severidade && $db.ocorrencias.equipamento_id ==? $input.equipamento_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.ocorrencias.responsavel_id ==? $responsavel && $db.ocorrencias.relatada_em >=? $input.de && $db.ocorrencias.relatada_em <=? $input.ate
      sort = {relatada_em: "desc"}
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        localizacao_id   : $db.equipamentos.localizacao_id
        localizacao      : $db.localizacoes.nome
      }

      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $items
  }

  response = $items
  guid = "GA2zdqddnKoUu3vRtbJikUOsuiY"
}
