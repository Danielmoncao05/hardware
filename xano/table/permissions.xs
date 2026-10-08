// Explicit permission keys checked by every protected API operation.
table permissions {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text chave filters=trim
    text descricao filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "chave", op: "asc"}]}
  ]
  guid = "UT-09nmIxoG39-ZW4hcsUbIqLBs"
}
