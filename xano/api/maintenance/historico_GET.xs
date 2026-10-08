// Chronological equipment history (operational.read), oldest first, built from the source tables:
// maintenance (all states, including completed and canceled), occurrences (all states), and component
// installation/removal events. Also returns the derived last/next maintenance dates.
// Works for decommissioned equipment; deactivated catalog entries and disabled users still resolve.
query "equipamentos/{equipamento_id}/historico" verb=GET {
  api_group = "Maintenance"
  auth = "user"

  input {
    int equipamento_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
      output = ["id", "nome", "numero_patrimonio", "status"]
    } as $equip

    precondition ($equip != null) {
      error_type = "notfound"
      error = "Equipment not found."
    }

    db.query manutencoes {
      join = {
        user: {
          table: "user"
          where: $db.manutencoes.responsavel_id == $db.user.id
        }
      }

      where = $db.manutencoes.equipamento_id == $input.equipamento_id
      eval = {responsavel: $db.user.name}
      return = {type: "list"}
    } as $manutencoes

    db.query ocorrencias {
      join = {
        user: {
          table: "user"
          where: $db.ocorrencias.relatada_por == $db.user.id
        }
      }

      where = $db.ocorrencias.equipamento_id == $input.equipamento_id
      eval = {relatada_por_nome: $db.user.name}
      return = {type: "list"}
    } as $ocorrencias

    db.query equipamento_componentes {
      join = {
        componentes: {
          table: "componentes"
          where: $db.equipamento_componentes.componente_id == $db.componentes.id
        }
      }

      where = $db.equipamento_componentes.equipamento_id == $input.equipamento_id
      eval = {
        componente: $db.componentes.nome
        tipo      : $db.componentes.tipo
      }

      return = {type: "list"}
    } as $componentes

    var $eventos {
      value = []
    }

    foreach ($manutencoes) {
      each as $m {
        // Date of the event: completion, else start, else the planned date (somente_data marks the last
        // case: a calendar date, which clients must not timezone-convert)
        var $data {
          value = $m.concluida_em ?? ($m.iniciada_em ?? ($m.data_planejada|to_timestamp))
        }

        var.update $eventos {
          value = $eventos|push:{
            data          : $data
            somente_data  : $m.concluida_em == null && $m.iniciada_em == null
            categoria     : "manutencao"
            registro_id   : $m.id
            tipo          : $m.tipo
            status        : $m.status
            data_planejada: $m.data_planejada
            responsavel   : $m.responsavel
            descricao     : $m.descricao
            resumo        : $m.resumo_execucao ?? $m.motivo_cancelamento
            ocorrencia_id : $m.ocorrencia_id
          }
        }
      }
    }

    foreach ($ocorrencias) {
      each as $o {
        var.update $eventos {
          value = $eventos|push:{
            data        : $o.relatada_em
            categoria   : "ocorrencia"
            registro_id : $o.id
            tipo        : $o.severidade
            status      : $o.status
            responsavel : $o.relatada_por_nome
            descricao   : $o.descricao_tecnica
            resumo      : $o.resumo_resolucao ?? $o.motivo_cancelamento
            resolvida_em: $o.resolvida_em
          }
        }
      }
    }

    foreach ($componentes) {
      each as $c {
        var.update $eventos {
          value = $eventos|push:{
            data       : $c.instalado_em ?? $c.created_at
            categoria  : "componente_instalado"
            registro_id: $c.id
            tipo       : $c.tipo
            descricao  : $c.componente
            quantidade : $c.quantidade
            slot       : $c.slot
            resumo     : $c.observacoes
          }
        }

        conditional {
          if ($c.removido_em != null) {
            var.update $eventos {
              value = $eventos|push:{
                data       : $c.removido_em
                categoria  : "componente_removido"
                registro_id: $c.id
                tipo       : $c.tipo
                descricao  : $c.componente
                quantidade : $c.quantidade
                slot       : $c.slot
                resumo     : $c.observacoes
              }
            }
          }
        }
      }
    }

    function.run "hhm/maintenance_dates" {
      input = {equipamento_id: $input.equipamento_id}
    } as $datas
  }

  response = {
    equipamento       : $equip
    ultima_manutencao : $datas.ultima_manutencao
    proxima_manutencao: $datas.proxima_manutencao
    eventos           : $eventos|sort:"data":"number":true
  }
  guid = "DKRnRCk3zR1p-brUBvwYryyAbjg"
}
