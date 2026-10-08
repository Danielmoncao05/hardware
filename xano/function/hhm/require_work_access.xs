// Autoriza mudanças em um registro de manutenção ou ocorrência. Permitido quando o usuário tem a
// permissão "<area>.manage", ou tem "<area>.manage_assigned" e é o responsável pelo registro
// (técnicos só atuam no que foi atribuído a eles). area é "maintenance" ou "occurrence".
// Devolve true quando o acesso veio da permissão manage completa, false para acesso só aos atribuídos.
function "hhm/require_work_access" {
  input {
    int user_id
    text area
    int? responsavel_id?
  }

  stack {
    function.run "hhm/has_permission" {
      input = {user_id: $input.user_id, permission: $input.area ~ ".manage"}
    } as $can_manage

    var $assigned_ok {
      value = false
    }

    conditional {
      if ($can_manage == false && $input.responsavel_id == $input.user_id) {
        function.run "hhm/has_permission" {
          input = {user_id: $input.user_id, permission: $input.area ~ ".manage_assigned"}
        } as $can_assigned

        var.update $assigned_ok {
          value = $can_assigned
        }
      }
    }

    precondition ($can_manage || $assigned_ok) {
      error_type = "accessdenied"
      error = "Access denied."
    }
  }

  response = $can_manage
  guid = "l6l2T_gnACgdjp8AEl_rtqOTIto"
}
