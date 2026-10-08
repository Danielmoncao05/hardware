// Stores user information and allows the user to authenticate  against
table user {
  auth = true

  schema {
    int id
    timestamp created_at?=now
    text name filters=trim
    email? email filters=trim|lower
    password? password filters=min:8|minAlpha:1|minDigit:1
  
    // Legacy quick-start role ('admin'/'member'). Superseded by role_id; kept only so
    // setup/migrate_users can map existing accounts. Not used for authorization.
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

    // Access role; permissions come from role_permissions. Null means no access.
    int? role_id? {
      table = "roles"
    }

    // Disabled users cannot authenticate and fail every permission check.
    // Accounts are disabled, never deleted, so historical references remain valid.
    bool ativo?=true

    timestamp? updated_at?

    // Set when an administrator creates the account with a temporary password. While true the user
    // holds no permissions (hhm/has_permission) and must change the password (auth/change_password)
    // before using the system. Null (accounts created before this change) counts as false.
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