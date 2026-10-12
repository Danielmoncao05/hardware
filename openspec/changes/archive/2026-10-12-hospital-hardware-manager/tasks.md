# Tarefas

## 1. Base de dados e migração

- [x] 1.1 Verificar o suporte do Xano a chaves estrangeiras, restrições de unicidade, transações e índices propostos; registrar um resultado de validação para cada restrição usada pelo schema do domínio.
- [ ] 1.2 Criar as tabelas relacionais, chaves primárias/estrangeiras, restrições e índices do `design.md`; verificar se as checagens do schema recusam referências inválidas, números de patrimônio duplicados, números de série não vazios duplicados e quantidades inválidas.
- [ ] 1.3 Criar as 12 categorias de equipamento, os tipos de componente, os perfis, as permissões e as concessões por perfil; verificar se cada valor exigido existe exatamente uma vez e se as concessões batem com a matriz aprovada.
- [ ] 1.4 Estender o modelo existente de usuário e de log de eventos; migrar `admin` para `administrator` e `member` para `viewer`, desativar o cadastro público e verificar se a migração preserva as contas e o histórico de auditoria sem conceder privilégios indevidos.

## 2. Autenticação, autorização e auditoria

- [ ] 2.1 Implementar a criação autenticada de contas (com senha temporária), a desabilitação e os fluxos de recuperação (`reset/confirm` em um passo; `reset/magic-link-login` e `reset/update_password`, que usavam sessão, desativados); verificar se o cadastro público não existe e se usuários desabilitados não conseguem se autenticar nem recuperar o acesso.
- [ ] 2.2 Aplicar as permissões dos perfis em toda operação protegida da API; verificar se requisições sem autenticação e cada combinação negada de perfil/ação devolvem erro de autorização sem alterar nem revelar dados protegidos.
- [ ] 2.3 Registrar eventos de auditoria para mudanças relevantes de inventário, componentes, manutenção, ocorrências, localização, status e permissões; verificar se quem agiu, a ação, o registro afetado, a data e hora e os detalhes de status antes/depois são mantidos.

## 3. Inventário de equipamentos

- [ ] 3.1 Implementar a gestão de fabricantes, categorias, modelos e localizações, com ativação/desativação; verificar as relações obrigatórias, a unicidade dos modelos e a recusa de referências inativas.
- [ ] 3.2 Implementar os fluxos de lista, cadastro/edição, detalhe, movimentação, troca de status e descomissionamento de equipamentos; verificar campos obrigatórios e opcionais, validação no servidor, categoria/fabricante derivados, unicidade e manutenção do histórico.
- [ ] 3.3 Implementar o catálogo de componentes e os fluxos de instalação/remoção de componentes nos equipamentos; verificar a relação N:N, a regra de quantidade positiva, slots repetidos do mesmo componente e o histórico de instalação/remoção mantido.

## 4. Manutenções e ocorrências

- [ ] 4.1 Implementar o agendamento preventivo, os dados de recorrência, a atribuição, as listas de próximas/atrasadas e as transições de estado da manutenção; verificar as exigências de conclusão/cancelamento e a exclusão de trabalhos concluídos/cancelados das listas de pendentes.
- [ ] 4.2 Implementar a manutenção corretiva e o registro, atribuição, resolução, cancelamento e vínculo de ocorrências; verificar a descrição técnica obrigatória, severidade, relator, detalhes da resolução e a relação entre ocorrência e manutenção.
- [ ] 4.3 Implementar o histórico cronológico do equipamento e as datas derivadas de última/próxima manutenção; verificar se registros concluídos e cancelados continuam visíveis e se as datas são calculadas a partir das manutenções de origem, não de cópias gravadas.

## 5. Painel e relatórios

- [ ] 5.1 Implementar o painel operacional autenticado com totais por status/categoria, filtro por localização, preventivas próximas/atrasadas, ocorrências abertas e atividade recente de serviço; verificar os totais contra registros de teste em cada filtro.
- [ ] 5.2 Implementar os relatórios filtrados de inventário, manutenções e ocorrências com exportação CSV; verificar se as linhas exportadas correspondem aos filtros da tela, às permissões e às colunas não clínicas permitidas.

## 6. Qualidade, acessibilidade e prontidão para lançamento

- [ ] 6.1 Implementar as telas e a navegação especificadas no `design.md`; verificar se os fluxos principais funcionam no desktop e no tablet e se os formulários têm rótulos acessíveis, foco de teclado lógico e erros de validação visíveis.
- [ ] 6.2 Medir o tempo de resposta da listagem padrão de inventário com filtros, com 10.000 equipamentos e carga nominal; verificar se o p95 fica em até 2 segundos e registrar a configuração e o resultado do teste.
- [ ] 6.3 Rodar testes de integração entre as capacidades para integridade referencial, aplicação de perfis, cobertura da auditoria, cálculos de manutenção/histórico e ausência de campos ou fluxos de pacientes/clínicos; verificar se todos os cenários das specs passam.
- [ ] 6.4 Documentar hospedagem em produção, backup/retenção, objetivos de recuperação, implantação e procedimentos de rollback; verificar se um ensaio de recuperação e rollback preserva os usuários, equipamentos e histórico de serviços existentes.

