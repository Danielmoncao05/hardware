// Throws accessdenied unless the user is enabled and holds the permission.
// The error text is identical for every denial so it does not disclose why access failed.
function "hhm/require_permission" {
  input {
    int user_id
    text permission filters=trim
  }

  stack {
    function.run "hhm/has_permission" {
      input = {user_id: $input.user_id, permission: $input.permission}
    } as $allowed

    precondition ($allowed) {
      error_type = "accessdenied"
      error = "Access denied."
    }
  }

  response = true
  guid = "b5bMg0-xoA7APLVT3-wLbO0V82E"
}
