# Spec Delta

## Purpose

Define o tema visual (claro ou escuro) com que as telas do app são mostradas e permite que cada usuário alterne entre os dois modos, mantendo a escolha entre visitas.

## ADDED Requirements

### Requirement: Tema claro como padrão
O sistema DEVE mostrar todas as telas, públicas e autenticadas, no tema claro quando o navegador ainda não tiver uma escolha de tema salva. O tema padrão NÃO DEVE depender da preferência de modo escuro do sistema operacional ou do navegador.

#### Scenario: Primeiro acesso com o sistema operacional em modo escuro
- **QUANDO** um usuário sem escolha de tema salva abre qualquer tela do app em um dispositivo configurado para modo escuro
- **ENTÃO** o sistema DEVE mostrar a tela no tema claro

#### Scenario: Primeiro acesso à tela de login
- **QUANDO** um visitante sem escolha de tema salva abre a tela de login
- **ENTÃO** o sistema DEVE mostrar a tela no tema claro

### Requirement: Alternância entre tema claro e escuro
O sistema DEVE oferecer, em todas as telas autenticadas, um controle visível para alternar entre o tema claro e o escuro: na barra lateral quando ela estiver visível e no topo da página quando a navegação estiver recolhida no menu. Ao acionar o controle, o sistema DEVE aplicar o outro tema na hora, a todos os elementos da tela, sem recarregar a página e sem descartar dados digitados, filtros ou diálogos abertos. O controle DEVE indicar o tema para o qual vai mudar.

#### Scenario: Mudar para o tema escuro
- **QUANDO** um usuário autenticado no tema claro aciona o controle de tema
- **ENTÃO** o sistema DEVE passar a mostrar a tela no tema escuro sem recarregar a página

#### Scenario: Voltar para o tema claro
- **QUANDO** um usuário autenticado no tema escuro aciona o controle de tema
- **ENTÃO** o sistema DEVE passar a mostrar a tela no tema claro sem recarregar a página

#### Scenario: Troca com formulário preenchido
- **QUANDO** o usuário troca o tema com um formulário parcialmente preenchido na tela
- **ENTÃO** o sistema DEVE manter os valores digitados no formulário

#### Scenario: Controle em tela estreita
- **QUANDO** um usuário autenticado acessa o app em uma tela de tablet ou celular, com a barra lateral recolhida
- **ENTÃO** o sistema DEVE mostrar o controle de tema no topo da página, sem exigir abrir o menu

### Requirement: Persistência da escolha de tema
O sistema DEVE guardar no navegador o último tema escolhido pelo usuário e DEVE aplicá-lo em todas as telas, inclusive nas públicas, nas visitas seguintes nesse navegador, até nova troca. A escolha NÃO DEVE ser gravada no servidor nem exigir sessão autenticada para ser aplicada.

#### Scenario: Escolha mantida após recarregar
- **QUANDO** o usuário escolhe o tema escuro e recarrega a página ou navega para outra tela
- **ENTÃO** o sistema DEVE mostrar a nova tela no tema escuro

#### Scenario: Escolha mantida após sair
- **QUANDO** o usuário escolhe o tema escuro, sai do app e volta à tela de login no mesmo navegador
- **ENTÃO** o sistema DEVE mostrar a tela de login no tema escuro

### Requirement: Controle de tema acessível
O controle de tema DEVE ter um rótulo acessível que descreva a ação (por exemplo, "Ativar tema escuro" ou "Ativar tema claro"), DEVE ser alcançável e acionável pelo teclado e DEVE manter contraste legível nos dois temas.

#### Scenario: Troca pelo teclado
- **QUANDO** o usuário leva o foco ao controle de tema com Tab e pressiona Enter ou Espaço
- **ENTÃO** o sistema DEVE trocar o tema e manter o foco no controle

#### Scenario: Rótulo para leitor de tela
- **QUANDO** um leitor de tela anuncia o controle de tema no tema claro
- **ENTÃO** o rótulo anunciado DEVE indicar que o controle ativa o tema escuro
