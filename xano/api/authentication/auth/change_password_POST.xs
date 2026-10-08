// The signed-in user replaces their own password (required on first login after an administrator
// created the account with a temporary password; also available any time afterwards).
// Requires the current password; the new one must meet the password policy, match its confirmation,
// and differ from the current one. Clears deve_trocar_senha so the user's permissions apply again.
// This only ever changes the caller's own password: there is no endpoint for administrators to set or
// reset an existing user's password.
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

    precondition ($input.nova_senha == $input.confirmar_senha) {
      error_type = "inputerror"
      error = "confirmar_senha does not match nova_senha."
    }

    security.check_password {
      text_password = $input.nova_senha
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
