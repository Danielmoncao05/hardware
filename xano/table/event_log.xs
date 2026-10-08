// Guarda os logs de atividades e eventos dos usuários no aplicativo.
table event_log {
  auth = false

  schema {
    int id
    timestamp created_at?=now
  
    // Referência ao usuário que executou a ação.
    int user_id? {
      table = "user"
    }
  
    // Descrição da ação executada pelo usuário (ex.: 'login', 'created_invoice', 'updated_profile').
    text action? filters=trim
  
    // Dados adicionais do evento, como IDs de recursos, valores antigos/novos ou outras informações de contexto.
    // Eventos de auditoria do domínio (hhm/audit) guardam {entidade, registro_id, antes, depois}. Nunca guarde credenciais aqui.
    json metadata?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "user_id", op: "asc"}, {name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "action", op: "asc"}]}
    {type: "gin", field: [{name: "metadata", op: "jsonb_path_op"}]}
  ]

  tags = ["xano:quick-start"]
  guid = "NFhTG3e5QiYUzRTNxmJENZROD7E"
}