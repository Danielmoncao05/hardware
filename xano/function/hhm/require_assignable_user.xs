// Throws inputerror unless the user can be made responsible for work in the area: enabled, and holding
// "<area>.manage" or "<area>.manage_assigned" (otherwise the assignee could not act on the record).
// area is "maintenance" or "occurrence".
function "hhm/require_assignable_user" {
  input {
    int user_id
    text area
  }

  stack {
    function.run "hhm/require_active_user" {
      input = {user_id: $input.user_id}
    } as $user

    function.run "hhm/has_permission" {
      input = {user_id: $input.user_id, permission: $input.area ~ ".manage"}
    } as $can_manage

    function.run "hhm/has_permission" {
      input = {user_id: $input.user_id, permission: $input.area ~ ".manage_assigned"}
    } as $can_assigned

    precondition ($can_manage || $can_assigned) {
      error_type = "inputerror"
      error = "responsavel_id must reference a user whose role can work on " ~ $input.area ~ " records."
    }
  }

  response = $user
  guid = "ekpPQB5oE6FaH5eXL1pzIEcb5bE"
}
