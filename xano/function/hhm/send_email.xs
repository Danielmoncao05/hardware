// Sends a transactional email through the configured email service (Resend, the only external
// provider util.send_email supports; the built-in "xano" provider only reaches the workspace owner).
// Environment: RESEND_API_KEY (secret) and HHM_EMAIL_FROM (a sender on a domain verified in Resend).
// Fails closed: without configuration it throws instead of silently not sending.
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
