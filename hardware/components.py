"""Blocos compartilhados de layout e formulário.

Todo controle de formulário tem um <label for=...> visível para que leitores de tela o anunciem,
e a ordem dos campos no DOM é a ordem de foco do teclado.
"""

import reflex as rx

from .options import TZ_NAME
from .state import AuthState

# ---- rótulos dos valores (os valores da API ficam em inglês; a interface mostra português) ----
EQUIP_STATUS = {
    "operational": "Operacional",
    "under_maintenance": "Em manutenção",
    "out_of_service": "Fora de serviço",
    "decommissioned": "Descomissionado",
}
MAINT_STATUS = {"planned": "Planejada", "in_progress": "Em andamento", "completed": "Concluída", "canceled": "Cancelada"}
MAINT_TYPE = {"preventive": "Preventiva", "corrective": "Corretiva"}
OCC_STATUS = {"open": "Aberta", "in_progress": "Em andamento", "resolved": "Resolvida", "canceled": "Cancelada"}
SEVERITY = {"low": "Baixa", "medium": "Média", "high": "Alta", "critical": "Crítica"}
COMPONENT_TYPE = {
    "processor": "Processador",
    "memory_ram": "Memória RAM",
    "storage": "Armazenamento",
    "motherboard": "Placa-mãe",
    "power_supply": "Fonte de alimentação",
    "sensor": "Sensor",
    "display": "Display",
    "battery": "Bateria",
    "electronic_module": "Módulo eletrônico",
    "communication_board": "Placa de comunicação",
    "other": "Outro",
}

STATUS_COLOR = {
    "operational": "green",
    "under_maintenance": "amber",
    "out_of_service": "red",
    "decommissioned": "gray",
    "planned": "blue",
    "in_progress": "amber",
    "completed": "green",
    "canceled": "gray",
    "open": "red",
    "resolved": "green",
    "low": "gray",
    "medium": "blue",
    "high": "orange",
    "critical": "red",
}


def label_of(mapping: dict[str, str], value) -> rx.Var:
    """Traduz uma Var de enum para exibição, usando o valor bruto quando não há tradução."""
    return rx.match(value, *[(k, v) for k, v in mapping.items()], value)


def timestamp_text(value, fmt: str = "DD/MM/YYYY HH:mm") -> rx.Component:
    """Data e hora armazenada, mostrada no fuso da instituição (HHM_TIMEZONE): o mesmo fuso usado para
    interpretar horários digitados nos formulários, então entrada e exibição sempre coincidem, qualquer que seja o fuso do navegador."""
    return rx.cond(value, rx.moment(value, format=fmt, tz=TZ_NAME), rx.text("—"))


def date_text(value) -> rx.Component:
    """Data de calendário ("YYYY-MM-DD"). Nunca convertida de fuso: a conversão poderia mudar o dia."""
    return rx.cond(value, rx.moment(value, format="DD/MM/YYYY"), rx.text("—"))


def badge(mapping: dict[str, str], value) -> rx.Component:
    return rx.badge(
        label_of(mapping, value),
        color_scheme=rx.match(value, *[(k, c) for k, c in STATUS_COLOR.items()], "gray"),
        variant="soft",
    )


# ---- formulários ----
def field(label: str, control: rx.Component, field_id: str, hint: str = "", required: bool = False) -> rx.Component:
    marker = [rx.text.span(" *", color=rx.color("red", 10), aria_hidden="true")] if required else []
    hint_node = [rx.text(hint, size="1", color_scheme="gray", id=f"{field_id}-hint")] if hint else []
    return rx.vstack(
        rx.el.label(label, *marker, html_for=field_id, class_name="text-sm font-medium"),
        control,
        *hint_node,
        spacing="1",
        width="100%",
    )


def text_input(label: str, name: str, required: bool = False, type_: str = "text", default_value="", hint: str = "", id_prefix: str = "f", **props) -> rx.Component:
    field_id = f"{id_prefix}-{name}"
    if hint:
        props["aria_describedby"] = f"{field_id}-hint"
    return field(
        label,
        rx.input(id=field_id, name=name, type=type_, required=required, default_value=default_value, width="100%", **props),
        field_id,
        hint,
        required,
    )


