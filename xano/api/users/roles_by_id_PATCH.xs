// Atualiza a descrição de um perfil ou o ativa/desativa (users.manage).
// A desativação é recusada para o perfil administrator (o sistema precisa manter um jeito de gerenciar acessos)
// e para qualquer perfil ainda atribuído a usuários habilitados (eles perderiam todas as permissões sem aviso);
// reatribua esses usuários antes. Perfis nunca são apagados, para as referências históricas da auditoria continuarem válidas.
query "roles/{role_id}" verb=PATCH {
  api_group = "Users"
  auth = "user"

  input {
    int role_id
    text? descricao? filters=trim
    bool? ativo?
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "users.manage"}
    }

    db.get roles {
      field_name = "id"
      field_value = $input.role_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Perfil não encontrado."
    }

    conditional {
      if ($input.ativo == false && $before.ativo == true) {
        precondition ($before.nome != "administrator") {
          error_type = "inputerror"
          error = "O perfil Administrador não pode ser desativado."
        }

        db.query user {
          where = $db.user.role_id == $input.role_id && $db.user.ativo == true
          return = {type: "count"}
        } as $em_uso

        precondition ($em_uso == 0) {
          error_type = "inputerror"
          error = "Este perfil está em uso por " ~ $em_uso ~ " usuário(s) habilitado(s). Troque o perfil deles antes de desativá-lo."
        }
      }
    }

    var $updates {
      value = {
        updated_at: "now"
        ativo     : $input.ativo ?? $before.ativo
      }
    }

    conditional {
      if ($input.descricao != null) {
        var.update $updates {
          value = $updates|set:"descricao":($input.descricao == "" ? null : $input.descricao)
        }
      }
    }

    db.transaction {
      stack {
        db.patch roles {
          field_name = "id"
          field_value = $input.role_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "role.updated"
            entidade   : "roles"
            registro_id: $input.role_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
  guid = "CgCtiDpU5gmDPXhpf0F1gog44Cs"
}
