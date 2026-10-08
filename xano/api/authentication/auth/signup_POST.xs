// O cadastro público está desativado: as contas são criadas por administradores (POST users no grupo Users).
// O endpoint é mantido, em vez de apagado, para que clientes existentes recebam uma recusa explícita.
query "auth/signup" verb=POST {
  api_group = "Authentication"

  input {
    text name?
    email email? filters=trim|lower
    text password?
  }

  stack {
    throw {
      name = "accessdenied"
      value = "Public signup is disabled. Ask an administrator to create your account."
    }
  }

  response = null
  tags = ["xano:quick-start"]
  guid = "ReqhttMODNVPrvgWYsj-u74vAqs"
}
