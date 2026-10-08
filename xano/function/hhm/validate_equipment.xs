// Validação no servidor compartilhada pelo cadastro e pela edição de equipamentos. Lança inputerror indicando o campo.
// - patrimônio obrigatório, não vazio e único; série opcional, em branco -> null, única quando informada
// - o modelo precisa existir (e estar ativo quando atribuído agora); fabricante/categoria informados precisam corresponder a ele
// - ano de fabricação entre 1900 e o ano atual; data de aquisição não futura
// Devolve a série normalizada e o modelo com seu fabricante e categoria.
function "hhm/validate_equipment" {
  input {
    int? equipamento_id?
    text nome filters=trim
    text numero_patrimonio filters=trim
    text? numero_serie?
    int modelo_id
    bool modelo_deve_estar_ativo?=true
    int? fabricante_id?
    int? categoria_id?
    int? ano_fabricacao?
    date? data_aquisicao?
  }

  stack {
    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "nome is required."
    }

    precondition ($input.numero_patrimonio != "") {
      error_type = "inputerror"
      error = "numero_patrimonio is required."
    }

    db.query equipamentos {
      where = $db.equipamentos.numero_patrimonio == $input.numero_patrimonio && $db.equipamentos.id !=? $input.equipamento_id
      return = {type: "exists"}
    } as $patrimonio_taken

    precondition ($patrimonio_taken == false) {
      error_type = "inputerror"
      error = "numero_patrimonio is already in use."
    }

    function.run "hhm/blank_to_null" {
      input = {value: $input.numero_serie}
    } as $serie

    conditional {
      if ($serie != null) {
        db.query equipamentos {
          where = $db.equipamentos.numero_serie == $serie && $db.equipamentos.id !=? $input.equipamento_id
          return = {type: "exists"}
        } as $serie_taken

        precondition ($serie_taken == false) {
          error_type = "inputerror"
          error = "numero_serie is already assigned to another equipment."
        }
      }
    }

    db.get modelos {
      field_name = "id"
      field_value = $input.modelo_id
    } as $modelo

    precondition ($modelo != null && ($modelo.ativo == true || $input.modelo_deve_estar_ativo == false)) {
      error_type = "inputerror"
      error = "modelo_id must reference an active model."
    }

    precondition ($input.fabricante_id == null || $input.fabricante_id == $modelo.fabricante_id) {
      error_type = "inputerror"
      error = "fabricante_id conflicts with the manufacturer of the selected model."
    }

    precondition ($input.categoria_id == null || $input.categoria_id == $modelo.categoria_id) {
      error_type = "inputerror"
      error = "categoria_id conflicts with the category of the selected model."
    }

    var $ano_atual {
      value = now|format_timestamp:"Y":"UTC"|to_int
    }

    precondition ($input.ano_fabricacao == null || ($input.ano_fabricacao >= 1900 && $input.ano_fabricacao <= $ano_atual)) {
      error_type = "inputerror"
      error = "ano_fabricacao must be a valid year no later than the current year."
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    precondition ($input.data_aquisicao == null || $input.data_aquisicao <= $hoje) {
      error_type = "inputerror"
      error = "data_aquisicao cannot be in the future."
    }

    db.get fabricantes {
      field_name = "id"
      field_value = $modelo.fabricante_id
      output = ["id", "nome"]
    } as $fabricante

    db.get categorias {
      field_name = "id"
      field_value = $modelo.categoria_id
      output = ["id", "nome"]
    } as $categoria
  }

  response = {
    numero_serie: $serie
    modelo      : $modelo
    fabricante  : $fabricante
    categoria   : $categoria
  }
  guid = "6TR-bgexQYxoh_Wjd79NoVEf0ZQ"
}
