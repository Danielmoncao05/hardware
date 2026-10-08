// Records an audit event: actor, action, affected record, and before/after details.
// The only writer of audit rows for domain changes; no endpoint edits or deletes event_log.
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
