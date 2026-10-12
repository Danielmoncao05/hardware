# Design

## Contexto

Ver `proposal.md`. Todas as telas autenticadas passam por `layout()` em `hardware/components.py` e usam os mesmos auxiliares (`empty_row`, `loading_overlay`, `native_select`); as tabelas são `rx.table.root` do Radix Themes, que gera classes estáveis (`rt-TableRoot`, `rt-TableRow`). As telas de conta não usam `layout()`.

## Decisões

### 1. Mudar nos componentes comuns, não tela a tela
Indicação da página atual, subtítulo e estado vazio ficam em `components.py`, então cada tela só passa o texto do subtítulo. Estilo de tabela fica em CSS global (`assets/app.css`, que substitui `assets/dashboard.css` e mantém a animação do painel), para não editar cada uma das ~20 tabelas.

### 2. Página atual pela URL
`nav_link` compara `AuthState.router.url.path` com o caminho do item: igual ao caminho, ou começa com ele seguido de "/" (assim `/equipamentos/5` destaca "Equipamentos"). `/novo-equipamento` também destaca "Equipamentos". O item ativo recebe `aria-current="page"`. Alternativa descartada: passar o item ativo como parâmetro de `layout()`, que exigiria mudar a assinatura em todas as telas.

### 3. Marca compartilhada
A marca (ícone `heart_pulse` num quadrado da cor da marca + nome) vira `brand_mark()` em `components.py`, usada na barra superior e nas telas de conta. A página institucional mantém a dela.

### 4. Telas de conta
Um `account_shell()` com fundo em gradiente suave da cor da marca (tokens `rx.color("accent", 2..3)`, que se adaptam aos dois temas), a marca acima do cartão e o cartão com sombra.

## Riscos / Concessões

- [CSS global nas tabelas pode afetar tabelas que não deveriam mudar] → Os seletores usam as classes do Radix só dentro de `#conteudo` (área autenticada).
- [Detecção da página atual depende do formato da URL] → Teste unitário da função que compara os caminhos.
