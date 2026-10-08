// Lança inputerror se o usuário não existir ou não estiver habilitado (para atribuir responsáveis).
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
