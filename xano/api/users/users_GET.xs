// Lista as contas de usuário com perfil (role_id) e habilitação (users.manage).
// A consulta é mínima de propósito: com a busca por texto (ilike também na coluna email, do tipo email) e o join
// com roles, ela devolvia lista vazia mesmo havendo usuários. O app monta o nome do perfil a partir de GET roles.
query users verb=GET {
  api_group = "Users"
  auth = "user"

  input {
    bool? ativo?
    int? role_id?
    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.query user {
      where = $db.user.ativo ==? $input.ativo && $db.user.role_id ==? $input.role_id
      sort = {name: "asc"}
      output = ["id", "created_at", "name", "email", "role_id", "ativo", "deve_trocar_senha"]
      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $users
  }

  response = $users
  guid = "vsN44BGD3ZDIDa1mFjDdKZiE_J4"
}
