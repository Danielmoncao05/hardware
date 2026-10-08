// Users that work in an area can be assigned to: id and name only (operational.read).
// Only enabled users whose role holds "<area>.manage" or "<area>.manage_assigned" are listed, matching
// the server-side check hhm/require_assignable_user. The full user list (email, role, enabled state)
// stays administrator-only in the Users group.
query responsaveis verb=GET {
  api_group = "Maintenance"
  auth = "user"

  input {
    enum area {
      values = ["maintenance", "occurrence"]
    }
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    var $chave_manage {
      value = $input.area ~ ".manage"
    }

    var $chave_assigned {
      value = $input.area ~ ".manage_assigned"
    }

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

      where = ($db.permissions.chave == $chave_manage || $db.permissions.chave == $chave_assigned) && $db.roles.ativo == true
      output = ["role_id"]
      return = {type: "list"}
    } as $grants

    var $role_ids {
      value = $grants|map:$$.role_id|unique
    }

    db.query user {
      where = $db.user.ativo == true && $db.user.role_id in $role_ids
      sort = {name: "asc"}
      output = ["id", "name"]
      return = {type: "list"}
    } as $users
  }

  response = $users
  guid = "woRFGAiqgET48UMvkLy98AQ1VJw"
}
