// Equipment categories (seeded with the 12 required categories).
table categorias {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text nome filters=trim
    text? descricao? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  guid = "9Ab7cUs1LBpM4WBAf7Sc-N8BCDU"
}
