// Relatório de ocorrências (reports.read): ocorrências abertas ou resolvidas, com equipamento e localização.
// abertas = true limita às abertas e em andamento; de/ate filtram a data do relato.
// formato = "csv" exporta todas as linhas encontradas (até 10.000) com os mesmos filtros.
query "relatorios/ocorrencias" verb=GET {
  api_group = "Reports"
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
    timestamp? de?
    timestamp? ate?
    enum formato?="json" {
      values = ["json", "csv"]
    }

    int page?=1 filters=min:1
    int per_page?=50 filters=min:1|max:200
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "reports.read"}
    }

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

    var $page {
      value = $input.formato == "csv" ? 1 : $input.page
    }

    var $per_page {
      value = $input.formato == "csv" ? 10000 : $input.per_page
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
        user: {
          table: "user"
          where: $db.ocorrencias.relatada_por == $db.user.id
        }
      }

      where = $db.ocorrencias.status ==? $input.status && $db.ocorrencias.status !=? $excluir_1 && $db.ocorrencias.status !=? $excluir_2 && $db.ocorrencias.severidade ==? $input.severidade && $db.ocorrencias.equipamento_id ==? $input.equipamento_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.ocorrencias.relatada_em >=? $input.de && $db.ocorrencias.relatada_em <=? $input.ate
      sort = {relatada_em: "desc"}
      output = ["id", "relatada_em", "severidade", "status", "descricao_tecnica", "resolvida_em", "resumo_resolucao", "motivo_cancelamento"]
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        localizacao      : $db.localizacoes.nome
        relatada_por     : $db.user.name
      }

      // Sem paginação: a consulta paginada devolvia lista vazia no Xano (ver users GET); o app recorta a página
      return = {type: "list"}
    } as $result

    conditional {
      if ($input.formato == "csv") {
        function.run "hhm/to_csv" {
          input = {
            colunas: [
              {key: "id", label: "ID"}
              {key: "relatada_em", label: "Relatada em"}
              {key: "numero_patrimonio", label: "Número de patrimônio"}
              {key: "equipamento", label: "Equipamento"}
              {key: "localizacao", label: "Localização"}
              {key: "severidade", label: "Severidade"}
              {key: "status", label: "Status"}
              {key: "relatada_por", label: "Relatada por"}
              {key: "descricao_tecnica", label: "Descrição técnica"}
              {key: "resolvida_em", label: "Resolvida em"}
              {key: "resumo_resolucao", label: "Resumo da resolução"}
              {key: "motivo_cancelamento", label: "Motivo do cancelamento"}
            ]
            linhas : $result
          }
        } as $csv

        util.set_header {
          value = "Content-Type: text/csv; charset=utf-8"
          duplicates = "replace"
        }

        util.set_header {
          value = "Content-Disposition: attachment; filename=\"relatorio_ocorrencias.csv\""
          duplicates = "replace"
        }

        return {
          value = $csv
        }
      }
    }
  }

  response = $result
  guid = "HwcnM6GsyPHrgHZ8zS17yJ8SmZI"
}
