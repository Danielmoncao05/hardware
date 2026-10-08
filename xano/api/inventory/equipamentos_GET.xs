// Paginated, filtered equipment list with derived manufacturer/category and location names
// (operational.read). Decommissioned equipment is excluded unless include_decommissioned is true
// or status = "decommissioned" is requested explicitly.
query equipamentos verb=GET {
  api_group = "Inventory"
  auth = "user"

  input {
    text? q? filters=trim
    int? categoria_id?
    int? fabricante_id?
    int? modelo_id?
    int? localizacao_id?
    enum? status? {
      values = ["operational", "under_maintenance", "out_of_service", "decommissioned"]
    }

    bool include_decommissioned?=false
    int page?=1 filters=min:1
    int per_page?=25 filters=min:1|max:100
  }

  stack {
    function.run "hhm/require_permission" {
      input = {user_id: $auth.id, permission: "operational.read"}
    }

    var $pattern {
      value = "%" ~ ($input.q ?? "") ~ "%"
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

      where = ($db.equipamentos.nome ilike $pattern || $db.equipamentos.numero_patrimonio ilike $pattern || $db.equipamentos.numero_serie ilike $pattern) && $db.modelos.categoria_id ==? $input.categoria_id && $db.modelos.fabricante_id ==? $input.fabricante_id && $db.equipamentos.modelo_id ==? $input.modelo_id && $db.equipamentos.localizacao_id ==? $input.localizacao_id && $db.equipamentos.status ==? $input.status && $db.equipamentos.status !=? $excluir_status
      sort = {nome: "asc"}
      eval = {
        modelo       : $db.modelos.nome
        fabricante_id: $db.modelos.fabricante_id
        fabricante   : $db.fabricantes.nome
        categoria_id : $db.modelos.categoria_id
        categoria    : $db.categorias.nome
        localizacao  : $db.localizacoes.nome
      }

      return = {
        type  : "list"
        paging: {page: $input.page, per_page: $input.per_page, totals: true}
      }
    } as $items
  }

  response = $items
  guid = "diwBgTJ32bhttwLSsScQRpDbzxE"
}
