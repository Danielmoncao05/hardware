# Delta da spec

## Propósito

Oferecer acesso controlado e auditável aos dados operacionais dos equipamentos e dar às equipes autorizadas visões e exportações objetivas para o planejamento de inventário e manutenção.

## ADDED Requirements

### Requirement: Autenticar usuários e aplicar as permissões dos perfis
O sistema DEVE exigir um usuário autenticado para todos os dados não públicos do aplicativo e DEVE aplicar autorização em cada operação protegida. Ele DEVE suportar os perfis `administrator`, `asset_manager`, `technician` e `viewer`, com permissões para gestão de equipamentos e catálogos, gestão de manutenções e ocorrências, administração de usuários e perfis, e acesso somente leitura. Administradores DEVEM gerenciar usuários, perfis e permissões; gestores de patrimônio DEVEM gerenciar o inventário e ver os dados operacionais; técnicos DEVEM gerenciar as manutenções e ocorrências atribuídas a eles e ver os equipamentos relacionados; visualizadores DEVEM ter acesso somente leitura. O sistema DEVE negar operações não concedidas ao perfil do usuário, inclusive requisições diretas à API, e NÃO DEVE depender só de esconder controles da interface.

#### Scenario: Negar acesso sem autenticação
- **QUANDO** um usuário sem sessão autenticada válida pede dados protegidos de equipamentos
- **ENTÃO** o sistema DEVE negar o acesso e NÃO DEVE devolver registros protegidos

#### Scenario: Aplicar o perfil somente leitura do visualizador
- **QUANDO** um visualizador tenta criar, atualizar, desativar ou apagar um registro de equipamento, manutenção, ocorrência, usuário ou catálogo
- **ENTÃO** o sistema DEVE negar a operação e preservar os dados gravados

#### Scenario: Administrador gerencia o acesso dos usuários
- **QUANDO** um administrador cria um usuário ou altera o perfil ou a habilitação de um usuário
- **ENTÃO** o sistema DEVE gravar a mudança de acesso e aplicar o novo conjunto de permissões nas operações protegidas seguintes

#### Scenario: Usuário logado sem permissão para uma tela
- **QUANDO** um usuário logado abre uma tela cuja permissão o perfil dele não tem
- **ENTÃO** o sistema DEVE mostrar uma página de acesso negado que só exige sessão, NÃO DEVE mostrar os dados protegidos e NÃO DEVE redirecionar entre telas protegidas em loop

### Requirement: Criar contas com senha temporária
As contas DEVEM ser criadas somente por administradores; o cadastro público NÃO DEVE existir. Um administrador DEVE definir uma senha temporária ao criar uma conta, e a conta NÃO DEVE ter permissões até o usuário trocar essa senha no primeiro acesso. Trocar a senha DEVE exigir a senha atual e uma nova senha que siga a política de senhas (pelo menos 8 caracteres, com letras e números) e seja diferente da atual. Administradores NÃO DEVEM definir nem redefinir a senha de uma conta existente, por nenhum meio.

#### Scenario: Obrigar a troca de senha no primeiro acesso
- **QUANDO** um usuário entra com a senha temporária que um administrador definiu ao criar a conta
- **ENTÃO** o sistema DEVE exigir uma nova senha antes de qualquer outro uso e DEVE negar toda operação protegida até a troca dar certo

#### Scenario: Administrador não consegue definir a senha de um usuário existente
- **QUANDO** um administrador tenta definir ou redefinir a senha de uma conta existente
- **ENTÃO** o sistema DEVE recusar e a senha da conta DEVE continuar a mesma

### Requirement: Recuperar o acesso somente por links de redefinição enviados por e-mail
Um usuário que esquecer a senha DEVE recuperar o acesso somente por um link de redefinição enviado por e-mail, por meio de um serviço de e-mail externo. Um link de redefinição DEVE ser de uso único, DEVE ser guardado só como hash, DEVE expirar depois de 60 minutos e DEVE ser invalidado por qualquer pedido mais novo. Concluir uma redefinição DEVE definir a nova senha em um passo e NÃO DEVE criar sessão nem dar acesso a nenhuma outra operação; também DEVE limpar uma senha temporária pendente. Pedidos para contas desconhecidas ou desabilitadas DEVEM receber a mesma resposta que pedidos para contas ativas.

