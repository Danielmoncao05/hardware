# Delta da spec

## Propósito

Definir os registros técnicos de inventário e de ciclo de vida usados para identificar, localizar, configurar e acompanhar os equipamentos hospitalares, sem tratar registros de pacientes ou clínicos.

## ADDED Requirements

### Requirement: Gerenciar os catálogos de referência dos equipamentos
O sistema DEVE permitir que usuários autorizados criem, vejam, atualizem e desativem fabricantes, categorias e modelos. Cada modelo DEVE referenciar exatamente um fabricante e uma categoria; um fabricante e uma categoria PODEM ser referenciados por vários modelos. As categorias DEVEM incluir o conjunto fornecido: monitor multiparamétrico, ventilador pulmonar, bomba de infusão, desfibrilador, eletrocardiógrafo, máquina de anestesia, ultrassom, raio-X, tomógrafo, ressonância magnética, oxímetro e aspirador hospitalar. A desativação DEVE preservar as referências históricas e impedir novas atribuições.

#### Scenario: Cadastrar um modelo com seu fabricante e sua categoria
- **QUANDO** um usuário autorizado salva um modelo com nome, fabricante e categoria existentes
- **ENTÃO** o sistema DEVE gravar o modelo com as duas chaves estrangeiras e deixá-lo disponível para o cadastro de equipamentos

#### Scenario: Recusar referências ausentes ou inativas no modelo
- **QUANDO** um usuário tenta salvar um modelo sem fabricante ou categoria, ou usando uma referência inativa
- **ENTÃO** o sistema DEVE recusar a mudança e indicar qual relação obrigatória é inválida

### Requirement: Cadastrar e manter os registros de equipamentos
O sistema DEVE permitir que usuários autorizados cadastrem e atualizem equipamentos com nome, número de patrimônio único, fabricante/modelo, localização e status operacional. O modelo DEVE determinar o fabricante e a categoria, e o sistema DEVE recusar um fabricante ou uma categoria informados à parte que sejam conflitantes. Número de série, ano de fabricação, data de aquisição, valor de aquisição, vida útil estimada e observações PODEM ficar em branco. Quando informados, o número de série DEVE ser único entre os equipamentos, o ano de fabricação DEVE ser um ano válido, o valor de aquisição NÃO DEVE ser negativo e a vida útil estimada DEVE ser positiva. A data de aquisição NÃO DEVE ser posterior à data atual. Equipamentos NÃO DEVEM ser cadastrados como `decommissioned`, e cadastrá-los como `out_of_service` DEVE exigir um motivo. O descomissionamento DEVE manter o registro do equipamento e seu histórico de manutenções e ocorrências.

#### Scenario: Cadastrar um equipamento com os campos obrigatórios válidos
- **QUANDO** um usuário autorizado envia nome do equipamento, número de patrimônio não usado, modelo, localização e um status permitido
- **ENTÃO** o sistema DEVE salvar o equipamento e mostrar a categoria e o fabricante derivados do modelo selecionado

#### Scenario: Recusar número de patrimônio ou de série duplicado
- **QUANDO** um usuário envia um número de patrimônio já em uso, ou um número de série não vazio já atribuído a outro equipamento
- **ENTÃO** o sistema DEVE recusar o salvamento sem alterar nenhum dos dois registros

#### Scenario: Preservar o histórico do equipamento ao descomissionar
- **QUANDO** um usuário autorizado descomissiona um equipamento que tem manutenções ou ocorrências
- **ENTÃO** o sistema DEVE manter o equipamento e o histórico relacionado e, por padrão, tirá-lo das visões de equipamentos ativos

### Requirement: Gerenciar localizações e o status operacional dos equipamentos
O sistema DEVE permitir que usuários autorizados mantenham as localizações e DEVE permitir que cada equipamento referencie uma localização ativa. O sistema DEVE oferecer os status `operational`, `under_maintenance`, `out_of_service` e `decommissioned`; uma troca de status DEVE ser autorizada, gravada e incluída no histórico de auditoria do equipamento. Trocar o status de um equipamento DEVE exigir a permissão de gestão de inventário, inclusive quando a troca é pedida ao iniciar ou concluir uma manutenção. Um motivo DEVE ser exigido, e registrado no histórico de auditoria, sempre que o equipamento passar a `out_of_service` ou `decommissioned`, por qualquer caminho. O descomissionamento DEVE ser definitivo: um equipamento descomissionado NÃO DEVE mudar de status, ser movido, ser editado nem ter componentes instalados ou removidos, e DEVE continuar legível com todo o seu histórico. Localizações inativas DEVEM continuar visíveis nos registros históricos, mas NÃO DEVEM poder ser escolhidas para equipamentos novos ou movidos. Os filtros de localização DEVEM considerar só a localização selecionada, não suas sublocalizações.

