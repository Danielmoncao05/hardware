// Cria as 12 categorias de equipamento, os 4 perfis, as chaves de permissão e as concessões aprovadas por perfil.
// Idempotente: as linhas são localizadas pelo nome/chave únicos e só as que faltam são adicionadas, então é seguro
// rodar de novo. Os tipos de componente são um enum em componentes.tipo e não precisam de linhas.
// Devolve as contagens por tabela e qualquer concessão diferente da matriz aprovada (faltando ou sobrando).
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
        {nome: "administrator", descricao: "Gerencia usuários, perfis e permissões, o inventário e as manutenções."}
        {nome: "asset_manager", descricao: "Gerencia o inventário, os catálogos e todas as manutenções e ocorrências."}
        {nome: "technician", descricao: "Atua nas manutenções e ocorrências atribuídas a ele e registra ocorrências."}
        {nome: "viewer", descricao: "Acesso somente leitura aos dados operacionais e relatórios."}
      ]
    }

    var $permissions {
      value = [
        {chave: "operational.read", descricao: "Ver equipamentos, catálogos, localizações, manutenções e ocorrências."}
        {chave: "inventory.manage", descricao: "Cadastrar, editar, mover, mudar o status e desativar equipamentos, catálogos, localizações e componentes."}
        {chave: "maintenance.manage", descricao: "Cadastrar, atribuir e mudar o andamento de qualquer manutenção."}
        {chave: "maintenance.manage_assigned", descricao: "Mudar o andamento e editar as manutenções atribuídas ao usuário."}
        {chave: "occurrence.report", descricao: "Relatar uma nova ocorrência de equipamento."}
        {chave: "occurrence.manage", descricao: "Atribuir, resolver, cancelar e vincular qualquer ocorrência."}
        {chave: "occurrence.manage_assigned", descricao: "Editar, resolver e cancelar as ocorrências atribuídas ao usuário."}
        {chave: "reports.read", descricao: "Ver o painel e os relatórios operacionais, inclusive a exportação em CSV."}
        {chave: "audit.read", descricao: "Ver o log de auditoria."}
        {chave: "users.manage", descricao: "Cadastrar, habilitar e desabilitar usuários e gerenciar perfis e permissões."}
      ]
    }

    // Matriz aprovada (design.md, Autorização e privacidade)
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

    // Verificação: compara as concessões gravadas dos perfis criados com a matriz
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
