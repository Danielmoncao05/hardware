# Tarefas

## 1. Componente

- [x] 1.1 `hardware/components.py`: `password_input` com o mesmo contrato de `text_input` e botão de olho em `rx.input.slot` (ícones `eye`/`eye-off`, `type="button"`, `aria-label`, `aria-pressed`, `title`) ; verificado com `test_password_input_has_eye_toggle_that_does_not_submit`
- [x] 1.2 Script no cliente (`rx.call_script`) que alterna `type` do campo pelo `id` e atualiza ícone, rótulo e `aria-pressed`; e script que oculta todos os campos de senha de um formulário no envio (feito com `assets/password.js`, carregado em todas as páginas, em vez de `rx.call_script`: um clique delegado no documento, sem ida ao servidor); verificado no navegador
- [x] 1.3 Estilo do botão dentro do campo e foco visível em `assets/app.css`, se o padrão do Radix não bastar

## 2. Telas

- [x] 2.1 `hardware/pages/login.py`: Senha (login), Nova senha e Confirmar senha (link de e-mail)
- [x] 2.2 `hardware/pages/change_password.py`: Senha atual, Nova senha e Confirmar nova senha
- [x] 2.3 `hardware/pages/users.py`: Senha temporária do novo usuário
- [x] 2.4 Ocultar os campos de novo no envio de cada um desses formulários (listener de `submit` em `assets/password.js`); verificado no navegador

## 3. Verificação

- [x] 3.1 Testes unitários: `password_input` gera input `password` com botão `type="button"` e rótulo "Mostrar senha"; nenhuma página usa `type_="password"` fora do componente
- [x] 3.2 Rodar `pytest` e `reflex compile --dry` (102 passed, 43 skipped; compilação ok)
- [ ] 3.3 Verificar no navegador (login já verificado: mostra, oculta, rótulos e oculta de novo no envio; faltam Alterar senha, teclado e a captura visual): mostrar/ocultar no login, campos independentes em Alterar senha, teclado (Tab + Enter/Espaço sem enviar) e senha oculta depois de um erro de validação
