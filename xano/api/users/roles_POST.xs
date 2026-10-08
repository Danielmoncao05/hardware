// Cria um perfil (users.manage). O perfil começa ativo e sem permissões; conceda-as por
// POST roles/{role_id}/permissions. Os nomes são únicos e imutáveis (o seed localiza os perfis pelo nome).
query roles verb=POST {
  api_group = "Users"
  auth = "user"

  input {
    text nome filters=trim|lower|min:2|max:50
    text? descricao? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.has roles {
      field_name = "nome"
      field_value = $input.nome
    } as $exists

    precondition ($exists == false) {
      error_type = "inputerror"
      error = "nome: a role with this name already exists."
    }

    db.transaction {
      stack {
        db.add roles {
          data = {nome: $input.nome, descricao: $input.descricao, ativo: true}
        } as $role

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "role.created"
            entidade   : "roles"
            registro_id: $role.id
            depois     : $role
          }
        }
      }
    }
  }

  response = $role|set:"permissions":[]
  guid = "jaz71tR-dbXQG3K6a2p8uqndr1E"
}
