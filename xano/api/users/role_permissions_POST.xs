// Concede uma permissão a um perfil (users.manage). Conceder de novo uma permissão existente não faz nada.
query "roles/{role_id}/permissions" verb=POST {
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

    precondition ($role != null) {
      error_type = "notfound"
      error = "Perfil não encontrado."
    }

    db.get permissions {
      field_name = "id"
      field_value = $input.permission_id
    } as $permission

    precondition ($permission != null) {
      error_type = "notfound"
      error = "Permissão não encontrada."
    }

    db.query role_permissions {
      where = $db.role_permissions.role_id == $input.role_id && $db.role_permissions.permission_id == $input.permission_id
      return = {type: "exists"}
    } as $granted

    conditional {
      if ($granted == false) {
        db.transaction {
          stack {
            db.add role_permissions {
              data = {role_id: $input.role_id, permission_id: $input.permission_id}
            }

            function.run "hhm/audit" {
              input = {
                user_id    : $auth.id
                action     : "role.permission_granted"
                entidade   : "roles"
                registro_id: $input.role_id
                depois     : {role: $role.nome, permission: $permission.chave}
              }
            }
          }
        }
      }
    }
  }

  response = {role_id: $input.role_id, permission: $permission.chave, granted: true}
  guid = "5jX3Kb0I2uIMGu-vGBnyrLnue7s"
}
