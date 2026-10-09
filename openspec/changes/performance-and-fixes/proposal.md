# Proposta

## Por quê

Com o backend no plano Free do Xano, as telas demoravam: cada chamada abria uma conexão nova (~0,4 s a mais), as chamadas de uma mesma tela saíam uma depois da outra e alguns endpoints faziam dezenas de consultas por requisição (o acompanhamento fazia 50 só para as datas de manutenção). Ao mesmo tempo, apareceram defeitos que deixavam controles sem resposta ou com erro ("Mostrar inativos" sem efeito visível, "Missing param: field_value" ao abrir a manutenção corretiva). Esta change registra as melhorias de tempo de resposta e as correções feitas depois da `dashboard-redesign`.

## O que muda

- **Conexões reaproveitadas:** o app mantém a conexão com o Xano aberta entre as requisições, em vez de abrir uma nova a cada chamada; leituras interrompidas por uma conexão fechada pelo servidor são repetidas automaticamente.
- **Carregamento em paralelo:** as chamadas independentes de cada tela (opções dos filtros, lista principal, histórico, auditoria, responsáveis) são feitas ao mesmo tempo.
- **Menos consultas no Xano:**
  - `GET acompanhamento` busca a última e a próxima manutenção da página inteira em 2 consultas (antes 2 por equipamento);
  - `GET dashboard` conta as ocorrências por severidade e status na lista que já busca (antes 8 consultas de contagem).
- **"Mostrar inativos" (catálogos):** o controle muda na hora, mostra que está carregando e informa quantos registros inativos foram incluídos (ou que não há nenhum).
- **Ids opcionais vazios no Xano:** `ocorrencias/{id}`, `auth/me` e `equipamentos/{id}` deixam de falhar quando o responsável, o perfil ou o criador não existe.

## Capacidades

### Novas capacidades
- `ui-responsiveness`: como as telas reagem às ações do usuário e ao carregamento de dados: resposta imediata dos controles, indicação de carregamento e retorno quando um filtro não muda o resultado.

### Capacidades modificadas
<!-- Nenhuma: ainda não há specs principais em openspec/specs/ para inventário, manutenção ou relatórios. A meta de
2 s no p95 para listagens (change hospital-hardware-manager) continua a mesma; esta change ajuda a cumpri-la. -->

## Impacto

- `hardware/api.py`: cliente HTTP compartilhado com keep-alive e nova tentativa de leituras.
- `hardware/options.py` e páginas (`dashboard`, `tracking`, `equipment`, `maintenance`, `occurrences`, `catalog`, `reports`, `users`): carregamento em paralelo.
- `hardware/pages/catalog.py`: controle "Mostrar inativos".
- `xano/api/reports/acompanhamento_GET.xs`, `xano/api/reports/dashboard_GET.xs`, `xano/api/maintenance/ocorrencias_by_id_GET.xs`, `xano/api/authentication/auth/me_GET.xs`, `xano/api/inventory/equipamentos_by_id_GET.xs`.
- Contagem de ocorrências no painel: ocorrências de equipamentos descomissionados deixam de ser contadas, como já acontecia na lista de alertas recentes.
- O número total de requisições por tela não muda (o limite do plano Free continua o mesmo).
