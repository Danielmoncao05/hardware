// Devolve true quando o usuário está habilitado, não tem troca de senha temporária pendente, tem um perfil ativo
// e esse perfil tem a chave de permissão.
// Toda operação protegida passa por aqui (via hhm/require_permission) em vez de verificar nomes de perfil.
function "hhm/has_permission" {
  input {
    int user_id
    text permission filters=trim
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $input.user_id
      output = ["id", "role_id", "ativo", "deve_trocar_senha"]
    } as $user

    var $allowed {
      value = false
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

          where = $db.role_permissions.role_id == $user.role_id && $db.permissions.chave == $input.permission && $db.roles.ativo == true
          return = {type: "exists"}
        } as $granted

        var.update $allowed {
          value = $granted
        }
      }
    }
  }

  response = $allowed
  guid = "UShv7O7bYS_2kX0JEyix2qaaW4k"
}
