// Localizações físicas, opcionalmente aninhadas por parent_id (ex.: prédio > andar > sala).
table localizacoes {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    timestamp? updated_at?
    text nome filters=trim
    int? parent_id? {
      table = "localizacoes"
    }

    text? tipo? filters=trim
    text? descricao? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "parent_id", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  guid = "2Ruxy-zVt2pFVS4iV5ZrY_FwoHQ"
}
