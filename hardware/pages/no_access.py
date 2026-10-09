"""Página de destino para usuários logados sem a permissão exigida por uma página.

Ela não exige permissão própria, então os guards sempre podem redirecionar para cá sem entrar em loop.
"""

import reflex as rx

from ..components import layout
from ..state import AuthState


def home_link() -> rx.Component:
    """"Ir para o início" só leva a uma área que o perfil pode abrir (nunca a outra tela negada); sem nenhuma, some."""
    button = lambda href: rx.link(rx.button(rx.icon("house", size=16), "Ir para o início"), href=href)  # noqa: E731
    return rx.cond(
        AuthState.can_read_reports,
        button("/painel"),
        rx.cond(AuthState.can_read_operational, button("/equipamentos"), rx.fragment()),
    )


def no_access_page() -> rx.Component:
    return layout(
        "Acesso não permitido",
        rx.card(
            rx.vstack(
                rx.center(
                    rx.icon("lock", size=28, color=rx.color("amber", 11)),
                    width="3.5rem",
                    height="3.5rem",
                    border_radius="full",
                    background=rx.color("amber", 3),
                ),
                rx.heading("Você não tem permissão para esta página", size="4", as_="h2"),
                rx.text(
                    "Use o menu para acessar as áreas liberadas para o seu perfil ou peça a um administrador para revisá-lo.",
                    color_scheme="gray",
                    size="2",
                    text_align="center",
                ),
                rx.cond(
                    AuthState.permissions.length() == 0,
                    rx.callout("Sua conta ainda não tem um perfil com permissões atribuído.", icon="info", color_scheme="amber", size="1"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(rx.icon("arrow_left", size=16), "Voltar", variant="soft", color_scheme="gray", on_click=rx.call_script("history.back()")),
                    home_link(),
                    spacing="3",
                    wrap="wrap",
                    justify="center",
                ),
                align="center",
                spacing="4",
                padding_y="1.5rem",
                width="100%",
            ),
            width="100%",
            max_width="36rem",
            role="alert",
        ),
        subtitle="Seu perfil não inclui esta área",
    )
