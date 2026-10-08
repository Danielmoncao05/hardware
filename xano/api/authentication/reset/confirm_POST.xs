// Completes a password reset from the emailed link in one step: verifies the one-time token and sets the
// new password. No session is created, so a reset link can only ever change that account's password
// (it never grants access to anything else). Replaces the magic-link-login + update_password pair.
// Token rules: stored only as a hash, valid 60 minutes, single use, replaced by any newer request.
// Every token or account problem gets the same answer, so the response never reveals which check failed.
query "reset/confirm" verb=POST {
  api_group = "Authentication"

  input {
    text magic_token filters=trim {
      sensitive = true
    }

    email email filters=trim|lower
    password nova_senha filters=min:8|minAlpha:1|minDigit:1 {
      sensitive = true
    }

    text confirmar_senha {
      sensitive = true
    }
  }

  stack {
    precondition ($input.nova_senha == $input.confirmar_senha) {
      error_type = "inputerror"
      error = "confirmar_senha does not match nova_senha."
    }

    db.get user {
      field_name = "email"
      field_value = $input.email
      output = [
        "id"
        "email"
        "ativo"
        "password_reset.token"
        "password_reset.expiration"
        "password_reset.used"
      ]
    } as $user

    var $link_ok {
      value = false
    }

    conditional {
      if ($user != null && $user.ativo == true && $user.password_reset != null && $user.password_reset.token != null) {
        security.check_password {
          text_password = $input.magic_token
          hash_password = $user.password_reset.token
        } as $token_ok

        var.update $link_ok {
          value = $token_ok && $user.password_reset.used == false && $user.password_reset.expiration > now
        }
      }
    }

    precondition ($link_ok) {
      error_type = "accessdenied"
      error = "This reset link is invalid, has expired, or was already used. Request a new one."
    }

    db.transaction {
      stack {
        // New password chosen by the user; it also replaces a pending temporary password
        db.edit user {
          field_name = "id"
          field_value = $user.id
          data = {
            password         : $input.nova_senha
            deve_trocar_senha: false
            updated_at       : "now"
            password_reset   : {token: null, expiration: $user.password_reset.expiration, used: true}
          }
        }

        function.run "hhm/audit" {
          input = {
            user_id    : $user.id
            action     : "user.password_reset"
            entidade   : "user"
            registro_id: $user.id
            depois     : {via: "email_link"}
          }
        }
      }
    }
  }

  response = {success: true}
  guid = "UBDFYbZ3BdtiVA06lRI7SB0CnWc"
}
