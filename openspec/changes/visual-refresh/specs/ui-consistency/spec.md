# Delta da spec

## Purpose

Define os elementos visuais comuns das telas do HospitalTech, para que o usuário saiba onde está, entenda para que serve cada tela e encontre o mesmo padrão em tabelas, listas vazias e telas de conta.

## ADDED Requirements

### Requirement: Indicação da página atual
O sistema DEVE destacar na navegação (barra lateral e menu do celular) o item da área em que o usuário está, inclusive nas telas internas dessa área (por exemplo, o detalhe de um equipamento destaca "Equipamentos"), e DEVE marcar esse item como a página atual para leitores de tela.

#### Scenario: Detalhe de equipamento
- **QUANDO** o usuário abre o detalhe de um equipamento
- **ENTÃO** o item "Equipamentos" da navegação DEVE aparecer destacado e marcado como página atual

#### Scenario: Só um item destacado
- **QUANDO** o usuário está em qualquer tela autenticada
- **ENTÃO** no máximo um item da navegação DEVE aparecer destacado

### Requirement: Descrição das telas
Cada tela autenticada DEVE mostrar, abaixo do título, uma frase curta dizendo para que a tela serve.

#### Scenario: Tela de manutenções
- **QUANDO** o usuário abre a tela de manutenções
- **ENTÃO** o sistema DEVE mostrar uma descrição abaixo do título "Manutenções"

### Requirement: Tabelas e listas vazias padronizadas
As tabelas DEVEM ter o mesmo estilo em todas as telas, com cabeçalho destacado e realce da linha sob o cursor. Quando uma tabela não tiver registros, o sistema DEVE mostrar uma mensagem centralizada com um ícone, no lugar das linhas.

#### Scenario: Lista sem registros
- **QUANDO** uma consulta não encontra registros
- **ENTÃO** a tabela DEVE mostrar a mensagem de lista vazia centralizada, com ícone

### Requirement: Identidade visual das telas de conta
As telas de login, recuperação de senha, redefinição de senha e troca de senha DEVEM mostrar a marca HospitalTech (ícone e nome) e seguir as cores da marca, nos temas claro e escuro.

#### Scenario: Tela de login
- **QUANDO** um visitante abre a tela de login
- **ENTÃO** o sistema DEVE mostrar o ícone e o nome HospitalTech acima do formulário

### Requirement: Acesso negado orienta o próximo passo
A tela de acesso negado DEVE explicar que o perfil não tem permissão e oferecer ações para voltar à tela anterior e para ir a uma área que o usuário pode acessar, sem levar a outra tela negada.

#### Scenario: Usuário sem permissão
- **QUANDO** um usuário abre uma tela que o perfil dele não permite
- **ENTÃO** o sistema DEVE mostrar a explicação e as ações "Voltar" e "Ir para o início"
