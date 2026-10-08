// Builds RFC 4180 CSV text from rows and an ordered column list [{key, label}].
// Every cell is quoted with embedded quotes doubled. Cells starting with = + - @ get a leading
// apostrophe so spreadsheet apps do not evaluate user-entered text as a formula.
function "hhm/to_csv" {
  input {
    json colunas
    json linhas
  }

  stack {
    var $linhas_csv {
      value = []
    }

    var $cabecalho {
      value = []
    }

    foreach ($input.colunas) {
      each as $col {
        var.update $cabecalho {
          value = $cabecalho|push:("\"" ~ ($col.label|replace:"\"":"\"\"") ~ "\"")
        }
      }
    }

    var.update $linhas_csv {
      value = $linhas_csv|push:($cabecalho|join:",")
    }

    foreach ($input.linhas) {
      each as $linha {
        var $celulas {
          value = []
        }

        foreach ($input.colunas) {
          each as $col {
            var $valor {
              value = ($linha|get:$col.key)
            }

            var $texto {
              value = ""
            }

            conditional {
              if ($valor != null) {
                var.update $texto {
                  value = $valor|to_text
                }
              }
            }

            conditional {
              if (($texto|starts_with:"=") || ($texto|starts_with:"+") || ($texto|starts_with:"-") || ($texto|starts_with:"@")) {
                var.update $texto {
                  value = "'" ~ $texto
                }
              }
            }

            var.update $celulas {
              value = $celulas|push:("\"" ~ ($texto|replace:"\"":"\"\"") ~ "\"")
            }
          }
        }

        var.update $linhas_csv {
          value = $linhas_csv|push:($celulas|join:",")
        }
      }
    }
  }

  response = $linhas_csv|join:"\r\n"
  guid = "sUaHEN552SCrJMmbPt1AjrhPKUw"
}
