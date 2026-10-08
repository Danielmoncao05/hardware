// Hardware component catalog. One catalog entry can be installed on many equipment items.
table componentes {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text nome filters=trim
    enum tipo {
      values = [
        "processor"
        "memory_ram"
        "storage"
        "motherboard"
        "power_supply"
        "sensor"
        "display"
        "battery"
        "electronic_module"
        "communication_board"
        "other"
      ]
    }

    int? fabricante_id? {
      table = "fabricantes"
    }

    text? modelo_componente? filters=trim
    text? numero_peca? filters=trim
    text? especificacoes? filters=trim
    text? observacoes? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "tipo", op: "asc"}]}
    {type: "btree", field: [{name: "fabricante_id", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  guid = "K_fwJ9mtAlLQJyAWAFohYbKTdnU"
}
