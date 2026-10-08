// Inventory / status / location report (reports.read). formato = "json" returns the paginated
// on-screen page; formato = "csv" returns every matching row (up to 10,000) with the same filters.
// Columns are equipment-management fields only.
query "relatorios/inventario" verb=GET {
  api_group = "Reports"
  auth = "user"

  input {
    int? categoria_id?
    int? fabricante_id?
    int? localizacao_id?
    enum? status? {
      values = ["operational", "under_maintenance", "out_of_service", "decommissioned"]
    }

    bool include_decommissioned?=false
    enum formato?="json" {
      values = ["json", "csv"]
    }

    int page?=1 filters=min:1
    int per_page?=50 filters=min:1|max:200
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "reports.read"}
    }

    var $excluir_status {
      value = null
    }

    conditional {
      if ($input.include_decommissioned == false && $input.status == null) {
        var.update $excluir_status {
          value = "decommissioned"
        }
      }
    }

    var $page {
      value = $input.formato == "csv" ? 1 : $input.page
    }

    var $per_page {
      value = $input.formato == "csv" ? 10000 : $input.per_page
    }

    db.query equipamentos {
      join = {
        modelos: {
          table: "modelos"
          where: $db.equipamentos.modelo_id == $db.modelos.id
        }
        fabricantes: {
          table: "fabricantes"
          where: $db.modelos.fabricante_id == $db.fabricantes.id
        }
        categorias: {
          table: "categorias"
          where: $db.modelos.categoria_id == $db.categorias.id
        }
        localizacoes: {
          table: "localizacoes"
          where: $db.equipamentos.localizacao_id == $db.localizacoes.id
        }
      }

      where = $db.modelos.categoria_id ==? $input.categoria_id && $db.modelos.fabricante_id ==? $input.fabricante_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.equipamentos.status ==? $input.status && $db.equipamentos.status !=? $excluir_status
      sort = {numero_patrimonio: "asc"}
      output = ["id", "numero_patrimonio", "nome", "numero_serie", "status", "ano_fabricacao", "data_aquisicao", "valor_aquisicao", "vida_util_anos"]
      eval = {
        modelo     : $db.modelos.nome
        fabricante : $db.fabricantes.nome
        categoria  : $db.categorias.nome
        localizacao: $db.localizacoes.nome
      }

      return = {
        type  : "list"
        paging: {page: $page, per_page: $per_page, totals: true}
      }
    } as $result

    conditional {
      if ($input.formato == "csv") {
        function.run "hhm/to_csv" {
          input = {
            colunas: [
              {key: "numero_patrimonio", label: "Número de patrimônio"}
              {key: "nome", label: "Nome"}
              {key: "numero_serie", label: "Número de série"}
              {key: "categoria", label: "Categoria"}
              {key: "fabricante", label: "Fabricante"}
              {key: "modelo", label: "Modelo"}
              {key: "localizacao", label: "Localização"}
              {key: "status", label: "Status"}
              {key: "ano_fabricacao", label: "Ano de fabricação"}
              {key: "data_aquisicao", label: "Data de aquisição"}
              {key: "valor_aquisicao", label: "Valor de aquisição"}
              {key: "vida_util_anos", label: "Vida útil (anos)"}
            ]
            linhas : $result.items
          }
        } as $csv

        util.set_header {
          value = "Content-Type: text/csv; charset=utf-8"
          duplicates = "replace"
        }

        util.set_header {
          value = "Content-Disposition: attachment; filename=\"relatorio_inventario.csv\""
          duplicates = "replace"
        }

        return {
          value = $csv
        }
      }
    }
  }

  response = $result
  guid = "svGPqRRZnanQKjJcR_JgJTdJcC4"
}
