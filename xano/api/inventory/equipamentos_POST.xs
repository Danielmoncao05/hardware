// Cadastra um equipamento (inventory.manage). Fabricante e categoria vêm do modelo; informar
// fabricante_id/categoria_id conflitantes é recusado. A localização precisa estar ativa.
// O status inicial segue as regras de troca de status: não dá para cadastrar já descomissionado, e
// cadastrar fora de serviço exige um motivo (registrado no evento de auditoria).
query equipamentos verb=POST {
  api_group = "Inventory"
  auth = "user"

  input {
    text nome filters=trim
    text numero_patrimonio filters=trim
    int modelo_id
    int localizacao_id
    enum status?="operational" {
      values = ["operational", "under_maintenance", "out_of_service"]
    }

    text? motivo? filters=trim

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

    precondition ($input.status != "out_of_service" || ($input.motivo != null && $input.motivo != "")) {
      error_type = "inputerror"
      error = "motivo is required to register equipment as out of service."
    }

    db.transaction {
      stack {
        function.run "hhm/validate_equipment" {
          input = {
            nome             : $input.nome
            numero_patrimonio: $input.numero_patrimonio
            numero_serie     : $input.numero_serie
            modelo_id        : $input.modelo_id
            fabricante_id    : $input.fabricante_id
            categoria_id     : $input.categoria_id
            ano_fabricacao   : $input.ano_fabricacao
            data_aquisicao   : $input.data_aquisicao
          }
        } as $valid

        function.run "hhm/require_active_location" {
          input = {localizacao_id: $input.localizacao_id}
        } as $loc

        db.add equipamentos {
          data = {
            nome             : $input.nome
            numero_patrimonio: $input.numero_patrimonio
            modelo_id        : $input.modelo_id
            localizacao_id   : $input.localizacao_id
            status           : $input.status
            numero_serie     : $valid.numero_serie
            ano_fabricacao   : $input.ano_fabricacao
            data_aquisicao   : $input.data_aquisicao
            valor_aquisicao  : $input.valor_aquisicao
            vida_util_anos   : $input.vida_util_anos
            observacoes      : $input.observacoes
            criado_por       : $auth.id
          }
        } as $item

        function.run "hhm/audit" {
          input = {
            user_id    : $auth.id
            action     : "equipamento.created"
            entidade   : "equipamentos"
            registro_id: $item.id
            depois     : $item|set:"motivo":$input.motivo
          }
        }
      }
    }
  }

  response = $item
    |set:"modelo":$valid.modelo.nome
    |set:"fabricante_id":$valid.fabricante.id
    |set:"fabricante":$valid.fabricante.nome
    |set:"categoria_id":$valid.categoria.id
    |set:"categoria":$valid.categoria.nome
    |set:"localizacao":$loc.nome
    guid = "dB6cBo_Uk9zLnGt2qhZI2tfCrWg"
}
