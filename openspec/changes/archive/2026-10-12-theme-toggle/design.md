# Design

## Context

- O app usa Reflex 0.9.12 com `RadixThemesPlugin(theme=rx.theme(accent_color="teal", radius="medium"))` em `rxconfig.py`, sem `appearance`. Nesse caso o Reflex usa `Config.default_color_mode`, cujo padrão é `"system"`: daí as telas seguirem o modo escuro do sistema operacional (ver proposal.md — Por quê).
- O provedor de tema do Reflex (`ThemeProvider` em `react-theme.js`) já guarda a escolha em `localStorage["theme"]` e só usa o padrão quando não há nada salvo. Um script de pré-carga aplica o tema antes da renderização, evitando o "piscar".
- Toda a estrutura autenticada passa por `layout()` em `hardware/components.py`: barra lateral (visível a partir do breakpoint de desktop) e um cabeçalho com o botão do menu recolhível (tablet/celular). As telas públicas (login, recuperar/redefinir senha) não usam `layout()`.
- As páginas usam tokens `rx.color(...)` e `color_scheme`; não há cores fixas (hex, `white`, `black`), então os dois temas funcionam sem ajuste nas páginas.

## Goals / Non-Goals

**Goals:**
- Tema claro como padrão, com troca instantânea no cliente e persistência no navegador.
- Um único componente de alternância reutilizado na barra lateral e no cabeçalho móvel.

**Non-Goals:**
- Guardar a preferência na conta do usuário (Xano) ou sincronizar entre dispositivos.
- Opção "seguir o sistema" na interface; o controle alterna só entre claro e escuro.
- Controle de tema nas telas públicas (elas só respeitam a escolha salva).
- Revisar paleta, cor de destaque ou contraste além do que o Radix já oferece.

## Decisions

1. **Padrão via `rx.Config(default_color_mode="light")`**, e não via `rx.theme(appearance="light")`.
   O `appearance` fixo no tema raiz força o Radix a ficar sempre claro e anula a troca. O `default_color_mode` só define o valor inicial do `ThemeProvider` e do script de pré-carga, preservando a alternância e a escolha salva.

2. **Troca no cliente com `rx.toggle_color_mode` e `rx.color_mode_cond`**, sem estado no servidor.
   A troca não passa pelo backend, então é imediata, não reinicia o estado das páginas e não perde formulários nem diálogos. Alternativa descartada: um `rx.State` com o tema, que exigiria ida e volta ao servidor e duplicaria o que o `ThemeProvider` já guarda.

3. **Componente próprio `theme_toggle()` em `components.py`**, um `rx.icon_button` com `on_click=rx.toggle_color_mode`, ícone `moon` no claro e `sun` no escuro, e `aria_label` via `rx.color_mode_cond("Ativar tema escuro", "Ativar tema claro")`.
   Alternativa descartada: `rx.color_mode.button`, que por padrão é posicionado de forma flutuante e cicla também por "system"; o componente próprio dá o rótulo em português e só os dois estados pedidos.

4. **Posição**: na barra lateral, no bloco do usuário (junto de "Alterar senha" / "Sair"); no cabeçalho de `layout()`, ao lado do botão de menu, visível só quando a barra lateral está oculta (`display=["flex","flex","flex","none"]`, os mesmos breakpoints do `mobile_menu`). Assim há sempre exatamente um controle visível.

## Risks / Trade-offs

- [Usuários que já usavam o app no modo escuro do sistema passam a ver o tema claro] → Comportamento desejado; eles podem voltar ao escuro com um clique e a escolha fica salva.
- [Navegadores que já tinham `localStorage["theme"] = "system"` gravado continuariam seguindo o sistema] → O Reflex só grava a chave quando o usuário troca o tema; como não havia controle, não deve haver valores salvos. Verificar na tarefa de teste manual.
- [Componentes com cor fixa adicionados no futuro podem ficar ilegíveis no escuro] → Manter o uso de tokens `rx.color`/`color_scheme`; a checagem visual das telas nos dois temas está nas tarefas.

## Migration Plan

Só frontend: publicar a nova versão. Rollback é reverter `rxconfig.py` e `components.py`; a chave `theme` no navegador é inofensiva para versões anteriores.
