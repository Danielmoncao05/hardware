// Altera o nome, o perfil ou a habilitação de um usuário (users.manage). Usuários são desabilitados, nunca apagados.
// Administradores não podem se desabilitar nem trocar o próprio perfil, para não bloquear o último administrador.
query "users/{user_id}" verb=PATCH {
  api_group = "Users"
  auth = "user"

  input {
    int user_id
    text? name? filters=trim
    int? role_id?
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.get user {
      field_name = "id"
      field_value = $input.user_id
      output = ["id", "name", "email", "role_id", "ativo"]
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    precondition ($input.user_id != $auth.id || ($input.role_id == null && $input.ativo == null)) {
      error_type = "inputerror"
      error = "Você não pode alterar o próprio perfil nem desabilitar a própria conta."
    }

    var $updates {
      value = {updated_at: "now"}
    }

    conditional {
      if ($input.name != null) {
        precondition ($input.name != "") {
          error_type = "inputerror"
          error = "O nome não pode ficar em branco."
        }

        var.update $updates {
          value = $updates|set:"name":$input.name
        }
      }
    }

    conditional {
      if ($input.role_id != null) {
        db.get roles {
          field_name = "id"
          field_value = $input.role_id
        } as $role

        precondition ($role != null && $role.ativo == true) {
          error_type = "inputerror"
          error = "Escolha um perfil ativo."
        }

        var.update $updates {
          value = $updates|set:"role_id":$input.role_id
        }
      }
    }

    conditional {
      if ($input.ativo != null) {
        var.update $updates {
          value = $updates|set:"ativo":$input.ativo
        }
      }
    }

    db.transaction {
      stack {
        db.patch user {
          field_name = "id"
          field_value = $input.user_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "user.updated"
            entidade   : "user"
            registro_id: $input.user_id
            antes      : {name: $before.name, role_id: $before.role_id, ativo: $before.ativo}
            depois     : {name: $after.name, role_id: $after.role_id, ativo: $after.ativo}
          }
        }
      }
    }
  }

  response = {
    id     : $after.id
    name   : $after.name
    email  : $after.email
    role_id: $after.role_id
    ativo  : $after.ativo
  }
  guid = "_3ioAw2Li9HTi2VwXmQ05jtMQks"
}
