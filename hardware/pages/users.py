"""Administrator-only user provisioning, enable/disable, role assignment, and role permissions."""

from typing import TypedDict

import reflex as rx

from .. import api
from ..components import empty_row, error_callout, form_key_field, layout, native_select, stale_submit, submit_button, text_input
from ..state import AuthState
from ..options import to_int


class GrantCell(TypedDict):
    role_id: int
    role: str
    granted: bool


class PermissionRow(TypedDict):
    id: int
    chave: str
    descricao: str
    cells: list[GrantCell]


class UsersState(AuthState):
    users: list[dict] = []
    roles: list[dict] = []
    permission_list: list[dict] = []
    error: str = ""
    form_error: str = ""
    form_key: int = 0
    role_form_error: str = ""
    role_form_key: int = 0
    saving: bool = False

    @rx.event
    async def on_load(self):
        redirect = await self._guard("users.manage")
        if redirect:
            return redirect
        await self._fetch()

    async def _fetch(self):
        self.error = ""
        try:
            self.users = await self._fetch_all("users", "users", page_size=100)
            data = await self.call("GET", "users", "roles")
            self.roles = data["roles"]
            self.permission_list = data["permissions"]
        except api.ApiError as err:
            self.error = err.message

    @rx.var
    def role_options(self) -> list[dict]:
        return [{"value": str(r["id"]), "label": r["nome"]} for r in self.roles if r.get("ativo")]

    @rx.var
    def matrix(self) -> list[PermissionRow]:
        """One row per permission with a granted flag per role (in self.roles order)."""
        return [
            {
                "id": p["id"],
                "chave": p["chave"],
                "descricao": p["descricao"],
                "cells": [
                    {"role_id": r["id"], "role": r["nome"], "granted": p["chave"] in (r.get("permissions") or [])}
                    for r in self.roles
                ],
            }
            for p in self.permission_list
        ]

    @rx.event
    async def create_user(self, form: dict):
        if stale_submit(form, self.form_key):
            return
        self.form_error = ""
        payload = {
            "name": (form.get("name") or "").strip(),
            "email": (form.get("email") or "").strip().lower(),
            "password": form.get("password") or "",
            "role_id": to_int(form.get("role_id")),
        }
        if not all(payload.values()):
            self.form_error = "Preencha nome, e-mail, senha inicial e perfil."
            return
        self.saving = True
        yield
        try:
            await self.call("POST", "users", "users", json=payload)
        except api.ApiError as err:
            self.form_error = err.message
            return
        finally:
            self.saving = False
        self.form_key += 1
        await self._fetch()
        yield rx.toast.success("Usuário criado. Informe a senha temporária por um canal seguro; ela deverá ser trocada no primeiro acesso.")

    async def _patch_user(self, user_id: int, payload: dict, message: str):
        try:
            await self.call("PATCH", "users", f"users/{user_id}", json=payload)
        except api.ApiError as err:
            return rx.toast.error(err.message)
        await self._fetch()
        return rx.toast.success(message)

    @rx.event
    async def set_enabled(self, user_id: int, ativo: bool):
        return await self._patch_user(user_id, {"ativo": ativo}, "Usuário habilitado." if ativo else "Usuário desabilitado.")

    @rx.event
    async def set_role(self, user_id: int, role_id: str):
        if not role_id:
            return
        return await self._patch_user(user_id, {"role_id": int(role_id)}, "Perfil atualizado.")

    @rx.event
    async def create_role(self, form: dict):
        if stale_submit(form, self.role_form_key):
            return
        self.role_form_error = ""
        nome = (form.get("nome") or "").strip().lower()
        if not nome:
            self.role_form_error = "Informe o nome do perfil."
            return
        self.saving = True
        yield
        try:
            await self.call("POST", "users", "roles", json={"nome": nome, "descricao": (form.get("descricao") or "").strip() or None})
        except api.ApiError as err:
            self.role_form_error = err.message
            return
        finally:
            self.saving = False
        self.role_form_key += 1
        await self._fetch()
        yield rx.toast.success("Perfil criado. Conceda as permissões na tabela abaixo.")

    @rx.event
    async def set_role_active(self, role_id: int, ativo: bool):
        try:
            await self.call("PATCH", "users", f"roles/{role_id}", json={"ativo": ativo})
        except api.ApiError as err:
            return rx.toast.error(err.message)
        await self._fetch()
        return rx.toast.success("Perfil ativado." if ativo else "Perfil desativado.")

    @rx.event
    async def toggle_grant(self, role_id: int, permission_id: int, granted: bool):
        try:
            if granted:
                await self.call("DELETE", "users", f"roles/{role_id}/permissions/{permission_id}")
            else:
                await self.call("POST", "users", f"roles/{role_id}/permissions", json={"permission_id": permission_id})
        except api.ApiError as err:
            return rx.toast.error(err.message)
        await self._fetch()
        return rx.toast.success("Permissões do perfil atualizadas.")