#### Scenario: Redefinir uma senha esquecida
- **QUANDO** um usuário abre um link de redefinição válido, não expirado e não usado, e envia uma nova senha que segue a política
- **ENTÃO** o sistema DEVE trocar a senha, marcar o link como usado e exigir um login normal depois

#### Scenario: Recusar um link de redefinição inutilizável sem revelar a conta
- **QUANDO** uma redefinição é tentada com um link inválido, expirado ou já usado, ou para uma conta desconhecida ou desabilitada
- **ENTÃO** o sistema DEVE recusar com a mesma resposta em todos os casos e NÃO DEVE revelar se a conta existe

### Requirement: Gerenciar perfis
Administradores DEVEM poder criar perfis, conceder e revogar permissões neles e ativá-los ou desativá-los; perfis NUNCA DEVEM ser apagados. O perfil `administrator` NÃO DEVE ser desativado e NÃO DEVE perder a permissão de administração de usuários. Um perfil ainda atribuído a usuários habilitados NÃO DEVE ser desativado. Mudanças em perfis DEVEM ser auditadas.

#### Scenario: Criar um perfil e conceder permissões
- **QUANDO** um administrador cria um perfil e concede permissões a ele
- **ENTÃO** o sistema DEVE gravar o perfil e as concessões, registrar eventos de auditoria e aplicar as concessões aos usuários com esse perfil

#### Scenario: Recusar uma desativação de perfil insegura
- **QUANDO** um administrador tenta desativar o perfil `administrator` ou um perfil atribuído a usuários habilitados
- **ENTÃO** o sistema DEVE recusar e manter o perfil ativo

### Requirement: Auditar mudanças operacionais e de acesso relevantes
O sistema DEVE registrar um evento de auditoria para mudanças de usuário relevantes à autenticação e para ações significativas de criação, atualização, troca de status e desativação em equipamentos, catálogos, instalações de componentes, manutenções, ocorrências e permissões de usuário. Cada evento DEVE identificar o usuário que agiu, a ação, o registro afetado e a data e hora. O histórico de auditoria DEVE ser legível só por usuários autorizados e NÃO DEVE ser editável pelos fluxos normais do aplicativo. Eventos de auditoria NÃO DEVEM conter material de credenciais, como hashes de senha ou tokens de redefinição; eventos registrados antes desta regra DEVEM ser mantidos, com apenas os valores de credenciais removidos.

#### Scenario: Registrar a troca de status de um equipamento
- **QUANDO** um usuário autorizado troca o status de um equipamento
- **ENTÃO** o sistema DEVE registrar quem agiu, o equipamento, o status anterior e o novo, e a data e hora

#### Scenario: Preservar uma mudança de manutenção auditável
- **QUANDO** um usuário muda o estado de uma manutenção ou registra a conclusão dela
- **ENTÃO** o sistema DEVE adicionar um evento de auditoria que identifica quem agiu, a manutenção, a ação e a data e hora

#### Scenario: Manter credenciais fora do histórico de auditoria
- **QUANDO** um usuário autorizado lê os eventos de auditoria, inclusive eventos registrados antes desta regra
- **ENTÃO** nenhum evento DEVE conter hash de senha ou token de redefinição, e nenhum evento histórico DEVE ter sido apagado

### Requirement: Oferecer um painel operacional
O sistema DEVE oferecer um painel autenticado que resuma os totais de equipamentos ativos por status e categoria, as manutenções preventivas próximas e atrasadas, as ocorrências abertas por severidade e status, e a atividade de manutenção recente. Os valores do painel DEVEM ser derivados dos registros gravados de equipamentos e manutenções e DEVEM respeitar as permissões de leitura do usuário e os filtros selecionados.

#### Scenario: Ver o resumo operacional
- **QUANDO** um usuário autorizado abre o painel
- **ENTÃO** o sistema DEVE mostrar, a partir dos registros disponíveis, os totais atuais por status/categoria, os trabalhos previstos e atrasados, as contagens de ocorrências abertas e a atividade de manutenção recente

#### Scenario: Filtrar o painel por localização
- **QUANDO** um usuário autorizado seleciona um filtro de localização
- **ENTÃO** o sistema DEVE recalcular os resumos de equipamentos e os resumos operacionais relacionados para essa localização, sem incluir registros não relacionados

#### Scenario: O filtro de localização não inclui sublocalizações
- **QUANDO** um usuário autorizado filtra por uma localização que tem sublocalizações
- **ENTÃO** o sistema DEVE incluir só os equipamentos atribuídos diretamente à localização selecionada, da mesma forma no painel, nas listas e nos relatórios

