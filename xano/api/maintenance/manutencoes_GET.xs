// Lista de manutenções e listas de trabalho pendente (operational.read).
// As listas de pendentes seguem a definição de trabalho pendente da spec, compartilhada com o painel e o relatório:
// somente manutenções PREVENTIVAS planejadas (tipo é forçado para "preventive"; concluídas/canceladas ficam de fora).
// situacao = "upcoming": datadas de hoje em diante (opcionalmente dentro de janela_dias);
// situacao = "overdue": datadas antes de hoje.
// Sem situacao, todos os estados são listados, com filtros por status/tipo/equipamento/responsável/período.
query manutencoes verb=GET {
  api_group = "Maintenance"
  auth = "user"

  input {
    enum? situacao? {
      values = ["upcoming", "overdue"]
    }

    int? janela_dias? filters=min:1
    enum? tipo? {
      values = ["preventive", "corrective"]
    }

    enum? status? {
      values = ["planned", "in_progress", "completed", "canceled"]
    }

    int? equipamento_id?
    int? responsavel_id?
    int? localizacao_id?
    date? de?
    date? ate?
    bool minhas?=false
    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
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
      if ($input.situacao == "upcoming") {
        var.update $status {
          value = "planned"
        }

        var.update $de {
          value = $hoje
        }

        conditional {
          if ($input.janela_dias != null) {
            var.update $ate {
              value = now|transform_timestamp:("+" ~ $input.janela_dias ~ " days")|format_timestamp:"Y-m-d":"UTC"
            }
          }
        }
      }

      elseif ($input.situacao == "overdue") {
        var.update $status {
          value = "planned"
        }

        var.update $ate {
          value = now|transform_timestamp:"-1 day"|format_timestamp:"Y-m-d":"UTC"
        }
      }
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

      where = $db.manutencoes.tipo ==? $tipo && $db.manutencoes.status ==? $status && $db.manutencoes.equipamento_id ==? $input.equipamento_id && $db.manutencoes.responsavel_id ==? $responsavel && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.manutencoes.data_planejada >=? $de && $db.manutencoes.data_planejada <=? $ate
      sort = {data_planejada: "asc"}
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        localizacao_id   : $db.equipamentos.localizacao_id
        localizacao      : $db.localizacoes.nome
        responsavel      : $db.user.name
      }

      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $items
  }

  response = $items
  guid = "6KNEaOkYoFlsWvcDMCjmKJCqFFs"
}
