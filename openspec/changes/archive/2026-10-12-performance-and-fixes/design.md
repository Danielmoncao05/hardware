# Design

## Contexto

Ver `proposal.md`. Medições feitas em 2026-10-09 contra o Xano (endpoint sem autenticação, para não depender de dados):

| Três chamadas seguidas | Tempo |
|---|---|
| Conexão nova a cada chamada (comportamento anterior) | ~1,8 s |
| Conexão reaproveitada | ~0,95 s |
| Conexão reaproveitada e em paralelo | ~0,65 s |

Com 4,4 s entre as chamadas, a conexão reaproveitada às vezes já tinha sido fechada pelo servidor; dentro de um carregamento de tela as chamadas saem em sequência curta, que é o caso que importa.

## Objetivos / Fora do escopo

**Objetivos:** reduzir o tempo de abertura e de troca de filtros das telas sem aumentar o número de requisições (limite do plano Free).

**Fora do escopo:** cache no servidor do Xano, troca de plano, e juntar as contagens de equipamentos do `GET dashboard` em uma lista (ver Decisão 4).

## Decisões

### 1. Cliente HTTP compartilhado por event loop
`api.client()` mantém um `httpx.AsyncClient` por event loop (`max_keepalive_connections=10`, `keepalive_expiry=30 s`). Um loop novo, como acontece em cada teste, ganha um cliente novo. Uma leitura (GET) interrompida por conexão fechada (`RemoteProtocolError`, `ReadError`) é repetida uma vez; uma gravação não, porque pode ter sido aplicada. Alternativa descartada: HTTP/2, que exigiria a dependência `h2` e não traria ganho com tão poucas chamadas simultâneas.

### 2. `asyncio.gather` no carregamento das telas
Cada `on_load` junta as chamadas independentes; cada uma trata o próprio erro, para uma falha não esconder as demais. Exceção: em manutenções, a abertura da corretiva vem depois da lista, porque `_fetch` limpa `self.error` ao terminar e apagaria um erro da corretiva.

### 3. Menos consultas por requisição no Xano
- `GET acompanhamento`: as datas de última e próxima manutenção da página saem de 2 consultas (`equipamento_id in $pagina_ids`), indexadas por equipamento, em vez de `hhm/maintenance_dates` por linha (2 consultas x 25 linhas).
- `GET dashboard`: as contagens por severidade e status saem da lista `$ocorrencias_recentes` (abertas e em andamento, mesmo filtro de localização, sem descomissionados).

### 4. Contagens de equipamentos do painel mantidas
Status (4), categorias (12) e localizações (N) continuam como consultas `count`. Juntá-las numa lista e contar no XanoScript reduziria as consultas, mas percorreria todos os equipamentos ativos a cada requisição (até 10.000); só vale mudar depois de medir com volume real.

### 5. Alternância "Mostrar inativos"
O handler devolve o controle (`yield`) antes de recarregar e desabilita o controle durante a recarga. O rótulo fica ao lado do controle: um `<label>` envolvendo o próprio controle com `html_for` disparava o clique duas vezes.

### 6. `db.get` com id opcional
Antes de `db.get` com um id que pode ser nulo (responsável da ocorrência, perfil do usuário, criador do equipamento), o endpoint verifica se o id existe; sem isso o Xano responde "Missing param: field_value".

## Riscos / Concessões

- [Requisições em paralelo chegam juntas ao Xano e podem bater no limite do plano Free] → O total por tela não mudou; o cliente já espera e repete em caso de HTTP 429.
- [Conexão reaproveitada fechada pelo servidor] → Leituras repetidas automaticamente; gravações sobem o erro para o usuário tentar de novo.
- [A contagem de ocorrências do painel mudou de regra] → Passa a ignorar equipamentos descomissionados, como a lista de alertas recentes; registrado na proposta.
