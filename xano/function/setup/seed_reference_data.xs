// Seeds the 12 equipment categories, the 4 roles, the permission keys, and the approved role grants.
// Idempotent: rows are matched by their unique name/key and only missing rows are added, so it is safe
// to re-run. Component types are an enum on componentes.tipo and need no rows.
// Returns per-table counts plus any grant that differs from the approved matrix (missing or extra).
function "setup/seed_reference_data" {
  input {
  }

  stack {
    var $categorias {
      value = [
        "monitor multiparamétrico"
        "ventilador pulmonar"
        "bomba de infusão"
        "desfibrilador"
        "eletrocardiógrafo"
        "máquina de anestesia"
        "ultrassom"
        "raio-X"
        "tomógrafo"
        "ressonância magnética"
        "oxímetro"
        "aspirador hospitalar"
      ]
    }

    var $roles {
      value = [
        {nome: "administrator", descricao: "Manages users, roles, permissions, inventory, and maintenance."}
        {nome: "asset_manager", descricao: "Manages inventory and catalogs and all maintenance and occurrences."}
        {nome: "technician", descricao: "Works on assigned maintenance and occurrences; reports occurrences."}
        {nome: "viewer", descricao: "Read-only access to operational data and reports."}
      ]
    }

    var $permissions {
      value = [
        {chave: "operational.read", descricao: "Read equipment, catalogs, locations, maintenance, and occurrences."}
        {chave: "inventory.manage", descricao: "Create, update, move, change status of, and deactivate equipment, catalogs, locations, and components."}
        {chave: "maintenance.manage", descricao: "Create, assign, and transition any maintenance record."}
        {chave: "maintenance.manage_assigned", descricao: "Transition and update maintenance assigned to the user."}
        {chave: "occurrence.report", descricao: "Report a new equipment occurrence."}
        {chave: "occurrence.manage", descricao: "Assign, resolve, cancel, and link any occurrence."}
        {chave: "occurrence.manage_assigned", descricao: "Update, resolve, and cancel occurrences assigned to the user."}
        {chave: "reports.read", descricao: "Read the dashboard and operational reports, including CSV export."}
        {chave: "audit.read", descricao: "Read the audit log."}
        {chave: "users.manage", descricao: "Provision, enable, and disable users and manage roles and permissions."}
      ]
    }

    // Approved matrix (design.md, Authorization and privacy)
    var $matrix {
      value = {
        administrator: ["operational.read", "inventory.manage", "maintenance.manage", "occurrence.report", "occurrence.manage", "reports.read", "audit.read", "users.manage"]
        asset_manager: ["operational.read", "inventory.manage", "maintenance.manage", "occurrence.report", "occurrence.manage", "reports.read"]
        technician   : ["operational.read", "maintenance.manage_assigned", "occurrence.report", "occurrence.manage_assigned", "reports.read"]
        viewer       : ["operational.read", "reports.read"]
      }
    }

    db.transaction {
      stack {
        foreach ($categorias) {
          each as $nome {
            db.has categorias {
              field_name = "nome"
              field_value = $nome
            } as $exists

            conditional {
              if ($exists == false) {
                db.add categorias {
                  data = {nome: $nome, ativo: true}
                }
              }
            }
          }
        }

        foreach ($roles) {
          each as $role {
            db.has roles {
              field_name = "nome"
              field_value = $role.nome
            } as $exists

            conditional {
              if ($exists == false) {
                db.add roles {
                  data = {nome: $role.nome, descricao: $role.descricao, ativo: true}
                }
              }
            }
          }
        }

        foreach ($permissions) {
          each as $perm {
            db.has permissions {
              field_name = "chave"
              field_value = $perm.chave
            } as $exists

            conditional {
              if ($exists == false) {
                db.add permissions {
                  data = {chave: $perm.chave, descricao: $perm.descricao}
                }
              }
            }
          }
        }

        foreach ($matrix|keys) {
          each as $role_nome {
            db.get roles {
              field_name = "nome"
              field_value = $role_nome
            } as $role

            foreach ($matrix|get:$role_nome) {
              each as $chave {
                db.get permissions {
                  field_name = "chave"
                  field_value = $chave
                } as $perm

                db.query role_permissions {
                  where = $db.role_permissions.role_id == $role.id && $db.role_permissions.permission_id == $perm.id
                  return = {type: "exists"}
                } as $granted

                conditional {
                  if ($granted == false) {
                    db.add role_permissions {
                      data = {role_id: $role.id, permission_id: $perm.id}
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    // Verification: compare stored grants for the seeded roles against the matrix
    var $divergencias {
      value = []
    }

    foreach ($matrix|keys) {
      each as $role_nome {
        db.get roles {
          field_name = "nome"
          field_value = $role_nome
        } as $role

        db.query role_permissions {
          join = {
            permissions: {
              table: "permissions"
              where: $db.role_permissions.permission_id == $db.permissions.id
            }
          }

          where = $db.role_permissions.role_id == $role.id
          eval = {chave: $db.permissions.chave}
          return = {type: "list"}
        } as $grants

        var $stored {
          value = $grants|map:$$.chave
        }

        var $expected {
          value = $matrix|get:$role_nome
        }

        foreach ($expected) {
          each as $chave {
            conditional {
              if (($stored|some:$$ == $chave) == false) {
                var.update $divergencias {
                  value = $divergencias|push:{role: $role_nome, chave: $chave, problema: "missing"}
                }
              }
            }
          }
        }

        foreach ($stored) {
          each as $chave {
            conditional {
              if (($expected|some:$$ == $chave) == false) {
                var.update $divergencias {
                  value = $divergencias|push:{role: $role_nome, chave: $chave, problema: "extra"}
                }
              }
            }
          }
        }
      }
    }

    db.query categorias {
      return = {type: "count"}
    } as $total_categorias

    db.query roles {
      return = {type: "count"}
    } as $total_roles

    db.query permissions {
      return = {type: "count"}
    } as $total_permissions

    db.query role_permissions {
      return = {type: "count"}
    } as $total_grants
  }

  response = {
    categorias      : $total_categorias
    roles           : $total_roles
    permissions     : $total_permissions
    role_permissions: $total_grants
    divergencias    : $divergencias
  }
  guid = "UgNytNkfHYjSYHFfGFi7JyoK7DU"
}
