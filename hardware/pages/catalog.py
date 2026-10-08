"""Catalogs and locations: manufacturers, categories, models, components, and the location tree.

Records are activated/deactivated, never deleted, so historical references keep resolving.
"""

import reflex as rx

from .. import api
from ..components import (
    COMPONENT_TYPE,
    empty_row,
    error_callout,
    form_key_field,
    label_of,
    layout,
    native_select,
    stale_submit,
    submit_button,
    text_area,
    text_input,
)
from ..options import OptionsState, opt_text, to_int

# kind -> (API path, singular label)
KINDS = {
    "fabricantes": ("fabricantes", "fabricante"),
    "categorias": ("categorias", "categoria"),
    "modelos": ("modelos", "modelo"),
    "componentes": ("componentes", "componente"),
    "localizacoes": ("localizacoes", "localização"),
}


class CatalogState(OptionsState):
    tab: str = "fabricantes"
    show_inactive: bool = False
    rows: dict[str, list[dict]] = {k: [] for k in KINDS}
    error: str = ""
    form_error: str = ""
    form_key: int = 0
    saving: bool = False

    # edit dialog
    edit_kind: str = ""
    edit_row: dict = {}
    edit_error: str = ""
    edit_key: int = 0

    @rx.event
    async def on_load(self):
        redirect = await self._guard("operational.read")
        if redirect:
            return redirect
        await self._refresh()

    async def _refresh(self):
        self.error = ""
        params = {"include_inactive": self.show_inactive}
        try:
            # Paginated catalogs are read to the end so no record is hidden
            fab = await self._fetch_all("inventory", "fabricantes", params)
            cat = await self.call("GET", "inventory", "categorias", params=params)
            mod = await self._fetch_all("inventory", "modelos", params)
            comp = await self._fetch_all("inventory", "componentes", params)
            loc = await self.call("GET", "inventory", "localizacoes", params=params)
            self.rows = {"fabricantes": fab, "categorias": cat, "modelos": mod, "componentes": comp, "localizacoes": loc}
        except api.ApiError as err:
            self.error = err.message
        # Create forms only offer active references
        await self._load_options("fabricantes", "categorias", "localizacoes")

    @rx.event
    def set_tab(self, value: str):
        self.tab = value
        self.form_error = ""

    @rx.event
    async def toggle_inactive(self, value: bool):
        self.show_inactive = value
        await self._refresh()

    @rx.event
    async def set_active(self, kind: str, record_id: int, ativo: bool):
        path, label = KINDS[kind]
        try:
            await self.call("PATCH", "inventory", f"{path}/{record_id}", json={"ativo": ativo})
        except api.ApiError as err:
            return rx.toast.error(err.message)
        await self._refresh()
        return rx.toast.success(f"{label.capitalize()} {'ativado(a)' if ativo else 'desativado(a)'}.")

    async def _create(self, kind: str, form: dict, payload: dict):
        """Event generator shared by the create forms; handlers re-yield its events."""
        if stale_submit(form, self.form_key):
            return
        self.form_error = ""
        path, label = KINDS[kind]
        self.saving = True
        yield
        try:
            await self.call("POST", "inventory", path, json=payload)
        except api.ApiError as err:
            self.form_error = err.message
            return
        finally:
            self.saving = False
        self.form_key += 1
        await self._refresh()
        yield rx.toast.success(f"{label.capitalize()} cadastrado(a).")

    @rx.event
    async def create_fabricante(self, form: dict):
        async for event in self._create(
            "fabricantes",
            form,
            {
                "nome": (form.get("nome") or "").strip(),
                "site": opt_text(form.get("site")),
                "contato_suporte": opt_text(form.get("contato_suporte")),
                "observacoes": opt_text(form.get("observacoes")),
            },
        ):
            yield event

    @rx.event
    async def create_categoria(self, form: dict):
        async for event in self._create("categorias", form, {"nome": (form.get("nome") or "").strip(), "descricao": opt_text(form.get("descricao"))}):
            yield event

    @rx.event
    async def create_modelo(self, form: dict):
        async for event in self._create(
            "modelos",
            form,
            {
                "nome": (form.get("nome") or "").strip(),
                "fabricante_id": to_int(form.get("fabricante_id")),
                "categoria_id": to_int(form.get("categoria_id")),
                "codigo": opt_text(form.get("codigo")),
                "observacoes": opt_text(form.get("observacoes")),
            },
        ):
            yield event

    @rx.event
    async def create_componente(self, form: dict):
        async for event in self._create(
            "componentes",
            form,
            {
                "nome": (form.get("nome") or "").strip(),
                "tipo": form.get("tipo") or None,
                "fabricante_id": to_int(form.get("fabricante_id")),
                "modelo_componente": opt_text(form.get("modelo_componente")),
                "numero_peca": opt_text(form.get("numero_peca")),
                "especificacoes": opt_text(form.get("especificacoes")),
                "observacoes": opt_text(form.get("observacoes")),
            },
        ):
            yield event

    @rx.event
    async def create_localizacao(self, form: dict):
        async for event in self._create(
            "localizacoes",
            form,
            {
                "nome": (form.get("nome") or "").strip(),
                "parent_id": to_int(form.get("parent_id")),
                "tipo": opt_text(form.get("tipo")),
                "descricao": opt_text(form.get("descricao")),
            },
        ):
            yield event

    # ---- edit ----
    @rx.event
    def open_edit(self, kind: str, row: dict):
        self.edit_kind = kind
        self.edit_row = row
        self.edit_error = ""
        self.edit_key += 1

    @rx.event
    def close_edit(self, _open: bool = False):
        self.edit_kind = ""
        self.edit_row = {}
        self.edit_error = ""

    @rx.var
    def edit_open(self) -> bool:
        return self.edit_kind != ""

    @rx.var
    def edit_title(self) -> str:
        return f"Editar {KINDS[self.edit_kind][1]}" if self.edit_kind in KINDS else ""

    def _edit_value(self, key: str) -> str:
        value = self.edit_row.get(key) if self.edit_row else None
        return "" if value is None else str(value)

    @rx.var
    def e_nome(self) -> str:
        return self._edit_value("nome")

    @rx.var
    def e_site(self) -> str:
        return self._edit_value("site")

    @rx.var
    def e_contato(self) -> str:
        return self._edit_value("contato_suporte")

    @rx.var
    def e_observacoes(self) -> str:
        return self._edit_value("observacoes")

    @rx.var
    def e_descricao(self) -> str:
        return self._edit_value("descricao")

    @rx.var
    def e_codigo(self) -> str:
        return self._edit_value("codigo")

    @rx.var
    def e_fabricante_id(self) -> str:
        return self._edit_value("fabricante_id")

    @rx.var
    def e_categoria_id(self) -> str:
        return self._edit_value("categoria_id")

    @rx.var
    def e_tipo(self) -> str:
        return self._edit_value("tipo")

    @rx.var
    def e_modelo_componente(self) -> str:
        return self._edit_value("modelo_componente")

    @rx.var
    def e_numero_peca(self) -> str:
        return self._edit_value("numero_peca")

    @rx.var
    def e_especificacoes(self) -> str:
        return self._edit_value("especificacoes")

    @rx.var
    def e_parent_id(self) -> str:
        return self._edit_value("parent_id")

    def _optional_ref(self, form: dict, key: str, options: list[dict]) -> int | None:
        """Value for an optional reference the API clears with 0 (component manufacturer, parent location).
        Returns None (field not sent, value kept) when unchanged, and also when the current reference is
        inactive: inactive records are not offered in the select, so the blank choice would otherwise
        silently remove it."""
        new = to_int(form.get(key))
        current = self.edit_row.get(key)
        if new == current:
            return None
        if new is None:
            if current is not None and str(current) not in {o["value"] for o in options}:
                return None
            return 0
        return new

    @rx.event
    async def save_edit(self, form: dict):
        """PATCH the record. Optional text left blank is cleared ("" tells the API to clear it); optional
        references (component manufacturer, parent location) follow _optional_ref."""
        self.edit_error = ""
        kind = self.edit_kind
        if kind not in KINDS or not self.edit_row:
            return
        nome = (form.get("nome") or "").strip()
        if not nome:
            self.edit_error = "O nome é obrigatório."
            return
        text = lambda key: (form.get(key) or "").strip()  # noqa: E731
        if kind == "fabricantes":
            payload = {"nome": nome, "site": text("site"), "contato_suporte": text("contato_suporte"), "observacoes": text("observacoes")}
        elif kind == "categorias":
            payload = {"nome": nome, "descricao": text("descricao")}
        elif kind == "modelos":
            payload = {
                "nome": nome,
                # Unchanged inactive references are not offered in the select; blank keeps the current one
                "fabricante_id": to_int(form.get("fabricante_id")),
                "categoria_id": to_int(form.get("categoria_id")),
                "codigo": text("codigo"),
                "observacoes": text("observacoes"),
            }
        elif kind == "componentes":
            payload = {
                "nome": nome,
                "tipo": form.get("tipo") or None,
                "fabricante_id": self._optional_ref(form, "fabricante_id", self.fabricantes),
                "modelo_componente": text("modelo_componente"),
                "numero_peca": text("numero_peca"),
                "especificacoes": text("especificacoes"),
                "observacoes": text("observacoes"),
            }
        else:
            payload = {
                "nome": nome,
                "parent_id": self._optional_ref(form, "parent_id", self.localizacoes),
                "tipo": text("tipo"),
                "descricao": text("descricao"),
            }
        path, label = KINDS[kind]
        self.saving = True
        yield
        try:
            await self.call("PATCH", "inventory", f"{path}/{self.edit_row['id']}", json=payload)
        except api.ApiError as err:
            self.edit_error = err.message
            return
        finally:
            self.saving = False
        self.edit_kind = ""
        self.edit_row = {}
        await self._refresh()
        yield rx.toast.success(f"{label.capitalize()} atualizado(a).")


