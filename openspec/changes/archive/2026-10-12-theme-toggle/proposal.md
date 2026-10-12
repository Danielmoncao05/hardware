# Proposta

## Por quê

Hoje o app não define um modo de cor: o Reflex usa o padrão `system`, então quem tem o sistema operacional em modo escuro abre todas as telas no tema escuro, e não há como trocar isso dentro do app. A equipe quer o tema claro como padrão, mais legível nos ambientes iluminados de hospital, e deixar cada usuário escolher o modo escuro quando preferir.

## O que muda

- O modo de cor padrão passa a ser **claro** para todas as telas, independentemente da preferência do sistema operacional, para quem ainda não escolheu um tema.
- Um botão de alternância claro/escuro passa a aparecer na interface autenticada: na barra lateral (desktop) e no topo da página, ao lado do botão de menu (tablet/celular).
- A troca é aplicada na hora, sem recarregar a página e sem perder o que está na tela.
- A escolha fica salva no navegador e vale nas próximas visitas, inclusive nas telas públicas (login e recuperação de senha).
- O botão tem rótulo acessível e funciona pelo teclado.

## Capacidades

### Novas capacidades
- `ui-theme`: modo de cor padrão do app e a alternância entre claro e escuro feita pelo usuário, com persistência da escolha no navegador.

### Capacidades modificadas
<!-- Nenhuma: ainda não há specs principais em openspec/specs/, e os requisitos da change hospital-hardware-manager não tratam de tema. -->

## Impacto

- `rxconfig.py`: definir o modo de cor padrão como claro.
- `hardware/components.py`: adicionar o botão de alternância ao `layout()` (barra lateral e cabeçalho do menu móvel).
- Telas que usam cores fixas: nenhuma encontrada; as páginas usam tokens `rx.color(...)` e `color_scheme`, que já se adaptam aos dois modos.
- Sem mudança no backend (Xano), na API ou em dependências. A preferência fica só no navegador, não na conta do usuário.
