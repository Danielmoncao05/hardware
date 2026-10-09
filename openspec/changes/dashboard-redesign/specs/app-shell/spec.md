# Delta da spec

## Purpose

Define a estrutura comum das telas autenticadas do HospitalTech: a marca, a barra superior com acesso aos alertas e ao menu do usuário, e a navegação entre as áreas do sistema.

## ADDED Requirements

### Requirement: Marca HospitalTech
O sistema DEVE identificar o aplicativo como "HospitalTech" no topo de todas as telas autenticadas, na tela de login e no título das páginas mostrado pelo navegador. O nome anterior "Gestão de Equipamentos" NÃO DEVE mais aparecer como nome do aplicativo.

#### Scenario: Marca nas telas autenticadas
- **QUANDO** um usuário autenticado abre qualquer tela do sistema
- **ENTÃO** o sistema DEVE mostrar a marca "HospitalTech" no topo da tela

#### Scenario: Marca na tela de login
- **QUANDO** um visitante abre a tela de login
- **ENTÃO** o sistema DEVE mostrar "HospitalTech" como nome do aplicativo

### Requirement: Barra superior com alertas e menu do usuário
O sistema DEVE mostrar, em todas as telas autenticadas, uma barra superior com a marca à esquerda e, à direita, um controle de alertas e um menu do usuário. O controle de alertas DEVE abrir a lista atual de equipamentos que precisam de atenção, com as mesmas regras e a mesma permissão dos alertas já existentes, e DEVE indicar quantos equipamentos estão nessa lista; quem não tem permissão de ler relatórios NÃO DEVE ver o controle. O menu do usuário DEVE mostrar o nome (ou o e-mail, quando não houver nome) e o perfil do usuário, e oferecer "Alterar senha" e "Sair". Os controles DEVEM ter rótulos acessíveis e funcionar pelo teclado.

#### Scenario: Abrir a lista de alertas
- **QUANDO** um usuário com permissão de ler relatórios aciona o controle de alertas
- **ENTÃO** o sistema DEVE mostrar os equipamentos que precisam de atenção agora, com a situação de cada um e um link para o equipamento

#### Scenario: Usuário sem permissão de relatórios
- **QUANDO** um usuário sem permissão de ler relatórios abre uma tela autenticada
- **ENTÃO** o sistema NÃO DEVE mostrar o controle de alertas

#### Scenario: Sair pelo menu do usuário
- **QUANDO** um usuário abre o menu do usuário e escolhe "Sair"
- **ENTÃO** o sistema DEVE encerrar a sessão e mostrar a tela de login

#### Scenario: Usuário sem nome cadastrado
- **QUANDO** um usuário sem nome cadastrado abre o menu do usuário
- **ENTÃO** o sistema DEVE mostrar o e-mail no lugar do nome

### Requirement: Navegação lateral
O sistema DEVE manter a navegação entre as áreas na barra lateral (desktop) e no menu recolhível (tablet e celular), mostrando só as áreas permitidas ao perfil do usuário, com os nomes em português.

#### Scenario: Navegação conforme o perfil
- **QUANDO** um visualizador abre uma tela autenticada
- **ENTÃO** o sistema DEVE mostrar na navegação só as áreas que o perfil dele pode acessar, e NÃO DEVE mostrar "Usuários e perfis"