### Requirement: Gerar relatórios operacionais
O sistema DEVE permitir que usuários autorizados vejam e filtrem relatórios de inventário de equipamentos, status e localização, manutenções próximas ou atrasadas, histórico de manutenções e ocorrências abertas ou resolvidas. Os relatórios DEVEM oferecer resultados na tela e uma exportação CSV para download, com os mesmos filtros e o mesmo escopo de dados autorizado. As colunas dos relatórios DEVEM conter só campos de gestão de equipamentos, manutenção, ocorrências e identificação de usuários, e NÃO DEVEM conter dados de pacientes ou clínicos.

#### Scenario: Filtrar e exportar um relatório de equipamentos
- **QUANDO** um usuário autorizado filtra um relatório de equipamentos por categoria, localização ou status e pede a exportação CSV
- **ENTÃO** o sistema DEVE exportar só os registros que atendem aos filtros e às permissões de leitura do usuário

#### Scenario: Exportar o relatório de manutenções atrasadas
- **QUANDO** um usuário autorizado pede um relatório de manutenções atrasadas para um período selecionado
- **ENTÃO** o sistema DEVE devolver as manutenções preventivas planejadas que estão atrasadas e não foram concluídas nem canceladas, com o equipamento e a localização correspondentes

### Requirement: Isolar os dados institucionais de cada implantação
Cada implantação DEVE atender uma única instituição, e todos os dados de equipamentos, catálogos de referência, manutenções, ocorrências, usuários, auditoria, painel e relatórios DEVEM ficar restritos a essa implantação. O sistema NÃO DEVE expor nem combinar dados de outra instituição por rotas do aplicativo, operações da API, buscas, exportações ou processamento em segundo plano.

#### Scenario: Consultar registros dentro de uma implantação
- **QUANDO** um usuário autenticado busca ou exporta registros em uma instalação
- **ENTÃO** o sistema DEVE devolver só os registros gravados para essa instalação

#### Scenario: Impedir o acesso a dados de outra implantação
- **QUANDO** uma requisição informa um identificador que pertence a dados de fora da implantação ativa
- **ENTÃO** o sistema NÃO DEVE devolver dados de outra implantação e NÃO DEVE revelar se o registro externo existe

### Requirement: Proteger a disponibilidade do serviço e os dados dos usuários
O sistema DEVE proteger credenciais e sessões autenticadas usando os mecanismos seguros suportados pela plataforma escolhida, DEVE usar transporte criptografado na comunicação entre o navegador e o serviço, e DEVE evitar expor segredos em estado visível ao cliente ou em logs. As listagens padrão com filtros DEVEM ter como meta um tempo de resposta de no máximo 2 segundos no percentil 95, em uma instalação com até 10.000 equipamentos e carga nominal. O aplicativo DEVE continuar utilizável em telas de desktop e tablet e DEVE oferecer controles com rótulos e fluxos principais operáveis pelo teclado.

#### Scenario: Carregar uma lista de inventário dentro da meta
- **QUANDO** um usuário carrega uma listagem de inventário padrão, paginada e filtrada, com carga nominal e até 10.000 equipamentos
- **ENTÃO** o sistema DEVE devolver a listagem em até 2 segundos no percentil 95

#### Scenario: Usar um fluxo principal com navegação pelo teclado
- **QUANDO** um usuário navega por um formulário de equipamento ou de manutenção usando o teclado
- **ENTÃO** o sistema DEVE oferecer controles com rótulos em uma ordem de foco lógica e permitir enviar e validar sem precisar do mouse

### Requirement: Usar um único fuso horário da instituição
Os horários digitados nos formulários e os horários exibidos DEVEM usar o fuso horário configurado da instituição, qualquer que seja o fuso do navegador do usuário. Datas de calendário, como as datas planejadas de manutenção e as datas de aquisição, DEVEM ser mostradas como foram digitadas e NÃO DEVEM mudar por conversão de fuso.

#### Scenario: Digitar e ver um horário de conclusão
- **QUANDO** um usuário registra o horário de conclusão de uma manutenção e depois o consulta, de um navegador em qualquer fuso
- **ENTÃO** o sistema DEVE mostrar o mesmo horário que foi digitado, no fuso da instituição, e as datas planejadas DEVEM mostrar o mesmo dia de calendário que foi agendado
