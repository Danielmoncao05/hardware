// Throws inputerror unless the user exists and is enabled (for assigning responsible users).
function "hhm/require_active_user" {
  input {
    int user_id
    text campo?="responsavel_id"
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $input.user_id
      output = ["id", "name", "ativo"]
    } as $user

    precondition ($user != null && $user.ativo == true) {
      error_type = "inputerror"
      error = $input.campo ~ " must reference an enabled user."
    }
  }

  response = $user
  guid = "Frv8ZiF1fP58_DtqmYTfpXDYaFY"
}
