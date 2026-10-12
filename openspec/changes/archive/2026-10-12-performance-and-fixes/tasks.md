# Tarefas

## 1. App

- [x] 1.1 Cliente HTTP compartilhado com keep-alive em `hardware/api.py` e nova tentativa de leituras em conexão fechada; verificado com os testes `test_requests_share_one_http_client` e `test_get_is_retried_once_on_a_dropped_keepalive_connection`
- [x] 1.2 Listas de opções carregadas em paralelo em `OptionsState._load_options`; verificado com `test_option_lists_are_reused_within_ttl`
- [x] 1.3 Carregamento em paralelo no painel, acompanhamento, equipamentos (lista, detalhe, formulário), manutenções, ocorrências, catálogos, relatórios e usuários; verificado com `pytest` e `reflex compile --dry`
- [x] 1.4 "Mostrar inativos" com resposta imediata, controle desabilitado durante a recarga, rótulo ao lado do controle e aviso de quantos inativos foram incluídos; verificado com `reflex compile --dry`
- [ ] 1.5 Verificar no navegador que "Mostrar inativos" liga na hora, mostra o carregamento e o aviso, e que um clique duplo não desfaz a escolha

## 2. Xano

- [x] 2.1 `GET acompanhamento`: datas de última e próxima manutenção em 2 consultas por página; verificado com `xano workspace push --dry-run`
- [x] 2.2 `GET dashboard`: contagens de ocorrências por severidade e status a partir de `ocorrencias_recentes`; verificado com `xano workspace push --dry-run`
- [x] 2.3 `ocorrencias/{id}`, `auth/me` e `equipamentos/{id}`: `db.get` só com id existente; verificado com `xano workspace push --dry-run`
- [ ] 2.4 Depois de publicado, verificar com `scripts/diagnostico_painel.py` os tempos de `GET dashboard` e `GET acompanhamento` (com e sem o filtro de saúde "critico") e que as linhas do acompanhamento continuam com as datas de manutenção; registrar os tempos aqui
- [ ] 2.5 Verificar no navegador que "Abrir manutenção corretiva" a partir do painel abre o formulário já vinculado à ocorrência, sem "Missing param: field_value"
