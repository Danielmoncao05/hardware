// Cria um registro na tabela de log de eventos
function "Quick Start/log_event" {
  input {
    // Identificador único do usuário que executou a ação.
    int user_id
  
    // Descrição da ação executada pelo usuário (ex.: 'login', 'created_invoice').
    text action
  
    // Dados adicionais do evento, como IDs de recursos ou valores antigos/novos.
    json metadata?
  }

  stack {
    // Adiciona uma nova entrada no log de eventos do usuário
    db.add event_log {
      data = {
        created_at: "now"
        user_id   : $input.user_id
        action    : $input.action
        metadata  : $input.metadata
      }
    } as $new_log_entry
  }

  response = null
  tags = ["xano:quick-start"]
  guid = "2TbgVrSk4dm4J7ehQwaI2SPVPbA"
}