# Validação das restrições do Xano (tarefa 1.1)

## Configuração

- **Data:** 2026-10-08
- **Alvo:** workspace 149197 ("Matheus's Workspace"), branch `v1` (live), instância `x8ki-letl-twmt.n7.xano.io`, Xano CLI 1.3.3.
- **Por que no live:** os ambientes de sandbox e tenant não estão disponíveis no plano Free (`Access Denied. Not supported with Free plan`). Branches não isolam tabelas.
- **Método:** foram enviados os objetos temporários `zz_probe_parent`, `zz_probe_child` (tabelas) e `zz_probe/run_checks` (função), todos com a tag `zz_probe`, e rodado `xano function run "zz_probe/run_checks"`. Cada caso executa `db.add`/`db.edit`/`db.del` dentro de `try_catch` e registra se o banco aceitou ou recusou. As linhas finais das tabelas foram lidas de volta para confirmar o que ficou gravado.
- **Limpeza:** apague os três objetos `zz_probe*` pelo painel do Xano. Eles não fazem parte do schema do domínio.

## Resultados

| # | Restrição usada pelo schema do domínio | Caso testado | Observado | Conclusão |
|---|---|---|---|---|
| 1 | Chave estrangeira recusa uma referência inexistente (campo `table = "x"`) | inserir filho com `parent_id = 999999999` | aceito, linha gravada | **O banco não garante** |
| 2 | Chave estrangeira impede apagar uma linha referenciada | apagar um pai que tem filho | aceito, filho fica órfão | **O banco não garante** |
| 3 | Unicidade de uma coluna (`btree|unique`): `numero_patrimonio`, `fabricantes.nome`, `usuarios.email`, ... | patrimônio duplicado; nome de pai duplicado | recusado | Garantido |
| 4 | Único só quando preenchido (`numero_serie`) | `"S-1"` duplicado | recusado | Garantido |
| 5 | Várias séries em branco permitidas | duas linhas com `numero_serie = null` | ambas aceitas | Garantido (NULLs são distintos) |
| 6 | Série com texto vazio tratada como ausente | duas linhas com `numero_serie = ""` | segunda recusada | **Só funciona com `null`**: `""` é um valor real |
| 7 | Unicidade composta (`modelos` (`fabricante_id`, `categoria_id`, `nome`); `role_permissions` (`role_id`, `permission_id`)) | (`parent_id`, `chave_a`, `chave_b`) duplicado | recusado | Garantido |
| 8 | Quantidade positiva (`filters=min:1`) ao inserir | `quantidade` 0 e -3 | recusado | Garantido |
| 9 | Quantidade positiva ao atualizar | `db.edit` para `quantidade = 0` | recusado | Garantido |
| 10 | Valor não negativo (`filters=min:0` em decimal anulável) | `valor = -1` | recusado | Garantido |
| 11 | Domínio de enum (status, tipo, severidade) | `status = "bogus"` | recusado | Garantido |
| 12 | Coluna obrigatória recebendo `null` | `numero_patrimonio = null` | recusado | Garantido |
| 13 | Coluna obrigatória omitida | inserir sem `numero_patrimonio` | aceito, gravado como `""` | **Não garantido**: texto omitido vira texto vazio |
| 14 | Transações desfeitas (`db.transaction`) | inserir e depois `throw` dentro de uma transação | 0 linhas restantes | Garantido |
| 15 | Chave primária composta (`role_permissions`) | não testado | o Xano exige uma chave primária `int id` (ou `uuid`) em toda tabela ([referência de tabelas](https://cdn.jsdelivr.net/npm/@xano/developer-mcp/dist/xanoscript_docs/tables.md)) | **Não suportado** |
| 16 | Índices B-tree em colunas de chave estrangeira, data e status | índice `btree` em `parent_id` | criado pelo push | Suportado |

O `$error` era `null` dentro do `catch` em todos os casos recusados, então a API não pode depender do texto de erro do banco. Os endpoints precisam verificar unicidade e validade por conta própria para devolver mensagens por campo, e tratar a restrição do banco como uma rede de segurança.

## Consequências para o design

1. **Chaves estrangeiras (#1, #2):** toda gravação que define uma referência precisa verificar se a linha de destino existe e, quando exigido, está ativa, dentro do mesmo `db.transaction`. Exclusões físicas de linhas referenciadas precisam ser bloqueadas na API. A regra existente "desativar, não apagar" cobre catálogos e usuários.
2. **Série opcional e única (#6):** a API converte um `numero_serie` vazio ou em branco para `null` antes de gravar.
3. **Texto obrigatório (#13):** a API recusa campos de texto obrigatórios ausentes ou em branco. O banco gravaria `""` no lugar.
4. **`role_permissions` (#15):** usar uma chave primária substituta `id` mais um índice único em (`role_id`, `permission_id`). A unicidade da concessão continua garantida pelo banco (#7).
5. Unicidade simples e composta, filtros `min:`, enums, null em campos obrigatórios e transações são garantidos pelo banco e podem ser usados como projetado.
