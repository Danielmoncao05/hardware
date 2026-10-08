// Lista as chaves de permissão concedidas a um usuário habilitado (vazia para usuários desabilitados, perfis inativos e
// usuários que ainda precisam trocar uma senha temporária).
// Usada por auth/me para o frontend esconder controles; a API continua verificando toda operação.
function "hhm/user_permissions" {
  input {
    int user_id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $input.user_id
      output = ["id", "role_id", "ativo", "deve_trocar_senha"]
    } as $user

    var $keys {
      value = []
    }

    conditional {
      if ($user != null && $user.ativo == true && $user.role_id != null && $user.deve_trocar_senha != true) {
        db.query role_permissions {
          join = {
            permissions: {
              table: "permissions"
              where: $db.role_permissions.permission_id == $db.permissions.id
            }
            roles: {
              table: "roles"
              where: $db.role_permissions.role_id == $db.roles.id
            }
          }

          where = $db.role_permissions.role_id == $user.role_id && $db.roles.ativo == true
          eval = {chave: $db.permissions.chave}
          return = {type: "list"}
        } as $grants

        var.update $keys {
          value = $grants|map:$$.chave
        }
      }
    }
  }

  response = $keys
  guid = "wG0_p4BDxB7mGEKMQWv-SPdhoRE"
}
