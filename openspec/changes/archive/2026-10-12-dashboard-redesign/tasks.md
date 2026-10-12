# Tarefas

## 1. API do painel

- [ ] 1.1 Em `xano/api/reports/dashboard_GET.xs`, trocar as listas paginadas (`atrasadas`, `proximas`, `recentes`) por `return = {type: "list"}` e calcular os totais com consultas `count`; verificar com `xano workspace push --dry-run` que não há erros e, depois de publicado, que preventivas atrasadas e próximas voltam a aparecer no painel atual
- [ ] 1.2 Acrescentar `localizacao` aos itens de `preventivas_proximas` (join com `localizacoes`) e verificar na resposta de `GET dashboard` que cada item traz o nome do setor
- [ ] 1.3 Acrescentar `por_localizacao` (equipamentos ativos por localização direta, ordenado por total, respeitando `localizacao_id`) e verificar que a soma dos totais é igual a `equipamentos_ativos`
- [ ] 1.4 Acrescentar `ocorrencias_recentes` (abertas e em andamento, mais recentes primeiro, com equipamento, setor, severidade, status, descrição e `relatada_em`) e verificar que uma ocorrência resolvida deixa de aparecer
- [ ] 1.5 Acrescentar `criticos` (um item por equipamento fora de serviço ou com ocorrência crítica aberta, com a ocorrência crítica mais recente quando houver) e verificar contra `GET alertas` que os equipamentos "critico" são os mesmos

## 2. Estrutura comum (app-shell)

- [x] 2.1 Trocar a marca para "HospitalTech" em `layout()`, na tela de login e nos títulos das páginas; atualizar os testes que citam "Gestão de Equipamentos" e verificar com `pytest` e `reflex compile --dry`
- [x] 2.2 Em `hardware/alerts.py`, guardar a lista atual completa a cada consulta (`current_items`) e verificar com um teste unitário que ela é atualizada mesmo sem novidades para o pop-up
- [ ] 2.3 Criar a barra superior em `layout()`: marca, botão de tema (movido da barra lateral), sino com contagem e popover dos alertas atuais (só com `can_read_reports`) e menu do usuário com nome ou e-mail, perfil, "Alterar senha" e "Sair"; verificar no navegador nos dois temas e pelo teclado
- [ ] 2.4 Deixar a barra lateral só com a navegação, com os nomes em português, e verificar que um visualizador não vê "Usuários e perfis"
- [x] 2.5 Atualizar as tarefas 2.2 e 2.3 da change `theme-toggle` para o botão de tema na barra superior e verificar que ele aparece uma única vez em cada largura de tela

## 3. Novo layout do painel

- [x] 3.1 Cabeçalho com título, subtítulo e data de hoje por extenso no fuso da instituição; verificar com um teste unitário da formatação da data
- [ ] 3.2 Quatro cartões de indicadores (ativos, disponíveis, em manutenção, críticos) em grade responsiva; verificar os números contra os dados de demonstração
- [ ] 3.3 Gráfico de barras por setor com `rx.recharts`, cores pelos tokens do tema, equivalente em texto para leitores de tela e mensagem quando não há equipamentos; verificar nos temas claro e escuro
- [x] 3.4 Lista de próximas manutenções (5 itens) com setor e prazo relativo, e link "Ver todas" para `/manutencoes`; verificar o prazo relativo com um teste unitário (hoje, amanhã, em N dias)
- [x] 3.5 Tabela de alertas recentes (5 itens) com setor, severidade e tempo relativo; verificar o tempo relativo com um teste unitário
- [ ] 3.6 Cartões de equipamentos críticos com motivo, "Abrir manutenção corretiva" (só com permissão de manutenção) e "Ver ocorrências", e mensagem quando não há críticos; verificar que a ação abre o formulário corretivo já vinculado e que um visualizador não a vê
- [ ] 3.7 Mover filtros, totais por status e categoria, preventivas atrasadas e atividade recente para a seção "Mais detalhes" abaixo do novo layout; verificar que o filtro de localização muda todas as seções

- [ ] 3.8 Animação de entrada (design, decisão 6): `assets/app.css` com a classe `hhm-enter` registrada no app e aplicada aos indicadores e às seções em sequência; verificar no navegador que os blocos entram em sequência e que, com "reduzir movimento" ligado no sistema, aparecem sem animação

## 4. Verificação

- [x] 4.1 Rodar `pytest` (incluindo `tests/test_no_clinical_data.py`) e `reflex compile --dry` e verificar que passam
- [ ] 4.2 Com os dados de demonstração, abrir o painel no desktop, tablet e celular, nos dois temas, e conferir com o mockup que todas as seções aparecem, sem rolagem horizontal e sem texto ilegível
- [ ] 4.3 Medir o tempo de `GET dashboard` com os dados de demonstração e verificar que fica abaixo de 2 s; registrar o resultado
