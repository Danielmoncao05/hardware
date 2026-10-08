// Faz login e devolve um token de autenticação. Contas desabilitadas não conseguem entrar.
query "auth/login" verb=POST {
  api_group = "Authentication"

  input {
    email email? filters=trim|lower
    text password?
  }

  stack {
    // Busca o registro do usuário pelo e-mail
    db.get user {
      field_name = "email"
      field_value = $input.email
      output = ["id", "email", "password", "ativo", "deve_trocar_senha"]
    } as $user

    // Verifica se existe um usuário com esse e-mail
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "Invalid Credentials."
    }

    // Confere a senha com o hash armazenado
    security.check_password {
      text_password = $input.password
      hash_password = $user.password
    } as $pass_result

    // Verifica se a conferência da senha passou
    precondition ($pass_result) {
      error_type = "accessdenied"
      error = "Invalid Credentials."
    }

    // Contas desabilitadas recebem a mesma resposta que credenciais erradas
    precondition ($user.ativo == true) {
      error_type = "accessdenied"
      error = "Invalid Credentials."
    }

    // Cria um token de autenticação
    security.create_auth_token {
      table = "user"
      extras = {}
      expiration = 86400
      id = $user.id
    } as $authToken

    // Registra o evento de login (nunca registrar o registro do usuário: ele contém o hash da senha)
    function.run "Quick Start/log_event" {
      input = {user_id: $user.id, action: "login", metadata: {email: $user.email}}
    } as $event_log
  }

  // deve_trocar_senha avisa o cliente para levar o usuário primeiro à troca de senha; a própria API
  // nega toda operação protegida até a troca ser feita (hhm/has_permission)
  response = {authToken: $authToken, user_id: $user.id, deve_trocar_senha: $user.deve_trocar_senha == true}
  tags = ["xano:quick-start"]
  guid = "daR-hB488R3lmzRni_EPtc3VKpY"
}
