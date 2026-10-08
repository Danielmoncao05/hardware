// Envia um e-mail transacional pelo serviço de e-mail configurado (Resend, o único provedor externo
// que util.send_email suporta; o provedor "xano" embutido só chega ao dono do workspace).
// Ambiente: RESEND_API_KEY (segredo) e HHM_EMAIL_FROM (um remetente em um domínio verificado no Resend).
// Falha de forma segura: sem configuração, lança erro em vez de deixar de enviar sem avisar.
function "hhm/send_email" {
  input {
    email to
    text subject
    text html
  }

  stack {
    precondition ($env.RESEND_API_KEY != null && $env.RESEND_API_KEY != "" && $env.HHM_EMAIL_FROM != null && $env.HHM_EMAIL_FROM != "") {
      error_type = "standard"
      error = "Email delivery is not configured (RESEND_API_KEY / HHM_EMAIL_FROM)."
    }

    util.send_email {
      service_provider = "resend"
      api_key = $env.RESEND_API_KEY
      to = $input.to
      from = $env.HHM_EMAIL_FROM
      subject = $input.subject
      message = $input.html
    } as $result
  }

  response = $result
  guid = "ULcCxvmFc29YWUlTBD9Uk3JXZ8c"
}
