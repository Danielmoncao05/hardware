// Relatório de manutenções (reports.read): histórico, previstas ou atrasadas, com equipamento e localização.
// situacao = "overdue" / "upcoming" usam a definição compartilhada de trabalho pendente (painel, lista, relatório): somente
// manutenções PREVENTIVAS planejadas, datadas antes de hoje / de hoje em diante, dentro de de/ate quando informados.
// Sem situacao, tipo filtra todos os registros (histórico).
// formato = "csv" exporta todas as linhas encontradas (até 10.000) com os mesmos filtros.
query "relatorios/manutencoes" verb=GET {
  api_group = "Reports"
  auth = "user"

  input {
    enum? situacao? {
      values = ["upcoming", "overdue"]
    }

    enum? tipo? {
      values = ["preventive", "corrective"]
    }

    enum? status? {
      values = ["planned", "in_progress", "completed", "canceled"]
    }

    int? equipamento_id?
    int? localizacao_id?
    int? responsavel_id?
    date? de?
    date? ate?
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    var $ontem {
      value = now|transform_timestamp:"-1 day"|format_timestamp:"Y-m-d":"UTC"
    }

    var $status {
      value = $input.status
    }

    var $tipo {
      value = $input.situacao != null ? "preventive" : $input.tipo
    }

    var $de {
      value = $input.de
    }

    var $ate {
      value = $input.ate
    }

    conditional {
      if ($input.situacao == "overdue") {
        var.update $status {
          value = "planned"
        }

        conditional {
          if ($ate == null || $ate > $ontem) {
            var.update $ate {
              value = $ontem
            }
          }
        }
      }

      elseif ($input.situacao == "upcoming") {
        var.update $status {
          value = "planned"
        }

        conditional {
          if ($de == null || $de < $hoje) {
            var.update $de {
              value = $hoje
            }
          }
        }
      }
    }

    var $page {
      value = $input.formato == "csv" ? 1 : $input.page
    }

    var $per_page {
      value = $input.formato == "csv" ? 10000 : $input.per_page
    }

    db.query manutencoes {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.manutencoes.equipamento_id == $db.equipamentos.id
        }
        localizacoes: {
          table: "localizacoes"
          where: $db.equipamentos.localizacao_id == $db.localizacoes.id
        }
        user: {
          table: "user"
          where: $db.manutencoes.responsavel_id == $db.user.id
        }
      }

      where = $db.manutencoes.tipo ==? $tipo && $db.manutencoes.status ==? $status && $db.manutencoes.equipamento_id ==? $input.equipamento_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.manutencoes.responsavel_id ==? $input.responsavel_id && $db.manutencoes.data_planejada >=? $de && $db.manutencoes.data_planejada <=? $ate
      sort = {data_planejada: "asc"}
      output = ["id", "tipo", "status", "data_planejada", "iniciada_em", "concluida_em", "descricao", "resumo_execucao", "motivo_cancelamento", "ocorrencia_id"]
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        localizacao      : $db.localizacoes.nome
        responsavel      : $db.user.name
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
              {key: "numero_patrimonio", label: "Número de patrimônio"}
              {key: "equipamento", label: "Equipamento"}
              {key: "localizacao", label: "Localização"}
              {key: "tipo", label: "Tipo"}
              {key: "status", label: "Status"}
              {key: "data_planejada", label: "Data planejada"}
              {key: "iniciada_em", label: "Iniciada em"}
              {key: "concluida_em", label: "Concluída em"}
              {key: "responsavel", label: "Responsável"}
              {key: "descricao", label: "Descrição"}
              {key: "resumo_execucao", label: "Resumo da execução"}
              {key: "motivo_cancelamento", label: "Motivo do cancelamento"}
              {key: "ocorrencia_id", label: "Ocorrência"}
            ]
            linhas : $result
          }
        } as $csv

        util.set_header {
          value = "Content-Type: text/csv; charset=utf-8"
          duplicates = "replace"
        }

        util.set_header {
          value = "Content-Disposition: attachment; filename=\"relatorio_manutencoes.csv\""
          duplicates = "replace"
        }

        return {
          value = $csv
        }
      }
    }
  }

  response = $result
  guid = "SgCT3PW3vUW2ajXhvcVHSfMS1UE"
}