def active_badge(ativo) -> rx.Component:
    return rx.cond(ativo, rx.badge("Ativo", color_scheme="green", variant="soft"), rx.badge("Inativo", color_scheme="gray", variant="soft"))


def toggle_button(kind: str, row) -> rx.Component:
    return rx.cond(
        CatalogState.can_manage_inventory,
        rx.hstack(
            rx.button("Editar", size="1", variant="soft", on_click=CatalogState.open_edit(kind, row)),
            rx.cond(
                row["ativo"],
                rx.button("Desativar", size="1", variant="soft", color_scheme="red", on_click=CatalogState.set_active(kind, row["id"], False)),
                rx.button("Ativar", size="1", variant="soft", on_click=CatalogState.set_active(kind, row["id"], True)),
            ),
            spacing="1",
        ),
        rx.fragment(),
    )


def edit_dialog() -> rx.Component:
    s = CatalogState
    p = "e"  # field-id prefix: the create forms on the page use the same field names
    fields = rx.match(
        s.edit_kind,
        (
            "fabricantes",
            rx.fragment(
                text_input("Nome", "nome", required=True, default_value=s.e_nome, id_prefix=p),
                text_input("Site", "site", type_="url", default_value=s.e_site, id_prefix=p),
                text_input("Contato de suporte", "contato_suporte", default_value=s.e_contato, id_prefix=p),
                text_input("Observações", "observacoes", default_value=s.e_observacoes, id_prefix=p),
            ),
        ),
        (
            "categorias",
            rx.fragment(
                text_input("Nome", "nome", required=True, default_value=s.e_nome, id_prefix=p),
                text_input("Descrição", "descricao", default_value=s.e_descricao, id_prefix=p),
            ),
        ),
        (
            "modelos",
            rx.fragment(
                text_input("Nome", "nome", required=True, default_value=s.e_nome, id_prefix=p),
                native_select("Fabricante", "fabricante_id", s.fabricantes, placeholder="Manter atual", default_value=s.e_fabricante_id, id_prefix=p),
                native_select("Categoria", "categoria_id", s.categorias, placeholder="Manter atual", default_value=s.e_categoria_id, id_prefix=p),
                text_input("Código", "codigo", default_value=s.e_codigo, id_prefix=p),
                text_input("Observações", "observacoes", default_value=s.e_observacoes, id_prefix=p),
                rx.text(
                    "Alterar fabricante ou categoria muda os dados derivados de todos os equipamentos deste modelo.",
                    size="1",
                    color_scheme="amber",
                ),
            ),
        ),
        (
            "componentes",
            rx.fragment(
                text_input("Nome", "nome", required=True, default_value=s.e_nome, id_prefix=p),
                native_select("Tipo", "tipo", list(COMPONENT_TYPE.items()), required=True, default_value=s.e_tipo, id_prefix=p),
                native_select("Fabricante", "fabricante_id", s.fabricantes, placeholder="Não informado", default_value=s.e_fabricante_id, id_prefix=p),
                text_input("Modelo do componente", "modelo_componente", default_value=s.e_modelo_componente, id_prefix=p),
                text_input("Número da peça", "numero_peca", default_value=s.e_numero_peca, id_prefix=p),
                text_area("Especificações", "especificacoes", default_value=s.e_especificacoes, id_prefix=p),
                text_input("Observações", "observacoes", default_value=s.e_observacoes, id_prefix=p),
            ),
        ),
        rx.fragment(
            text_input("Nome", "nome", required=True, default_value=s.e_nome, id_prefix=p),
            native_select("Localização superior", "parent_id", s.localizacoes, placeholder="Nenhuma (nível principal)", default_value=s.e_parent_id, id_prefix=p),
            text_input("Tipo (ex.: prédio, andar, sala)", "tipo", default_value=s.e_tipo, id_prefix=p),
            text_input("Descrição", "descricao", default_value=s.e_descricao, id_prefix=p),
        ),
    )
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(s.edit_title),
            rx.form(
                rx.vstack(
                    error_callout(s.edit_error),
                    fields,
                    rx.text("Campos opcionais deixados em branco são apagados.", size="1", color_scheme="gray"),
                    rx.hstack(submit_button("Salvar", loading=s.saving), rx.dialog.close(rx.button("Cancelar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                key=s.edit_key,
                on_submit=s.save_edit,
                reset_on_submit=False,
                aria_label="Editar registro do catálogo",
            ),
            max_width="34rem",
        ),
        open=s.edit_open,
        on_open_change=s.close_edit,
    )


def catalog_table(kind: str, headers: list[str], cells) -> rx.Component:
    rows = CatalogState.rows[kind]
    return rx.box(
        rx.table.root(
            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in headers + ["Situação", ""]])),
            rx.table.body(
                rx.cond(
                    rows.length() > 0,
                    rx.foreach(
                        rows,
                        lambda r: rx.table.row(*cells(r), rx.table.cell(active_badge(r["ativo"])), rx.table.cell(toggle_button(kind, r))),
                    ),
                    empty_row(len(headers) + 2),
                )
            ),
            width="100%",
            size="1",
        ),
        overflow_x="auto",
        width="100%",
    )


