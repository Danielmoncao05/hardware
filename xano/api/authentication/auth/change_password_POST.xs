// O usuário logado troca a própria senha (obrigatório no primeiro acesso depois que um administrador
// criou a conta com senha temporária; também disponível a qualquer momento depois).
// Exige a senha atual; a nova precisa seguir a política de senhas, coincidir com a confirmação
// e ser diferente da atual. Limpa deve_trocar_senha para as permissões do usuário voltarem a valer.
// Só altera a senha de quem chama: não existe endpoint para administradores definirem ou
// redefinirem a senha de um usuário existente.
query "auth/change_password" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    text senha_atual {
      sensitive = true
    }

    password nova_senha filters=min:8|minAlpha:1|minDigit:1 {
      sensitive = true
    }

    text confirmar_senha {
      sensitive = true
    }
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "email", "password", "ativo", "deve_trocar_senha"]
    } as $user

    precondition ($user != null && $user.ativo == true) {
      error_type = "accessdenied"
      error = "Access denied."
    }

    security.check_password {
      text_password = $input.senha_atual
      hash_password = $user.password
    } as $atual_ok

    precondition ($atual_ok) {
      error_type = "inputerror"
      error = "senha_atual is incorrect."
    }

    // nova_senha é do tipo password: o Xano já a recebe em hash. Por isso as comparações usam
    // security.check_password com a confirmação (texto puro), nunca == com nova_senha, que nunca seria igual.
    security.check_password {
      text_password = $input.confirmar_senha
      hash_password = $input.nova_senha
    } as $confirmacao_ok

    precondition ($confirmacao_ok) {
      error_type = "inputerror"
      error = "confirmar_senha does not match nova_senha."
    }

    // Com a confirmação igual à nova senha, ela serve de texto puro para comparar com a senha atual
    security.check_password {
      text_password = $input.confirmar_senha
      hash_password = $user.password
    } as $mesma_senha

    precondition ($mesma_senha == false) {
      error_type = "inputerror"
      error = "nova_senha must be different from the current password."
    }

    db.transaction {
      stack {
        db.edit user {
          field_name = "id"
          field_value = $auth.id
          data = {password: $input.nova_senha, deve_trocar_senha: false, updated_at: "now"}
        }

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "user.password_changed"
            entidade   : "user"
            registro_id: $auth.id
            antes      : {deve_trocar_senha: $user.deve_trocar_senha == true}
            depois     : {deve_trocar_senha: false}
          }
        }
      }
    }
  }

  response = {success: true, deve_trocar_senha: false}
  guid = "yMealZz8cIe9a-8vWeAHIYa0cKU"
}