## 7. Decisões da revisão e escopo adicionado

- [ ] 7.1 Implementar a criação de perfis, concessão/revogação de permissões e ativação/desativação; verificar se o perfil `administrator` e perfis de usuários habilitados não podem ser desativados, se `users.manage` não pode ser revogada de `administrator` e se toda mudança é auditada.
- [ ] 7.2 Implementar senhas temporárias na criação de contas e a troca no primeiro acesso (`auth/change_password`); verificar se a conta fica sem permissões até a troca, se a troca exige a senha atual e a política de senhas, e se administradores não conseguem definir nem redefinir a senha de um usuário existente por nenhum meio.
- [ ] 7.3 Implementar a recuperação de senha somente por e-mail, pela função de e-mail compartilhada e `reset/confirm`; verificar se os links são de uso único, guardados como hash, expiram em 60 minutos, não criam sessão, devolvem respostas idênticas para casos desconhecidos, desabilitados e inválidos, e se a recuperação falha de forma segura até `HHM_APP_URL`, `RESEND_API_KEY` e `HHM_EMAIL_FROM` estarem configuradas.
- [ ] 7.4 Implementar a limpeza de credenciais da auditoria (`setup/scrub_audit_credentials`); verificar se depois disso nenhum evento de auditoria contém hash de senha ou token de redefinição e se nenhum evento foi apagado.
- [ ] 7.5 Aplicar as regras de equipamento confirmadas; verificar se é exigido motivo para `out_of_service` e `decommissioned` em todos os caminhos, se o descomissionamento é definitivo e se trocas de status feitas ao iniciar ou concluir manutenção exigem `inventory.manage`.
- [ ] 7.6 Implementar trabalho pendente só com preventivas, recorrência como sugestão, a regra de permissão do responsável e a manutenção corretiva preenchida a partir de uma ocorrência; verificar se a definição de atrasada é a mesma na lista, no painel e no relatório, se a conclusão não cria registro novo, se responsáveis sem permissão são recusados e se o vínculo com a ocorrência é definido automaticamente.
- [ ] 7.7 Implementar os comportamentos do frontend: página de acesso negado e guards, edição de catálogos, histórico com os mais antigos primeiro e exibição no fuso da instituição; verificar se os guards nunca entram em loop, se referências inativas não são apagadas na edição e se as datas planejadas não mudam por fuso.
- [ ] 7.8 Implementar o passo único de setup após o push (`setup/run_deployment_setup`: seed, migração, limpeza da auditoria) e o procedimento de janela de manutenção em `docs/operations.md`; verificar se ele é idempotente, recusa concessões divergentes e não deixa nenhuma conta sem perfil.

## 8. Correções e desempenho (revisão de 2026-10-08)

- [x] 8.1 Impedir registros duplicados por clique duplo nos formulários de manutenção, ocorrência, usuários, perfis e catálogos; verificar com testes unitários do descarte de envio repetido.
- [x] 8.2 Calcular o horário "agora" pré-preenchido quando o diálogo abre (var sem cache); verificar com teste unitário.
- [x] 8.3 Voltar para a página 1 ao entrar em manutenções/ocorrências e à aba padrão ao limpar o filtro de equipamento.
- [x] 8.4 Reaproveitar perfil (60 s), listas de opções (5 min) e páginas de listagem (30 s, esvaziadas por qualquer escrita) e filtrar abas localmente quando a lista completa cabe em uma resposta; verificar com testes unitários de cache e das regras das abas.
- [x] 8.5 Tratar HTTP 429 com nova tentativa e mensagem em português; verificar com testes unitários.
- [x] 8.6 Normalizar listagens que o Xano devolve sem paginação (`api.as_page`) e trocar `router.page` (descontinuado) por `router.url`.
- [x] 8.7 Reescrever `setup/scrub_audit_credentials` sem paginação.
- [x] 8.8 Validar `iniciada_em` e `relatada_em` só quando enviadas pelo cliente.
- [x] 8.9 Criar o script de dados de demonstração (`scripts/seed_demo.py`), que cadastra pela API, com prefixo DEMO e de forma reexecutável.
- [ ] 8.10 Publicar no Xano os endpoints corrigidos (8.7, 8.8) e rodar `setup/run_deployment_setup`; verificar `divergencias: []`, `without_role: 0` e que iniciar uma manutenção pelo app funciona.
- [x] 8.11 Corrigir a confirmação de senha em `auth/change_password` e `reset/confirm` (a entrada `password` chega em hash; comparar com `security.check_password`); verificado no navegador: o usuário criado troca a senha temporária no primeiro acesso.
- [x] 8.12 Fazer `users GET` listar as contas: com paginação a consulta devolvia lista vazia; sem paginação (o app recorta a página) funciona. Verificado no navegador: os usuários criados aparecem na tela de usuários.
- [ ] 8.13 Revisar os demais endpoints que paginam e verificar se algum devolve lista vazia ou incompleta no lugar da página. Feito: os três relatórios operacionais (sem paginação na consulta; tela e CSV verificados no navegador). Falta: listas de inventário, manutenções, ocorrências, auditoria e `my_events`.
