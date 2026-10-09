# Design

## Contexto

Ver `proposal.md` para a motivação e as três specs de capacidades para o comportamento observável e os cenários de aceitação. Hoje o repositório tem uma tela inicial em Reflex e exportações do quick-start do Xano para usuários, autenticação, verificação de perfis e log de eventos; não há implementação do domínio de equipamentos. O escopo escolhido é uma implantação por instituição, usando Reflex para o aplicativo e Xano para as APIs autenticadas e a persistência relacional.

## Objetivos / Fora do escopo

**Objetivos:**

- Estabelecer um modelo relacional normalizado para equipamentos, catálogos, instalações de componentes, localizações, manutenções, ocorrências, usuários, permissões e eventos de auditoria.
- Manter as regras de negócio e a autorização aplicadas na fronteira da API/dados, não só na interface.
- Oferecer um caminho implementável a partir da base existente, sem trocar a plataforma escolhida.
- Manter os dados operacionais dos equipamentos separados das informações de pacientes e clínicas.

**Fora do escopo:**

- Particionamento de dados multi-tenant dentro de uma implantação; cada instituição recebe uma implantação separada.
- Fluxos clínicos, registros de pacientes, diagnóstico médico, coleta de telemetria ou controle de dispositivos.
- Integrações com sistemas de informação hospitalar, compras, financeiro ou fornecedores externos de manutenção neste escopo inicial.
- Exclusão definitiva de registros que têm histórico operacional.

## Decisões

### Arquitetura do aplicativo

- **Frontend:** usar o aplicativo Python Reflex existente para as telas autenticadas, navegação, formulários, filtros e apresentação do painel e dos relatórios.
- **API e persistência:** usar os grupos de endpoints do Xano como fronteira da API e o banco relacional do Xano para as tabelas do aplicativo. Manter a validação oficial, as verificações de relacionamento, as verificações de perfil e as transições de estado nas operações da API. O frontend DEVE chamar essas operações em vez de manipular a persistência diretamente.
- **Autenticação:** estender o modelo de autenticação existente do Xano. Desativar o cadastro público em produção; administradores criam e desabilitam contas. Manter as credenciais no mecanismo de autenticação, nunca em tabelas gerais do aplicativo ou em estado visível ao cliente.
- **Alternativas consideradas:** uma API própria com banco relacional separado daria portabilidade, mas duplicaria a base do Xano já existente. Um design em que o navegador acessa o banco diretamente exporia credenciais e enfraqueceria a autorização centralizada, por isso não foi escolhido.

### Desempenho com o limite do plano do Xano

O plano Free do Xano aceita 10 requisições a cada 20 segundos. Para a navegação não esbarrar nesse limite:

- **Perfil reaproveitado por 60 s**: o guard das páginas só consulta `auth/me` de novo depois desse tempo. Mudanças de perfil, permissão ou habilitação aparecem na interface em até 60 s; a API as aplica na hora em toda operação.
- **Listas de opções reaproveitadas por 5 min** (localizações, categorias, fabricantes, modelos, componentes, responsáveis). A tela de catálogos atualiza essas listas a partir dos próprios dados depois de cada cadastro ou edição.
- **Páginas de listagem reaproveitadas por 30 s** (equipamentos, manutenções, ocorrências, relatórios). Qualquer escrita (método diferente de GET) esvazia esse cache, e o encerramento da sessão também.
- **Filtragem local:** quando todas as ocorrências ou manutenções do filtro cabem em uma resposta (até 100), abas, paginação e calendário são filtrados no app, com as mesmas regras da API (trabalho pendente = preventivas planejadas, comparando com a data de hoje em UTC). Acima disso, a paginação continua na API.
- **Resposta imediata:** abas, páginas e filtros mudam na tela antes da resposta da API, com indicação de carregamento.
- **HTTP 429:** o cliente espera (respeitando `Retry-After`, no máximo 8 s) e tenta de novo até 2 vezes. Se ainda falhar, mostra uma mensagem em português.

### Schema relacional e chaves

As tabelas usam uma chave primária `id` gerada e imutável. O Xano exige essa chave em toda tabela, então `role_permissions` também tem uma chave `id`, e o par (`role_id`, `permission_id`) é protegido por um índice único em vez de uma chave primária composta (ver `validation.md`). A tabela associativa `equipamento_componentes` usa seu próprio `id` gerado para que o mesmo item do catálogo de componentes possa ter várias instâncias instaladas em um equipamento. As chaves estrangeiras usam semântica de exclusão restritiva para registros com histórico; dados de referência são desativados em vez de apagados fisicamente. Colunas obrigatórias não aceitam null. Colunas opcionais aceitam null. As datas e horas são gravadas de forma consistente em UTC e apresentadas no fuso da instituição (`HHM_TIMEZONE`), o mesmo fuso usado para interpretar horários digitados nos formulários.

