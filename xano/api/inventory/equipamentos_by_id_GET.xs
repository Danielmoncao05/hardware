// Detalhe do equipamento (operational.read): registro, fabricante/categoria derivados, localização, datas
// derivadas da última/próxima manutenção, componentes (instalados e removidos) e contagem de ocorrências.
// O histórico cronológico é servido por equipamentos/{id}/historico, no grupo Maintenance.
query "equipamentos/{equipamento_id}" verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    int equipamento_id
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
    } as $equip

    precondition ($equip != null) {
      error_type = "notfound"
      error = "Equipment not found."
    }

    db.get modelos {
      field_name = "id"
      field_value = $equip.modelo_id
    } as $modelo

    db.get fabricantes {
      field_name = "id"
      field_value = $modelo.fabricante_id
      output = ["id", "nome", "ativo"]
    } as $fabricante

    db.get categorias {
      field_name = "id"
      field_value = $modelo.categoria_id
      output = ["id", "nome", "ativo"]
    } as $categoria

    db.get localizacoes {
      field_name = "id"
      field_value = $equip.localizacao_id
      output = ["id", "nome", "ativo", "parent_id"]
    } as $localizacao

    function.run "hhm/maintenance_dates" {
      input = {equipamento_id: $input.equipamento_id}
    } as $datas

    db.query equipamento_componentes {
      join = {
        componentes: {
          table: "componentes"
          where: $db.equipamento_componentes.componente_id == $db.componentes.id
        }
      }

      where = $db.equipamento_componentes.equipamento_id == $input.equipamento_id
      sort = {instalado_em: "desc"}
      eval = {
        componente: $db.componentes.nome
        tipo      : $db.componentes.tipo
      }

      return = {type: "list"}
    } as $componentes

    db.query ocorrencias {
      where = $db.ocorrencias.equipamento_id == $input.equipamento_id && ($db.ocorrencias.status == "open" || $db.ocorrencias.status == "in_progress")
      return = {type: "count"}
    } as $ocorrencias_abertas

    db.get user {
      field_name = "id"
      field_value = $equip.criado_por
      output = ["id", "name"]
    } as $criador
  }

  response = $equip
    |set:"modelo":{id: $modelo.id, nome: $modelo.nome, ativo: $modelo.ativo}
    |set:"fabricante":$fabricante
    |set:"categoria":$categoria
    |set:"localizacao":$localizacao
    |set:"criado_por_nome":$criador.name
    |set:"ultima_manutencao":$datas.ultima_manutencao
    |set:"proxima_manutencao":$datas.proxima_manutencao
    |set:"componentes_instalados":($componentes|filter:$$.removido_em == null)
    |set:"componentes_removidos":($componentes|filter:$$.removido_em != null)
    |set:"ocorrencias_abertas":$ocorrencias_abertas
    guid = "ir85q0KjS69QseU8sMbJ6QMY4hI"
}
