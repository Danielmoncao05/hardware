// Public signup is disabled: accounts are provisioned by administrators (POST users in the Users group).
// The endpoint is kept, rather than deleted, so existing clients get an explicit refusal.
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
