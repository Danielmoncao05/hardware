"""Troca de senha do usuário logado.

Obrigatória no primeiro acesso quando um administrador criou a conta com senha temporária (a API não
concede permissões até ela ser trocada); também disponível a qualquer momento pelo menu. Esta página exige
só uma sessão, nunca uma permissão, então os guards sempre podem redirecionar para cá sem entrar em loop.
"""

import reflex as rx

from .. import api
from ..components import error_callout, submit_button, text_input
from ..state import AuthState


class ChangePasswordState(AuthState):
    error: str = ""
    saving: bool = False
    form_key: int = 0

    @rx.event
    async def on_load(self):
        self.error = ""
        self.form_key += 1
        if not self._token:
            self._clear_session()
            return rx.redirect("/login")
        try:
            await self._load_me()
        except api.ApiError:
            self._clear_session()
            return rx.redirect("/login")

    @rx.event
    async def change(self, form: dict):
        self.error = ""
        atual = form.get("senha_atual") or ""
        nova = form.get("nova_senha") or ""
        confirmar = form.get("confirmar_senha") or ""
        if not atual or not nova:
            self.error = "Informe a senha atual e a nova senha."
            return
        if len(nova) < 8 or not any(c.isalpha() for c in nova) or not any(c.isdigit() for c in nova):
            self.error = "A nova senha deve ter pelo menos 8 caracteres, com letras e números."
            return
        if nova != confirmar:
            self.error = "A confirmação não corresponde à nova senha."
            return
        if nova == atual:
            self.error = "A nova senha deve ser diferente da senha atual."
            return
        self.saving = True
        yield
        try:
            await self.call(
                "POST", "auth", "auth/change_password",
                json={"senha_atual": atual, "nova_senha": nova, "confirmar_senha": confirmar},
            )
            await self._load_me()
        except api.ApiError as err:
            self.error = "Senha atual incorreta." if "senha_atual" in err.message else err.message
            return
        finally:
            self.saving = False
        yield rx.toast.success("Senha alterada.")
        yield rx.redirect("/painel")


def change_password_page() -> rx.Component:
    s = ChangePasswordState
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Alterar senha", size="6", as_="h1"),
                rx.cond(
                    s.must_change_password,
                    rx.callout(
                        "Sua conta foi criada com uma senha temporária. Defina uma senha pessoal para continuar.",
                        icon="key_round",
                        color_scheme="amber",
                        role="status",
                    ),
                    rx.fragment(),
                ),
                rx.form(
                    rx.vstack(
                        error_callout(s.error),
                        text_input(
                            "Senha atual (ou temporária)",
                            "senha_atual",
                            required=True,
                            type_="password",
                            custom_attrs={"autocomplete": "current-password"},
                            auto_focus=True,
                        ),
                        text_input(
                            "Nova senha",
                            "nova_senha",
                            required=True,
                            type_="password",
                            hint="Mínimo de 8 caracteres, com pelo menos uma letra e um número.",
                            custom_attrs={"autocomplete": "new-password"},
                        ),
                        text_input(
                            "Confirmar nova senha",
                            "confirmar_senha",
                            required=True,
                            type_="password",
                            custom_attrs={"autocomplete": "new-password"},
                        ),
                        submit_button("Salvar nova senha", loading=s.saving, width="100%"),
                        spacing="3",
                    ),
                    key=s.form_key,
                    on_submit=s.change,
                    reset_on_submit=False,
                    aria_label="Alterar senha",
                ),
                rx.hstack(
                    rx.cond(s.must_change_password, rx.fragment(), rx.link("Voltar", href="/painel", size="2")),
                    rx.spacer(),
                    rx.button("Sair", variant="ghost", size="1", on_click=AuthState.logout),
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="100%",
            max_width="26rem",
            size="3",
        ),
        min_height="100vh",
        padding="1rem",
    )
