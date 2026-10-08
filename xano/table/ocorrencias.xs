// Technical occurrences (equipment malfunctions/observations). Never holds patient or clinical data.
table ocorrencias {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    int equipamento_id {
      table = "equipamentos"
    }

    timestamp relatada_em
    text descricao_tecnica filters=trim
    enum severidade {
      values = ["low", "medium", "high", "critical"]
    }

    enum status?="open" {
      values = ["open", "in_progress", "resolved", "canceled"]
    }

    int relatada_por {
      table = "user"
    }

    int? responsavel_id? {
      table = "user"
    }

    timestamp? resolvida_em?
    text? resumo_resolucao? filters=trim
    text? motivo_cancelamento? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "equipamento_id", op: "asc"}, {name: "relatada_em", op: "desc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}, {name: "severidade", op: "asc"}]}
    {type: "btree", field: [{name: "responsavel_id", op: "asc"}]}
  ]
  guid = "kpujd6-kqOogRdPY5MyTJcDGsj4"
}
