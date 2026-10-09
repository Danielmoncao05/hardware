# Tarefas

## 1. Tema padrão

- [x] 1.1 Em `rxconfig.py`, adicionar `default_color_mode="light"` ao `rx.Config` (sem `appearance` no `rx.theme`) e verificar com `reflex compile` que a compilação passa e que o `ThemeProvider` gerado recebe `defaultTheme: "light"`
- [ ] 1.2 Verificar no navegador, com o sistema operacional em modo escuro e `localStorage` limpo, que login e painel abrem no tema claro

## 2. Botão de alternância

- [x] 2.1 Criar `theme_toggle()` em `hardware/components.py`: `rx.icon_button` com `on_click=rx.toggle_color_mode`, ícone `moon`/`sun` via `rx.color_mode_cond` e `aria_label` "Ativar tema escuro"/"Ativar tema claro"; verificar com um teste em `tests/test_frontend_unit.py` que o componente renderiza com o evento de troca e os dois rótulos
- [ ] 2.2 Incluir `theme_toggle()` na barra superior (`top_bar()`, change `dashboard-redesign`), visível em todas as larguras, e verificar no desktop que o botão aparece ao lado do sino e do menu do usuário e troca o tema sem recarregar a página
- [ ] 2.3 Verificar em largura de tablet/celular que o botão de tema aparece na barra superior sem abrir o menu e que existe um único botão de tema em cada largura (teste `test_theme_toggle_is_only_in_the_top_bar`)

## 3. Verificação

- [ ] 3.1 Trocar o tema com um formulário parcialmente preenchido e com um diálogo aberto e verificar que os valores e o diálogo continuam na tela
- [ ] 3.2 Escolher o tema escuro, recarregar, navegar entre telas, sair e voltar ao login; verificar que o tema escuro é mantido em todas
- [ ] 3.3 Acionar o botão com Tab + Enter/Espaço e conferir com o leitor de tela (ou inspeção do `aria-label`) que o rótulo muda conforme o tema e o foco permanece no botão
- [ ] 3.4 Percorrer todas as telas (painel, acompanhamento, equipamentos, manutenções, ocorrências, catálogos, relatórios, usuários, login, pop-up de alertas) nos dois temas e verificar que não há texto ilegível ou cor fixa destoando
- [x] 3.5 Rodar `pytest` e verificar que toda a suíte passa
