// Cria uma conta de usuário com senha temporária e um perfil ativo (users.manage).
// A conta fica marcada com deve_trocar_senha: até o usuário trocar a senha temporária
// (auth/change_password) ela não tem permissões. Administradores não podem definir nem redefinir a senha de uma
// conta existente; senhas esquecidas passam somente pelo fluxo de redefinição por e-mail.
query users verb=POST {
  api_group = "Users"
  auth = "user"

  input {
    text name filters=trim|min:1
    email email filters=trim|lower
    password password filters=min:8|minAlpha:1|minDigit:1 {
      sensitive = true
    }

    int role_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.get roles {
      field_name = "id"
      field_value = $input.role_id
    } as $role

    precondition ($role != null && $role.ativo == true) {
      error_type = "inputerror"
      error = "Escolha um perfil ativo."
    }

    db.has user {
      field_name = "email"
      field_value = $input.email
    } as $email_taken

    precondition ($email_taken == false) {
      error_type = "inputerror"
      error = "Este e-mail já está em uso."
    }

    db.transaction {
      stack {
        db.add user {
          data = {
            created_at: "now"
            name      : $input.name
            email     : $input.email
            password  : $input.password
            role_id   : $input.role_id
            ativo     : true
            deve_trocar_senha: true
          }
        } as $user

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "user.created"
            entidade   : "user"
            registro_id: $user.id
            depois     : {name: $user.name, email: $user.email, role_id: $user.role_id, ativo: true, deve_trocar_senha: true}
          }
        }
      }
    }
  }

  response = {
    id     : $user.id
    name   : $user.name
    email  : $user.email
    role_id: $user.role_id
    role   : $role.nome
    ativo  : true
    deve_trocar_senha: true
  }
  guid = "eHt0nDfW9tmFEjHtLkRphDzcbbI"
}
