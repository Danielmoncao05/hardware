"""Landing page for signed-in users who lack the permission a page requires.

It has no permission requirement of its own, so guards can always redirect here without looping.
"""

import reflex as rx

from ..components import layout
from ..state import AuthState


def no_access_page() -> rx.Component:
    return layout(
        "Acesso não permitido",
        rx.callout(
            "Seu perfil não tem permissão para a página solicitada. Use o menu para acessar as áreas liberadas "
            "ou peça a um administrador para revisar seu perfil.",
            icon="lock",
            color_scheme="amber",
            role="alert",
        ),
        rx.cond(
            AuthState.permissions.length() == 0,
            rx.text(
                "Sua conta ainda não tem um perfil com permissões atribuído.",
                color_scheme="gray",
            ),
            rx.fragment(),
        ),
    )
