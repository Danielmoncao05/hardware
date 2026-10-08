// Lança inputerror se a localização não existir ou não estiver ativa (para equipamentos novos ou movidos).
function "hhm/require_active_location" {
  input {
    int localizacao_id
  }

  stack {
    db.get localizacoes {
      field_name = "id"
      field_value = $input.localizacao_id
    } as $loc

    precondition ($loc != null && $loc.ativo == true) {
      error_type = "inputerror"
      error = "localizacao_id must reference an active location."
    }
  }

  response = $loc
  guid = "Xg5bdqXJI-FKwvV9YqQAi9j90wo"
}
