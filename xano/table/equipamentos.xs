// Equipment inventory. Manufacturer and category are derived through modelo_id, never stored here.
// numero_serie is unique when present; the API stores blank serials as null.
table equipamentos {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text nome filters=trim
    text numero_patrimonio filters=trim
    int modelo_id {
      table = "modelos"
    }

    int localizacao_id {
      table = "localizacoes"
    }

    enum status {
      values = ["operational", "under_maintenance", "out_of_service", "decommissioned"]
    }

    text? numero_serie? filters=trim
    int? ano_fabricacao? filters=min:1900
    date? data_aquisicao?
    decimal? valor_aquisicao? filters=min:0
    int? vida_util_anos? filters=min:1
    text? observacoes? filters=trim
    int? criado_por? {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "numero_patrimonio", op: "asc"}]}
    {type: "btree|unique", field: [{name: "numero_serie", op: "asc"}]}
    {type: "btree", field: [{name: "modelo_id", op: "asc"}]}
    {type: "btree", field: [{name: "localizacao_id", op: "asc"}, {name: "status", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {type: "btree", field: [{name: "nome", op: "asc"}]}
  ]
  guid = "Blw37GvmHqcnuJIHBFUPEOBrJK8"
}
