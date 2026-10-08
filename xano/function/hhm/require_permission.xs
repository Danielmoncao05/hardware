// Lança accessdenied se o usuário não estiver habilitado ou não tiver a permissão.
// O texto do erro é igual em toda negação, para não revelar por que o acesso falhou.
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
