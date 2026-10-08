// Lists the permission keys granted to an enabled user (empty for disabled users, inactive roles, and
// users who must still replace a temporary password).
// Used by auth/me so the frontend can hide controls; the API still checks every operation.
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
