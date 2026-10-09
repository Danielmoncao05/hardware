// Painel operacional (reports.read). Todos os números são calculados a partir dos registros gravados, no momento
// da requisição e, quando localizacao_id é informado, só com os equipamentos daquela localização (e trabalhos/ocorrências
// desses equipamentos).
//  - totais de equipamentos por status (ativos = todos menos os descomissionados, que são informados à parte)
//  - totais de equipamentos ativos por categoria
//  - preventivas: atrasadas e previstas dentro de janela_dias (só planejadas; concluídas/canceladas ficam de fora)
//  - ocorrências abertas e em andamento por severidade e status
//  - manutenções concluídas nos últimos atividade_dias dias
//  - equipamentos ativos por localização direta, ocorrências abertas/em andamento mais recentes e equipamentos
//    críticos (fora de serviço ou com ocorrência crítica aberta/em andamento, mesma regra de GET alertas)
// As listas não usam paginação (a consulta paginada devolvia lista vazia no Xano, ver users GET); os totais são a
// contagem das listas e o app limita quantos itens mostra.
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

    // Equipamentos por status
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

    // Equipamentos ativos por categoria
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

    // Preventivas previstas e atrasadas
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

      return = {type: "list"}
    } as $atrasadas

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
      }

      where = $db.manutencoes.tipo == "preventive" && $db.manutencoes.status == "planned" && $db.manutencoes.data_planejada >= $hoje && $db.manutencoes.data_planejada <= $limite && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {data_planejada: "asc"}
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        localizacao      : $db.localizacoes.nome
      }

      return = {type: "list"}
    } as $proximas

    // Equipamentos ativos por localização direta (só as localizações com algum equipamento)
    db.query localizacoes {
      sort = {nome: "asc"}
      output = ["id", "nome"]
      return = {type: "list"}
    } as $localizacoes

    var $por_localizacao {
      value = []
    }

    foreach ($localizacoes) {
      each as $loc {
        db.query equipamentos {
          where = $db.equipamentos.localizacao_id == $loc.id && $db.equipamentos.status != "decommissioned" && $db.equipamentos.localizacao_id ==? $input.localizacao_id
          return = {type: "count"}
        } as $n

        conditional {
          if ($n > 0) {
            var.update $por_localizacao {
              value = $por_localizacao|push:{localizacao_id: $loc.id, localizacao: $loc.nome, total: $n}
            }
          }
        }
      }
    }

    // Ocorrências abertas e em andamento, mais recentes primeiro
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

      // O status do equipamento não vai no eval: com a coluna status da ocorrência no output, o Xano não o
      // encontrava ("Unable to locate var: oc.equipamento_status"); descomissionados saem pelo where
      where = ($db.ocorrencias.status == "open" || $db.ocorrencias.status == "in_progress") && $db.equipamentos.status != "decommissioned" && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {relatada_em: "desc"}
      output = ["id", "equipamento_id", "severidade", "status", "descricao_tecnica", "relatada_em"]
      eval = {
        equipamento      : $db.equipamentos.nome
        numero_patrimonio: $db.equipamentos.numero_patrimonio
        localizacao      : $db.localizacoes.nome
      }

      return = {type: "list"}
    } as $ocorrencias_recentes

    // Equipamentos críticos: um item por equipamento, com a ocorrência crítica mais recente quando houver.
    // Só campos diretos das tabelas: dentro de um laço o Xano não enxerga os campos de eval (vinham vazios e o
    // painel mostrava "0" no lugar do equipamento). Nome e patrimônio vêm de equipamentos; a localização, da lista
    // $localizacoes já buscada.
    var $critica_por_equip {
      value = {}
    }

    var $ids_criticos {
      value = [0]
    }

    foreach ($ocorrencias_recentes) {
      each as $oc {
        var $k {
          value = $oc.equipamento_id|to_text
        }

        conditional {
          if ($oc.severidade == "critical" && ($critica_por_equip|get:$k) == null) {
            var.update $critica_por_equip {
              value = $critica_por_equip|set:$k:{ocorrencia_id: $oc.id, descricao_tecnica: $oc.descricao_tecnica, ocorrencia_status: $oc.status}
            }

            var.update $ids_criticos {
              value = $ids_criticos|push:$oc.equipamento_id
            }
          }
        }
      }
    }

    db.query equipamentos {
      where = ($db.equipamentos.id in $ids_criticos || $db.equipamentos.status == "out_of_service") && $db.equipamentos.status != "decommissioned" && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {nome: "asc"}
      output = ["id", "nome", "numero_patrimonio", "status", "localizacao_id"]
      return = {type: "list"}
    } as $equip_criticos

    var $nome_localizacao {
      value = {}
    }

    foreach ($localizacoes) {
      each as $loc {
        var $k_loc {
          value = $loc.id|to_text
        }

        var.update $nome_localizacao {
          value = $nome_localizacao|set:$k_loc:$loc.nome
        }
      }
    }

    var $criticos {
      value = []
    }

    foreach ($equip_criticos) {
      each as $eq {
        // Chaves em variáveis: get com expressão entre parênteses devolvia o objeto inteiro (o painel recebia o
        // índice de localizações no lugar do nome e quebrava)
        var $k_equip {
          value = $eq.id|to_text
        }

        var $k_loc {
          value = $eq.localizacao_id|to_text
        }

        var $occ {
          value = ($critica_por_equip|get:$k_equip) ?? {ocorrencia_id: null, descricao_tecnica: null, ocorrencia_status: null}
        }

        var.update $criticos {
          value = $criticos|push:{
            equipamento_id   : $eq.id
            equipamento      : $eq.nome
            numero_patrimonio: $eq.numero_patrimonio
            localizacao      : $nome_localizacao|get:$k_loc
            status           : $eq.status
            ocorrencia_id    : $occ.ocorrencia_id
            descricao_tecnica: $occ.descricao_tecnica
            ocorrencia_status: $occ.ocorrencia_status
          }
        }
      }
    }

    // Ocorrências abertas por severidade e status (open / in_progress), contadas na lista $ocorrencias_recentes já
    // buscada acima (mesmo filtro), em vez de 8 consultas de contagem
    var $ocorrencias {
      value = {
        critical: {open: 0, in_progress: 0}
        high    : {open: 0, in_progress: 0}
        medium  : {open: 0, in_progress: 0}
        low     : {open: 0, in_progress: 0}
      }
    }

    var $ocorrencias_por_status {
      value = {open: 0, in_progress: 0}
    }

    var $ocorrencias_total {
      value = $ocorrencias_recentes|count
    }

    foreach ($ocorrencias_recentes) {
      each as $oc {
        var $sev_atual {
          value = $ocorrencias|get:$oc.severidade
        }

        var.update $ocorrencias {
          value = $ocorrencias|set:$oc.severidade:($sev_atual|set:$oc.status:(($sev_atual|get:$oc.status) + 1))
        }

        var.update $ocorrencias_por_status {
          value = $ocorrencias_por_status|set:$oc.status:(($ocorrencias_por_status|get:$oc.status) + 1)
        }
      }
    }

    // Atividade de manutenção recente
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

      return = {type: "list"}
    } as $recentes
  }

  response = {
    filtros               : {localizacao_id: $input.localizacao_id, janela_dias: $input.janela_dias, atividade_dias: $input.atividade_dias}
    equipamentos_ativos   : $por_status.operational + $por_status.under_maintenance + $por_status.out_of_service
    por_status            : $por_status
    por_categoria         : $por_categoria
    por_localizacao       : $por_localizacao
    preventivas_atrasadas : {total: $atrasadas|count, itens: $atrasadas}
    preventivas_proximas  : {total: $proximas|count, itens: $proximas}
    ocorrencias_abertas   : {total: $ocorrencias_total, por_status: $ocorrencias_por_status, por_severidade: $ocorrencias}
    ocorrencias_recentes  : $ocorrencias_recentes
    criticos              : $criticos
    manutencoes_recentes  : {total: $recentes|count, itens: $recentes}
  }
  guid = "ET9YfSEdH330FqZwMm6TQD_lFbI"
}
