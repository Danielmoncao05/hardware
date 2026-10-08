// Concessões dos perfis. O Xano exige uma chave primária id, então o par (role_id, permission_id) tem índice único.
table role_permissions {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    int role_id {
      table = "roles"
    }

    int permission_id {
      table = "permissions"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "role_id", op: "asc"}, {name: "permission_id", op: "asc"}]}
    {type: "btree", field: [{name: "permission_id", op: "asc"}]}
  ]
  guid = "QCVt51YswxuvG-2KELz5keSBMUw"
}
