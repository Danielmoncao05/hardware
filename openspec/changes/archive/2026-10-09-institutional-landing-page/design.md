# Design

## Context

O app é Reflex (Radix Themes + plugin Tailwind v4), com tema global `accent_color="teal"` e modo claro padrão com alternância (change `theme-toggle`). As telas usam tokens `rx.color(...)`/`color_scheme`, que se adaptam ao modo escuro. A rota `/` hoje é o Painel, protegido por `DashboardState.on_load` → `_guard("reports.read")`. Não há página pública além de login e recuperação de senha. A regra do projeto proíbe dados clínicos/de pacientes na interface (`tests/test_no_clinical_data.py`). Motivação: ver proposal.md.

## Goals / Non-Goals

**Goals:**
- Página institucional estática em Python/Reflex, sem estado de servidor nem chamadas à API.
- Paleta azul/branco/cinza aplicada só nessa página, compatível com claro e escuro.
- Mover o Painel para `/painel` sem alterar suas regras de acesso.

**Non-Goals:**
- Alterar o tema global, a tela de login ou as telas internas.
- Formulário de contato, cadastro público, CMS ou conteúdo editável.
- Redirecionar automaticamente usuários logados da página institucional para o Painel.
- SEO avançado além de `title` e `description` da página.

## Decisions

1. **Novo módulo `hardware/pages/landing.py`** com funções pequenas por seção (`_header`, `_hero`, `_features`, `_about`, `_footer`) e `landing_page()`. Registrado com `app.add_page(landing_page, route="/", title="HospitalTech — Gestão de equipamentos hospitalares", description=...)`, sem `on_load`. Alternativa descartada: reaproveitar `layout()` — ele exige sessão e mostra o menu interno.

2. **Paleta local via `rx.theme(accent_color="indigo")` envolvendo só a página.** O Radix permite temas aninhados: `rx.theme(..., accent_color="indigo", gray_color="slate", has_background=True)` como raiz da página faz botões, links e `rx.color("accent", n)` ficarem azuis ali, sem tocar no tema global. Usa-se `indigo` (o azul do Radix #3E63DD) e não `blue`: o `blue-9` (#0090FF) com texto branco fica em ~3,2:1, abaixo do AA; o `indigo-9` passa de 4,5:1. Fundo branco = `rx.color("gray", 1)`/fundo do tema; seções alternadas em `rx.color("gray", 2)`; textos secundários com `color_scheme="gray"`. Sem hex fixos, então o modo escuro funciona sozinho. O tema aninhado não pode fixar `appearance`, para não travar o modo escolhido. Alternativa descartada: trocar o `accent_color` global (o usuário pediu escopo só na página) ou hex fixos (quebram no escuro).

3. **Imagens locais em `assets/landing/`**, fotos com licença livre para uso comercial sem atribuição obrigatória (CC0 ou domínio público do Wikimedia Commons; a busca do Unsplash bloqueia acesso automatizado), baixadas uma vez, redimensionadas (~1600 px no lado maior) e convertidas para `.webp`. Três imagens: `hero.webp` (sala cirúrgica vazia), `manutencao.webp` (mãos de técnico testando a placa de um equipamento médico) e `sobre.webp` (corredor de hospital). Fonte, autor, URL e licença ficam em `assets/landing/CREDITS.md`. Servidas por `rx.image(src="/landing/....webp", alt=..., loading="lazy")` (exceto a do hero, carregada imediatamente) com `object_fit="cover"` e `border_radius`. Alternativa descartada: URLs externas (dependência de terceiros e bloqueios em redes hospitalares); ilustrações SVG próprias (custo de produção maior, aspecto menos institucional) — ficam como reserva se uma foto adequada não for encontrada.

4. **Ícones `rx.icon` (lucide) nos cards de recursos**, reaproveitando os já usados no menu (`monitor`, `wrench`, `circle_alert`, `activity`, `file_chart_column`) para manter coerência com o sistema.

5. **Responsividade com props responsivas do Reflex** (`columns=["1", "1", "2"]`, `direction=["column", "column", "row"]`) e `max_width` central (~72rem) com `padding_x="1rem"`. O cabeçalho mantém o botão "Acessar o sistema" visível em todas as larguras.

6. **Acesso ao login com `rx.link(rx.button(..., tab_index=-1), href="/login")`** — navegação do cliente; só o link recebe foco, então Tab + Enter funciona e não depende de evento de servidor. No cabeçalho, em telas estreitas, o rótulo visível vira "Entrar" (o `aria-label` continua "Acessar o sistema") para não quebrar linha. A página inclui o `theme_toggle()` existente no cabeçalho, para que o visitante possa alternar o tema também ali.

7. **Mudança de rota do Painel**: `route="/painel"` em `hardware.py`; `rx.redirect("/painel")` em `AuthState.login` e em `ChangePasswordState`; link "Voltar" e `NAV` para `/painel`. O guard continua redirecionando apenas para `/login`, `/sem-acesso` e `/trocar-senha`. Testes estáticos que mapeiam rotas (`test_every_nav_link_is_gated_by_its_page_permission`, `test_temporary_password_routes_to_change_page_before_anything_else`) são atualizados.

## Risks / Trade-offs

- [Favoritos e links antigos para `/` levavam ao Painel] → Agora abrem a página institucional, que tem o botão de acesso; usuários com sessão chegam ao Painel em dois cliques. Aceito, conforme decisão do usuário.
- [Tema aninhado do Radix pode não herdar o modo escuro corretamente] → Não definir `appearance` no tema aninhado e verificar visualmente nos dois modos; se falhar, usar `color_scheme="blue"` componente a componente.
- [Fotos de banco podem mostrar pacientes ou telas com dados] → Critério de seleção explícito na tarefa e revisão manual de cada imagem antes de incluir.
- [Peso das imagens afeta o carregamento] → WebP redimensionado, alvo < 300 KB por imagem, `loading="lazy"` fora do hero.
- [Ano do rodapé] → `current_year()` em `components.py` usa `rx.moment` no fuso da instituição, calculado no navegador; fica em `components.py` porque os testes proíbem `rx.moment` direto nas páginas.
- [Rota `/` sem `on_load` muda o comportamento testado em `test_no_clinical_data.py`] → Esse teste só verifica nomes de rota/colunas; a página não usa termos clínicos.

## Migration Plan

Deploy normal do frontend. Rollback: reverter o commit (volta `/` para o Painel). Não há dados nem backend envolvidos.
