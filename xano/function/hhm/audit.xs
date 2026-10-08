// Registra um evento de auditoria: autor, ação, registro afetado e detalhes de antes/depois.
// É o único que grava linhas de auditoria para mudanças de domínio; nenhum endpoint edita ou apaga event_log.
function "hhm/audit" {
  input {
    int? user_id
    text action filters=trim
    text entidade filters=trim
    int? registro_id
    json? antes?
    json? depois?
  }

  stack {
    db.add event_log {
      data = {
        created_at: "now"
        user_id   : $input.user_id
        action    : $input.action
        metadata  : {
          entidade   : $input.entidade
          registro_id: $input.registro_id
          antes      : $input.antes
          depois     : $input.depois
        }
      }
    } as $event
  }

  response = $event.id
  guid = "mk_eNVqY37d_8I3Xz04gTieVxyA"
}
