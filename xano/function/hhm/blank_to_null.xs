// Converte texto opcional em branco para null. Necessário para colunas opcionais únicas como
// equipamentos.numero_serie: o banco trata "" como um valor real (validation.md #6).
function "hhm/blank_to_null" {
  input {
    text? value?
  }

  stack {
    var $result {
      value = null
    }

    conditional {
      if ($input.value != null && ($input.value|trim) != "") {
        var.update $result {
          value = $input.value|trim
        }
      }
    }
  }

  response = $result
  guid = "YFzx_vH9u0rW3n2QlrgkiTQ8Cp8"
}
