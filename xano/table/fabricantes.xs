// Equipment and component manufacturers. Deactivate instead of deleting once referenced.
table fabricantes {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text nome filters=trim
    text? site? filters=trim
    text? contato_suporte? filters=trim
    text? observacoes? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  guid = "EHCBUl8f6fL_yF9dwrCatoiYAik"
}
