// Pull event logs for the authenticated user. Audit history is restricted to audit.read holders
// (administrators); use the Audit group for filtered access across users.
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

    // Retrieve event logs for the authenticated user
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
