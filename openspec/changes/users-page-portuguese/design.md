# Design

## Decisões

### 1. Tradução no app, códigos intactos no banco
Os códigos de perfil e permissão são usados nas regras de autorização do Xano e nos testes. Por isso eles não mudam: `hardware/labels.py` mapeia código → (nome, descrição) em português e a página usa esse mapa. As bases já publicadas têm as descrições do seed em inglês; como o app usa o mapa para os perfis e permissões padrão, não é preciso migrar dados.

### 2. Perfis personalizados como digitados
Para perfis fora do mapa, o app mostra o `nome` e a `descricao` gravados.

### 3. Mensagens de erro no Xano
As mensagens do grupo Users são traduzidas na origem (os arquivos `.xs`), como as demais mensagens já em português, em vez de um dicionário de tradução no app.