#### Scenario: Mover um equipamento para uma localização ativa
- **QUANDO** um usuário autorizado seleciona uma localização ativa para um equipamento
- **ENTÃO** o sistema DEVE atualizar a localização atual e manter a mudança no histórico de auditoria

#### Scenario: Impedir a atribuição de uma localização inativa
- **QUANDO** um usuário tenta cadastrar ou mover um equipamento para uma localização inativa
- **ENTÃO** o sistema DEVE recusar a operação e manter a localização existente

#### Scenario: Colocar um equipamento em manutenção
- **QUANDO** um usuário autorizado registra uma manutenção em andamento para um equipamento
- **ENTÃO** o sistema DEVE permitir colocar o status do equipamento em `under_maintenance` e DEVE mostrar esse status de forma consistente no inventário e nos painéis

#### Scenario: Exigir motivo para fora de serviço ou descomissionamento
- **QUANDO** um usuário cadastra um equipamento como `out_of_service`, troca o status dele para `out_of_service` ou `decommissioned`, ou conclui uma manutenção deixando-o `out_of_service`, sem informar um motivo
- **ENTÃO** o sistema DEVE recusar a operação e manter o status atual

#### Scenario: O descomissionamento é definitivo
- **QUANDO** um usuário tenta trocar o status, mover, editar ou alterar os componentes de um equipamento descomissionado
- **ENTÃO** o sistema DEVE recusar a operação e manter o registro e seu histórico inalterados

#### Scenario: Trocar o status pela manutenção exige permissão de inventário
- **QUANDO** um usuário sem a permissão de gestão de inventário inicia ou conclui uma manutenção e pede para trocar o status do equipamento
- **ENTÃO** o sistema DEVE recusar a requisição inteira, deixando inalterados tanto a manutenção quanto o status do equipamento

### Requirement: Catalogar e instalar componentes de hardware
O sistema DEVE permitir que usuários autorizados cataloguem componentes de hardware por nome e tipo, com fabricante, modelo, identificador de peça ou de série, especificações e observações opcionais. Os tipos de componente suportados DEVEM incluir processador, memória RAM, armazenamento, placa-mãe, fonte de alimentação, sensores, displays, baterias, módulos eletrônicos, placas de comunicação e outros componentes. Um equipamento DEVE aceitar zero ou mais componentes instalados, e um componente do catálogo DEVE poder ser instalado em zero ou mais equipamentos. Cada instalação DEVE identificar o equipamento e o componente e PODE registrar slot ou sequência, quantidade, data de instalação, data de remoção e observações. As instalações históricas DEVEM continuar consultáveis depois da remoção.

#### Scenario: Instalar e remover componentes
- **QUANDO** um usuário autorizado instala um componente do catálogo em um equipamento e depois registra a remoção dele
- **ENTÃO** o sistema DEVE preservar a relação entre equipamento e componente e os detalhes de instalação/remoção no histórico técnico do equipamento

#### Scenario: Recusar uma instalação de componente inválida
- **QUANDO** um usuário tenta uma instalação sem equipamento ou componente, ou com quantidade que não seja positiva
- **ENTÃO** o sistema DEVE recusá-la e NÃO DEVE criar uma relação órfã

### Requirement: Manter os dados de inventário técnicos e não clínicos
O sistema DEVE coletar e mostrar somente informações técnicas e operacionais dos equipamentos. Ele NÃO DEVE oferecer diagnóstico médico, prontuários, identificadores de pacientes, observações clínicas nem campos relacionados a pacientes nos fluxos de equipamentos, componentes, localizações, manutenções, ocorrências, painel ou relatórios. As descrições de ocorrência digitadas pelos usuários DEVEM tratar de sintomas do equipamento ou observações operacionais e NÃO DEVEM ser usadas para tomar decisões clínicas.

#### Scenario: Registrar uma observação técnica do equipamento
- **QUANDO** um usuário registra a descrição de uma falha usando os campos de equipamento e manutenção
- **ENTÃO** o sistema DEVE associar a observação só às operações do equipamento e NÃO DEVE criar nem deduzir um registro de paciente ou de diagnóstico

#### Scenario: Tentar usar um fluxo clínico fora do escopo
- **QUANDO** um usuário procura registros de pacientes ou funcionalidades de diagnóstico
- **ENTÃO** o sistema NÃO DEVE oferecer nenhum fluxo, entidade ou relatório desse tipo no sistema de gestão de equipamentos
