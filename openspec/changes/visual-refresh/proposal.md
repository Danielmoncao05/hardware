# Proposta

## Por quê

As telas funcionam, mas o visual não ajuda quem usa o sistema o dia todo: o menu não mostra em que página o usuário está, as telas não dizem para que servem, as tabelas são linhas soltas sem destaque, as listas vazias mostram só um texto cinza e as telas de conta (login, recuperação e troca de senha) não têm a identidade HospitalTech que a página institucional e o novo painel já usam.

## O que muda

- **Menu:** a página atual fica destacada na barra lateral e no menu do celular, e é anunciada a leitores de tela.
- **Cabeçalho das telas:** cada tela autenticada ganha uma linha de descrição abaixo do título.
- **Tabelas:** borda, cabeçalho destacado e realce da linha sob o cursor, iguais em todas as telas.
- **Estados vazios:** ícone e mensagem centralizada no lugar do texto solto.
- **Telas de conta:** marca HospitalTech (ícone e nome) e fundo com a cor da marca no login, na recuperação, na redefinição e na troca de senha.
- **Acesso negado:** ícone, explicação e botões para voltar ou ir à página inicial do usuário.
- **Detalhe do equipamento:** dados agrupados em cartões e cabeçalho com status e patrimônio em destaque.

Nada muda nos dados, nas permissões, nas rotas ou na API.

## Capacidades

### Novas capacidades
- `ui-consistency`: elementos visuais comuns das telas: indicação da página atual, descrição das telas, tabelas, estados vazios e identidade visual das telas de conta.

### Capacidades modificadas
<!-- Nenhuma: a navegação e a marca estão na change dashboard-redesign (app-shell), ainda não arquivada; esta change só
acrescenta requisitos visuais sem alterar os dela. -->

## Impacto

- `hardware/components.py`: `nav_link` (página atual), `layout(..., subtitle=...)`, `empty_row`, marca compartilhada.
- `assets/dashboard.css`: estilos globais das tabelas (passa a se chamar `assets/app.css`).
- Páginas: subtítulos em todas as telas autenticadas; `login.py`, `change_password.py`, `no_access.py` e o detalhe em `equipment.py`.
- Sem mudança no backend (Xano) nem em dependências.
