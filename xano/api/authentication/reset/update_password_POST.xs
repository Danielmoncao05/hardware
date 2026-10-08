// Desativado. Ele definia uma nova senha para qualquer sessão logada sem pedir a atual, então uma
// sessão roubada podia tomar a conta. Use auth/change_password (exige a senha atual)
// quando estiver logado, ou reset/confirm com o link do e-mail quando esquecer a senha.
// O endpoint é mantido (em vez de apagado) para que clientes antigos recebam uma recusa explícita.
query "reset/update_password" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    text password? filters=trim
    text confirm_password? filters=trim
  }

  stack {
    throw {
      name = "accessdenied"
      value = "This endpoint is no longer available. Use auth/change_password or reset/confirm."
    }
  }

  response = null
  tags = ["xano:quick-start"]
  guid = "mDh0W9G081ieSpgLISiQBNE_tGY"
}
