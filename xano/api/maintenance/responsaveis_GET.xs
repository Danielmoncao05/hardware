// Usuários que podem ser atribuídos a trabalhos de uma área: só id e nome (operational.read).
// Só lista usuários habilitados cujo perfil tem "<area>.manage" ou "<area>.manage_assigned", igual
// à verificação no servidor hhm/require_assignable_user. A lista completa de usuários (e-mail, perfil, habilitação)
// continua exclusiva de administradores, no grupo Users.
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
