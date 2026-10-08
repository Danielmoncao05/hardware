// Lança inputerror se o usuário não puder ser responsável por trabalhos da área: precisa estar habilitado e ter
// "<area>.manage" ou "<area>.manage_assigned" (senão o responsável não conseguiria atuar no registro).
// area é "maintenance" ou "occurrence".
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
