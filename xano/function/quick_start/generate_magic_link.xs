// Esta função gera um token mágico que expira em 60 minutos.
function "Quick Start/generate_magic_link" {
  input {
    email email?
  }

  stack {
    // Verifica se o e-mail informado não está vazio
    precondition ($input.email != null) {
      error = "email is required but was not suppiled. "
    }
  
    // Busca o registro do usuário pelo e-mail
    db.query user {
      where = $db.user.email == $input.email
      return = {type: "single"}
    } as $user

    // Contas desconhecidas ou desabilitadas não recebem link. Devolve null em vez de erro para o
    // chamador poder responder igual nos dois casos, sem revelar quais e-mails existem.
    conditional {
      if ($user == null || $user.ativo != true) {
        return {
          value = null
        }
      }
    }

    // Cria um UUID único como token
    security.create_uuid as $token
  
    // Monta o objeto de redefinição de senha
    var $password_reset {
      value = {}
        |set:"token":$token
        |set:"expiration":(now
          |add_secs_to_timestamp:(3600|to_int)
        )
        |set:"used":false
    }
  
    // Atualiza o registro do usuário com o objeto de redefinição de senha
    db.edit user {
      field_name = "id"
      field_value = $user|get:"id":0
      data = {password_reset: $password_reset}
    } as $updated_password_reset
  }

  response = {token: $token, email: $updated_password_reset.email}
  tags = ["xano:quick-start"]
  guid = "BnNILjOuTlyiGrvOpF3UnK_7Bvg"
}