// Revokes a permission from a role (users.manage). users.manage cannot be revoked from the
// administrator role, so the deployment always keeps a way to manage access.
query "roles/{role_id}/permissions/{permission_id}" verb=DELETE {
  api_group = "Users"
  auth = "user"

  input {
    int role_id
    int permission_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.get roles {
      field_name = "id"
      field_value = $input.role_id
    } as $role

    db.get permissions {
      field_name = "id"
      field_value = $input.permission_id
    } as $permission

    precondition ($role != null && $permission != null) {
      error_type = "notfound"
      error = "Role or permission not found."
    }

    precondition ($role.nome != "administrator" || $permission.chave != "users.manage") {
      error_type = "inputerror"
      error = "users.manage cannot be revoked from the administrator role."
    }

    db.query role_permissions {
      where = $db.role_permissions.role_id == $input.role_id && $db.role_permissions.permission_id == $input.permission_id
      return = {type: "single"}
    } as $grant

    conditional {
      if ($grant != null) {
        db.transaction {
          stack {
            db.del role_permissions {
              field_name = "id"
              field_value = $grant.id
            }

            function.run "hhm/audit" {
              input = {
                user_id    : $auth.id
                action     : "role.permission_revoked"
                entidade   : "roles"
                registro_id: $input.role_id
                antes      : {role: $role.nome, permission: $permission.chave}
              }
            }
          }
        }
      }
    }
  }

  response = {role_id: $input.role_id, permission: $permission.chave, granted: false}
  guid = "obdqmbsiMMhUSo5s3OxE-T206e4"
}
