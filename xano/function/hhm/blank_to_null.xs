// Normalizes blank optional text to null. Required for optional unique columns such as
// equipamentos.numero_serie: the datastore treats "" as a real value (validation.md #6).
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
