# Delta da spec

## Propósito

Permitir que as equipes de manutenção planejem e documentem serviços preventivos e corretivos, registrem ocorrências operacionais e consultem um histórico confiável de serviços de cada equipamento.

## ADDED Requirements

### Requirement: Agendar manutenção preventiva
O sistema DEVE permitir que usuários autorizados agendem manutenção preventiva para um equipamento, com data planejada, descrição ou checklist da manutenção e usuário responsável. Um agendamento PODE ter um intervalo de recorrência; quando um trabalho recorrente é concluído, o sistema DEVE sugerir a próxima data planejada (data planejada mais o intervalo) e NÃO DEVE agendá-la automaticamente. O responsável DEVE ser um usuário habilitado cujo perfil pode atuar em manutenções. O sistema DEVE identificar os trabalhos preventivos próximos e atrasados pela data planejada e pelo status atual da manutenção; trabalho pendente (próximo e atrasado) DEVE significar somente manutenção preventiva planejada, com a mesma definição nas listas de manutenção, no painel e nos relatórios. A data da próxima manutenção mostrada para um equipamento DEVE ser derivada da manutenção preventiva planejada futura mais próxima e NÃO DEVE ser gravada como uma cópia editável à parte.

#### Scenario: Agendar uma manutenção preventiva
- **QUANDO** um usuário autorizado agenda uma manutenção preventiva com um equipamento, uma data planejada e um responsável válidos
- **ENTÃO** o sistema DEVE criar uma manutenção planejada vinculada a esse equipamento e mostrá-la no calendário de manutenções e nas listas de trabalho pendente

#### Scenario: Identificar trabalhos próximos e atrasados
- **QUANDO** um usuário consulta as datas previstas das manutenções
- **ENTÃO** o sistema DEVE diferenciar os trabalhos próximos dos trabalhos planejados atrasados pela data planejada e excluir os registros concluídos ou cancelados

#### Scenario: Trabalho pendente não inclui manutenção corretiva
- **QUANDO** uma manutenção corretiva planejada e uma preventiva planejada estão datadas antes de hoje
- **ENTÃO** só o registro preventivo DEVE aparecer como atrasado, da mesma forma na lista de manutenções, no painel e no relatório de atrasadas

#### Scenario: A recorrência sugere sem agendar
- **QUANDO** um usuário autorizado conclui uma manutenção preventiva que tem intervalo de recorrência
- **ENTÃO** o sistema DEVE devolver a próxima data planejada sugerida e NÃO DEVE criar um novo registro de manutenção

#### Scenario: Recusar um responsável que não pode atuar na área
- **QUANDO** um usuário atribui uma manutenção ou ocorrência a um usuário cujo perfil não pode atuar nessa área
- **ENTÃO** o sistema DEVE recusar a atribuição e manter o responsável atual

### Requirement: Registrar manutenções corretivas e preventivas
O sistema DEVE permitir que usuários autorizados acompanhem as manutenções pelos estados `planned`, `in_progress`, `completed` e `canceled`, com tipo de manutenção `preventive` ou `corrective`. Um registro de manutenção DEVE referenciar um equipamento e DEVE guardar a data planejada, as datas reais de início/conclusão, o serviço executado, o resultado, o responsável e, quando houver, a ocorrência relacionada. Concluir uma manutenção DEVE exigir data de conclusão e resumo do serviço; cancelar DEVE exigir um motivo de cancelamento. Manutenções concluídas e canceladas DEVEM continuar no histórico. Uma manutenção corretiva PODE referenciar a ocorrência que motivou o serviço. Usuários limitados aos trabalhos atribuídos DEVEM alterar só as manutenções atribuídas a eles.

#### Scenario: Concluir uma manutenção com os detalhes do serviço
- **QUANDO** um usuário autorizado conclui uma manutenção e informa a data de conclusão e o resumo do serviço
- **ENTÃO** o sistema DEVE guardar os detalhes da conclusão no histórico do equipamento e atualizar a data derivada da última manutenção do equipamento

