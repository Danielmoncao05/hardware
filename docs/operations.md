# Operação: hospedagem, implantação, backup, recuperação e rollback

Roteiro de operação para a implantação do sistema de gestão de equipamentos em uma instituição
(frontend Reflex + API/banco de dados Xano). Uma implantação = os dados de uma instituição.

## 1. Decisões ainda em aberto (responsável: líder do projeto)

Estas são decisões de implantação vindas de `design.md` → Questões em aberto. Os valores recomendados são propostas,
não compromissos; registre aqui o valor combinado e a data antes de entrar em produção.

| Decisão | Recomendação | Valor combinado |
|---|---|---|
| Plano do Xano | Um plano pago com branch que não seja o live, ambientes de sandbox/tenant e backups gerenciados. O plano Free usado no desenvolvimento não tem sandbox, então todo teste mexe nos dados reais (ver `openspec/changes/hospital-hardware-manager/validation.md`). | _A definir_ |
| Hospedagem do frontend | Reflex Cloud, ou qualquer host de contêiner rodando `reflex run --env prod` atrás de HTTPS, na mesma região da instância do Xano. | _A definir_ |
| Objetivo de ponto de recuperação (RPO) | ≤ 24 h (backups diários); ≤ 1 h se o plano oferecer recuperação para um ponto no tempo. | _A definir_ |
| Objetivo de tempo de recuperação (RTO) | ≤ 4 h em horário comercial. | _A definir_ |
| Retenção de backups | Backups diários guardados por 30 dias, mais backups mensais guardados por 12 meses. | _A definir_ |
| Retenção do log de auditoria | A mesma dos registros de equipamentos (o aplicativo nunca apaga). | _A definir_ |
| Provedor de e-mail para redefinição de senha | Decidido: um serviço de e-mail externo. O `util.send_email` do XanoScript só suporta `resend`, além do provedor `xano`, que só envia para o dono do workspace; por isso o código usa o Resend: crie a conta, verifique o domínio do remetente e defina as variáveis da seção 2. Um servidor SMTP comum precisaria de um relay na frente. | Resend (2026-10-08) |

## 2. Ambientes e configuração

| Configuração | Onde | Finalidade |
|---|---|---|
| `HHM_APP_URL` | Variável de ambiente do Xano | URL de produção do frontend, usada nos links de redefinição de senha (página `/reset-password`). |
| `RESEND_API_KEY` | Variável de ambiente do Xano (segredo) | Chave da API do serviço de e-mail, para os e-mails de redefinição e de boas-vindas. |
| `HHM_EMAIL_FROM` | Variável de ambiente do Xano | Endereço do remetente, em um domínio verificado no serviço de e-mail. |
| `XANO_BASE_URL` | Ambiente do frontend | URL da instância do Xano. |
| `XANO_*_GROUP` | Ambiente do frontend (opcional) | Identificadores dos grupos de API; os padrões batem com `xano/api/*/api_group.xs`. |
| `HHM_TIMEZONE` | Ambiente do frontend | Fuso horário da instituição para horários digitados e exibidos (padrão `America/Sao_Paulo`). |

A recuperação de senha falha de forma segura: enquanto `HHM_APP_URL`, `RESEND_API_KEY` e `HHM_EMAIL_FROM`
não estiverem definidas, `reset/request-reset-link` devolve erro em toda requisição (sem nunca revelar se um
e-mail existe) e nenhum e-mail é enviado.

O frontend guarda o token de autenticação do Xano só no estado do backend (servidor); nada secreto é enviado ao
navegador. Sirva o frontend somente por HTTPS; os endpoints do Xano já usam HTTPS por padrão.

**Estado de sessão e escala.** Por padrão, o Reflex mantém esse estado na memória do processo do app. Com um
único processo, um reinício só desconecta todo mundo. Para rodar mais de um processo ou worker (ou para
sobreviver a reinícios), configure o Redis para o estado do Reflex (`REFLEX_REDIS_URL`, ou seja, `redis_url` no
`rxconfig.py`); caso contrário, os usuários são desconectados sempre que uma requisição cai em outro processo.

**Limite de requisições.** O plano Free do Xano aceita 10 requisições a cada 20 segundos. O frontend espera e
tenta de novo quando recebe HTTP 429, mas várias telas abertas ou recarregadas seguidamente ainda podem
estourar o limite. Em produção, use um plano pago.

## 3. Primeira implantação

**Janela de manutenção.** Entre o push (passo 4) e o comando de setup (passo 6), todas as contas existentes
ficam bloqueadas: o login e todas as verificações de permissão exigem `ativo = true` e um perfil, que só a
migração atribui. Avise sobre uma janela curta e rode os passos 4 a 6 em seguida.

