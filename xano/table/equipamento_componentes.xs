// N:N assignment of catalog components to equipment. Each installed instance has its own id;
// removal is recorded in removido_em rather than deleting the row.
table equipamento_componentes {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    int equipamento_id {
      table = "equipamentos"
    }

    int componente_id {
      table = "componentes"
    }

    int quantidade?=1 filters=min:1
    text? slot? filters=trim
    text? numero_serie_instalado? filters=trim
    timestamp? instalado_em?
    timestamp? removido_em?
    text? observacoes? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "equipamento_id", op: "asc"}, {name: "removido_em", op: "asc"}]}
    {type: "btree", field: [{name: "componente_id", op: "asc"}]}
  ]
  guid = "YbIGVB6dQ6FPgnBfnxAdbq92y7Q"
}
