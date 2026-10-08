// Login and retrieve an authentication token. Disabled accounts cannot log in.
query "auth/login" verb=POST {
  api_group = "Authentication"

  input {
    email email? filters=trim|lower
    text password?
  }

  stack {
    // Get the user record via email
    db.get user {
      field_name = "email"
      field_value = $input.email
      output = ["id", "email", "password", "ativo", "deve_trocar_senha"]
    } as $user

    // Check to make sure a user with that email exists
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "Invalid Credentials."
    }

    // Check that the password matches the hashed password
    security.check_password {
      text_password = $input.password
      hash_password = $user.password
    } as $pass_result

    // Verify that the password check passed
    precondition ($pass_result) {
      error_type = "accessdenied"
      error = "Invalid Credentials."
    }

    // Disabled accounts get the same response as wrong credentials
    precondition ($user.ativo == true) {
      error_type = "accessdenied"
      error = "Invalid Credentials."
    }

    // Create an authentication token
    security.create_auth_token {
      table = "user"
      extras = {}
      expiration = 86400
      id = $user.id
    } as $authToken

    // Create an event log for login (never log the user record: it holds the password hash)
    function.run "Quick Start/log_event" {
      input = {user_id: $user.id, action: "login", metadata: {email: $user.email}}
    } as $event_log
  }

  // deve_trocar_senha tells the client to send the user to the password change first; the API itself
  // denies every protected operation until the change is made (hhm/has_permission)
  response = {authToken: $authToken, user_id: $user.id, deve_trocar_senha: $user.deve_trocar_senha == true}
  tags = ["xano:quick-start"]
  guid = "daR-hB488R3lmzRni_EPtc3VKpY"
}
