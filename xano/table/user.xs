// Guarda as informações do usuário e permite que ele se autentique
table user {
  auth = true

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    email? email filters=trim|lower
    password? password filters=min:8|minAlpha:1|minDigit:1
  
    // Perfil legado do quick-start ('admin'/'member'). Substituído por role_id; mantido só para
    // setup/migrate_users conseguir mapear as contas existentes. Não é usado para autorização.
    enum role? {
      values = ["admin", "member"]
    }

    object password_reset? {
      schema {
        password token?
        timestamp? expiration?
        bool used?
      }
    }

    // Perfil de acesso; as permissões vêm de role_permissions. Null significa sem acesso.
    int? role_id? {
      table = "roles"
    }

    // Usuários desabilitados não conseguem se autenticar e falham em toda verificação de permissão.
    // Contas são desabilitadas, nunca apagadas, para as referências históricas continuarem válidas.
    bool ativo?=true

    timestamp? updated_at?

    // Definido quando um administrador cria a conta com senha temporária. Enquanto for true, o usuário
    // não tem permissões (hhm/has_permission) e precisa trocar a senha (auth/change_password)
    // antes de usar o sistema. Null (contas criadas antes desta mudança) conta como false.
    bool deve_trocar_senha?=false
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
    {type: "btree", field: [{name: "role_id", op: "asc"}]}
  ]

  tags = ["xano:quick-start"]
  guid = "00nQt_Uw1EIm_mz8wzrzasyoSrM"
}