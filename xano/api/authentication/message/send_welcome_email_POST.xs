// Sends a welcome email to a provisioned user. Administrator-only (users.manage): it was public in the
// quick start, which let anyone trigger emails.
query "message/send_welcome_email" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    // The ID of the user to send the welcome email to.
    int user_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    // Retrieve the user record for the given user ID.
    db.get user {
      field_name = "id"
      field_value = $input.user_id
    } as $user_record
  
    // Ensure the user record exists before proceeding.
    precondition ($user_record != null) {
      error_type = "notfound"
      error = "User not found."
    }
  
    // Subject and body (the name is HTML-escaped: it is user-entered text)
    var $email_subject {
      value = "Bem-vindo(a) ao sistema de gestão de equipamentos"
    }
  
    var $email_body {
      value = "<html><body><h1>Olá, " ~ ($user_record.name|escape) ~ "!</h1><p>Sua conta no sistema de gestão de equipamentos foi criada por um administrador. Você receberá uma senha temporária por um canal seguro. No primeiro acesso, o sistema pedirá que você a troque por uma senha pessoal antes de continuar.</p></body></html>"
    }
  
    // Send welcome email through the configured email service
    function.run "hhm/send_email" {
      input = {
        to     : $user_record.email
        subject: $email_subject
        html   : $email_body
      }
    } as $send_email
  
    // Log welcome email sent for user
    function.run "Quick Start/log_event" {
      input = {
        user_id : $input.user_id
        action  : "welcome_email_sent"
        metadata: {}
      }
    } as $event_log
  }

  response = $send_email
  tags = ["xano:quick-start"]
  guid = "T8I4x4ej-XGZ0xNLsVwUz0htoL4"
}