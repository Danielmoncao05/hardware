// Manutenção preventiva e corretiva. As datas da última/próxima manutenção dos equipamentos são derivadas
// desta tabela no momento da leitura e nunca gravadas em equipamentos.
table manutencoes {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    int equipamento_id {
      table = "equipamentos"
    }

    enum tipo {
      values = ["preventive", "corrective"]
    }

    date data_planejada
    text descricao filters=trim
    enum status?="planned" {
      values = ["planned", "in_progress", "completed", "canceled"]
    }

    int responsavel_id {
      table = "user"
    }

    int criado_por {
      table = "user"
    }

    timestamp? iniciada_em?
    timestamp? concluida_em?
    text? resumo_execucao? filters=trim
    json? checklist?
    text? motivo_cancelamento? filters=trim
    int? intervalo_recorrencia_dias? filters=min:1
    int? ocorrencia_id? {
      table = "ocorrencias"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "equipamento_id", op: "asc"}, {name: "status", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}, {name: "data_planejada", op: "asc"}]}
    {type: "btree", field: [{name: "equipamento_id", op: "asc"}, {name: "concluida_em", op: "desc"}]}
    {type: "btree", field: [{name: "responsavel_id", op: "asc"}]}
    {type: "btree", field: [{name: "ocorrencia_id", op: "asc"}]}
  ]
  guid = "cyl7jxUiSo58fnvrtad54eYKNHo"
}
