# Proposta

## Por quê

Hoje quem abre o endereço do sistema cai direto no Painel (rota `/`) e, sem sessão, é jogado para a tela de login, sem nenhuma apresentação da empresa ou do produto. A HospitalTech quer uma página inicial institucional, com identidade visual hospitalar (azul, branco e cinza), que apresente a empresa e o sistema de gestão de equipamentos hospitalares e leve o visitante até o login.

## O que muda

- Nova **página inicial institucional pública** da HospitalTech na rota `/`, acessível sem login, com:
  - cabeçalho com a marca "HospitalTech" e botão "Acessar o sistema";
  - seção principal (hero) com título, texto de apresentação, imagem hospitalar e chamada para o login;
  - seção de recursos do sistema (inventário, manutenções preventivas e corretivas, ocorrências, acompanhamento e relatórios), com ícones e imagens ligados à gestão de equipamentos;
  - seção institucional "Sobre a HospitalTech" e rodapé com o nome da empresa e o ano.
- Paleta da página: azul (destaque), branco (fundo) e cinza (textos e superfícies secundárias), usando tokens de cor que também funcionam no tema escuro já existente.
- Imagens hospitalares (equipamentos médicos, ambiente hospitalar, equipe técnica) servidas localmente em `assets/`, com texto alternativo, sem pacientes identificáveis e sem qualquer dado clínico.
- Todos os botões de acesso da página levam à tela de login existente (`/login`), que não muda.
- **BREAKING (rotas internas)**: o Painel sai de `/` e passa para `/painel`. O redirecionamento após o login, o retorno da troca de senha e o item "Painel" do menu passam a apontar para `/painel`.
- As cores das telas internas e do login continuam como estão (accent `teal`); a paleta azul vale só para a página institucional.

## Capacidades

### Novas capacidades
- `institutional-landing`: página inicial pública da HospitalTech, com conteúdo institucional, identidade visual azul/branco/cinza, imagens hospitalares e acesso à tela de login.

### Capacidades modificadas
<!-- Nenhuma em openspec/specs/ (ainda não há specs principais). A mudança de rota do Painel é coberta como requisito da nova capacidade. -->

## Impacto

- `hardware/pages/landing.py` (novo): componentes e página institucional.
- `hardware/hardware.py`: registrar a página institucional em `/` e mover o Painel para `/painel`.
- `hardware/state.py`: redirecionamento pós-login para `/painel`.
- `hardware/pages/change_password.py`: redirecionamento e link "Voltar" para `/painel`.
- `hardware/components.py`: item "Painel" do menu (`NAV`) para `/painel`.
- `assets/landing/` (novo): imagens da página, com créditos/licenças registrados.
- `tests/test_frontend_unit.py`: atualizar as verificações que esperam o Painel em `/`; incluir testes da página institucional.
- Sem mudança no backend (Xano), na API ou em dependências Python.
