// Lista as contas de usuário com perfil (role_id) e habilitação (users.manage).
// A consulta é mínima de propósito: com busca por texto, join com roles, filtros opcionais e paginação ela devolvia
// lista vazia mesmo havendo usuários (a mesma tabela é lida sem paginação em setup/migrate_users, e funciona).
// Devolve todos os usuários em uma lista; page/per_page são aceitos e ignorados (o app recorta a página).
// O app monta o nome do perfil a partir de GET roles.
query users verb=GET {
  api_group = "Users"
  auth = "user"

  input {
    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.query user {
      sort = {id: "asc"}
      output = ["id", "created_at", "name", "email", "role_id", "ativo", "deve_trocar_senha"]
      return = {type: "list"}
    } as $users
  }

  response = $users
  guid = "vsN44BGD3ZDIDa1mFjDdKZiE_J4"
}
