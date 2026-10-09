# Proposta

## Por quê

A página **Usuários e perfis** mostrava textos em inglês: os nomes dos perfis vinham como código (`asset_manager`, `technician`), as permissões apareciam como chave técnica (`inventory.manage`) com descrição em inglês gravada pelo seed, e os erros do Xano desse grupo (e-mail em uso, perfil em uso etc.) chegavam em inglês.

## O que muda

- **Perfis padrão em português:** Administrador, Gestor de patrimônio, Técnico e Visualizador, com descrição em português, na lista de perfis, nos seletores de perfil, nos cabeçalhos da matriz de permissões e no menu do usuário. Perfis criados pelo administrador continuam com o nome e a descrição digitados.
- **Permissões em português:** a matriz mostra o nome da permissão (ex.: "Gerenciar inventário") e a descrição, sem a chave técnica.
- **Mensagens do Xano em português** nos endpoints do grupo Users.
- **Seed em português:** novas implantações já gravam as descrições em português (os códigos de perfil e permissão não mudam).

## Capacidades

### Novas capacidades
- `users-page-language`: idioma dos textos da página de usuários e perfis.

### Capacidades modificadas
<!-- Nenhuma -->

## Impacto

- `hardware/labels.py` (novo), `hardware/state.py` (`role_label`), `hardware/components.py` (menu do usuário), `hardware/pages/users.py`.
- Xano: `api/users/*.xs` (mensagens) e `function/setup/seed_reference_data.xs` (descrições). Precisa publicar para as mensagens novas valerem.
- Os códigos gravados (`administrator`, `inventory.manage` …) não mudam; a tradução é só de exibição.
