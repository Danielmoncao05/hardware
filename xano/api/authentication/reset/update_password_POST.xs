// Disabled. It set a new password for any signed-in session without asking for the current one, so a
// stolen session could take over the account. Use auth/change_password (requires the current password)
// when signed in, or reset/confirm with the emailed link when the password is forgotten.
// The endpoint is kept (rather than deleted) so old clients get an explicit refusal.
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
