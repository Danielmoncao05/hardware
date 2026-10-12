# Delta da spec

## Purpose

Define como as telas autenticadas reagem às ações do usuário enquanto os dados são carregados: os controles respondem na hora, o carregamento é indicado e o usuário sabe quando uma escolha não muda o resultado.

## ADDED Requirements

### Requirement: Controles respondem antes da resposta do servidor
Ao acionar um controle que recarrega dados (abas, paginação, filtros, alternâncias), o sistema DEVE mostrar a nova escolha na tela imediatamente e indicar que está carregando até os dados chegarem. Enquanto a recarga de uma alternância estiver em andamento, o sistema NÃO DEVE aceitar um novo acionamento do mesmo controle.

#### Scenario: Ligar "Mostrar inativos"
- **QUANDO** um usuário liga "Mostrar inativos" na tela de catálogos
- **ENTÃO** o controle DEVE aparecer ligado na hora, com indicação de carregamento, e os catálogos DEVEM ser recarregados incluindo os registros inativos

#### Scenario: Clique duplo na alternância
- **QUANDO** o usuário clica duas vezes seguidas em "Mostrar inativos"
- **ENTÃO** o sistema DEVE tratar só o primeiro clique até a recarga terminar

### Requirement: Retorno quando um filtro não muda o resultado
Quando o usuário liga "Mostrar inativos", o sistema DEVE informar quantos registros inativos foram incluídos ou, se não houver nenhum, que não há registros inativos cadastrados.

#### Scenario: Nenhum registro inativo
- **QUANDO** o usuário liga "Mostrar inativos" e nenhum registro de catálogo está desativado
- **ENTÃO** o sistema DEVE mostrar "Nenhum registro inativo cadastrado."

#### Scenario: Registros inativos incluídos
- **QUANDO** o usuário liga "Mostrar inativos" e existem registros desativados
- **ENTÃO** o sistema DEVE mostrar quantos registros inativos foram incluídos e marcá-los como inativos nas tabelas

### Requirement: Telas carregam os dados independentes ao mesmo tempo
Ao abrir uma tela, o sistema DEVE buscar ao mesmo tempo os dados que não dependem uns dos outros (por exemplo, as opções dos filtros e a lista principal), de forma que o tempo de abertura seja próximo ao da requisição mais lenta, e não à soma de todas. Uma falha em um desses dados NÃO DEVE impedir a exibição dos demais.

#### Scenario: Opções e lista ao abrir a tela
- **QUANDO** um usuário abre a lista de equipamentos
- **ENTÃO** as opções dos filtros e a lista DEVEM ser buscadas ao mesmo tempo

#### Scenario: Falha em um dos dados
- **QUANDO** a lista de usuários falha ao carregar
- **ENTÃO** o sistema DEVE mostrar o erro e ainda assim mostrar as opções de perfil do formulário de cadastro