def create_card(title: str, handler, *fields) -> rx.Component:
    return rx.cond(
        CatalogState.can_manage_inventory,
        rx.card(
            rx.form(
                rx.vstack(
                    rx.heading(title, size="3", as_="h3"),
                    error_callout(CatalogState.form_error),
                    rx.grid(*fields, columns=rx.breakpoints(initial="1", md="2"), spacing="3", width="100%"),
                    form_key_field(CatalogState.form_key),
                    submit_button("Cadastrar", loading=CatalogState.saving),
                    spacing="3",
                ),
                key=CatalogState.form_key,
                on_submit=handler,
                reset_on_submit=False,
            ),
            width="100%",
        ),
        rx.fragment(),
    )


def catalog_page() -> rx.Component:
    s = CatalogState
    return layout(
        "Catálogos e localizações",
        error_callout(s.error),
        edit_dialog(),
        rx.el.label(
            rx.hstack(rx.switch(checked=s.show_inactive, on_change=s.toggle_inactive, id="f-show-inactive"), rx.text("Mostrar inativos", size="2")),
            html_for="f-show-inactive",
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Fabricantes", value="fabricantes"),
                rx.tabs.trigger("Categorias", value="categorias"),
                rx.tabs.trigger("Modelos", value="modelos"),
                rx.tabs.trigger("Componentes", value="componentes"),
                rx.tabs.trigger("Localizações", value="localizacoes"),
            ),
            rx.tabs.content(
                rx.vstack(
                    create_card(
                        "Novo fabricante",
                        s.create_fabricante,
                        text_input("Nome", "nome", required=True),
                        text_input("Site", "site", type_="url"),
                        text_input("Contato de suporte", "contato_suporte"),
                        text_input("Observações", "observacoes"),
                    ),
                    catalog_table(
                        "fabricantes",
                        ["Nome", "Site", "Contato de suporte"],
                        lambda r: [rx.table.cell(r["nome"]), rx.table.cell(r["site"]), rx.table.cell(r["contato_suporte"])],
                    ),
                    spacing="4",
                    padding_top="1rem",
                ),
                value="fabricantes",
            ),
            rx.tabs.content(
                rx.vstack(
                    create_card("Nova categoria", s.create_categoria, text_input("Nome", "nome", required=True), text_input("Descrição", "descricao")),
                    catalog_table("categorias", ["Nome", "Descrição"], lambda r: [rx.table.cell(r["nome"]), rx.table.cell(r["descricao"])]),
                    spacing="4",
                    padding_top="1rem",
                ),
                value="categorias",
            ),
            rx.tabs.content(
                rx.vstack(
                    create_card(
                        "Novo modelo",
                        s.create_modelo,
                        text_input("Nome", "nome", required=True),
                        native_select("Fabricante", "fabricante_id", s.fabricantes, required=True),
                        native_select("Categoria", "categoria_id", s.categorias, required=True),
                        text_input("Código", "codigo"),
                        text_input("Observações", "observacoes"),
                    ),
                    catalog_table(
                        "modelos",
                        ["Nome", "Fabricante", "Categoria", "Código"],
                        lambda r: [rx.table.cell(r["nome"]), rx.table.cell(r["fabricante"]), rx.table.cell(r["categoria"]), rx.table.cell(r["codigo"])],
                    ),
                    spacing="4",
                    padding_top="1rem",
                ),
                value="modelos",
            ),
            rx.tabs.content(
                rx.vstack(
                    create_card(
                        "Novo componente",
                        s.create_componente,
                        text_input("Nome", "nome", required=True),
                        native_select("Tipo", "tipo", list(COMPONENT_TYPE.items()), required=True),
                        native_select("Fabricante", "fabricante_id", s.fabricantes, placeholder="Não informado"),
                        text_input("Modelo do componente", "modelo_componente"),
                        text_input("Número da peça", "numero_peca"),
                        text_area("Especificações", "especificacoes"),
                        text_input("Observações", "observacoes"),
                    ),
                    catalog_table(
                        "componentes",
                        ["Nome", "Tipo", "Fabricante", "Nº da peça"],
                        lambda r: [
                            rx.table.cell(r["nome"]),
                            rx.table.cell(label_of(COMPONENT_TYPE, r["tipo"])),
                            rx.table.cell(r["fabricante"]),
                            rx.table.cell(r["numero_peca"]),
                        ],
                    ),
                    spacing="4",
                    padding_top="1rem",
                ),
                value="componentes",
            ),
            rx.tabs.content(
                rx.vstack(
                    create_card(
                        "Nova localização",
                        s.create_localizacao,
                        text_input("Nome", "nome", required=True),
                        native_select("Localização superior", "parent_id", s.localizacoes, placeholder="Nenhuma (nível principal)"),
                        text_input("Tipo (ex.: prédio, andar, sala)", "tipo"),
                        text_input("Descrição", "descricao"),
                    ),
                    catalog_table(
                        "localizacoes",
                        ["Nome", "Dentro de", "Tipo"],
                        lambda r: [rx.table.cell(r["nome"]), rx.table.cell(r["parent"]), rx.table.cell(r["tipo"])],
                    ),
                    spacing="4",
                    padding_top="1rem",
                ),
                value="localizacoes",
            ),
            value=s.tab,
            on_change=s.set_tab,
            width="100%",
        ),
    )
