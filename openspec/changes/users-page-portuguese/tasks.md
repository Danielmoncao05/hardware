# Tarefas

## 1. App

- [x] 1.1 `hardware/labels.py`: nomes e descrições em português dos perfis e permissões padrão
- [x] 1.2 `hardware/pages/users.py`: perfis (lista, seletores, cabeçalhos da matriz) e permissões (nome + descrição) em português; texto de ajuda sem código técnico
- [x] 1.3 `AuthState.role_label` no menu do usuário e na própria linha da tabela de usuários
- [x] 1.4 Testes `test_roles_and_permissions_are_shown_in_portuguese` e `test_users_api_errors_are_in_portuguese`; `pytest` e `reflex compile --dry`

## 2. Xano

- [x] 2.1 Mensagens de erro de `api/users/*.xs` em português; validado com `xano workspace push --dry-run`
- [x] 2.2 Descrições de perfis e permissões do seed em português
- [ ] 2.3 Publicar os endpoints do grupo Users e conferir uma mensagem (ex.: e-mail já em uso) no app

## 3. Verificação

- [ ] 3.1 Conferir no navegador a página Usuários e perfis com o administrador
