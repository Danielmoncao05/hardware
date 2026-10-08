// Deriva as datas da última e da próxima manutenção de um equipamento a partir de manutencoes, no momento da leitura.
// Última: maior concluida_em entre os registros concluídos. Próxima: menor data de preventiva planejada de hoje em diante.
// Nenhum dos dois valores é gravado em equipamentos.
function "hhm/maintenance_dates" {
  input {
    int equipamento_id
  }

  stack {
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    db.query manutencoes {
      where = $db.manutencoes.equipamento_id == $input.equipamento_id && $db.manutencoes.status == "completed"
      sort = {concluida_em: "desc"}
      return = {type: "single"}
    } as $ultima

    db.query manutencoes {
      where = $db.manutencoes.equipamento_id == $input.equipamento_id && $db.manutencoes.tipo == "preventive" && $db.manutencoes.status == "planned" && $db.manutencoes.data_planejada >= $hoje
      sort = {data_planejada: "asc"}
      return = {type: "single"}
    } as $proxima

    // Sem registro a consulta devolve null, e ler um campo de null é erro no Xano: só lê quando existe
    var $ultima_manutencao {
      value = null
    }

    var $proxima_manutencao {
      value = null
    }

    conditional {
      if ($ultima != null) {
        var.update $ultima_manutencao {
          value = $ultima.concluida_em
        }
      }
    }

    conditional {
      if ($proxima != null) {
        var.update $proxima_manutencao {
          value = $proxima.data_planejada
        }
      }
    }
  }

  response = {
    ultima_manutencao: $ultima_manutencao
    proxima_manutencao: $proxima_manutencao
  }
  guid = "lhU7ZlVecEo6of-F9FxLAKAimpQ"
}
