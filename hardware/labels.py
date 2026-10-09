"""Nomes em português dos perfis e permissões padrão.

No Xano os perfis e as permissões são gravados por código (ex.: `asset_manager`, `inventory.manage`) e as
descrições do seed estão em inglês. O app mostra sempre os textos daqui; perfis criados pelo administrador
continuam com o nome e a descrição que ele digitou.
"""

ROLES = {
    "administrator": ("Administrador", "Gerencia usuários, perfis e permissões, o inventário e as manutenções."),
    "asset_manager": ("Gestor de patrimônio", "Gerencia o inventário, os catálogos e todas as manutenções e ocorrências."),
    "technician": ("Técnico", "Atua nas manutenções e ocorrências atribuídas a ele e registra ocorrências."),
    "viewer": ("Visualizador", "Acesso somente leitura aos dados operacionais e relatórios."),
}

PERMISSIONS = {
    "operational.read": ("Consultar dados operacionais", "Ver equipamentos, catálogos, localizações, manutenções e ocorrências."),
    "inventory.manage": (
        "Gerenciar inventário",
        "Cadastrar, editar, mover, mudar o status e desativar equipamentos, catálogos, localizações e componentes.",
    ),
    "maintenance.manage": ("Gerenciar manutenções", "Cadastrar, atribuir e mudar o andamento de qualquer manutenção."),
    "maintenance.manage_assigned": ("Atuar nas manutenções atribuídas", "Mudar o andamento e editar as manutenções atribuídas ao usuário."),
    "occurrence.report": ("Registrar ocorrências", "Relatar uma nova ocorrência de equipamento."),
    "occurrence.manage": ("Gerenciar ocorrências", "Atribuir, resolver, cancelar e vincular qualquer ocorrência."),
    "occurrence.manage_assigned": ("Atuar nas ocorrências atribuídas", "Editar, resolver e cancelar as ocorrências atribuídas ao usuário."),
    "reports.read": ("Consultar relatórios", "Ver o painel e os relatórios operacionais, inclusive a exportação em CSV."),
    "audit.read": ("Consultar auditoria", "Ver o log de auditoria."),
    "users.manage": ("Gerenciar usuários e perfis", "Cadastrar, habilitar e desabilitar usuários e gerenciar perfis e permissões."),
}


def role_label(nome: str | None) -> str:
    """Nome do perfil para exibição: o padrão traduzido ou o nome gravado."""
    if not nome:
        return ""
    return ROLES.get(nome, (nome, ""))[0]


def role_description(nome: str | None, descricao: str | None) -> str:
    return ROLES[nome][1] if nome in ROLES else (descricao or "")


def permission_label(chave: str) -> str:
    return PERMISSIONS.get(chave, (chave, ""))[0]


def permission_description(chave: str, descricao: str | None) -> str:
    return PERMISSIONS[chave][1] if chave in PERMISSIONS else (descricao or "")
