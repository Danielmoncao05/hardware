// Edita os dados de identificação e aquisição do equipamento (inventory.manage). Localização e status só mudam
// pelos endpoints de mover e de status, para cada um ser uma transição auditada separadamente.
// Campos omitidos (null) mantêm o valor. Envie "" para limpar a série ou as observações; campos numéricos e de
// data opcionais podem ser alterados, mas não limpos, por este endpoint.
query "equipamentos/{equipamento_id}" verb=PATCH {
  api_group = "Inventory"
  auth = "user"

  input {
    int equipamento_id
    text? nome? filters=trim
    text? numero_patrimonio? filters=trim
    int? modelo_id?
    int? fabricante_id?
    int? categoria_id?
    text? numero_serie? filters=trim
    int? ano_fabricacao?
    date? data_aquisicao?
    decimal? valor_aquisicao? filters=min:0
    int? vida_util_anos? filters=min:1
    text? observacoes? filters=trim
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "inventory.manage"}
    }

    db.get equipamentos {
      field_name = "id"
      field_value = $input.equipamento_id
    } as $before

    precondition ($before != null) {
      error_type = "notfound"
      error = "Equipment not found."
    }

    // Equipamento descomissionado fica somente leitura, como histórico (mesma regra de mover/status/componentes)
    precondition ($before.status != "decommissioned") {
      error_type = "inputerror"
      error = "Decommissioned equipment cannot be edited."
    }

    var $modelo_id {
      value = $input.modelo_id ?? $before.modelo_id
    }

    // Série: null mantém o valor atual, "" limpa, qualquer outro valor substitui
    var $serie_in {
      value = $before.numero_serie
    }

    conditional {
      if ($input.numero_serie != null) {
        var.update $serie_in {
          value = $input.numero_serie
        }
      }
    }

    db.transaction {
      stack {
        function.run "hhm/validate_equipment" {
          input = {
            equipamento_id         : $input.equipamento_id
            nome                   : $input.nome ?? $before.nome
            numero_patrimonio      : $input.numero_patrimonio ?? $before.numero_patrimonio
            numero_serie           : $serie_in
            modelo_id              : $modelo_id
            modelo_deve_estar_ativo: $modelo_id != $before.modelo_id
            fabricante_id          : $input.fabricante_id
            categoria_id           : $input.categoria_id
            ano_fabricacao         : $input.ano_fabricacao ?? $before.ano_fabricacao
            data_aquisicao         : $input.data_aquisicao ?? $before.data_aquisicao
          }
        } as $valid

        var $updates {
          value = {
            updated_at       : "now"
            nome             : $input.nome ?? $before.nome
            numero_patrimonio: $input.numero_patrimonio ?? $before.numero_patrimonio
            modelo_id        : $modelo_id
            numero_serie     : $valid.numero_serie
            ano_fabricacao   : $input.ano_fabricacao ?? $before.ano_fabricacao
            data_aquisicao   : $input.data_aquisicao ?? $before.data_aquisicao
            valor_aquisicao  : $input.valor_aquisicao ?? $before.valor_aquisicao
            vida_util_anos   : $input.vida_util_anos ?? $before.vida_util_anos
          }
        }

        conditional {
          if ($input.observacoes != null) {
            var.update $updates {
              value = $updates|set:"observacoes":($input.observacoes == "" ? null : $input.observacoes)
            }
          }
        }

        db.patch equipamentos {
          field_name = "id"
          field_value = $input.equipamento_id
          data = $updates
        } as $after

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "equipamento.updated"
            entidade   : "equipamentos"
            registro_id: $input.equipamento_id
            antes      : $before
            depois     : $after
          }
        }
      }
    }
  }

  response = $after
    |set:"modelo":$valid.modelo.nome
    |set:"fabricante":$valid.fabricante.nome
    |set:"categoria":$valid.categoria.nome
    guid = "LEvqLj2xc5ZeihB1Zop5r8i0oYk"
}