1. **Avise** os usuários atuais sobre a janela de manutenção.
2. **Snapshot.** Faça um backup/exportação do workspace do Xano (backup pelo painel, ou `xano workspace pull` para uma pasta datada fora do repositório) e anote o identificador.
3. **Simulação.** A partir de `xano/`: `xano workspace push -d . --dry-run`. Confirme que a prévia só cria as tabelas, funções e grupos de API do domínio, e atualiza os endpoints de autenticação, `user` e `event_log`. Não pode aparecer nenhuma exclusão.
4. **Push.** Rode `xano workspace push -d .`. O push só adiciona e roda em uma transação por padrão; não use `--no-transaction`, `--truncate`, `--sync --delete` nem `--records`.
5. **Defina `HHM_APP_URL`, `RESEND_API_KEY` e `HHM_EMAIL_FROM`** no ambiente do Xano.
6. **Seed e migração, logo em seguida:** `xano function run "setup/run_deployment_setup"`. Ele cria os dados de referência (espere `categorias: 12, roles: 4, permissions: 10, role_permissions: 21, divergencias: []`), se recusa a continuar se as concessões dos perfis forem diferentes da matriz aprovada e depois migra as contas: todo antigo `admin` vira `administrator` e as demais contas viram `viewer` com `needs_review: true`. Confirme `without_role: 0`. Por fim, apaga o hash da senha e o hash do token de redefinição que os endpoints antigos do quick-start gravaram nos eventos de auditoria (os eventos são mantidos; ver `scrub.eventos_corrigidos`).
7. **Revise as contas:** um administrador revisa e reatribui as contas `needs_review` em **Usuários e perfis** antes de entrar em produção.
   As contas que existiam antes desta versão mantêm as senhas. Contas novas são criadas com senha
   temporária, entregue ao usuário por um canal seguro separado, e precisam ser trocadas no primeiro acesso.
   Administradores não conseguem redefinir senhas existentes; quem esquecer a sua usa **Esqueci minha senha**.
8. **Verifique:** rode `pytest tests/test_no_clinical_data.py`. Em um ambiente de teste (não em produção), rode também `pytest tests/test_api_integration.py` e `python tests/perf/inventory_list_p95.py`, e registre os resultados em `validation.md`.
9. **Publique o frontend:** `pip install -r requirements.txt` e depois `reflex run --env prod` (ou o equivalente do host), com o ambiente da seção 2.
10. **Teste rápido** com uma conta de cada perfil: login, painel, lista de equipamentos e uma ação negada como viewer; crie uma conta nova e confirme que o primeiro acesso obriga a troca de senha. Encerre a janela de manutenção.

A função legada do quick-start `Quick Start/enforce_role` foi removida dos fontes locais; um push que só adiciona
não a apaga do workspace, então apague-a pelo painel do Xano (nada a chama).

## 4. Versões de rotina

1. Faça backup (seção 3, passo 2).
2. Rode `xano workspace push --dry-run` e revise a prévia. Qualquer `DELETE` ou mudança de tipo de campo precisa de aprovação explícita e de um plano de correção para a frente.
3. Publique o backend primeiro e depois o frontend (a API continua compatível com a versão anterior dentro de uma versão).
4. Faça o teste rápido; procure erros no `reflex.log` e no histórico de requisições do Xano.

## 5. Backup

- Backups gerenciados conforme o plano escolhido na seção 1, com a frequência e a retenção combinadas.
- Depois de cada versão, e pelo menos uma vez por mês, exporte as definições do workspace (`xano workspace pull`) para um armazenamento versionado fora do host do aplicativo.
- Os backups contêm dados operacionais dos equipamentos, nomes/e-mails dos usuários e o histórico de auditoria. Guarde-os criptografados, com acesso só para administradores.

## 6. Recuperação (perda ou corrupção de dados)

1. Bloqueie o acesso dos usuários: coloque os grupos de API `Inventory`, `Maintenance`, `Reports` e `Users` como `active = false`, ou pare o frontend.
2. Identifique o último backup bom dentro do RPO.
3. Restaure primeiro em um ambiente **que não seja o live** (tenant/branch, conforme o plano) e confira as contagens de `user`, `equipamentos`, `manutencoes`, `ocorrencias`, `event_log` e o histórico de uma amostra de equipamentos.
4. Promova/restaure no live, libere o acesso e registre o incidente, a janela de perda de dados e os tempos em relação ao RPO/RTO.

## 7. Rollback (versão com problema)

O rollback nunca remove tabelas nem apaga registros.

1. Desative as novas rotas/endpoints (grupos de API com `active = false`, ou publique de novo o frontend anterior).
2. Restaure as definições anteriores de funções/endpoints a partir do snapshot de antes da versão (pasta do `xano workspace pull` ou backup pelo painel).
3. Se foram criados registros com o novo schema, mantenha-os e aplique uma mudança de **correção para a frente**, em vez de restaurar um snapshot de dados por cima deles.
4. Libere o acesso e repita o teste rápido.

## 8. Ensaio de recuperação e rollback (obrigatório antes de produção)

Rode em um ambiente que não seja o live, com dados parecidos com os de produção, e registre o resultado:

| Passo | Verificação | Resultado |
|---|---|---|
| Restaurar o backup mais recente | As contagens de usuários, equipamentos, manutenções, ocorrências e eventos de auditoria são iguais às da origem | _pendente_ |
| Histórico de equipamentos | 3 equipamentos de amostra mostram histórico e datas de última/próxima manutenção idênticos | _pendente_ |
| Logins | Uma conta de cada perfil consegue entrar; uma conta desabilitada não consegue | _pendente_ |
| Rollback | Depois de publicar uma mudança de teste e fazer o rollback, tudo acima continua valendo e nenhuma linha foi perdida | _pendente_ |
| Tempo | Tempo de restauração medido em relação ao RTO | _pendente_ |
