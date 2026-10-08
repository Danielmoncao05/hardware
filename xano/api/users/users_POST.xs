// Provisions a user account with a temporary password and an active role (users.manage).
// The account is flagged deve_trocar_senha: until the user replaces the temporary password
// (auth/change_password) it holds no permissions. Administrators cannot set or reset the password of an
// existing account; forgotten passwords go through the email reset flow only.
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
      error = "role_id must reference an active role."
    }

    db.has user {
      field_name = "email"
      field_value = $input.email
    } as $email_taken

    precondition ($email_taken == false) {
      error_type = "inputerror"
      error = "email is already in use."
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
