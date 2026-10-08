// Devolve o usuário autenticado com seu perfil e as chaves de permissão.
// Usuários desabilitados são recusados mesmo que um token anterior ainda não tenha expirado.
query "auth/me" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    // Busca o registro do usuário pelo ID da autenticação
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "created_at", "name", "email", "role_id", "ativo", "deve_trocar_senha"]
    } as $user

    precondition ($user != null && $user.ativo == true) {
      error_type = "accessdenied"
      error = "Access denied."
    }

    db.get roles {
      field_name = "id"
      field_value = $user.role_id
      output = ["id", "nome"]
    } as $role

    function.run "hhm/user_permissions" {
      input = {user_id: $user.id}
    } as $permissions
  }

  response = {
    id         : $user.id
    created_at : $user.created_at
    name       : $user.name
    email      : $user.email
    role       : $role.nome
    permissions: $permissions
    deve_trocar_senha: $user.deve_trocar_senha == true
  }

  tags = ["xano:quick-start"]
  guid = "K0AvjJV61cO5B3ExwMT2qOV7tSw"
}
