// Equipamentos ativos que precisam de atenção agora (reports.read), para os avisos da interface. Mesmas regras de
// saúde de GET acompanhamento, mas só as faixas "critico" e "atencao" e sem datas de manutenção, para ser leve o
// bastante para consultas periódicas:
//  - critico: status "out_of_service" ou alguma ocorrência crítica aberta/em andamento
//  - atencao: status "under_maintenance", alguma ocorrência aberta/em andamento ou preventiva atrasada
query alertas verb=GET {
  api_group = "Reports"
  auth = "user"

  input {
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "reports.read"}
    }

    var $ontem {
      value = now|transform_timestamp:"-1 day"|format_timestamp:"Y-m-d":"UTC"
    }

    db.query ocorrencias {
      where = $db.ocorrencias.status == "open" || $db.ocorrencias.status == "in_progress"
      output = ["equipamento_id", "severidade"]
      return = {type: "list"}
    } as $ocorrencias

    db.query manutencoes {
      where = $db.manutencoes.tipo == "preventive" && $db.manutencoes.status == "planned" && $db.manutencoes.data_planejada <= $ontem
      output = ["equipamento_id"]
      return = {type: "list"}
    } as $atrasadas

    db.query equipamentos {
      where = $db.equipamentos.status == "under_maintenance" || $db.equipamentos.status == "out_of_service"
      output = ["id"]
      return = {type: "list"}
    } as $fora_de_operacao

    // Índices por equipamento (chave = id em texto); a lista de ids começa com 0 para nunca ficar vazia
    var $ocorr_por_equip {
      value = {}
    }

    var $atraso_por_equip {
      value = {}
    }

    var $ids {
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

        var.update $ids {
          value = $ids|push:$oc.equipamento_id
        }
      }
    }

    foreach ($atrasadas) {
      each as $mt {
        var $k {
          value = $mt.equipamento_id|to_text
        }

        var.update $atraso_por_equip {
          value = $atraso_por_equip|set:$k:((($atraso_por_equip|get:$k) ?? 0) + 1)
        }

        var.update $ids {
          value = $ids|push:$mt.equipamento_id
        }
      }
    }

    foreach ($fora_de_operacao) {
      each as $eq {
        var.update $ids {
          value = $ids|push:$eq.id
        }
      }
    }

    var.update $ids {
      value = $ids|unique
    }

    db.query equipamentos {
      join = {
        localizacoes: {
          table: "localizacoes"
          where: $db.equipamentos.localizacao_id == $db.localizacoes.id
        }
      }

      where = $db.equipamentos.id in $ids && $db.equipamentos.status != "decommissioned"
      sort = {nome: "asc"}
      output = ["id", "nome", "numero_patrimonio", "status"]
      eval = {
        localizacao: $db.localizacoes.nome
      }

      return = {type: "list"}
    } as $equipamentos

    var $linhas {
      value = []
    }

    foreach ($equipamentos) {
      each as $eq {
        var $k {
          value = $eq.id|to_text
        }

        var $ocs {
          value = ($ocorr_por_equip|get:$k) ?? {abertas: 0, rank: 0, severidade: null}
        }

        var $atrasos {
          value = ($atraso_por_equip|get:$k) ?? 0
        }

        var.update $linhas {
          value = $linhas|push:($eq
            |set:"saude":(($eq.status == "out_of_service" || $ocs.rank == 4) ? "critico" : "atencao")
            |set:"ocorrencias_abertas":$ocs.abertas
            |set:"maior_severidade":$ocs.severidade
            |set:"preventivas_atrasadas":$atrasos
          )
        }
      }
    }
  }

  response = $linhas
  guid = "qMG36A9YKQdPUcjXaahR9YcL6UE"
}
