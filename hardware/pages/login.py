"""Login and account recovery. There is no public sign-up: administrators provision accounts."""

import reflex as rx

from .. import api
from ..components import error_callout, submit_button, text_input
from ..state import AuthState


class RecoveryState(AuthState):
    request_sent: bool = False
    request_loading: bool = False
    reset_error: str = ""
    reset_ok: bool = False
    reset_loading: bool = False

    @rx.event
    async def request_link(self, form: dict):
        email = (form.get("email") or "").strip().lower()
        if not email:
            return
        self.request_loading = True
        yield
        try:
            await api.request("GET", "auth", "reset/request-reset-link", params={"email": email})
        except api.ApiError:
            # The response must not reveal whether the email exists
            pass
        self.request_loading = False
        self.request_sent = True

    @rx.event
    async def reset_password(self, form: dict):
        """Set the new password with the one-time emailed link (reset/confirm, a single step that never
        creates a session)."""
        self.reset_error = ""
        params = self.router.page.params
        token = params.get("magic_token") or ""
        email = params.get("email") or ""
        password = form.get("password") or ""
        confirm = form.get("confirm_password") or ""
        if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            self.reset_error = "A senha deve ter pelo menos 8 caracteres, com letras e números."
            return
        if password != confirm:
            self.reset_error = "As senhas não coincidem."
            return
        if not token or not email:
            self.reset_error = "Link de redefinição inválido. Solicite um novo link."
            return
        self.reset_loading = True
        yield
        try:
            await api.request(
                "POST",
                "auth",
                "reset/confirm",
                json={"magic_token": token, "email": email, "nova_senha": password, "confirmar_senha": confirm},
            )
            self.reset_ok = True
        except api.ApiError as err:
            self.reset_error = (
                "O link é inválido, expirou ou já foi usado. Solicite um novo link."
                if err.status in (401, 403)
                else err.message
            )
        finally:
            self.reset_loading = False


def _card(*children) -> rx.Component:
    return rx.center(
        rx.card(rx.vstack(*children, spacing="4", width="100%"), width="100%", max_width="26rem", size="3"),
        min_height="100vh",
        padding="1rem",
    )


def login_page() -> rx.Component:
    return _card(
        rx.heading("Gestão de Equipamentos", size="6", as_="h1"),
        rx.text("Entre com a conta fornecida pelo administrador.", color_scheme="gray", size="2"),
        rx.form(
            rx.vstack(
                error_callout(AuthState.login_error),
                text_input("E-mail", "email", required=True, type_="email", custom_attrs={"autocomplete": "username"}, auto_focus=True),
                text_input("Senha", "password", required=True, type_="password", custom_attrs={"autocomplete": "current-password"}),
                submit_button("Entrar", loading=AuthState.login_loading, width="100%"),
                spacing="3",
            ),
            on_submit=AuthState.login,
            aria_label="Entrar",
        ),
        rx.link("Esqueci minha senha", href="/recuperar-senha", size="2"),
    )


def forgot_page() -> rx.Component:
    return _card(
        rx.heading("Recuperar senha", size="6", as_="h1"),
        rx.cond(
            RecoveryState.request_sent,
            rx.callout(
                "Se o e-mail estiver cadastrado e ativo, você receberá um link para redefinir a senha.",
                icon="mail",
                role="status",
            ),
            rx.form(
                rx.vstack(
                    text_input("E-mail", "email", required=True, type_="email", custom_attrs={"autocomplete": "username"}, auto_focus=True),
                    submit_button("Enviar link", loading=RecoveryState.request_loading, width="100%"),
                    spacing="3",
                ),
                on_submit=RecoveryState.request_link,
                aria_label="Recuperar senha",
            ),
        ),
        rx.link("Voltar ao login", href="/login", size="2"),
    )


def reset_page() -> rx.Component:
    return _card(
        rx.heading("Definir nova senha", size="6", as_="h1"),
        rx.cond(
            RecoveryState.reset_ok,
            rx.vstack(
                rx.callout("Senha atualizada. Entre com a nova senha.", icon="check", color_scheme="green", role="status"),
                rx.link("Ir para o login", href="/login"),
            ),
            rx.form(
                rx.vstack(
                    error_callout(RecoveryState.reset_error),
                    text_input(
                        "Nova senha",
                        "password",
                        required=True,
                        type_="password",
                        custom_attrs={"autocomplete": "new-password"},
                        hint="Mínimo de 8 caracteres, com pelo menos uma letra e um número.",
                    ),
                    text_input("Confirmar senha", "confirm_password", required=True, type_="password", custom_attrs={"autocomplete": "new-password"}),
                    submit_button("Salvar senha", loading=RecoveryState.reset_loading, width="100%"),
                    spacing="3",
                ),
                on_submit=RecoveryState.reset_password,
                aria_label="Definir nova senha",
            ),
        ),
    )
