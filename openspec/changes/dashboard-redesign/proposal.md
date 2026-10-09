# Proposta

## Por quê

O painel atual é uma sequência de cartões e tabelas com o mesmo peso visual: quem abre o app não vê de imediato quantos equipamentos estão disponíveis, o que está crítico e o que vence em breve. A equipe aprovou um novo layout (mockup "HospitalTech") que destaca esses números, mostra a distribuição dos equipamentos por setor e coloca os problemas críticos com ação direta, e quer adotar a marca HospitalTech no app.

## O que muda

- **Marca HospitalTech:** o nome "Gestão de Equipamentos" é trocado por "HospitalTech" no topo das telas autenticadas, na tela de login e no título das páginas.
- **Barra superior nas telas autenticadas:** marca à esquerda; à direita, um sino que abre a lista atual de equipamentos que precisam de atenção (reaproveitando os alertas que já existem) e um menu do usuário (nome, perfil, "Alterar senha", "Sair"). Não há sistema novo de notificações.
- **Novo layout do painel**, nesta ordem:
  - título "Painel" com subtítulo e a data de hoje no fuso da instituição;
  - quatro cartões de indicadores: total de equipamentos ativos, disponíveis (operacionais), em manutenção e com problemas críticos;
  - gráfico de barras com a distribuição dos equipamentos ativos por setor (localização);
  - lista de próximas manutenções preventivas, com equipamento, setor e prazo relativo ("Amanhã", "Em 3 dias"), e link "Ver todas";
  - tabela de alertas recentes (ocorrências abertas e em andamento mais recentes): equipamento, setor, alerta com severidade e tempo relativo;
  - cartões de equipamentos com problemas críticos, com o motivo e ações que usam fluxos existentes: "Abrir manutenção corretiva" (já vinculada à ocorrência) e "Ver ocorrências".
- **Conteúdo atual preservado:** filtros de localização e de período, totais por status e por categoria, preventivas atrasadas e atividade de manutenção recente continuam no painel, numa seção abaixo do novo layout, para manter os requisitos já aprovados.
- **API do painel:** `GET dashboard` passa a devolver a distribuição por setor, as ocorrências recentes, a lista de equipamentos críticos e o setor das próximas manutenções, sem usar paginação nas consultas.
- Os textos do mockup que citam pacientes ou leitos ("Paciente realocado", "UTI Leito 04") **não** entram: o painel só mostra dados técnicos dos equipamentos e o nome da localização.

## Capacidades

### Novas capacidades
- `app-shell`: estrutura comum das telas autenticadas: marca, barra superior com acesso aos alertas e menu do usuário, e navegação.
- `operational-dashboard`: conteúdo e organização do painel operacional: indicadores, distribuição por setor, próximas manutenções, alertas recentes, equipamentos críticos com ações, e as seções e filtros já existentes.

### Capacidades modificadas
<!-- Nenhuma: ainda não há specs principais em openspec/specs/. O requisito "Oferecer um painel operacional" da change
hospital-hardware-manager (access-and-reporting) continua valendo; esta change o detalha e não remove nada dele. -->

## Impacto

- `hardware/components.py`: `layout()` ganha a barra superior (marca, sino, menu do usuário); a barra lateral deixa de repetir nome do usuário e "Sair". O botão de tema da change `theme-toggle` passa para a barra superior.
- `hardware/pages/dashboard.py`: nova organização, cartões de indicadores, gráfico (`rx.recharts`), listas e cartões de críticos.
- `hardware/alerts.py`: guardar a última lista de alertas para o sino mostrar a situação atual, não só as novidades.
- `hardware/pages/login.py` e `hardware/hardware.py`: marca HospitalTech na tela de login e nos títulos.
- `xano/api/reports/dashboard_GET.xs`: novos campos na resposta; consultas de lista sem paginação (a paginação devolvia lista vazia, ver change hospital-hardware-manager, tarefa 8.13).
- Depende das changes `hospital-hardware-manager` (painel, alertas, localizações) e `theme-toggle` (botão de tema); o painel precisa ficar legível nos dois temas.
- Sem novas dependências: `rx.recharts` já vem com o Reflex instalado.
