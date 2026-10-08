// Disabled. A reset link used to be exchanged here for a full login session, which could then call any
// endpoint. Password resets are now completed in one step by reset/confirm, which never creates a session.
// The endpoint is kept (rather than deleted) so old clients get an explicit refusal.
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
