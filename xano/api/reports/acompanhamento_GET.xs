// Acompanhamento por equipamento (reports.read): uma linha por equipamento ativo com a saúde calculada no momento
// da requisição a partir dos registros gravados (nada é gravado em equipamentos).
//  - critico: status "out_of_service" ou alguma ocorrência crítica aberta/em andamento
//  - atencao: (não crítico) status "under_maintenance", alguma ocorrência aberta/em andamento ou preventiva atrasada
//  - ok:      o restante (operacional, sem ocorrências abertas e sem preventivas atrasadas)
// resumo traz os totais por saúde com os mesmos filtros (exceto o próprio filtro de saúde).
// Preventiva atrasada = planejada com data_planejada até ontem, como no painel operacional.
query acompanhamento verb=GET {
  api_group = "Reports"
  auth = "user"

  input {
    text? q? filters=trim
    int? localizacao_id?
    int? categoria_id?
    enum? status? {
      values = ["operational", "under_maintenance", "out_of_service"]
    }

    enum? saude? {
      values = ["critico", "atencao", "ok"]
    }

    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "reports.read"}
    }

    var $ontem {
      value = now|transform_timestamp:"-1 day"|format_timestamp:"Y-m-d":"UTC"
    }

    var $pattern {
      value = "%" ~ ($input.q ?? "") ~ "%"
    }

    // Ocorrências abertas e em andamento dos equipamentos ativos (na localização, quando filtrada)
    db.query ocorrencias {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.ocorrencias.equipamento_id == $db.equipamentos.id
        }
      }

      where = ($db.ocorrencias.status == "open" || $db.ocorrencias.status == "in_progress") && $db.equipamentos.status != "decommissioned" && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      output = ["equipamento_id", "severidade"]
      return = {type: "list"}
    } as $ocorrencias

    // Preventivas atrasadas, da mais antiga para a mais recente
    db.query manutencoes {
      join = {
        equipamentos: {
          table: "equipamentos"
          where: $db.manutencoes.equipamento_id == $db.equipamentos.id
        }
      }

      where = $db.manutencoes.tipo == "preventive" && $db.manutencoes.status == "planned" && $db.manutencoes.data_planejada <= $ontem && $db.equipamentos.status != "decommissioned" && $db.equipamentos.localizacao_id ==? $input.localizacao_id
      sort = {data_planejada: "asc"}
      output = ["equipamento_id", "data_planejada"]
      return = {type: "list"}
    } as $atrasadas

    // Índices por equipamento (chave = id em texto). As listas de ids começam com 0 (nenhum equipamento tem
    // id 0) para os filtros "in" / "not in" nunca receberem uma lista vazia.
    var $ocorr_por_equip {
      value = {}
    }

    var $atraso_por_equip {
      value = {}
    }

    var $criticos_ids {
      value = [0]
    }

    var $problema_ids {
      value = [0]
    }

    foreach ($ocorrencias) {
      each as $oc {
        var $k {
          value = $oc.equipamento_id|to_text
        }

        var $atual {
          value = ($ocorr_por_equip|get:$k) ?? {abertas: 0, rank: 0, severidade: null}
        }

        var $rank {
          value = $oc.severidade == "critical" ? 4 : ($oc.severidade == "high" ? 3 : ($oc.severidade == "medium" ? 2 : 1))
        }

        var.update $ocorr_por_equip {
          value = $ocorr_por_equip|set:$k:{abertas: $atual.abertas + 1, rank: $rank > $atual.rank ? $rank : $atual.rank, severidade: $rank > $atual.rank ? $oc.severidade : $atual.severidade}
        }

        var.update $problema_ids {
          value = $problema_ids|push:$oc.equipamento_id
        }

        conditional {
          if ($oc.severidade == "critical") {
            var.update $criticos_ids {
              value = $criticos_ids|push:$oc.equipamento_id
            }
          }
        }
      }
    }

    foreach ($atrasadas) {
      each as $mt {
        var $k {
          value = $mt.equipamento_id|to_text
        }

        var $atual {
          value = ($atraso_por_equip|get:$k) ?? {total: 0, mais_antiga: $mt.data_planejada}
        }

        var.update $atraso_por_equip {
          value = $atraso_por_equip|set:$k:{total: $atual.total + 1, mais_antiga: $atual.mais_antiga}
        }

        var.update $problema_ids {
          value = $problema_ids|push:$mt.equipamento_id
        }
      }
    }

    var.update $criticos_ids {
      value = $criticos_ids|unique
    }

    var.update $problema_ids {
      value = $problema_ids|unique
    }

    // Cada faixa de saúde vira o mesmo filtro estático:
    //   status in status_in && id not in excluir && (status in status_ou || id in ids_ou)
    var $ativos {
      value = ["operational", "under_maintenance", "out_of_service"]
    }

    var $faixas {
      value = {
        todos  : {status_in: $ativos, excluir: [0], status_ou: $ativos, ids_ou: [0]}
        critico: {status_in: $ativos, excluir: [0], status_ou: ["out_of_service"], ids_ou: $criticos_ids}
        atencao: {status_in: ["operational", "under_maintenance"], excluir: $criticos_ids, status_ou: ["under_maintenance"], ids_ou: $problema_ids}
        ok     : {status_in: ["operational"], excluir: $problema_ids, status_ou: ["operational"], ids_ou: [0]}
      }
    }

    // Totais por saúde, com os demais filtros
    var $resumo {
      value = {}
    }

    foreach (["critico", "atencao", "ok"]) {
      each as $faixa {
        var $f {
          value = $faixas|get:$faixa
        }

        db.query equipamentos {
          join = {
            modelos: {
              table: "modelos"
              where: $db.equipamentos.modelo_id == $db.modelos.id
            }
          }

          where = ($db.equipamentos.nome ilike $pattern || $db.equipamentos.numero_patrimonio ilike $pattern || $db.equipamentos.numero_serie ilike $pattern) && $db.modelos.categoria_id ==? $input.categoria_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.equipamentos.status ==? $input.status && $db.equipamentos.status in $f.status_in && $db.equipamentos.id not in $f.excluir && ($db.equipamentos.status in $f.status_ou || $db.equipamentos.id in $f.ids_ou)
          return = {type: "count"}
        } as $n

        var.update $resumo {
          value = $resumo|set:$faixa:$n
        }
      }
    }

    var $filtro {
      value = $faixas|get:($input.saude ?? "todos")
    }

    // Página pedida, em ordem de nome. O Xano às vezes ignora o bloco paging e devolve a lista inteira, então a
    // paginação é feita aqui: primeiro os ids de todos os equipamentos encontrados (só o id), depois os dados
    // completos apenas dos ids da página.
    db.query equipamentos {
      join = {
        modelos: {
          table: "modelos"
          where: $db.equipamentos.modelo_id == $db.modelos.id
        }
      }

      where = ($db.equipamentos.nome ilike $pattern || $db.equipamentos.numero_patrimonio ilike $pattern || $db.equipamentos.numero_serie ilike $pattern) && $db.modelos.categoria_id ==? $input.categoria_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.equipamentos.status ==? $input.status && $db.equipamentos.status in $filtro.status_in && $db.equipamentos.id not in $filtro.excluir && ($db.equipamentos.status in $filtro.status_ou || $db.equipamentos.id in $filtro.ids_ou)
      sort = {nome: "asc"}
      output = ["id"]
      return = {type: "list"}
    } as $encontrados

    var $total {
      value = $encontrados|count
    }

    var $inicio {
      value = ($input.page - 1) * $input.per_page
    }

    var $fim {
      value = $inicio + $input.per_page
    }

    var $pagina_ids {
      value = [0]
    }

    var $i {
      value = 0
    }

    foreach ($encontrados) {
      each as $row {
        conditional {
          if ($i >= $inicio && $i < $fim) {
            var.update $pagina_ids {
              value = $pagina_ids|push:$row.id
            }
          }
        }

        math.add $i {
          value = 1
        }
      }
    }

    db.query equipamentos {
      join = {
        modelos: {
          table: "modelos"
          where: $db.equipamentos.modelo_id == $db.modelos.id
        }
        categorias: {
          table: "categorias"
          where: $db.modelos.categoria_id == $db.categorias.id
        }
        localizacoes: {
          table: "localizacoes"
          where: $db.equipamentos.localizacao_id == $db.localizacoes.id
        }
      }

      where = $db.equipamentos.id in $pagina_ids
      sort = {nome: "asc"}
      output = ["id", "nome", "numero_patrimonio", "status"]
      eval = {
        modelo     : $db.modelos.nome
        categoria  : $db.categorias.nome
        localizacao: $db.localizacoes.nome
      }

      return = {type: "list"}
    } as $pagina

    var $linhas {
      value = []
    }

    foreach ($pagina) {
      each as $eq {
        var $k {
          value = $eq.id|to_text
        }

        var $ocs {
          value = ($ocorr_por_equip|get:$k) ?? {abertas: 0, rank: 0, severidade: null}
        }

        var $at {
          value = ($atraso_por_equip|get:$k) ?? {total: 0, mais_antiga: null}
        }

        function.run "hhm/maintenance_dates" {
          input = {equipamento_id: $eq.id}
        } as $datas

        var $saude {
          value = ($eq.status == "out_of_service" || $ocs.rank == 4) ? "critico" : (($eq.status == "under_maintenance" || $ocs.abertas > 0 || $at.total > 0) ? "atencao" : "ok")
        }

        var.update $linhas {
          value = $linhas|push:($eq
            |set:"saude":$saude
            |set:"ocorrencias_abertas":$ocs.abertas
            |set:"maior_severidade":$ocs.severidade
            |set:"preventivas_atrasadas":$at.total
            |set:"atrasada_desde":$at.mais_antiga
            |set:"ultima_manutencao":$datas.ultima_manutencao
            |set:"proxima_manutencao":$datas.proxima_manutencao
          )
        }
      }
    }
  }

  response = {
    resumo      : $resumo
    items       : $linhas
    itemsTotal  : $total
    nextPage    : $fim < $total ? $input.page + 1 : null
    curPage     : $input.page
  }
  guid = "pTWvg6bfykD8OB9csEv6zBzaTJY"
}
