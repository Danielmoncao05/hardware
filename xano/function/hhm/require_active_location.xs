// Throws inputerror unless the location exists and is active (for new or moved equipment).
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
