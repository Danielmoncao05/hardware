// Lists roles with their granted permission keys, plus the full permission catalog (users.manage).
query roles verb=GET {
  api_group = "Users"
  auth = "user"

  input {
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.query roles {
      sort = {nome: "asc"}
      return = {type: "list"}
    } as $roles

    db.query role_permissions {
      join = {
        permissions: {
          table: "permissions"
          where: $db.role_permissions.permission_id == $db.permissions.id
        }
      }

      eval = {chave: $db.permissions.chave}
      return = {type: "list"}
    } as $grants

    db.query permissions {
      sort = {chave: "asc"}
      return = {type: "list"}
    } as $permissions

    var $result {
      value = []
    }

    foreach ($roles) {
      each as $role {
        var.update $result {
          value = $result|push:($role|set:"permissions":($grants|filter:$$.role_id == $role.id|map:$$.chave))
        }
      }
    }
  }

  response = {roles: $result, permissions: $permissions}
  guid = "GXD6ZlFpBx6xDj0CowgGPF_asCU"
}