def users_page() -> rx.Component:
    s = UsersState
    return layout(
        "Usuários e perfis",
        error_callout(s.error),
        rx.tabs.root(
            rx.tabs.list(rx.tabs.trigger("Usuários", value="usuarios"), rx.tabs.trigger("Permissões por perfil", value="perfis")),
            rx.tabs.content(
                rx.vstack(
                    rx.card(
                        rx.form(
                            rx.vstack(
                                rx.heading("Novo usuário", size="3", as_="h2"),
                                error_callout(s.form_error),
                                rx.grid(
                                    text_input("Nome", "name", required=True),
                                    text_input("E-mail", "email", type_="email", required=True),
                                    text_input(
                                        "Senha temporária",
                                        "password",
                                        type_="password",
                                        required=True,
                                        hint="Mínimo de 8 caracteres, com letras e números. O usuário deverá trocá-la no primeiro acesso.",
                                        custom_attrs={"autocomplete": "new-password"},
                                    ),
                                    native_select("Perfil", "role_id", s.role_options, required=True),
                                    columns=rx.breakpoints(initial="1", md="2"),
                                    spacing="3",
                                    width="100%",
                                ),
                                form_key_field(s.form_key),
                                submit_button("Criar usuário", loading=s.saving),
                                spacing="3",
                            ),
                            key=s.form_key,
                            on_submit=s.create_user,
                            reset_on_submit=False,
                        ),
                        width="100%",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Nome", "E-mail", "Perfil", "Situação", ""]])),
                            rx.table.body(
                                rx.cond(
                                    s.users.length() > 0,
                                    rx.foreach(
                                        s.users,
                                        lambda u: rx.table.row(
                                            rx.table.cell(u["name"]),
                                            rx.table.cell(u["email"]),
                                            rx.table.cell(
                                                rx.cond(
                                                    u["id"] == s.user_id,
                                                    rx.text(u["role"]),
                                                    rx.el.select(
                                                        rx.el.option("Sem perfil", value=""),
                                                        rx.foreach(s.role_options, lambda o: rx.el.option(o["label"], value=o["value"])),
                                                        value=rx.cond(u["role_id"], u["role_id"].to_string(), ""),
                                                        on_change=lambda v: s.set_role(u["id"], v),
                                                        aria_label="Perfil de " + u["name"].to(str),
                                                        class_name="rounded-md border px-2 py-1 text-sm bg-[var(--color-panel-solid)]",
                                                    ),
                                                )
                                            ),
                                            rx.table.cell(
                                                rx.hstack(
                                                    rx.cond(u["ativo"], rx.badge("Habilitado", color_scheme="green", variant="soft"), rx.badge("Desabilitado", color_scheme="gray", variant="soft")),
                                                    rx.cond(u["deve_trocar_senha"], rx.badge("Senha temporária", color_scheme="amber", variant="soft"), rx.fragment()),
                                                    spacing="1",
                                                    wrap="wrap",
                                                )
                                            ),
                                            rx.table.cell(
                                                rx.cond(
                                                    u["id"] == s.user_id,
                                                    rx.text("Você", size="1", color_scheme="gray"),
                                                    rx.cond(
                                                        u["ativo"],
                                                        rx.button("Desabilitar", size="1", variant="soft", color_scheme="red", on_click=s.set_enabled(u["id"], False)),
                                                        rx.button("Habilitar", size="1", variant="soft", on_click=s.set_enabled(u["id"], True)),
                                                    ),
                                                )
                                            ),
                                        ),
                                    ),
                                    empty_row(5),
                                )
                            ),
                            width="100%",
                            size="1",
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    spacing="4",
                    padding_top="1rem",
                    width="100%",
                ),
                value="usuarios",
            ),
            rx.tabs.content(
                rx.vstack(
                    rx.card(
                        rx.form(
                            rx.vstack(
                                rx.heading("Novo perfil", size="3", as_="h2"),
                                error_callout(s.role_form_error),
                                rx.grid(
                                    text_input("Nome (ex.: supervisor_manutencao)", "nome", required=True),
                                    text_input("Descrição", "descricao"),
                                    columns=rx.breakpoints(initial="1", md="2"),
                                    spacing="3",
                                    width="100%",
                                ),
                                form_key_field(s.role_form_key),
                                submit_button("Criar perfil", loading=s.saving),
                                spacing="3",
                            ),
                            key=s.role_form_key,
                            on_submit=s.create_role,
                            reset_on_submit=False,
                        ),
                        width="100%",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Perfil", "Descrição", "Situação", ""]])),
                            rx.table.body(
                                rx.foreach(
                                    s.roles,
                                    lambda r: rx.table.row(
                                        rx.table.row_header_cell(rx.code(r["nome"])),
                                        rx.table.cell(r["descricao"]),
                                        rx.table.cell(
                                            rx.cond(r["ativo"], rx.badge("Ativo", color_scheme="green", variant="soft"), rx.badge("Inativo", color_scheme="gray", variant="soft"))
                                        ),
                                        rx.table.cell(
                                            rx.cond(
                                                r["nome"] == "administrator",
                                                rx.text("Obrigatório", size="1", color_scheme="gray"),
                                                rx.cond(
                                                    r["ativo"],
                                                    rx.button("Desativar", size="1", variant="soft", color_scheme="red", on_click=s.set_role_active(r["id"], False)),
                                                    rx.button("Ativar", size="1", variant="soft", on_click=s.set_role_active(r["id"], True)),
                                                ),
                                            )
                                        ),
                                    ),
                                )
                            ),
                            width="100%",
                            size="1",
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    rx.text(
                        "Um perfil só pode ser desativado quando nenhum usuário habilitado o utiliza. "
                        "Marque ou desmarque para conceder ou revogar. A permissão users.manage não pode ser removida do perfil administrator.",
                        size="2",
                        color_scheme="gray",
                    ),
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Permissão"),
                                    rx.foreach(s.roles, lambda r: rx.table.column_header_cell(r["nome"])),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    s.matrix,
                                    lambda p: rx.table.row(
                                        rx.table.row_header_cell(rx.vstack(rx.code(p["chave"]), rx.text(p["descricao"], size="1", color_scheme="gray"), spacing="1")),
                                        rx.foreach(
                                            p["cells"],
                                            lambda c: rx.table.cell(
                                                rx.checkbox(
                                                    checked=c["granted"],
                                                    on_change=lambda _v: s.toggle_grant(c["role_id"], p["id"], c["granted"]),
                                                    aria_label=p["chave"].to(str) + " para " + c["role"].to(str),
                                                )
                                            ),
                                        ),
                                    ),
                                )
                            ),
                            width="100%",
                            size="1",
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    spacing="3",
                    padding_top="1rem",
                    width="100%",
                ),
                value="perfis",
            ),
            default_value="usuarios",
            width="100%",
        ),
    )
