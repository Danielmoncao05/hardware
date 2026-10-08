// Performance fixture (task 6.2): bulk-inserts synthetic equipment so the inventory list can be measured
// at 10,000 records. Rows are tagged with the PERF- asset prefix and reuse existing active models and
// locations. Run only in a test deployment; it refuses to exceed the requested total.
function "setup/seed_perf_data" {
  input {
    int total?=10000 filters=min:1|max:20000
    int lote?=500 filters=min:1|max:1000
  }

  stack {
    db.query modelos {
      where = $db.modelos.ativo == true
      output = ["id"]
      return = {type: "list"}
    } as $modelos

    db.query localizacoes {
      where = $db.localizacoes.ativo == true
      output = ["id"]
      return = {type: "list"}
    } as $locais

    precondition (($modelos|count) > 0 && ($locais|count) > 0) {
      error_type = "inputerror"
      error = "Create at least one active model and location first."
    }

    db.query equipamentos {
      where = $db.equipamentos.numero_patrimonio ilike "PERF-%"
      return = {type: "count"}
    } as $existentes

    var $faltam {
      value = $input.total - $existentes
    }

    var $status {
      value = ["operational", "operational", "operational", "under_maintenance", "out_of_service"]
    }

    var $n {
      value = $existentes
    }

    while ($faltam > 0) {
      each {
        var $tamanho {
          value = $faltam|min:$input.lote
        }

        var $linhas {
          value = []
        }

        for ($tamanho) {
          each as $i {
            math.add $n {
              value = 1
            }

            var.update $linhas {
              value = $linhas|push:{
                nome             : "Equipamento de carga " ~ $n
                numero_patrimonio: "PERF-" ~ ($n|to_text)
                modelo_id        : ($modelos|get:($n % ($modelos|count))).id
                localizacao_id   : ($locais|get:($n % ($locais|count))).id
                status           : $status|get:($n % 5)
              }
            }
          }
        }

        db.bulk.add equipamentos {
          items = $linhas
        }

        math.sub $faltam {
          value = $tamanho
        }
      }
    }

    db.query equipamentos {
      return = {type: "count"}
    } as $total_equipamentos
  }

  response = {perf_rows_before: $existentes, total_equipamentos: $total_equipamentos}
  guid = "A2VzaZdtyuvZ-uQH-B_wnqFFoGs"
}
