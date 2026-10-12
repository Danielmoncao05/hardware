# Design

## Contexto

Ver `proposal.md` para a motivação. O painel atual (`hardware/pages/dashboard.py`) lê tudo de `GET dashboard` (`xano/api/reports/dashboard_GET.xs`), que já devolve totais por status e categoria, preventivas atrasadas e próximas, ocorrências abertas por severidade e status, e a atividade recente. O layout comum (`layout()` em `hardware/components.py`) tem a marca e o bloco do usuário na barra lateral, e o botão de tema da change `theme-toggle`. Os alertas já existem: `GET alertas` classifica cada equipamento como "critico" (fora de serviço ou ocorrência crítica aberta) ou "atencao", e `hardware/alerts.py` consulta esse endpoint a cada 60 s e abre um pop-up só quando há novidade.

Restrições que moldam a solução:
- O plano Free do Xano aceita 10 requisições a cada 20 s, e o painel já faz 1 a 2 por visita.
- Consultas paginadas do Xano devolveram lista vazia em `users GET` e nos relatórios (change `hospital-hardware-manager`, tarefas 8.12 e 8.13). As listas de `GET dashboard` também usam paginação e podem estar vindo vazias hoje.
- Nada de dados de pacientes ou clínicos (`tests/test_no_clinical_data.py`).

## Objetivos / Fora do escopo

**Objetivos:**
- Todo o novo painel sai de **uma** chamada a `GET dashboard`; o sino reaproveita a consulta de alertas que já roda.
- Mesmas regras de "crítico" no indicador, nos cartões, nos alertas e no acompanhamento.

**Fora do escopo:**
- Sistema de notificações (histórico, lidas/não lidas, envio por e-mail).
- Configurações do usuário (a engrenagem do mockup) e foto de perfil: o avatar mostra as iniciais.
- Central de ajuda ("Help Center" do mockup).
- Gráficos além da distribuição por setor.

## Decisões

### 1. Um endpoint, novos campos em `GET dashboard`
Acrescentar à resposta:
- `por_localizacao`: `[{localizacao_id, localizacao, total}]` com equipamentos ativos por localização direta (mesma regra de filtro de localização já aprovada), ordenado por total decrescente;
- `ocorrencias_recentes`: ocorrências abertas e em andamento, mais recentes primeiro, com `id`, `equipamento_id`, `equipamento`, `numero_patrimonio`, `localizacao`, `severidade`, `status`, `descricao_tecnica`, `relatada_em`;
- `criticos`: um item por equipamento crítico, com `equipamento_id`, `equipamento`, `numero_patrimonio`, `localizacao`, `status`, e a ocorrência crítica mais recente (`ocorrencia_id`, `descricao_tecnica`, `ocorrencia_status`) quando houver;
- `localizacao` em cada item de `preventivas_proximas`.

Alternativas consideradas: montar a distribuição no app a partir da lista de equipamentos (várias páginas de requisições, inviável no plano Free) ou chamar `GET alertas` e `GET ocorrencias` em separado (mais duas requisições por visita). Manter tudo em `GET dashboard` deixa a visita ao painel com uma chamada e garante que tudo use o mesmo filtro de localização.

### 2. Consultas sem paginação, totais por contagem
As listas novas e as existentes (`atrasadas`, `proximas`, `recentes`) passam a usar `return = {type: "list"}` sem `paging`, e os totais vêm de consultas `type: "count"`. O tamanho das listas é limitado no app (5 itens por seção no novo layout; 10 nas seções detalhadas). Com o volume esperado (até 10.000 equipamentos, poucas dezenas de ocorrências e preventivas abertas), devolver as listas inteiras é aceitável; se crescer, a solução é um filtro de data no `where`, não a paginação.

### 3. Regra de "crítico" compartilhada
A regra (status `out_of_service` ou ocorrência `critical` com status `open`/`in_progress`) é a de `GET alertas` e `GET acompanhamento`. No `GET dashboard` ela é calculada da mesma forma: lista das ocorrências críticas abertas + equipamentos fora de serviço, unidos por `equipamento_id`. O indicador é o tamanho de `criticos`, então indicador e cartões nunca divergem.

### 4. Barra superior em `layout()`
`layout()` ganha uma barra superior fixa no topo do conteúdo:
- esquerda: marca "HospitalTech" (e o botão de menu em telas estreitas);
- direita: botão de tema (movido da barra lateral), sino de alertas e menu do usuário (`rx.menu` com nome ou e-mail, perfil, "Alterar senha", "Sair"; avatar com as iniciais).

