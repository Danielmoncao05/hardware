// Transições de estado da ocorrência (gestor ou o técnico atribuído):
//   acao = "iniciar":  open -> in_progress
//   acao = "resolver": open/in_progress -> resolved; exige resolvida_em (não futura, não
//                      anterior ao relato) e resumo_resolucao
//   acao = "cancelar": open/in_progress -> canceled; exige motivo_cancelamento
// Uma transição recusada deixa a ocorrência inalterada.
query "ocorrencias/{ocorrencia_id}/transicao" verb=POST {
  api_group = "Maintenance"
  auth = "user"

  input {
    int ocorrencia_id
    enum acao {
      values = ["iniciar", "resolver", "cancelar"]
    }

    timestamp? resolvida_em?
    text? resumo_resolucao? filters=trim
    text? motivo_cancelamento? filters=trim
  }

  stack {
    db.get ocorrencias {
      field_name = "id"
      field_value = $input.ocorrencia_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Occurrence not found."
    }

    function.run "hhm/require_work_access" {
      input = {user_id: $auth.id, area: "occurrence", responsavel_id: $before.responsavel_id}
    }

    precondition ($before.status == "open" || $before.status == "in_progress") {
      error_type = "inputerror"
      error = "Resolved or canceled occurrences cannot change state."
    }

    var $data {
      value = {updated_at: "now"}
    }

    switch ($input.acao) {
      case ("iniciar") {
        precondition ($before.status == "open") {
          error_type = "inputerror"
          error = "Only open occurrences can be started."
        }

        var.update $data {
          value = $data|set:"status":"in_progress"
        }
      } break

      case ("resolver") {
        precondition ($input.resolvida_em != null && $input.resumo_resolucao != null && $input.resumo_resolucao != "") {
          error_type = "inputerror"
          error = "resolvida_em and resumo_resolucao are required to resolve an occurrence."
        }

        precondition ($input.resolvida_em <= now && $input.resolvida_em >= $before.relatada_em) {
          error_type = "inputerror"
          error = "resolvida_em must be between the report date and now."
        }

        var.update $data {
          value = $data
            |set:"status":"resolved"
            |set:"resolvida_em":$input.resolvida_em
            |set:"resumo_resolucao":$input.resumo_resolucao
        }
      } break

      default {
        precondition ($input.motivo_cancelamento != null && $input.motivo_cancelamento != "") {
          error_type = "inputerror"
          error = "motivo_cancelamento is required to cancel an occurrence."
        }

        var.update $data {
          value = $data
            |set:"status":"canceled"
            |set:"motivo_cancelamento":$input.motivo_cancelamento
        }
      }
    }

    db.transaction {
      stack {
        db.patch ocorrencias {
          field_name = "id"
          field_value = $input.ocorrencia_id
          data = $data
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "ocorrencia." ~ $after.status
            entidade   : "ocorrencias"
            registro_id: $input.ocorrencia_id
            antes      : {status: $before.status}
            depois     : $data
          }
        }
      }
    }
  }

  response = $after
  guid = "C3iyPXRvWY6O8Hgp2BXrOSYMqUA"
}
