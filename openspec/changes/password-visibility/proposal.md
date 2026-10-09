# Proposta

## Por quê

Nos campos de senha não dá para conferir o que foi digitado. Isso gera erros de login e de troca de senha (principalmente com a senha temporária e na confirmação da nova senha), e o usuário só descobre depois de enviar o formulário.

## O que muda

- **Botão de olho em todo campo de senha:** um ícone dentro do campo, à direita, mostra a senha (olho riscado passa a ser exibido) ou volta a escondê-la (olho).
- **Campos atendidos:** login (Senha); definir nova senha pelo link de e-mail (Nova senha, Confirmar senha); Alterar senha (Senha atual, Nova senha, Confirmar nova senha); Usuários e perfis (Senha temporária).
- **Cada campo tem o seu controle:** mostrar a nova senha não mostra a confirmação, nem o contrário.
- **Sempre começa escondida:** ao abrir a tela e depois de enviar o formulário, a senha volta a ficar oculta.
- **Acessível:** o botão é alcançável pelo teclado, tem rótulo "Mostrar senha" / "Ocultar senha" para leitores de tela, informa se está ativo e não envia o formulário.
- **Sem ida ao servidor:** alternar a visibilidade acontece só no navegador; a senha não passa pelo estado do Reflex nem é registrada em lugar nenhum.

## Capacidades

### Novas capacidades
- `password-visibility`: mostrar e ocultar o conteúdo dos campos de senha do app.

### Capacidades modificadas
<!-- Nenhuma -->

## Impacto

- `hardware/components.py`: novo componente `password_input` (mesmo contrato de `text_input`, com o botão de olho).
- `hardware/pages/login.py`, `hardware/pages/change_password.py`, `hardware/pages/users.py`: campos de senha passam a usar `password_input`.
- `assets/app.css`: estilo do botão dentro do campo, se necessário.
- `tests/test_frontend_unit.py`: testes do componente e de que não sobrou `type_="password"` fora dele.
- Sem mudanças no Xano.