O sino usa `AlertState`: a cada consulta, o estado passa a guardar a lista atual completa (`current_items`), além das novidades que abrem o pop-up. O sino mostra a contagem e abre um popover com essa lista. Isso não adiciona requisições.

A barra lateral fica só com a navegação, com os nomes em português ("Painel", "Equipamentos", "Manutenções", "Ocorrências", "Catálogos e locais", "Acompanhamento", "Relatórios", "Usuários e perfis"), sem repetir usuário e "Sair".

### 5. Componentes do painel
- **Indicadores:** um `stat_card(ícone, rótulo, valor, cor)` em grade de 4 colunas (2 no tablet, 1 no celular).
- **Gráfico:** `rx.recharts.bar_chart` com `por_localizacao`, cores pelos tokens do tema (`rx.color("accent", 9)`) para funcionar nos dois temas. Abaixo dele vai uma lista com a mesma informação, visualmente oculta e lida por leitores de tela (o equivalente em texto exigido pela spec).
- **Próximas manutenções:** prazo relativo calculado no app a partir de `data_planejada` e da data de hoje no fuso da instituição (`options.TZ`), sem converter a data de calendário.
- **Alertas recentes:** tempo relativo calculado no app a partir de `relatada_em` (ms). A severidade aparece num `badge` com o ícone e a cor de `STATUS_COLOR`.
- **Críticos:** cartões com borda vermelha. "Abrir manutenção corretiva" leva a `/manutencoes?equipamento_id=X&ocorrencia_id=Y`, fluxo que já existe, mostrado só com `can_work_maintenance`; a API continua conferindo a permissão. "Ver ocorrências" leva a `/ocorrencias?equipamento_id=X`. Sem ocorrência crítica, isto é, só fora de serviço, o cartão mostra o link para o equipamento.
- **Seções detalhadas:** filtros, totais por status e categoria, preventivas atrasadas e atividade recente vão para uma seção abaixo, recolhível ("Mais detalhes"), aberta por padrão para não esconder conteúdo já aprovado.

### 6. Animação de entrada
Pedido do usuário durante a implementação: os indicadores e as seções do painel entram com uma animação curta (opacidade de 0 a 1 e subida de 8 px, 400 ms), em sequência (60 ms de atraso entre um bloco e o seguinte). É só CSS (`assets/app.css`, classe `hhm-enter` com a variável `--hhm-delay`), sem JavaScript nem nova dependência, e roda uma vez quando a página monta, não a cada atualização dos dados. Com `prefers-reduced-motion: reduce`, a animação é desligada. Alternativa descartada: animar os números contando até o valor (exigiria JavaScript e chamaria atenção demais num painel consultado o dia todo).

### 7. Textos do mockup
Itens com pacientes ou leitos ("Paciente realocado", "UTI Leito 04", "Risco de Quench") são substituídos pelos dados técnicos gravados: nome da localização e `descricao_tecnica`. Os rótulos do mockup em inglês ("Inventory", "Staff") ficam em português.

## Riscos / Concessões

- [O painel passa a depender de mais consultas dentro de `GET dashboard`] → São contagens e listas simples; medir o tempo de resposta com os dados de demonstração e, se passar de 2 s, mover `por_localizacao` para uma única consulta agrupada.
- [Listas sem paginação crescem com o histórico] → Só entram ocorrências abertas e em andamento e preventivas futuras dentro da janela; a atividade recente é limitada por `atividade_dias`.
- [O sino mostra a lista da última consulta (até 60 s de atraso)] → Mesmo comportamento dos alertas atuais; o painel em si é atualizado a cada visita.
- [Conflito com a change `theme-toggle`, que posiciona o botão de tema na barra lateral] → Esta change move o botão para a barra superior; atualizar as tarefas 2.2 e 2.3 daquela change (ou implementá-la antes) para não duplicar o botão.
- [Mudar a marca afeta testes e textos que procuram "Gestão de Equipamentos"] → Procurar e atualizar as ocorrências em `hardware/` e `tests/`.

## Plano de migração

1. Publicar o novo `dashboard_GET.xs` (só acrescenta campos; o painel atual continua funcionando com a resposta nova).
2. Publicar o frontend com o novo layout.
3. Rollback: voltar o frontend anterior; os campos extras da API não atrapalham.