def text_area(label: str, name: str, required: bool = False, default_value="", hint: str = "", id_prefix: str = "f", **props) -> rx.Component:
    field_id = f"{id_prefix}-{name}"
    return field(
        label,
        rx.text_area(id=field_id, name=name, required=required, default_value=default_value, width="100%", **props),
        field_id,
        hint,
        required,
    )


def native_select(label: str, name: str, options, required: bool = False, placeholder: str = "Selecione…", value=None, on_change=None, default_value=None, id_prefix: str = "f") -> rx.Component:
    """<select> nativo: totalmente operável pelo teclado e anunciado por leitores de tela.

    options: uma Var ou lista de dicts {"value": ..., "label": ...}, ou uma lista de tuplas (value, label).
    """
    field_id = f"{id_prefix}-{name}"
    if isinstance(options, list) and options and isinstance(options[0], tuple):
        option_nodes = [rx.el.option(lbl, value=val) for val, lbl in options]
    else:
        option_nodes = [rx.foreach(options, lambda o: rx.el.option(o["label"], value=o["value"]))]
    props = {}
    if value is not None:
        props["value"] = value
    if default_value is not None:
        props["default_value"] = default_value
    if on_change is not None:
        props["on_change"] = on_change
    return field(
        label,
        rx.el.select(
            rx.el.option(placeholder, value=""),
            *option_nodes,
            id=field_id,
            name=name,
            required=required,
            class_name="w-full rounded-md border px-2 py-1.5 text-sm bg-[var(--color-panel-solid)]",
            **props,
        ),
        field_id,
        "",
        required,
    )


def equipment_picker(state, default_value="") -> rx.Component:
    """Caixa de busca com lista de resultados para escolher um equipamento (nome, patrimônio ou número de série).

    state: uma subclasse de OptionsState (equip_query, equip_options, equip_searching, search_equipment).
    O select mantém name="equipamento_id" para o formulário em volta.
    """
    return rx.vstack(
        field(
            "Buscar equipamento",
            rx.input(
                id="f-equip-busca",
                type="search",
                value=state.equip_query,
                on_change=state.search_equipment.debounce(400),
                placeholder="Nome, patrimônio ou número de série",
                aria_describedby="f-equip-busca-hint",
                width="100%",
            ),
            "f-equip-busca",
            "Mostra até 25 resultados; refine a busca para encontrar outros equipamentos.",
        ),
        rx.cond(state.equip_searching, rx.text("Buscando…", size="1", role="status"), rx.fragment()),
        native_select("Equipamento", "equipamento_id", state.equip_options, required=True, default_value=default_value),
        spacing="2",
        width="100%",
    )


def error_callout(message) -> rx.Component:
    """Erro de validação/API visível e anunciado."""
    return rx.cond(
        message != "",
        rx.callout(message, icon="triangle_alert", color_scheme="red", role="alert", width="100%"),
        rx.fragment(),
    )


def form_key_field(key) -> rx.Component:
    """Cópia oculta da chave do formulário. Os eventos rodam um de cada vez, então um envio enfileirado por clique duplo
    é tratado depois que o primeiro deu certo e incrementou a chave: o handler o descarta (ver stale_submit).
    Coloque dentro de um formulário com key na mesma var, para o campo ser remontado com o novo valor."""
    return rx.el.input(type="hidden", name="_form_key", default_value=key.to_string())


def stale_submit(form: dict, key: int) -> bool:
    return form.get("_form_key") != str(key)


def submit_button(text: str, loading=False, **props) -> rx.Component:
    return rx.button(text, type="submit", loading=loading, **props)


# ---- layout ----
# (texto, rota, ícone, flag do AuthState exigida para mostrar o link: a mesma permissão que o guard da página verifica)
NAV = [
    ("Painel", "/", "layout_dashboard", "can_read_reports"),
    ("Equipamentos", "/equipamentos", "monitor", "can_read_operational"),
    ("Manutenções", "/manutencoes", "wrench", "can_read_operational"),
    ("Ocorrências", "/ocorrencias", "circle_alert", "can_read_operational"),
    ("Catálogos e locais", "/catalogos", "library", "can_read_operational"),
    ("Relatórios", "/relatorios", "file_chart_column", "can_read_reports"),
    ("Usuários e perfis", "/usuarios", "users", "can_manage_users"),
]


