# Spec Delta

## Purpose

Define a página inicial institucional pública da HospitalTech: o que ela apresenta, a identidade visual hospitalar (azul, branco e cinza), as imagens usadas e como o visitante chega dela à tela de login.

## ADDED Requirements

### Requirement: Página institucional pública na raiz do site
O sistema DEVE mostrar a página institucional da HospitalTech no endereço raiz (`/`) para qualquer visitante, com ou sem sessão, sem exigir login e sem fazer chamadas à API. A página NÃO DEVE redirecionar o visitante para o login nem para outra tela de forma automática.

#### Scenario: Visitante sem sessão abre o site
- **QUANDO** um visitante sem sessão abre o endereço raiz do sistema
- **ENTÃO** o sistema DEVE mostrar a página institucional da HospitalTech, sem redirecionar para `/login`

#### Scenario: Usuário com sessão abre o site
- **QUANDO** um usuário com sessão ativa abre o endereço raiz do sistema
- **ENTÃO** o sistema DEVE mostrar a página institucional, e o acesso ao sistema DEVE continuar disponível pelos botões da página

### Requirement: Conteúdo institucional da HospitalTech
A página institucional DEVE exibir o nome da empresa "HospitalTech" no cabeçalho e no rodapé e DEVE conter, nesta ordem: um cabeçalho com a marca e um botão de acesso ao sistema; uma seção principal com título, texto de apresentação da empresa e do sistema de gestão de equipamentos hospitalares e uma chamada para acessar o sistema; uma seção de recursos que apresente ao menos inventário de equipamentos, manutenções preventivas e corretivas, registro de ocorrências, acompanhamento e relatórios; uma seção "Sobre a HospitalTech"; e um rodapé com o nome da empresa e o ano corrente. Todo o texto DEVE estar em português do Brasil. A página NÃO DEVE exibir nem mencionar dados de pacientes, dados clínicos ou diagnósticos.

#### Scenario: Seções da página
- **QUANDO** um visitante abre a página institucional
- **ENTÃO** o sistema DEVE mostrar o cabeçalho com "HospitalTech", a seção principal, a seção de recursos, a seção "Sobre a HospitalTech" e o rodapé

#### Scenario: Recursos apresentados
- **QUANDO** um visitante chega à seção de recursos
- **ENTÃO** o sistema DEVE apresentar inventário de equipamentos, manutenções preventivas e corretivas, ocorrências, acompanhamento e relatórios

### Requirement: Acesso à tela de login a partir da página institucional
A página institucional DEVE oferecer ao menos dois controles de acesso ao sistema — um no cabeçalho e um na seção principal — e todos DEVEM levar à tela de login existente (`/login`). Os controles DEVEM ser links navegáveis por teclado e DEVEM ter texto que indique a ação (por exemplo, "Acessar o sistema"). A tela de login NÃO DEVE ser alterada por esta capacidade.

#### Scenario: Acessar o sistema pelo cabeçalho
- **QUANDO** o visitante aciona o botão de acesso no cabeçalho da página institucional
- **ENTÃO** o sistema DEVE abrir a tela de login em `/login`

#### Scenario: Acessar o sistema pela seção principal
- **QUANDO** o visitante aciona a chamada de acesso na seção principal
- **ENTÃO** o sistema DEVE abrir a tela de login em `/login`

#### Scenario: Acesso pelo teclado
- **QUANDO** o visitante navega pela página usando apenas a tecla Tab e aciona um controle de acesso com Enter
- **ENTÃO** o sistema DEVE abrir a tela de login em `/login`

### Requirement: Identidade visual azul, branco e cinza
A página institucional DEVE usar azul como cor de destaque (marca, títulos de destaque, botões e ícones), branco como fundo principal e cinza para textos secundários, bordas e fundos de seções alternadas. A página DEVE seguir o tema claro ou escuro ativo no navegador, mantendo contraste legível (mínimo WCAG AA para texto) nos dois temas. As cores das demais telas do sistema, incluindo o login, NÃO DEVEM mudar.

#### Scenario: Tema claro
- **QUANDO** um visitante abre a página institucional no tema claro
- **ENTÃO** o sistema DEVE mostrar a página com fundo branco, destaques em azul e textos secundários em cinza

#### Scenario: Tema escuro escolhido pelo usuário
- **QUANDO** um visitante que escolheu o tema escuro abre a página institucional
- **ENTÃO** o sistema DEVE mostrar a página com as variantes escuras da mesma paleta, com texto legível

#### Scenario: Demais telas inalteradas
- **QUANDO** o visitante sai da página institucional para a tela de login
- **ENTÃO** a tela de login DEVE manter as mesmas cores que tinha antes desta mudança

### Requirement: Imagens hospitalares adequadas ao sistema
A página institucional DEVE exibir imagens relacionadas ao contexto do sistema — equipamentos médico-hospitalares, ambiente hospitalar ou equipe técnica de manutenção — ao menos na seção principal e na seção "Sobre a HospitalTech". As imagens DEVEM ser servidas pelo próprio sistema (sem depender de sites de terceiros em tempo de execução), DEVEM ter licença que permita o uso registrada no projeto e DEVEM ter texto alternativo descritivo em português. As imagens NÃO DEVEM mostrar pacientes identificáveis nem informações clínicas legíveis (prontuários, monitores com dados de paciente).

#### Scenario: Imagens com texto alternativo
- **QUANDO** um leitor de tela percorre a página institucional
- **ENTÃO** cada imagem informativa DEVE ser anunciada com um texto alternativo descritivo em português

#### Scenario: Imagens disponíveis sem acesso externo
- **QUANDO** a página institucional é aberta em uma rede que bloqueia sites de imagens de terceiros
- **ENTÃO** todas as imagens da página DEVEM carregar normalmente

### Requirement: Layout responsivo
A página institucional DEVE ser utilizável em celular, tablet e desktop, sem rolagem horizontal. Em telas estreitas, as seções com texto e imagem lado a lado DEVEM empilhar o conteúdo verticalmente e o botão de acesso do cabeçalho DEVE continuar visível.

#### Scenario: Página no celular
- **QUANDO** um visitante abre a página institucional em uma tela com 360 px de largura
- **ENTÃO** o sistema DEVE mostrar o conteúdo empilhado em uma coluna, sem rolagem horizontal, com o botão de acesso visível no cabeçalho

### Requirement: Painel acessível em novo endereço
O Painel autenticado DEVE ficar disponível em `/painel`, com as mesmas regras de sessão e permissão que tinha em `/`. Após um login bem-sucedido sem senha temporária pendente, o sistema DEVE levar o usuário para `/painel`. Após a troca de senha, o sistema DEVE levar o usuário para `/painel`. O item "Painel" do menu DEVE apontar para `/painel`.

#### Scenario: Login bem-sucedido
- **QUANDO** um usuário sem senha temporária pendente entra com e-mail e senha válidos
- **ENTÃO** o sistema DEVE levá-lo para `/painel`

#### Scenario: Painel sem sessão
- **QUANDO** um visitante sem sessão abre `/painel`
- **ENTÃO** o sistema DEVE redirecioná-lo para `/login`

#### Scenario: Painel sem permissão
- **QUANDO** um usuário com sessão, mas sem a permissão de relatórios, abre `/painel`
- **ENTÃO** o sistema DEVE redirecioná-lo para `/sem-acesso`

#### Scenario: Troca de senha concluída
- **QUANDO** um usuário conclui a troca de senha
- **ENTÃO** o sistema DEVE levá-lo para `/painel`
