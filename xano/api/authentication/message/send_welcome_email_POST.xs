// Envia um e-mail de boas-vindas a um usuário criado. Exclusivo de administradores (users.manage): no
// quick start ele era público, o que deixava qualquer pessoa disparar e-mails.
query "message/send_welcome_email" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    // ID do usuário que vai receber o e-mail de boas-vindas.
    int user_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    // Busca o registro do usuário com o ID informado.
    db.get user {
      field_name = "id"
      field_value = $input.user_id
    } as $user_record
  
    // Garante que o registro do usuário existe antes de continuar.
    precondition ($user_record != null) {
      error_type = "notfound"
      error = "User not found."
    }
  
    // Assunto e corpo (o nome é escapado para HTML: é texto digitado pelo usuário)
    var $email_subject {
      value = "Bem-vindo(a) ao sistema de gestão de equipamentos"
    }
  
    var $email_body {
      value = "<html><body><h1>Olá, " ~ ($user_record.name|escape) ~ "!</h1><p>Sua conta no sistema de gestão de equipamentos foi criada por um administrador. Você receberá uma senha temporária por um canal seguro. No primeiro acesso, o sistema pedirá que você a troque por uma senha pessoal antes de continuar.</p></body></html>"
    }
  
    // Envia o e-mail de boas-vindas pelo serviço de e-mail configurado
    function.run "hhm/send_email" {
      input = {
        to     : $user_record.email
        subject: $email_subject
        html   : $email_body
      }
    } as $send_email
  
    // Registra o envio do e-mail de boas-vindas para o usuário
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