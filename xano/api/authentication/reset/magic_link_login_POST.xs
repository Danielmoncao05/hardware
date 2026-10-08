// Desativado. Antes, um link de redefinição era trocado aqui por uma sessão de login completa, que podia chamar qualquer
// endpoint. Agora a redefinição de senha é concluída em um passo por reset/confirm, que nunca cria sessão.
// O endpoint é mantido (em vez de apagado) para que clientes antigos recebam uma recusa explícita.
query "reset/magic-link-login" verb=POST {
  api_group = "Authentication"

  input {
    text magic_token? filters=trim
    text email? filters=trim
  }

  stack {
    throw {
      name = "accessdenied"
      value = "This endpoint is no longer available. Use reset/confirm with the emailed link."
    }
  }

  response = null
  tags = ["xano:quick-start"]
  guid = "EfGyGpjNmIutC9ZQf2Wq1RNGui4"
}
