# Design

## Contexto

Ver `proposal.md`. Hoje há 7 campos de senha, todos criados com `text_input(..., type_="password")` de `hardware/components.py`, que gera um `rx.input` (Radix TextField) com `id` próprio e rótulo ligado por `field()`.

## Objetivos / Fora do escopo

**Objetivos:** mostrar e ocultar a senha em cada campo, com resposta imediata, teclado e leitor de tela.

**Fora do escopo:** medidor de força da senha, gerar senha temporária automaticamente, mudanças no Xano.

## Decisões

### 1. Componente único `password_input`
`password_input(label, name, required=False, hint="", id_prefix="f", **props)` em `components.py`, com o mesmo contrato de `text_input` (rótulo, dica, `aria-describedby`, `autocomplete` via `custom_attrs`). Ele monta `rx.input(rx.input.slot(botão, side="right"), type="password", ...)`. Todas as telas trocam `text_input(..., type_="password")` por `password_input(...)`, e um teste garante que não sobra `type_="password"` fora do componente.

### 2. Alternância só no navegador
O botão troca `type` entre `password` e `text` do input pelo `id`, com um script em `assets/password.js` (clique delegado no documento, carregado em todas as páginas por `head_components`), e atualiza o próprio `aria-label` ("Mostrar senha" / "Ocultar senha"), `aria-pressed` e o ícone. Nada vai ao backend: a senha não entra no estado do Reflex (os formulários continuam lendo os valores só no envio) e não há espera pela conexão com o servidor.
Alternativa descartada: um `bool` por campo no estado do Reflex. Funciona, mas cada clique faria uma ida e volta ao servidor e exigiria um estado por tela.

### 3. Ícone e botão
Ícones `eye` (senha oculta, ação "mostrar") e `eye-off` (senha visível, ação "ocultar"), os dois no DOM, alternando a visibilidade via classe, para não depender de re-renderizar o componente. Botão `type="button"` (não envia o formulário), `variant="ghost"`, tamanho do campo, com foco visível; `title` igual ao `aria-label`.

### 4. Volta a esconder
Ao montar a tela o campo começa como `password`. No envio do formulário (`on_submit` das telas de login, nova senha, alterar senha e novo usuário), o script devolve todos os campos do formulário a `password` e os botões ao estado inicial, para a senha não ficar exposta depois de um erro de validação.

### 5. Gerenciadores de senha
`autocomplete` (`current-password`, `new-password`) continua no input. A troca de `type` não muda o `name` nem o `id`, então o preenchimento automático e o salvamento pelo navegador seguem funcionando.

## Riscos / Trade-offs

- **Senha visível na tela:** é escolha do usuário em cada campo e volta a esconder no envio.
- **Script no cliente:** pequeno e só usa o `id` do próprio campo; se falhar, o campo continua funcionando como senha comum.