def nav_link(text: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.hstack(rx.icon(icon, size=18, aria_hidden="true"), rx.text(text, size="3"), spacing="2", align="center"),
        href=href,
        underline="none",
        padding_x="0.75rem",
        padding_y="0.5rem",
        border_radius="var(--radius-2)",
        width="100%",
        color=rx.color("gray", 12),
        _hover={"background": rx.color("accent", 3)},
    )


def nav_items() -> list[rx.Component]:
    items = []
    for text, href, icon, flag in NAV:
        link = nav_link(text, href, icon)
        items.append(rx.cond(getattr(AuthState, flag), link, rx.fragment()) if flag else link)
    return items


def layout(title: str, *children, actions: rx.Component | None = None) -> rx.Component:
    """Estrutura das páginas autenticadas: barra lateral no desktop, menu recolhível no tablet/celular."""
    sidebar = rx.vstack(
        rx.heading("Gestão de Equipamentos", size="4", padding="0.75rem"),
        rx.el.nav(rx.vstack(*nav_items(), spacing="1", width="100%"), aria_label="Navegação principal", width="100%"),
        rx.spacer(),
        rx.vstack(
            rx.text(AuthState.user_name, weight="medium", size="2"),
            rx.text(AuthState.role, size="1", color_scheme="gray"),
            rx.link("Alterar senha", href="/trocar-senha", size="1"),
            rx.button("Sair", on_click=AuthState.logout, variant="soft", size="1"),
            padding="0.75rem",
            spacing="1",
            align="start",
        ),
        height="100vh",
        width="15rem",
        min_width="15rem",
        border_right=f"1px solid {rx.color('gray', 5)}",
        position="sticky",
        top="0",
        display=["none", "none", "none", "flex"],
    )
    mobile_menu = rx.box(
        rx.drawer.root(
            rx.drawer.trigger(rx.icon_button(rx.icon("menu"), variant="ghost", aria_label="Abrir menu")),
            rx.drawer.overlay(),
            rx.drawer.portal(
                rx.drawer.content(
                    rx.vstack(
                        rx.drawer.close(rx.icon_button(rx.icon("x"), variant="ghost", aria_label="Fechar menu")),
                        rx.el.nav(rx.vstack(*nav_items(), spacing="1", width="100%"), aria_label="Navegação principal", width="100%"),
                        rx.button("Sair", on_click=AuthState.logout, variant="soft"),
                        padding="1rem",
                        width="100%",
                    ),
                    width="16rem",
                    height="100%",
                    background=rx.color("gray", 1),
                )
            ),
            direction="left",
        ),
        display=["block", "block", "block", "none"],
    )
    return rx.hstack(
        sidebar,
        rx.el.main(
            rx.vstack(
                rx.hstack(
                    mobile_menu,
                    rx.heading(title, size="6", as_="h1"),
                    rx.spacer(),
                    actions if actions is not None else rx.fragment(),
                    align="center",
                    width="100%",
                    wrap="wrap",
                    spacing="3",
                ),
                *children,
                spacing="4",
                width="100%",
                padding=["1rem", "1rem", "1.5rem"],
            ),
            id="conteudo",
            width="100%",
            min_width="0",
        ),
        spacing="0",
        align="start",
        width="100%",
    )


def loading_overlay(cond) -> rx.Component:
    return rx.cond(cond, rx.hstack(rx.spinner(), rx.text("Carregando…"), role="status"), rx.fragment())


def empty_row(cols: int, text: str = "Nenhum registro encontrado.") -> rx.Component:
    return rx.table.row(rx.table.cell(rx.text(text, color_scheme="gray"), col_span=cols))


def pager(page, has_next, on_prev, on_next) -> rx.Component:
    return rx.hstack(
        rx.button("Anterior", on_click=on_prev, disabled=page <= 1, variant="soft", size="2"),
        rx.text("Página ", page, size="2"),
        rx.button("Próxima", on_click=on_next, disabled=~has_next, variant="soft", size="2"),
        align="center",
        spacing="3",
    )


def no_clinical_notice() -> rx.Component:
    return rx.callout(
        "Registre apenas informações técnicas do equipamento. Não inclua dados de pacientes ou informações clínicas.",
        icon="shield_alert",
        color_scheme="amber",
        size="1",
    )
