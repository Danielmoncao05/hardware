// Derives an equipment item's last and next maintenance dates from manutencoes at read time.
// Last: latest concluida_em among completed records. Next: earliest planned preventive date from today on.
// Neither value is ever stored on equipamentos.
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
  }

  response = {
    ultima_manutencao: $ultima.concluida_em
    proxima_manutencao: $proxima.data_planejada
  }
  guid = "lhU7ZlVecEo6of-F9FxLAKAimpQ"
}
