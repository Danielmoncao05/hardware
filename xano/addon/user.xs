addon user {
  input {
    int user_id? {
      table = "user"
    }
  }

  stack {
    db.query user {
      where = $db.user.id == $input.user_id
      return = {type: "single"}
    }
  }

  guid = "hfgHQ4MBGqI7hSD3yjLy8SfT1ns"
}