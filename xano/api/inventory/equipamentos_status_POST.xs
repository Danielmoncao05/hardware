// Changes equipment status, including decommissioning (inventory.manage). Decommissioning keeps the
// record and its maintenance/occurrence history; the record only leaves active lists.
// A reason is required to decommission or take equipment out of service.
query "equipamentos/{equipamento_id}/status" verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    int equipamento_id
    enum status {
      values = ["operational", "under_maintenance", "out_of_service", "decommissioned"]
    }

    text? motivo? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.transaction {
      stack {
        function.run "hhm/set_equipment_status" {
          input = {
            equipamento_id: $input.equipamento_id
            status        : $input.status
            motivo        : $input.motivo
            user_id       : $auth.id
          }
        } as $after
      }
    }
  }

  response = $after
  guid = "hEhTLRvMpgWDjwJ7ggJEUSK0rIM"
}
