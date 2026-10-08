// Authorizes changes to a maintenance or occurrence record. Allowed when the user holds the
// "<area>.manage" permission, or holds "<area>.manage_assigned" and is the record's responsible user
// (technicians work only on what is assigned to them). area is "maintenance" or "occurrence".
// Returns true when access came from the full manage permission, false for assigned-only access.
function "hhm/require_work_access" {
  input {
    int user_id
    text area
    int? responsavel_id?
  }

  stack {
    function.run "hhm/has_permission" {
      input = {user_id: $input.user_id, permission: $input.area ~ ".manage"}
    } as $can_manage

    var $assigned_ok {
      value = false
    }

    conditional {
      if ($can_manage == false && $input.responsavel_id == $input.user_id) {
        function.run "hhm/has_permission" {
          input = {user_id: $input.user_id, permission: $input.area ~ ".manage_assigned"}
        } as $can_assigned

        var.update $assigned_ok {
          value = $can_assigned
        }
      }
    }

    precondition ($can_manage || $assigned_ok) {
      error_type = "accessdenied"
      error = "Access denied."
    }
  }

  response = $can_manage
  guid = "l6l2T_gnACgdjp8AEl_rtqOTIto"
}
