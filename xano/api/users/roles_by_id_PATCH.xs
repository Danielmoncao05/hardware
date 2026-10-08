// Updates a role's description or activates/deactivates it (users.manage).
// Deactivation is refused for the administrator role (the deployment must keep a way to manage access)
// and for any role still assigned to enabled users (they would silently lose every permission);
// reassign those users first. Roles are never deleted, so historical audit references stay valid.
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
      error = "Role not found."
    }

    conditional {
      if ($input.ativo == false && $before.ativo == true) {
        precondition ($before.nome != "administrator") {
          error_type = "inputerror"
          error = "The administrator role cannot be deactivated."
        }

        db.query user {
          where = $db.user.role_id == $input.role_id && $db.user.ativo == true
          return = {type: "count"}
        } as $em_uso

        precondition ($em_uso == 0) {
          error_type = "inputerror"
          error = "This role is assigned to " ~ $em_uso ~ " enabled user(s). Reassign them before deactivating it."
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
