"""Catálogos e localizações: fabricantes, categorias, modelos, componentes e a árvore de localizações.

Registros são ativados/desativados, nunca apagados, para que referências históricas continuem válidas.
"""

import asyncio

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

# tipo -> (caminho na API, rótulo no singular)
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
    loading: bool = False
    rows: dict[str, list[dict]] = {k: [] for k in KINDS}
    error: str = ""
    form_error: str = ""
    form_key: int = 0
    saving: bool = False

    # diálogo de edição
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
            # Catálogos paginados são lidos até o fim para nenhum registro ficar oculto; os cinco em paralelo
            fab, cat, mod, comp, loc = await asyncio.gather(
                self._fetch_all("inventory", "fabricantes", params),
                self.call("GET", "inventory", "categorias", params=params),
                self._fetch_all("inventory", "modelos", params),
                self._fetch_all("inventory", "componentes", params),
                self.call("GET", "inventory", "localizacoes", params=params),
            )
            self.rows = {"fabricantes": fab, "categorias": cat, "modelos": mod, "componentes": comp, "localizacoes": loc}
        except api.ApiError as err:
            self.error = err.message
            return
        # As listas de opções (só registros ativos) saem dos mesmos dados, sem novas requisições; assim um
        # cadastro ou edição aparece na hora nos selects das outras páginas
        for kind, rows in self.rows.items():
            self._set_options(kind, [r for r in rows if r.get("ativo")])

    @rx.event
    def set_tab(self, value: str):
        self.tab = value
        self.form_error = ""

    @rx.event
    async def toggle_inactive(self, value: bool):
        # Devolve o controle antes de buscar: o botão muda na hora, com "Carregando…", em vez de esperar os 5 catálogos
        self.show_inactive = value
        self.loading = True
        yield
        try:
            await self._refresh()
        finally:
            self.loading = False

    @rx.var
    def inactive_count(self) -> int:
        """Quantos registros inativos vieram nos catálogos (só quando "Mostrar inativos" está ligado)."""
        return sum(1 for rows in self.rows.values() for r in rows if not r.get("ativo"))

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
        """Gerador de eventos compartilhado pelos formulários de cadastro; os handlers repassam seus eventos."""
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

    # ---- edição ----
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
        """Valor de uma referência opcional que a API limpa com 0 (fabricante do componente, localização superior).
        Devolve None (campo não enviado, valor mantido) quando não mudou e também quando a referência atual está
        inativa: registros inativos não aparecem no select, então a opção em branco acabaria
        removendo a referência sem aviso."""
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
        """Faz o PATCH do registro. Texto opcional deixado em branco é apagado ("" diz à API para limpar); referências
        opcionais (fabricante do componente, localização superior) seguem _optional_ref."""
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
                # Referências inativas inalteradas não aparecem no select; em branco mantém a atual
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
    p = "e"  # prefixo dos ids dos campos: os formulários de cadastro da página usam os mesmos nomes de campo
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
        # Rótulo ao lado do botão (não em volta dele): um <label> envolvendo o próprio controle dispara o clique duas vezes
        rx.hstack(
            rx.switch(checked=s.show_inactive, on_change=s.toggle_inactive, id="f-show-inactive", disabled=s.loading),
            rx.el.label("Mostrar inativos", html_for="f-show-inactive", class_name="text-sm", cursor="pointer"),
            rx.cond(s.loading, rx.spinner(size="1"), rx.fragment()),
            rx.cond(
                s.show_inactive & ~s.loading,
                rx.text(
                    rx.cond(s.inactive_count > 0, s.inactive_count.to_string() + " registro(s) inativo(s) incluído(s).", "Nenhum registro inativo cadastrado."),
                    size="1",
                    color_scheme="gray",
                    role="status",
                ),
                rx.fragment(),
            ),
            align="center",
            spacing="2",
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
