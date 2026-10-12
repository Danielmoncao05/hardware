# Tarefas

## 1. Componentes comuns

- [x] 1.1 Destacar a página atual em `nav_link` (barra lateral e menu do celular) com `aria-current="page"`; verificar com um teste unitário da comparação de caminhos (`/equipamentos/5` destaca "Equipamentos", `/` não destaca nada)
- [x] 1.2 `layout(..., subtitle=...)` e descrição em todas as telas autenticadas; verificar com um teste que toda chamada de `layout` nas páginas passa `subtitle`
- [x] 1.3 `empty_row` com ícone e mensagem centralizada; verificar com `reflex compile --dry`
- [x] 1.4 `assets/app.css` (substitui `dashboard.css`) com o estilo das tabelas dentro de `#conteudo` e a animação do painel; verificar com o teste da animação atualizado
- [x] 1.5 `brand_mark()` compartilhada na barra superior; verificar com o teste da barra superior

## 2. Telas

- [x] 2.1 Telas de conta (login, recuperar, redefinir e trocar senha) com `account_shell()`: marca e fundo da marca; verificar com `reflex compile --dry` e com o teste da marca no login
- [x] 2.2 Acesso negado com ícone, explicação e ações "Voltar" e "Ir para o início"; verificar que "Ir para o início" leva a `/painel` só para quem tem `reports.read` e a `/equipamentos` para os demais
- [x] 2.3 Detalhe do equipamento: cabeçalho com status e patrimônio em destaque e dados da visão geral em cartões; verificar com `reflex compile --dry`

- [x] 2.4 "Mais detalhes" do painel: barras de proporção por status e por categoria (categorias da maior para a menor), zeros apagados na tabela de severidade, preventivas com data dd/mm/aaaa e selo do prazo ("há N dias" / "Em N dias") e cartões alinhados pelo topo; verificado com testes unitários de `overdue_label`, `br_date`, `share` e da ordenação das categorias, e com `reflex compile --dry`

## 3. Verificação

- [x] 3.1 Rodar `pytest` e `reflex compile --dry`
- [ ] 3.2 Percorrer todas as telas no navegador, nos temas claro e escuro, no desktop e no celular, e verificar que a página atual aparece destacada, as tabelas e listas vazias seguem o mesmo padrão e não há texto ilegível
