// Perfis de acesso: administrator, asset_manager, technician, viewer.
table roles {
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
  ]
  guid = "48j8yvV5q_Xhmjsovf6A-bq9Ch8"
}
