// Busca os logs de eventos do usuário autenticado. O histórico de auditoria é restrito a quem tem audit.read
// (administradores); use o grupo de auditoria para consultar com filtros entre usuários.
query "logs/user/my_events" verb=GET {
  api_group = "Event Logs"
  auth = "user"

  input {
    int page?=1 filters=min:1
    int per_page?=50 filters=min:1|max:200
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "audit.read"}
    }

    // Busca os logs de eventos do usuário autenticado
    db.query event_log {
      where = $db.event_log.user_id == $auth.id
      sort = {created_at: "desc"}
      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $user_events
  }

  response = $user_events
  tags = ["xano:quick-start"]
  guid = "b1zcqjqucDY40ujwzKRVw8HYpt4"
}
