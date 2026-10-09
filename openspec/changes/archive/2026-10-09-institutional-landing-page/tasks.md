# Tarefas

## 1. Imagens

- [x] 1.1 Selecionar três fotos com licença livre (CC0/domínio público do Wikimedia Commons) — equipamento/ambiente hospitalar (hero), técnico em manutenção de equipamento médico, e equipe/corredor hospitalar (sobre) — sem pacientes identificáveis nem telas com dados clínicos legíveis; verificar revisando cada imagem manualmente
- [x] 1.2 Redimensionar (~1600 px no lado maior), converter para WebP e salvar em `assets/landing/` como `hero.webp`, `manutencao.webp` e `sobre.webp`; verificar que cada arquivo tem menos de 300 KB
- [x] 1.3 Criar `assets/landing/CREDITS.md` com autor, URL de origem e licença de cada imagem; verificar que as três imagens estão listadas

## 2. Página institucional

- [x] 2.1 Criar `hardware/pages/landing.py` com `landing_page()` envolvida em `rx.theme(accent_color="indigo", gray_color="slate", has_background=True)` sem `appearance`; verificar com `reflex compile` que a página compila
- [x] 2.2 Implementar o cabeçalho com a marca "HospitalTech" (ícone + nome em azul), `theme_toggle()` e o link-botão "Acessar o sistema" para `/login`; verificar que o botão continua visível em 360 px de largura
- [x] 2.3 Implementar a seção principal: título, texto de apresentação da HospitalTech e do sistema de gestão de equipamentos hospitalares, chamada "Acessar o sistema" para `/login` e `hero.webp` com `alt` em português; verificar que texto e imagem ficam lado a lado no desktop e empilhados no celular
- [x] 2.4 Implementar a seção de recursos com cards (ícones lucide `monitor`, `wrench`, `circle_alert`, `activity`, `file_chart_column`) para inventário, manutenções preventivas e corretivas, ocorrências, acompanhamento e relatórios, mais `manutencao.webp`; verificar que os cinco recursos aparecem e o grid vira uma coluna no celular
- [x] 2.5 Implementar a seção "Sobre a HospitalTech" com `sobre.webp` (`loading="lazy"`) e fundo cinza alternado (`rx.color("gray", 2)`), e o rodapé com "HospitalTech" e o ano corrente; verificar visualmente a ordem das seções
- [x] 2.6 Registrar a página em `hardware/hardware.py` com `route="/"`, título e `description`, sem `on_load`; verificar que `/` abre sem sessão e sem redirecionar para `/login`

## 3. Painel em `/painel`

- [x] 3.1 Mudar a rota do Painel para `/painel` em `hardware/hardware.py` e o item "Painel" de `NAV` em `hardware/components.py`; verificar que o menu leva a `/painel`
- [x] 3.2 Trocar `rx.redirect("/")` por `rx.redirect("/painel")` em `AuthState.login` (`hardware/state.py`) e em `ChangePasswordState`, e o link "Voltar" de `hardware/pages/change_password.py`; verificar com `grep` que não sobra redirecionamento ou link interno para `"/"` fora da página institucional
- [ ] 3.3 Verificar no navegador: login válido leva a `/painel`; `/painel` sem sessão vai para `/login`; usuário sem `reports.read` vai para `/sem-acesso`; troca de senha concluída leva a `/painel`

## 4. Testes

- [x] 4.1 Atualizar `tests/test_frontend_unit.py` (mapa de rotas de `test_every_nav_link_is_gated_by_its_page_permission` e a asserção de redirecionamento pós-login) para `/painel`; verificar que esses testes passam
- [x] 4.2 Adicionar testes estáticos da página institucional: rota `/` registrada sem `on_load`, presença de "HospitalTech", todos os links de acesso apontando para `/login`, todas as `rx.image` com `alt` não vazio e `src` local (`/landing/...`); verificar que passam
- [x] 4.3 Rodar `pytest` e verificar que toda a suíte passa, incluindo `tests/test_no_clinical_data.py`

## 5. Verificação visual

- [x] 5.1 Abrir a página institucional nos temas claro e escuro e verificar fundo branco/destaques azuis/textos cinza no claro, contraste legível no escuro, e que o login e as telas internas mantêm as cores atuais (teal)
- [x] 5.2 Testar em 360 px, 768 px e 1280 px de largura sem rolagem horizontal, e navegar só com Tab/Enter até o login a partir do cabeçalho e da seção principal
- [x] 5.3 Bloquear acesso a domínios externos (DevTools → request blocking) e verificar que todas as imagens carregam
