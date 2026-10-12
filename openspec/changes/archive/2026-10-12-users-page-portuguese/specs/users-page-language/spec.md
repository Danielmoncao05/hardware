## ADDED Requirements

### Requirement: Página de usuários e perfis em português
A página de usuários e perfis DEVE mostrar todos os textos em português: os perfis padrão pelos nomes Administrador, Gestor de patrimônio, Técnico e Visualizador, com descrição em português; as permissões pelo nome e descrição em português, sem a chave técnica; e as mensagens de erro da API de usuários e perfis em português. Perfis criados pelo administrador DEVEM aparecer com o nome e a descrição informados. Os códigos gravados de perfis e permissões NÃO DEVEM mudar.

#### Scenario: Matriz de permissões em português
- **QUANDO** o administrador abre a aba "Permissões por perfil"
- **ENTÃO** as colunas DEVEM mostrar os nomes dos perfis em português e cada linha o nome e a descrição da permissão em português

#### Scenario: Erro da API em português
- **QUANDO** o administrador tenta criar um usuário com um e-mail já cadastrado
- **ENTÃO** o app DEVE mostrar a mensagem "Este e-mail já está em uso."

#### Scenario: Perfil personalizado
- **QUANDO** existe um perfil criado pelo administrador com nome e descrição próprios
- **ENTÃO** a página DEVE mostrar esse nome e essa descrição sem alteração
