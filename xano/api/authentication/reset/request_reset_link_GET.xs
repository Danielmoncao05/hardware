// Request a one-time password-reset link by email.
// Security: the token is a random UUID stored only as a hash (password field), valid for 60 minutes,
// single use, and replaced whenever a new link is requested. Unknown and disabled accounts get the
// same response as a sent link, and configuration is checked before the account lookup so a missing
// configuration cannot reveal which emails exist.
query "reset/request-reset-link" verb=GET {
  api_group = "Authentication"

  input {
    email email?
  }

  stack {
    precondition ($env.HHM_APP_URL != null && $env.HHM_APP_URL != "" && $env.RESEND_API_KEY != null && $env.RESEND_API_KEY != "" && $env.HHM_EMAIL_FROM != null && $env.HHM_EMAIL_FROM != "") {
      error_type = "standard"
      error = "Password recovery is not configured yet. Contact an administrator."
    }

    // Generate a one-time magic link
    function.run "Quick Start/generate_magic_link" {
      input = {email: $input.email}
    } as $token_and_email

    // Unknown or disabled account: answer exactly like a sent link so emails cannot be enumerated
    conditional {
      if ($token_and_email == null) {
        return {
          value = {
            message: {}|set:"success":true|set:"message":"magic link sent"
          }
        }
      }
    }

    // Link to the application's reset page (HHM_APP_URL is the production URL, e.g. https://equipamentos.example.org)
    var $magic_link {
      value = $env.HHM_APP_URL ~ "/reset-password?magic_token=" ~ ($token_and_email.token|url_encode) ~ "&email=" ~ ($token_and_email.email|url_encode)
    }

    // HTML message with the reset link
    util.template_engine {
      value = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Redefinição de senha</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
          <div style="max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2>Redefinição de senha</h2>
            <p>Recebemos uma solicitação para redefinir a senha da sua conta no sistema de gestão de equipamentos.</p>
            <p style="text-align: center; margin: 30px 0;">
              <a href="{{ $var.magic_link }}" style="display: inline-block; padding: 12px 25px; background-color: #0d7377; color: #ffffff; text-decoration: none; border-radius: 4px; font-size: 16px;">
                Definir nova senha
              </a>
            </p>
            <p>O link é válido por 60 minutos e pode ser usado uma única vez. Um novo pedido invalida links anteriores.</p>
            <p>Se você não fez esta solicitação, ignore este e-mail; sua senha atual continua válida.</p>
          </div>
        </body>
        </html>
        """
    } as $message

    function.run "hhm/send_email" {
      input = {
        to     : $token_and_email.email
        subject: "Redefinição de senha"
        html   : $message
      }
    } as $send_email
  }

  response = {
    message: {}|set:"success":true|set:"message":"magic link sent"
  }

  tags = ["xano:quick-start"]
  guid = "9AEaNez846VunbEzAq_g3tbKGzE"
}
