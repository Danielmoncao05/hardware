// Operational dashboard (reports.read). Every figure is computed from the persisted records at request
// time and, when localizacao_id is given, only from equipment at that location (and work/occurrences
// on that equipment).
//  - equipment totals by status (active = all but decommissioned, which is reported separately)
//  - active equipment totals by category
//  - preventive work: overdue and due within janela_dias (planned only; completed/canceled excluded)
//  - open and in-progress occurrences by severity and status
//  - maintenance completed in the last atividade_dias days
query dashboard verb=GET {
  api_group = "Reports"
  auth = "user"

  input {
    int? localizacao_id?
    int janela_dias?=30 filters=min:1|max:365
    int atividade_dias?=30 filters=min:1|max:365
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

    var $limite {
      value = now|transform_timestamp:("+" ~ $input.janela_dias ~ " days")|format_timestamp:"Y-m-d":"UTC"
    }

    var $atividade_desde {
      value = now|transform_timestamp:("-" ~ $input.atividade_dias ~ " days")
    }

    // Equipment by status
    var $por_status {
      value = {}
    }

    foreach (["operational", "under_maintenance", "out_of_service", "decommissioned"]) {
      each as $st {
        db.query equipamentos {
          where = $db.equipamentos.status == $st && $db.equipamentos.localizacao_id ==? $input.localizacao_id
          return = {type: "count"}
        } as $n

        var.update $por_status {
          value = $por_status|set:$st:$n
        }
      }
    }

    // Active equipment by category
    db.query categorias {
      sort = {nome: "asc"}
      output = ["id", "nome", "ativo"]
      return = {type: "list"}
    } as $categorias

    var $por_categoria {
      value = []
    }

    foreach ($categorias) {
      each as $cat {
        db.query equipamentos {
          join = {
            modelos: {
              table: "modelos"
              where: $db.equipamentos.modelo_id == $db.modelos.id
            }
          }

          where = $db.modelos.categoria_id == $cat.id && $db.equipamentos.status != "decommissioned" && $db.equipamentos.localizacao_id ==? $input.localizacao_id
          return = {type: "count"}
        } as $n

        var.update $por_categoria {
          value = $por_categoria|push:{categoria_id: $cat.id, categoria: $cat.nome, total: $n}
        }
      }
    }

    // Preventive work due and overdue
    db.query manutencoes {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.manutencoes.equipamento_id == $db.equipamentos.id
        }
      }

      where = $db.manutencoes.tipo == "preventive" && $db.manutencoes.status == "planned" && $db.manutencoes.data_planejada <= $ontem && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {data_planejada: "asc"}
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
      }

      return = {
        type  : "list"
        paging: {page: 1, per_page: 10, totals: true}
      }
    } as $atrasadas

    db.query manutencoes {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.manutencoes.equipamento_id == $db.equipamentos.id
        }
      }

      where = $db.manutencoes.tipo == "preventive" && $db.manutencoes.status == "planned" && $db.manutencoes.data_planejada >= $hoje && $db.manutencoes.data_planejada <= $limite && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {data_planejada: "asc"}
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
      }

      return = {
        type  : "list"
        paging: {page: 1, per_page: 10, totals: true}
      }
    } as $proximas

    // Open occurrences by severity and status (open / in_progress)
    var $ocorrencias {
      value = {}
    }

    var $ocorrencias_por_status {
      value = {open: 0, in_progress: 0}
    }

    var $ocorrencias_total {
      value = 0
    }

    foreach (["critical", "high", "medium", "low"]) {
      each as $sev {
        var $por_status_sev {
          value = {}
        }

        foreach (["open", "in_progress"]) {
          each as $st {
            db.query ocorrencias {
              join = {
                equipamentos: {
                  table: "equipamentos"
                  where: $db.ocorrencias.equipamento_id == $db.equipamentos.id
                }
              }

              where = $db.ocorrencias.severidade == $sev && $db.ocorrencias.status == $st && $db.equipamentos.localizacao_id ==? $input.localizacao_id
              return = {type: "count"}
            } as $n

            var.update $por_status_sev {
              value = $por_status_sev|set:$st:$n
            }

            var.update $ocorrencias_por_status {
              value = $ocorrencias_por_status|set:$st:(($ocorrencias_por_status|get:$st) + $n)
            }

            math.add $ocorrencias_total {
              value = $n
            }
          }
        }

        var.update $ocorrencias {
          value = $ocorrencias|set:$sev:$por_status_sev
        }
      }
    }

    // Recent service activity
    db.query manutencoes {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.manutencoes.equipamento_id == $db.equipamentos.id
        }
        user: {
          table: "user"
          where: $db.manutencoes.responsavel_id == $db.user.id
        }
      }

      where = $db.manutencoes.status == "completed" && $db.manutencoes.concluida_em >= $atividade_desde && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {concluida_em: "desc"}
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        responsavel      : $db.user.name
      }

      return = {
        type  : "list"
        paging: {page: 1, per_page: 10, totals: true}
      }
    } as $recentes
  }

  response = {
    filtros               : {localizacao_id: $input.localizacao_id, janela_dias: $input.janela_dias, atividade_dias: $input.atividade_dias}
    equipamentos_ativos   : $por_status.operational + $por_status.under_maintenance + $por_status.out_of_service
    por_status            : $por_status
    por_categoria         : $por_categoria
    preventivas_atrasadas : {total: $atrasadas.itemsTotal, itens: $atrasadas.items}
    preventivas_proximas  : {total: $proximas.itemsTotal, itens: $proximas.items}
    ocorrencias_abertas   : {total: $ocorrencias_total, por_status: $ocorrencias_por_status, por_severidade: $ocorrencias}
    manutencoes_recentes  : {total: $recentes.itemsTotal, itens: $recentes.items}
  }
  guid = "ET9YfSEdH330FqZwMm6TQD_lFbI"
}
