# Proposta

## Por quê

Hospitais, clínicas e equipes de manutenção precisam de um registro operacional compartilhado dos equipamentos médicos: configuração técnica e localização, status atual, histórico de serviços e problemas relatados. Esta mudança define um aplicativo de gestão de equipamentos focado, para as equipes coordenarem o ciclo de vida dos ativos e a manutenção sem transformar o sistema em um prontuário ou produto de diagnóstico.

## O que muda

- Define um inventário de equipamentos com fabricantes, categorias, modelos, equipamentos, componentes de hardware, instalações de componentes nos equipamentos, localizações e status dos equipamentos.
- Define manutenção preventiva e corretiva, ocorrências e um histórico de manutenção auditável, vinculado aos equipamentos e aos responsáveis.
- Define perfis e permissões de usuário, painéis operacionais e relatórios de equipamentos e manutenção.
- Especifica um modelo de dados relacional normalizado, regras de validação e de integridade referencial, os principais fluxos de usuário e a estrutura do aplicativo.
- Exclui explicitamente diagnóstico médico, prontuários e informações clínicas de pacientes.

## Capacidades

### Novas capacidades

- `equipment-inventory`: gerenciar equipamentos, fabricantes, categorias, modelos, componentes de hardware, instalações de componentes, localizações e status operacional.
- `maintenance-operations`: agendar e registrar manutenções preventivas e corretivas, registrar ocorrências dos equipamentos e consultar o histórico de serviços.
- `access-and-reporting`: gerenciar o acesso e as permissões dos usuários e oferecer painéis operacionais e relatórios.

### Capacidades alteradas

Nenhuma.

## Impacto

- Adiciona requisitos e arquitetura à base existente do aplicativo Reflex em `hardware/`.
- Define a API e a persistência relacional pretendidas, com base no Xano; as exportações atuais do Xano têm as tabelas iniciais de usuário e de log de eventos, endpoints de autenticação e exemplos relacionados a perfis, mas ainda não têm o domínio de equipamentos pedido.
- Não introduz código de implementação nem mudanças de dependências nesta fase de proposta.
- Exige manter os dados dos equipamentos separados dos dados de pacientes e clínicos em toda a interface, API, persistência e relatórios.