| Tabela | Chave primária | Campos obrigatórios | Campos opcionais e relacionamentos |
|---|---|---|---|
| `fabricantes` | `id` | `nome` (único) | `site`, `contato_suporte`, `observacoes`, `ativo`, datas de registro |
| `categorias` | `id` | `nome` (único) | `descricao`, `ativo`, datas de registro. Criar as 12 categorias especificadas em `equipment-inventory/spec.md`. |
| `modelos` | `id` | `nome`, FK `fabricante_id`, FK `categoria_id` | `codigo`, `observacoes`, `ativo`, datas de registro. Único (`fabricante_id`, `categoria_id`, `nome`). |
| `localizacoes` | `id` | `nome` | `parent_id`, FK para a própria tabela e anulável, para a hierarquia de localizações, `tipo`, `descricao`, `ativo`, datas de registro. |
| `equipamentos` | `id` | `nome`, `numero_patrimonio` (único), FK `modelo_id`, FK `localizacao_id`, `status` | `numero_serie` (único quando informado), `ano_fabricacao`, `data_aquisicao`, `valor_aquisicao`, `vida_util_anos`, `observacoes`, FK `criado_por`, datas de registro. Fabricante e categoria são derivados por `modelos`, sem duplicação. |
| `componentes` | `id` | `nome`, `tipo` | FK `fabricante_id` anulável, `modelo_componente`, `numero_peca`, `especificacoes`, `observacoes`, `ativo`, datas de registro. `tipo` é restrito a processador, memória RAM, armazenamento, placa-mãe, fonte de alimentação, sensores, displays, baterias, módulos eletrônicos, placas de comunicação e outros. |
| `equipamento_componentes` | `id` | FK `equipamento_id`, FK `componente_id`, `quantidade` (> 0) | `slot`, `numero_serie_instalado`, `instalado_em`, `removido_em`, `observacoes`, datas de registro. Uma chave substituta permite várias instâncias do mesmo componente do catálogo em um equipamento. |
| `ocorrencias` | `id` | FK `equipamento_id`, `relatada_em`, `descricao_tecnica`, `severidade`, `status`, FK `relatada_por` | FK `responsavel_id`, `resolvida_em`, `resumo_resolucao`, `motivo_cancelamento`, datas de registro. |
| `manutencoes` | `id` | FK `equipamento_id`, `tipo`, `data_planejada`, `descricao`, `status`, FK `responsavel_id`, FK `criado_por` | `iniciada_em`, `concluida_em`, `resumo_execucao`, `checklist`, `motivo_cancelamento`, `intervalo_recorrencia_dias`, FK `ocorrencia_id`, datas de registro. |
| `user` (tabela de autenticação existente do Xano, estendida) | `id` | `name`, `email` (único), FK `role_id`, `ativo` | Campos de credenciais gerenciados pela autenticação e datas de registro; o enum legado `role` é mantido só para a migração. Manter as contas desabilitadas que são referenciadas por registros históricos. |
| `roles` | `id` | `nome` (único) | `descricao`, `ativo`, datas de registro. Criar `administrator`, `asset_manager`, `technician`, `viewer`. |
| `permissions` | `id` | `chave` (única), `descricao` | Datas de registro. As permissões correspondem às operações protegidas de leitura, criação, atualização, desativação, manutenção, ocorrência, relatório, auditoria e administração de usuários. |
| `role_permissions` | `id`; único (`role_id`, `permission_id`), ambas FKs | As duas chaves | Datas de registro. O índice único impede concessões duplicadas de permissão a um perfil. |
| `event_log` | `id` | `action`, `created_at` | FK `user_id`, `metadata` para detalhes estruturados de antes/depois e identificadores do registro afetado. Estender a tabela de log de eventos existente do Xano para uso em auditoria; restringir a edição a operações confiáveis do servidor. `action` é exigida por todos que gravam (`hhm/audit` e o `log_event` do quick-start recebem como entrada obrigatória); a coluna em si continua anulável porque a tabela do quick-start já tem linhas e uma coluna mais rígida poria em risco o push aditivo do schema (`validation.md` #13 mostra que texto omitido seria gravado como `""`). |

**Relacionamentos e integridade referencial**

- `fabricantes` 1:N `modelos`; `categorias` 1:N `modelos`; `modelos` 1:N `equipamentos`.
- `localizacoes` 1:N `equipamentos`; `localizacoes` 1:N localizações filhas pelo `parent_id` anulável.
- `equipamentos` N:N `componentes` por `equipamento_componentes`; cada instalação tem sua própria chave e histórico de instalação/remoção.
- `equipamentos` 1:N `manutencoes` e 1:N `ocorrencias`; uma ocorrência PODE ser referenciada por várias manutenções corretivas.
- `user` 1:N registros criados, relatados, atribuídos e auditados. `roles` N:N `permissions` por `role_permissions`, e `roles` 1:N `user`.
- As chaves estrangeiras de modelo, localização, componente, usuário e perfil DEVEM ser validadas pela API. O banco do Xano não garante referências: aceita IDs inexistentes e permite apagar linhas referenciadas (`validation.md` #1, #2). Por isso, toda gravação que define uma referência verifica se o destino existe e, quando exigido, está ativo, dentro do mesmo `db.transaction`, e a API bloqueia a exclusão física de linhas referenciadas. Índices únicos, índices únicos compostos, filtros `min:`, enums e verificações de não nulo são garantidos pelo banco. Mesmo assim, a API os verifica antes, para devolver erros por campo, porque a recusa do banco não traz detalhes do erro.
- A API converte valores únicos opcionais em branco (como `numero_serie`) para `null` antes de gravar e recusa texto obrigatório ausente ou em branco, que o banco gravaria como `""` (`validation.md` #6, #13). Não apagar em cascata equipamentos nem histórico. Desativar registros de catálogo; desabilitar usuários. Recusar a exclusão de linhas referenciadas, exceto quando um registro não tem referências e a exclusão é permitida explicitamente por um administrador.

### Regras de domínio e de ciclo de vida

- `equipamentos.status`: `operational`, `under_maintenance`, `out_of_service`, `decommissioned`. Equipamentos descomissionados são mantidos e, por padrão, ficam fora das listas ativas.
- `manutencoes.tipo`: `preventive` ou `corrective`; status: `planned`, `in_progress`, `completed`, `canceled`. A conclusão exige data de conclusão e resumo do serviço; o cancelamento exige motivo. Trabalho preventivo planejado tem data planejada e responsável.
- `ocorrencias.severidade`: `low`, `medium`, `high`, `critical`; status: `open`, `in_progress`, `resolved`, `canceled`. A resolução exige data e resumo; o cancelamento exige motivo.
- A categoria e o fabricante do modelo são a fonte oficial; os clientes não gravam à parte uma categoria ou um fabricante conflitante no equipamento.
- O número de patrimônio é obrigatório e único. O número de série é opcional e único quando informado. O valor não é negativo; a vida útil é positiva; o ano de fabricação é válido; a data de aquisição não pode ser futura.
- A quantidade de um componente instalado é positiva. As datas de instalação/remoção são preservadas; a remoção é registrada em vez de apagar a instalação.
- A última manutenção é um valor derivado na leitura: a data de conclusão mais recente entre as manutenções concluídas. A próxima manutenção é derivada como a data preventiva planejada futura mais próxima. Esses valores nunca são editados à parte na linha do equipamento.
- Trocar o status, a localização ou o perfil, ou o estado de uma manutenção ou ocorrência, é uma transição de estado autorizada que adiciona um evento de auditoria. Guardar os fatos centrais do domínio em colunas relacionais; reservar `event_log.metadata` para detalhes de auditoria, não como substituto das tabelas do domínio.
- Uma implantação contém os dados de uma instituição. Não adicionar chave de tenant, a menos que o modelo de implantação mude por uma mudança especificada à parte.
- Regras confirmadas (decisões da revisão, 2026-10-08):
  - É exigido um motivo sempre que um equipamento passa a `out_of_service` ou `decommissioned`, por qualquer caminho (cadastro, ação de status ou conclusão de manutenção), e ele é registrado no evento de auditoria.
  - O descomissionamento é definitivo: um equipamento descomissionado não pode trocar de status, ser movido, ser editado nem ter componentes instalados ou removidos. Ele continua legível com todo o histórico.
  - Um intervalo de recorrência preventiva só sugere a próxima data planejada quando o trabalho é concluído; nunca agenda manutenção automaticamente.
  - Os filtros de localização (listas, painel, relatórios) consideram só a localização selecionada, não suas sublocalizações.
- Trabalho pendente ("upcoming"/"overdue") significa manutenção preventiva planejada, da mesma forma no painel, nas listas de manutenção e nos relatórios.
- O histórico do equipamento é mostrado com os mais antigos primeiro (ordem cronológica).
- Datas e horas são digitadas e mostradas em um único fuso da instituição (`HHM_TIMEZONE`), independente do fuso do navegador. Datas de calendário (datas planejadas, data de aquisição) nunca são convertidas de fuso.

### Autorização e privacidade

Usar RBAC com menor privilégio e aplicar as permissões no servidor em toda operação da API. A matriz inicial de perfis é:

| Operação | Administrador | Gestor de patrimônio | Técnico | Visualizador |
|---|---:|---:|---:|---:|
| Ler equipamentos, catálogos, localizações, manutenções e ocorrências | Sim | Sim | Sim | Sim |
| Gerenciar equipamentos e catálogos | Sim | Sim | Não | Não |
| Criar/atualizar manutenções e ocorrências | Sim | Sim | Trabalhos atribuídos/relacionados | Não |
| Gerenciar usuários, perfis e permissões | Sim | Não | Não | Não |
| Ler o painel e os relatórios operacionais | Sim | Sim | Sim | Sim |
| Ler o log de auditoria | Sim | Não | Não | Não |

A matriz é uma política inicial de perfis; as permissões DEVEM ser representadas como concessões explícitas para poderem ser refinadas sem espalhar verificações de nome de perfil pelo aplicativo. Usuários `admin` existentes viram `administrator`. Usuários `member` existentes viram inicialmente `viewer` (menor privilégio), e os administradores os revisam/reatribuem antes do uso operacional. Desativar o cadastro público; não conceder acesso privilegiado automaticamente às contas existentes.

Não adicionar colunas, telas, endpoints, análises ou exportações relacionadas a pacientes. Os textos dos formulários e os campos de ocorrência tratam só do comportamento técnico do equipamento. Usar transporte criptografado, proteção de senha/sessão suportada pela plataforma, autorização no servidor, consultas paginadas e controle de acesso à auditoria. A meta de 2 segundos no p95 para as listagens e o escopo de carga nominal estão definidos em `access-and-reporting/spec.md`.

- Trocar o status do equipamento exige `inventory.manage`, inclusive quando pedido ao iniciar ou concluir uma manutenção; um técnico sem essa permissão pode mudar o estado da manutenção, mas não o status do equipamento.
- Os responsáveis por manutenções ou ocorrências precisam estar habilitados e ter a permissão `manage` ou `manage_assigned` da área.
- A recuperação de senha usa links de redefinição de uso único, guardados como hash e válidos por 60 minutos, enviados por um serviço de e-mail externo (Resend via `util.send_email`; configurado com `RESEND_API_KEY`, `HHM_EMAIL_FROM`, `HHM_APP_URL`). Um link de redefinição nunca cria sessão: `reset/confirm` valida o token e define a nova senha em um passo, então o link só consegue alterar a senha daquela conta. O `reset/magic-link-login` do quick-start (que devolvia uma sessão completa) e o `reset/update_password` (que alterava a senha de qualquer sessão logada sem pedir a atual) estão desativados. Administradores criam contas com senha temporária; a conta fica marcada com `deve_trocar_senha` e não tem permissões até o usuário trocar essa senha no primeiro acesso (`auth/change_password`, que exige a senha atual). Administradores não podem definir nem redefinir a senha de um usuário existente; uma senha esquecida só é recuperada pelo fluxo de redefinição por e-mail, e concluí-lo também limpa uma senha temporária pendente.
- Os eventos de auditoria gravados pelos endpoints do quick-start antes desta mudança continham o hash da senha e o hash do token de redefinição. Eles são mantidos pela integridade histórica e só esses dois valores são apagados (`setup/scrub_audit_credentials`); nenhum evento de auditoria é apagado.

### Telas e navegação

1. **Login / recuperação de conta:** entrada autenticada; sem criação pública de contas.
2. **Painel:** resumo por status/categoria, manutenções próximas e atrasadas, ocorrências abertas, atividade recente de serviço; filtro por localização e pelo período relevante.
3. **Lista de equipamentos:** inventário pesquisável e paginado; filtros por categoria, fabricante/modelo, localização e status; ações liberadas conforme as permissões.
4. **Detalhe do equipamento:** visão geral e datas de manutenção derivadas, componentes instalados, lista de ocorrências e histórico cronológico; ações de editar/mover/status quando permitidas.
5. **Cadastro/edição de equipamento:** identificação do patrimônio, modelo, localização e status obrigatórios; série, aquisição, vida útil e observações opcionais; o modelo define fabricante e categoria.
6. **Catálogos e localizações:** fabricantes, categorias, modelos, catálogo de componentes e localizações hierárquicas, com ações de cadastrar, editar e ativar/desativar.
7. **Manutenções:** visões de calendário e lista para trabalhos planejados/próximos/atrasados; formulários de criar, atribuir, iniciar, concluir ou cancelar, com validação das transições.
8. **Ocorrências:** filas de abertas/em andamento/resolvidas/canceladas; relatar, atribuir, resolver, cancelar e abrir um formulário de manutenção corretiva preenchido a partir da ocorrência e vinculado a ela automaticamente.
9. **Usuários e perfis:** exclusivo de administradores: criação de usuários, habilitar/desabilitar e gestão de perfis e permissões.
10. **Relatórios e auditoria:** visões filtradas de inventário, status/localização, manutenções pendentes, histórico de manutenções, ocorrências e auditoria exclusiva de administradores; os relatórios operacionais filtrados podem ser exportados em CSV.

Formulários não criam registros duplicados com clique duplo: o botão fica em carregamento durante o envio, e um envio repetido que chega depois do primeiro é descartado (diálogo já fechado ou chave do formulário já trocada). Horários pré-preenchidos ("agora") são calculados quando o diálogo abre.

## Riscos / Concessões

- [Os perfis de usuário existentes no Xano (`admin`/`member`) não correspondem ao novo conjunto de perfis] → Migrar `admin` para `administrator`, `member` para `viewer` por padrão e exigir revisão de um administrador antes do lançamento.
- [O endpoint público de cadastro existente poderia criar contas sem controle] → Desativá-lo no aplicativo em produção e criar usuários só por operações exclusivas de administradores.
- [Datas derivadas e contagens do painel podem ficar caras à medida que o histórico cresce] → Usar chaves estrangeiras e colunas de data/status indexadas, paginar listas e otimizar as consultas medidas, preservando a fonte relacional da verdade.
- [Anotações livres de ocorrências poderiam conter informações de pacientes apesar do limite do produto] → Manter os campos explicitamente técnicos, não criar campos de pacientes, avisar os usuários na interface, restringir exportações e definir a política operacional de retenção/acesso antes da produção.
- [Trocar perfis ou desativar dados de referência pode afetar o acesso e a exibição do histórico] → Preservar as linhas referenciadas, usar flags de ativo, validar mudanças na API e manter os eventos de auditoria.
- [As capacidades relacionais nativas do Xano e o schema de exportação precisam ser validados contra cada restrição planejada] → Verificar restrições de unicidade, comportamento de chaves estrangeiras, transações e suporte a índices no workspace do Xano de destino antes da implementação; relatar qualquer invariante não suportado em vez de enfraquecê-lo em silêncio.
- [O plano Free do Xano limita as requisições, e várias telas abertas ou recarregadas seguidamente podem estourar o limite] → Caches e filtragem local descritos em "Desempenho com o limite do plano do Xano"; em produção, plano pago (ver `docs/operations.md`).
- [O Xano às vezes ignora o bloco de paginação e devolve a lista inteira, sem metadados] → O frontend normaliza toda listagem para `{items, nextPage, itemsTotal}` (`api.as_page`) e recorta a página. Funções do Xano que percorrem dados não dependem da paginação (`setup/scrub_audit_credentials` lê sem paginar). A causa ainda não foi identificada; quando vem a lista inteira, a tela baixa todos os registros.
- [Comparar um valor padrão `now` com um segundo `now` falhou no Xano ("iniciada_em cannot be in the future" sem data enviada)] → Datas opcionais só são validadas quando o cliente as envia (iniciar manutenção, registrar ocorrência).

## Plano de migração

1. Confirmar as restrições relacionais e o comportamento de autenticação do Xano contra o schema proposto antes de alterar dados de produção.
2. Criar os catálogos de referência, perfis, permissões e concessões por perfil; criar as 12 categorias de equipamento e as definições de perfis.
3. Estender o schema existente de usuário e de log de eventos; mapear `admin` para `administrator` e `member` para `viewer`, e depois exigir revisão de um administrador.
4. Criar as demais tabelas e índices do domínio, validar chaves estrangeiras e unicidade e manter os novos fluxos indisponíveis até o schema estar pronto.
5. Publicar a validação e a autorização da API e depois as telas Reflex; verificar os casos de negação por perfil e os limites de dados não clínicos antes de liberar o acesso aos usuários.
6. Fazer rollback desativando as novas rotas e endpoints do aplicativo e restaurando o snapshot anterior da implantação/schema. Não remover tabelas nem apagar dados no rollback; usar uma migração de correção para a frente se foram criados registros com o novo schema.

## Questões em aberto

- Hospedagem em produção, retenção de backups e objetivos de tempo de recuperação continuam sendo decisões de implantação; definir antes do lançamento em produção, sem mudar o modelo de domínio inicial.