#### Scenario: Recusar conclusão ou cancelamento incompleto
- **QUANDO** um usuário tenta concluir uma manutenção sem data de conclusão ou sem resumo do serviço, ou cancelá-la sem motivo
- **ENTÃO** o sistema DEVE recusar a transição e manter o estado atual da manutenção

#### Scenario: Manter o histórico depois do cancelamento
- **QUANDO** um usuário cancela uma manutenção planejada informando o motivo
- **ENTÃO** o sistema DEVE guardar o registro cancelado e o motivo e DEVE excluir o registro dos cálculos futuros de trabalho pendente

### Requirement: Registrar e resolver ocorrências dos equipamentos
O sistema DEVE permitir que usuários autorizados criem uma ocorrência vinculada a um equipamento, com data do relato, descrição técnica e severidade. Quem relatou DEVE ser registrado, e a atribuição a um responsável, a data de resolução, o resumo da resolução e a manutenção relacionada PODEM ser registrados. Os estados da ocorrência DEVEM incluir `open`, `in_progress`, `resolved` e `canceled`. A resolução DEVE exigir data de resolução e resumo; o cancelamento DEVE exigir um motivo. As ocorrências DEVEM continuar disponíveis no histórico do equipamento depois de resolvidas ou canceladas. O responsável DEVE ser um usuário habilitado cujo perfil pode atuar em ocorrências. A partir de uma ocorrência aberta ou em andamento, um usuário autorizado DEVE poder abrir um formulário de manutenção corretiva já preenchido com o tipo corretivo e o equipamento da ocorrência, com a ocorrência vinculada automaticamente.

#### Scenario: Relatar uma ocorrência de equipamento
- **QUANDO** um usuário autorizado relata um problema com equipamento, data, descrição técnica e severidade válidos
- **ENTÃO** o sistema DEVE criar uma ocorrência aberta associada ao equipamento e ao usuário que relatou

#### Scenario: Resolver uma ocorrência com o resultado
- **QUANDO** um usuário autorizado resolve uma ocorrência e registra a data e o resumo da resolução
- **ENTÃO** o sistema DEVE guardar os detalhes da resolução e mostrar a ocorrência como resolvida no histórico do equipamento

#### Scenario: Recusar uma resolução incompleta
- **QUANDO** um usuário tenta resolver uma ocorrência sem data de resolução ou sem resumo
- **ENTÃO** o sistema DEVE recusar a mudança de estado e manter a ocorrência aberta ou em andamento

#### Scenario: Abrir uma manutenção corretiva a partir de uma ocorrência
- **QUANDO** um usuário autorizado escolhe abrir uma manutenção corretiva a partir de uma ocorrência aberta e salva o formulário
- **ENTÃO** o sistema DEVE criar uma manutenção corretiva para o equipamento da ocorrência, vinculada a ela, sem o usuário digitar o tipo, o equipamento ou a ocorrência

### Requirement: Oferecer o histórico completo de manutenção do equipamento
O sistema DEVE oferecer um histórico cronológico do equipamento (mais antigos primeiro) com as manutenções, as ocorrências e os eventos de instalação/remoção de componentes, com datas, tipos, estados, responsáveis e resumos registrados, quando houver. O sistema DEVE derivar a data da última manutenção da manutenção concluída mais recente e NÃO DEVE mostrar data quando não houver manutenção concluída. O histórico DEVE continuar disponível para equipamentos descomissionados e NÃO DEVE ser alterado pela exclusão de um item de catálogo ou de um usuário. Uma manutenção que ainda não começou DEVE ser datada no histórico pela data planejada no calendário.

#### Scenario: Consultar o histórico do equipamento
- **QUANDO** um usuário autorizado abre o histórico de um equipamento
- **ENTÃO** o sistema DEVE mostrar os eventos de manutenção, ocorrência e troca de componentes em ordem cronológica, inclusive os registros concluídos e cancelados

#### Scenario: Derivar as datas de manutenção
- **QUANDO** um usuário autorizado consulta um equipamento com manutenções concluídas e planejadas
- **ENTÃO** o sistema DEVE mostrar a data concluída mais recente como última manutenção e a data preventiva planejada futura mais próxima como próxima manutenção
