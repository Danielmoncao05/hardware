// Modelos de equipamento. Cada modelo pertence a exatamente um fabricante e uma categoria;
// o equipamento deriva fabricante e categoria pelo modelo.
table modelos {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text nome filters=trim
    int fabricante_id {
      table = "fabricantes"
    }

    int categoria_id {
      table = "categorias"
    }

    text? codigo? filters=trim
    text? observacoes? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "fabricante_id", op: "asc"}, {name: "categoria_id", op: "asc"}, {name: "nome", op: "asc"}]}
    {type: "btree", field: [{name: "categoria_id", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  guid = "wNZxCFmClOVJNSpSBRkPGvSCoEU"
}
