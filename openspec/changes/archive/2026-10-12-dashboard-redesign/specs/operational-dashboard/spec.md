# Delta da spec

## Purpose

Define o conteúdo e a organização do painel operacional: indicadores do parque de equipamentos, distribuição por setor, próximas manutenções, alertas recentes e equipamentos com problemas críticos, com acesso direto às ações de correção.

## ADDED Requirements

### Requirement: Cabeçalho do painel
O painel DEVE mostrar o título "Painel", um subtítulo descrevendo o resumo operacional e a data de hoje por extenso, calculada no fuso horário da instituição.

#### Scenario: Data de hoje no fuso da instituição
- **QUANDO** um usuário abre o painel de um navegador configurado em outro fuso horário
- **ENTÃO** o sistema DEVE mostrar a data de hoje no fuso da instituição, por extenso e em português

### Requirement: Indicadores do parque de equipamentos
O painel DEVE mostrar quatro indicadores, calculados a partir dos registros gravados e respeitando o filtro de localização: total de equipamentos ativos (todos menos os descomissionados), equipamentos disponíveis (status operacional), equipamentos em manutenção e equipamentos com problemas críticos. Um equipamento tem problema crítico quando está fora de serviço ou tem alguma ocorrência crítica aberta ou em andamento, a mesma regra dos alertas.

#### Scenario: Indicadores conferem com os registros
- **QUANDO** um usuário autorizado abre o painel
- **ENTÃO** cada indicador DEVE mostrar a mesma quantidade que os registros gravados para aquela regra

#### Scenario: Equipamento crítico contado uma vez
- **QUANDO** um equipamento está fora de serviço e também tem duas ocorrências críticas abertas
- **ENTÃO** o indicador de problemas críticos DEVE contar esse equipamento uma única vez

### Requirement: Distribuição de equipamentos por setor
O painel DEVE mostrar um gráfico de barras com a quantidade de equipamentos ativos em cada localização (setor), considerando só os equipamentos atribuídos diretamente a cada localização. O gráfico DEVE ter um equivalente em texto acessível a leitores de tela e DEVE continuar legível nos temas claro e escuro.

#### Scenario: Ver a distribuição por setor
- **QUANDO** um usuário autorizado abre o painel
- **ENTÃO** o sistema DEVE mostrar uma barra para cada localização com equipamentos ativos, com a quantidade correspondente

#### Scenario: Nenhum equipamento ativo
- **QUANDO** não há equipamentos ativos no filtro atual
- **ENTÃO** o sistema DEVE mostrar uma mensagem de que não há equipamentos, em vez de um gráfico vazio

### Requirement: Próximas manutenções
O painel DEVE listar as próximas manutenções preventivas planejadas, das mais próximas para as mais distantes, com o equipamento, a localização e o prazo relativo à data de hoje ("Hoje", "Amanhã", "Em N dias"), e oferecer um link para a lista completa de manutenções.

#### Scenario: Prazo relativo
- **QUANDO** existe uma preventiva planejada para daqui a 3 dias
- **ENTÃO** o painel DEVE mostrá-la com o prazo "Em 3 dias"

#### Scenario: Ver todas as manutenções
- **QUANDO** o usuário aciona "Ver todas"
- **ENTÃO** o sistema DEVE abrir a lista de manutenções na aba de preventivas próximas

### Requirement: Alertas recentes
O painel DEVE mostrar uma tabela com as ocorrências abertas e em andamento mais recentes, com o equipamento, a localização, a descrição técnica com a severidade indicada visualmente e o tempo decorrido desde o relato ("10 min atrás", "2 h atrás"). A tabela NÃO DEVE mostrar dados de pacientes nem informações clínicas.

#### Scenario: Ocorrência recente aparece nos alertas
- **QUANDO** uma ocorrência acabou de ser registrada para um equipamento
- **ENTÃO** ela DEVE aparecer no topo da tabela de alertas recentes com o tempo decorrido desde o relato

#### Scenario: Ocorrência resolvida sai dos alertas
- **QUANDO** uma ocorrência é resolvida ou cancelada
- **ENTÃO** ela NÃO DEVE mais aparecer na tabela de alertas recentes

### Requirement: Equipamentos com problemas críticos
O painel DEVE mostrar um cartão para cada equipamento com problema crítico, com o equipamento, a localização, o motivo (fora de serviço e/ou a descrição técnica da ocorrência crítica) e a situação. Quando houver uma ocorrência crítica aberta ou em andamento, o cartão DEVE oferecer "Abrir manutenção corretiva", que abre o formulário de manutenção corretiva já vinculado a essa ocorrência e sujeito às mesmas permissões, e "Ver ocorrências", que abre as ocorrências do equipamento. Ações que o perfil do usuário não pode executar NÃO DEVEM ser oferecidas.

#### Scenario: Abrir manutenção corretiva a partir do painel
- **QUANDO** um usuário com permissão de gerenciar manutenções aciona "Abrir manutenção corretiva" no cartão de um equipamento crítico
- **ENTÃO** o sistema DEVE abrir o formulário de manutenção corretiva com o equipamento e a ocorrência já preenchidos

#### Scenario: Visualizador não vê a ação de manutenção
- **QUANDO** um visualizador abre o painel com equipamentos críticos
- **ENTÃO** o sistema DEVE mostrar os cartões sem a ação "Abrir manutenção corretiva"

#### Scenario: Nenhum problema crítico
- **QUANDO** nenhum equipamento está crítico
- **ENTÃO** o sistema DEVE mostrar uma mensagem de que não há problemas críticos

### Requirement: Filtros e seções detalhadas preservados
O painel DEVE manter o filtro por localização e os períodos das manutenções futuras e da atividade recente, aplicados a todas as seções, e DEVE manter, abaixo do novo layout, os totais por status e por categoria, as preventivas atrasadas e a atividade de manutenção recente. O layout DEVE se reorganizar em uma coluna em telas de tablet e celular.

#### Scenario: Filtrar o painel por localização
- **QUANDO** um usuário autorizado seleciona uma localização
- **ENTÃO** os indicadores, o gráfico, as listas e os cartões DEVEM considerar só os equipamentos daquela localização

#### Scenario: Painel em tela de celular
- **QUANDO** um usuário abre o painel em uma tela estreita
- **ENTÃO** as seções DEVEM aparecer uma abaixo da outra, sem rolagem horizontal da página
