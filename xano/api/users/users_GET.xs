// Lists user accounts with role and enabled state (users.manage).
query users verb=GET {
  api_group = "Users"
  auth = "user"

  input {
    text? q? filters=trim
    bool? ativo?
    int? role_id?
    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    var $pattern {
      value = "%" ~ ($input.q ?? "") ~ "%"
    }

    db.query user {
      join = {
        roles: {
          table: "roles"
          type : "left"
          where: $db.user.role_id == $db.roles.id
        }
      }

      where = ($db.user.name ilike $pattern || $db.user.email ilike $pattern) && $db.user.ativo ==? $input.ativo && $db.user.role_id ==? $input.role_id
      sort = {name: "asc"}
      output = ["id", "created_at", "name", "email", "role_id", "ativo", "deve_trocar_senha"]
      eval = {role: $db.roles.nome}
      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $users
  }

  response = $users
  guid = "vsN44BGD3ZDIDa1mFjDdKZiE_J4"
}
