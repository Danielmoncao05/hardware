"""Lista e detalhe de equipamentos (visão geral, componentes, histórico), cadastro/edição, movimentação e troca de status."""

import reflex as rx

from .. import api
from ..components import (
    date_text,
    timestamp_text,
    COMPONENT_TYPE,
    EQUIP_STATUS,
    MAINT_STATUS,
    MAINT_TYPE,
    OCC_STATUS,
    SEVERITY,
    badge,
    empty_row,
    error_callout,
    label_of,
    layout,
    loading_overlay,
    native_select,
    pager,
    submit_button,
    text_area,
    text_input,
)
from ..options import OptionsState, opt_text, to_float, to_int

STATUS_OPTIONS = list(EQUIP_STATUS.items())
COMPONENT_TYPE_OPTIONS = list(COMPONENT_TYPE.items())


# ------------------------------------------------------------------ lista
class EquipmentListState(OptionsState):
    items: list[dict] = []
    total: int = 0
    page: int = 1
    has_next: bool = False
    loading: bool = False
    error: str = ""
    filters: dict[str, str] = {}

    @rx.event
    async def on_load(self):
        redirect = await self._guard("operational.read")
        if redirect:
            return redirect
        await self._load_options("localizacoes", "categorias", "fabricantes", "modelos")
        await self._fetch()

    async def _fetch(self):
        self.loading = True
        self.error = ""
        f = self.filters
        try:
            result = await self._cached_list(
                "inventory",
                "equipamentos",
                {
                    "q": f.get("q"),
                    "categoria_id": to_int(f.get("categoria_id")),
                    "fabricante_id": to_int(f.get("fabricante_id")),
                    "modelo_id": to_int(f.get("modelo_id")),
                    "localizacao_id": to_int(f.get("localizacao_id")),
                    "status": f.get("status") or None,
                    "include_decommissioned": f.get("include_decommissioned") == "on",
                    "page": self.page,
                    "per_page": 25,
                },
            )
            self.items = result["items"]
            self.total = result.get("itemsTotal") or len(self.items)
            self.has_next = result.get("nextPage") is not None
        except api.ApiError as err:
            self.error = err.message
        finally:
            self.loading = False

    # Os handlers abaixo devolvem o controle (yield) antes de buscar, para a tela reagir na hora
    @rx.event
    async def apply_filters(self, form: dict):
        self.filters = {k: str(v) for k, v in form.items()}
        self.page = 1
        self.loading = True
        yield
        await self._fetch()

    @rx.event
    async def next_page(self):
        self.page += 1
        self.loading = True
        yield
        await self._fetch()

    @rx.event
    async def prev_page(self):
        self.page = max(1, self.page - 1)
        self.loading = True
        yield
        await self._fetch()


def equipment_list_page() -> rx.Component:
    s = EquipmentListState
    return layout(
        "Equipamentos",
        rx.card(
            rx.form(
                rx.grid(
                    text_input("Buscar (nome, patrimônio ou série)", "q"),
                    native_select("Categoria", "categoria_id", s.categorias, placeholder="Todas"),
                    native_select("Fabricante", "fabricante_id", s.fabricantes, placeholder="Todos"),
                    native_select("Modelo", "modelo_id", s.modelos, placeholder="Todos"),
                    native_select("Localização", "localizacao_id", s.localizacoes, placeholder="Todas"),
                    native_select("Status", "status", STATUS_OPTIONS, placeholder="Todos os ativos"),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.el.label(
                        rx.hstack(rx.checkbox(name="include_decommissioned", id="f-include_decommissioned"), rx.text("Incluir descomissionados", size="2")),
                        html_for="f-include_decommissioned",
                    ),
                    rx.spacer(),
                    submit_button("Filtrar"),
                    margin_top="0.75rem",
                    align="center",
                    width="100%",
                ),
                on_submit=s.apply_filters,
                reset_on_submit=False,
                aria_label="Filtrar equipamentos",
            ),
            width="100%",
        ),
        error_callout(s.error),
        loading_overlay(s.loading),
        rx.text(s.total, " equipamento(s) encontrado(s)", size="2", color_scheme="gray", role="status"),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Patrimônio"),
                        rx.table.column_header_cell("Nome"),
                        rx.table.column_header_cell("Categoria"),
                        rx.table.column_header_cell("Fabricante / modelo"),
                        rx.table.column_header_cell("Localização"),
                        rx.table.column_header_cell("Status"),
                    )
                ),
                rx.table.body(
                    rx.cond(
                        s.items.length() > 0,
                        rx.foreach(
                            s.items,
                            lambda e: rx.table.row(
                                rx.table.cell(rx.link(e["numero_patrimonio"], href="/equipamentos/" + e["id"].to_string())),
                                rx.table.cell(e["nome"]),
                                rx.table.cell(e["categoria"]),
                                rx.table.cell(e["fabricante"], " / ", e["modelo"]),
                                rx.table.cell(e["localizacao"]),
                                rx.table.cell(badge(EQUIP_STATUS, e["status"])),
                            ),
                        ),
                        empty_row(6),
                    )
                ),
                width="100%",
            ),
            overflow_x="auto",
            width="100%",
        ),
        pager(s.page, s.has_next, s.prev_page, s.next_page),
        actions=rx.cond(
            s.can_manage_inventory,
            rx.link(rx.button(rx.icon("plus", size=16), "Novo equipamento"), href="/novo-equipamento"),
            rx.fragment(),
        ),
    )


# ------------------------------------------------------------------ cadastro / edição
class EquipmentFormState(OptionsState):
    equipment_id: int = 0
    current: dict = {}
    error: str = ""
    saving: bool = False
    form_key: int = 0

    @rx.event
    async def on_load(self):
        redirect = await self._guard("inventory.manage")
        if redirect:
            return redirect
        self.error = ""
        await self._load_options("localizacoes", "modelos")
        self.equipment_id = self._path_id() or 0
        self.current = {}
        if self.equipment_id:
            try:
                self.current = await self.call("GET", "inventory", f"equipamentos/{self.equipment_id}")
            except api.ApiError as err:
                self.error = err.message
        self.form_key += 1

    @rx.var
    def is_edit(self) -> bool:
        return self.equipment_id != 0

    @rx.var
    def default_modelo(self) -> str:
        return str(self.current.get("modelo", {}).get("id", "")) if self.current else ""

    @rx.var
    def default_localizacao(self) -> str:
        return str(self.current.get("localizacao_id", "")) if self.current else ""

    def _field(self, key: str) -> str:
        value = self.current.get(key) if self.current else None
        return "" if value is None else str(value)

    @rx.var
    def d_nome(self) -> str:
        return self._field("nome")

    @rx.var
    def d_patrimonio(self) -> str:
        return self._field("numero_patrimonio")

    @rx.var
    def d_serie(self) -> str:
        return self._field("numero_serie")

    @rx.var
    def d_ano(self) -> str:
        return self._field("ano_fabricacao")

    @rx.var
    def d_data(self) -> str:
        return self._field("data_aquisicao")

    @rx.var
    def d_valor(self) -> str:
        return self._field("valor_aquisicao")

    @rx.var
    def d_vida(self) -> str:
        return self._field("vida_util_anos")

    @rx.var
    def d_obs(self) -> str:
        return self._field("observacoes")

    @rx.event
    async def save(self, form: dict):
        self.error = ""
        nome = (form.get("nome") or "").strip()
        patrimonio = (form.get("numero_patrimonio") or "").strip()
        modelo_id = to_int(form.get("modelo_id"))
        if not nome or not patrimonio or not modelo_id:
            self.error = "Preencha nome, número de patrimônio e modelo."
            return
        valor = to_float(form.get("valor_aquisicao"))
        if form.get("valor_aquisicao") and valor is None:
            self.error = "Valor de aquisição inválido."
            return
        payload = {
            "nome": nome,
            "numero_patrimonio": patrimonio,
            "modelo_id": modelo_id,
            # "" limpa o número de série na edição; no cadastro, série em branco simplesmente não é gravada
            "numero_serie": (form.get("numero_serie") or "").strip() if self.is_edit else opt_text(form.get("numero_serie")),
            "ano_fabricacao": to_int(form.get("ano_fabricacao")),
            "data_aquisicao": opt_text(form.get("data_aquisicao")),
            "valor_aquisicao": valor,
            "vida_util_anos": to_int(form.get("vida_util_anos")),
            "observacoes": (form.get("observacoes") or "").strip() if self.is_edit else opt_text(form.get("observacoes")),
        }
        self.saving = True
        yield
        try:
            if self.is_edit:
                result = await self.call("PATCH", "inventory", f"equipamentos/{self.equipment_id}", json=payload)
            else:
                localizacao_id = to_int(form.get("localizacao_id"))
                if not localizacao_id:
                    self.error = "Selecione a localização."
                    return
                status = form.get("status") or "operational"
                motivo = opt_text(form.get("motivo"))
                if status == "out_of_service" and not motivo:
                    self.error = "Informe o motivo para cadastrar o equipamento como fora de serviço."
                    return
                payload |= {"localizacao_id": localizacao_id, "status": status, "motivo": motivo}
                result = await self.call("POST", "inventory", "equipamentos", json=payload)
        except api.ApiError as err:
            self.error = err.message
            return
        finally:
            self.saving = False
        yield rx.toast.success("Equipamento salvo.")
        yield rx.redirect(f"/equipamentos/{result['id']}")


def equipment_form_page() -> rx.Component:
    s = EquipmentFormState
    return layout(
        rx.cond(s.is_edit, "Editar equipamento", "Novo equipamento"),
        rx.card(
            rx.form(
                rx.vstack(
                    error_callout(s.error),
                    rx.heading("Identificação", size="3", as_="h2"),
                    rx.grid(
                        text_input("Nome", "nome", required=True, default_value=s.d_nome),
                        text_input("Número de patrimônio", "numero_patrimonio", required=True, default_value=s.d_patrimonio),
                        text_input("Número de série", "numero_serie", default_value=s.d_serie, hint="Opcional. Deve ser único quando informado."),
                        native_select(
                            "Modelo (define fabricante e categoria)",
                            "modelo_id",
                            s.modelos,
                            required=True,
                            default_value=s.default_modelo,
                        ),
                        columns=rx.breakpoints(initial="1", md="2"),
                        spacing="3",
                        width="100%",
                    ),
                    rx.cond(
                        s.is_edit,
                        rx.text(
                            "Localização e status são alterados pelas ações “Mover” e “Alterar status” na página do equipamento.",
                            size="2",
                            color_scheme="gray",
                        ),
                        rx.grid(
                            native_select("Localização", "localizacao_id", s.localizacoes, required=True),
                            native_select("Status inicial", "status", STATUS_OPTIONS[:3], placeholder="Operacional"),
                            text_input("Motivo", "motivo", hint="Obrigatório quando o status inicial for “Fora de serviço”."),
                            columns=rx.breakpoints(initial="1", md="2"),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    rx.heading("Aquisição", size="3", as_="h2"),
                    rx.grid(
                        text_input("Ano de fabricação", "ano_fabricacao", type_="number", default_value=s.d_ano, min="1900"),
                        text_input("Data de aquisição", "data_aquisicao", type_="date", default_value=s.d_data, hint="Não pode ser futura."),
                        text_input("Valor de aquisição (R$)", "valor_aquisicao", type_="number", default_value=s.d_valor, min="0", step="0.01"),
                        text_input("Vida útil estimada (anos)", "vida_util_anos", type_="number", default_value=s.d_vida, min="1"),
                        columns=rx.breakpoints(initial="1", md="2"),
                        spacing="3",
                        width="100%",
                    ),
                    text_area("Observações técnicas", "observacoes", default_value=s.d_obs),
                    rx.hstack(
                        submit_button("Salvar", loading=s.saving),
                        rx.button("Cancelar", type="button", variant="soft", color_scheme="gray", on_click=rx.call_script("history.back()")),
                        spacing="3",
                    ),
                    spacing="4",
                    width="100%",
                ),
                key=s.form_key,
                on_submit=s.save,
                reset_on_submit=False,
                aria_label="Dados do equipamento",
            ),
            width="100%",
            max_width="56rem",
        ),
    )


# ------------------------------------------------------------------ detalhe
class EquipmentDetailState(OptionsState):
    equipment_id: int = 0
    equip: dict = {}
    historico: list[dict] = []
    error: str = ""
    loading: bool = False
    action_error: str = ""
    move_open: bool = False
    status_open: bool = False
    component_open: bool = False

    @rx.event
    async def on_load(self):
        redirect = await self._guard("operational.read")
        if redirect:
            return redirect
        self.equipment_id = self._path_id() or 0
        self.move_open = self.status_open = self.component_open = False
        await self._fetch()
        if self.can_manage_inventory:
            await self._load_options("localizacoes", "componentes")

    async def _fetch(self):
        self.loading = True
        self.error = ""
        try:
            self.equip = await self.call("GET", "inventory", f"equipamentos/{self.equipment_id}")
            hist = await self.call("GET", "maintenance", f"equipamentos/{self.equipment_id}/historico")
            # Mais antigos primeiro: ordem cronológica como a API devolve (spec: Consultar o histórico do equipamento)
            self.historico = hist.get("eventos", [])
        except api.ApiError as err:
            self.error = err.message
        finally:
            self.loading = False

    @rx.var
    def is_decommissioned(self) -> bool:
        return self.equip.get("status") == "decommissioned"

    @rx.var
    def fabricante_nome(self) -> str:
        return (self.equip.get("fabricante") or {}).get("nome", "")

    @rx.var
    def categoria_nome(self) -> str:
        return (self.equip.get("categoria") or {}).get("nome", "")

    @rx.var
    def modelo_nome(self) -> str:
        return (self.equip.get("modelo") or {}).get("nome", "")

    @rx.var
    def localizacao_nome(self) -> str:
        loc = self.equip.get("localizacao") or {}
        suffix = " (inativa)" if loc and not loc.get("ativo") else ""
        return loc.get("nome", "") + suffix

    @rx.var
    def instalados(self) -> list[dict]:
        return self.equip.get("componentes_instalados", [])

    @rx.var
    def removidos(self) -> list[dict]:
        return self.equip.get("componentes_removidos", [])

    @rx.event
    def set_move_open(self, value: bool):
        self.move_open = value
        self.action_error = ""

    @rx.event
    def set_status_open(self, value: bool):
        self.status_open = value
        self.action_error = ""

    @rx.event
    def set_component_open(self, value: bool):
        self.component_open = value
        self.action_error = ""

    async def _action(self, method: str, path: str, payload: dict, success: str):
        self.action_error = ""
        try:
            await self.call(method, "inventory", path, json=payload)
        except api.ApiError as err:
            self.action_error = err.message
            return False
        self.move_open = self.status_open = self.component_open = False
        await self._fetch()
        return True

    @rx.event
    async def move(self, form: dict):
        localizacao_id = to_int(form.get("localizacao_id"))
        if not localizacao_id:
            self.action_error = "Selecione a nova localização."
            return
        if await self._action(
            "POST",
            f"equipamentos/{self.equipment_id}/mover",
            {"localizacao_id": localizacao_id, "observacao": opt_text(form.get("observacao"))},
            "",
        ):
            return rx.toast.success("Equipamento movido.")

    @rx.event
    async def change_status(self, form: dict):
        status = form.get("status") or ""
        if not status:
            self.action_error = "Selecione o novo status."
            return
        if await self._action(
            "POST",
            f"equipamentos/{self.equipment_id}/status",
            {"status": status, "motivo": opt_text(form.get("motivo"))},
            "",
        ):
            return rx.toast.success("Status atualizado.")

    @rx.event
    async def install_component(self, form: dict):
        componente_id = to_int(form.get("componente_id"))
        quantidade = to_int(form.get("quantidade")) or 0
        if not componente_id:
            self.action_error = "Selecione o componente."
            return
        if quantidade <= 0:
            self.action_error = "A quantidade deve ser maior que zero."
            return
        if await self._action(
            "POST",
            f"equipamentos/{self.equipment_id}/componentes",
            {
                "componente_id": componente_id,
                "quantidade": quantidade,
                "slot": opt_text(form.get("slot")),
                "numero_serie_instalado": opt_text(form.get("numero_serie_instalado")),
                "observacoes": opt_text(form.get("observacoes")),
            },
            "",
        ):
            return rx.toast.success("Componente instalado.")

    @rx.event
    async def remove_component(self, atribuicao_id: int):
        if await self._action("POST", f"equipamentos/{self.equipment_id}/componentes/{atribuicao_id}/remover", {}, ""):
            return rx.toast.success("Remoção registrada.")
        return rx.toast.error(self.action_error)


def info(label: str, value) -> rx.Component:
    return rx.vstack(rx.text(label, size="1", color_scheme="gray"), rx.text(value, size="3"), spacing="0")




def _dialog(title: str, open_var, on_open_change, form: rx.Component) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            form,
            max_width="32rem",
        ),
        open=open_var,
        on_open_change=on_open_change,
    )


def detail_actions() -> rx.Component:
    s = EquipmentDetailState
    return rx.cond(
        s.can_manage_inventory & ~s.is_decommissioned,
        rx.hstack(
            rx.link(rx.button("Editar", variant="soft"), href="/equipamentos/" + s.equipment_id.to_string() + "/editar"),
            rx.button("Mover", variant="soft", on_click=s.set_move_open(True)),
            rx.button("Alterar status", variant="soft", on_click=s.set_status_open(True)),
            wrap="wrap",
        ),
        rx.fragment(),
    )


def dialogs() -> rx.Component:
    s = EquipmentDetailState
    return rx.fragment(
        _dialog(
            "Mover equipamento",
            s.move_open,
            s.set_move_open,
            rx.form(
                rx.vstack(
                    error_callout(s.action_error),
                    native_select("Nova localização (somente ativas)", "localizacao_id", s.localizacoes, required=True),
                    text_input("Observação", "observacao"),
                    rx.hstack(submit_button("Mover"), rx.dialog.close(rx.button("Cancelar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                on_submit=s.move,
                reset_on_submit=False,
            ),
        ),
        _dialog(
            "Alterar status",
            s.status_open,
            s.set_status_open,
            rx.form(
                rx.vstack(
                    error_callout(s.action_error),
                    native_select("Novo status", "status", STATUS_OPTIONS, required=True),
                    text_area("Motivo", "motivo", hint="Obrigatório para “Fora de serviço” e “Descomissionado”."),
                    rx.callout(
                        "O descomissionamento é definitivo: o equipamento e seu histórico são mantidos, mas saem das listas ativas.",
                        icon="info",
                        size="1",
                    ),
                    rx.hstack(submit_button("Salvar"), rx.dialog.close(rx.button("Cancelar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                on_submit=s.change_status,
                reset_on_submit=False,
            ),
        ),
        _dialog(
            "Instalar componente",
            s.component_open,
            s.set_component_open,
            rx.form(
                rx.vstack(
                    error_callout(s.action_error),
                    native_select("Componente do catálogo", "componente_id", s.componentes, required=True),
                    text_input("Quantidade", "quantidade", type_="number", default_value="1", min="1", required=True),
                    text_input("Slot / posição", "slot"),
                    text_input("Número de série instalado", "numero_serie_instalado"),
                    text_input("Observações", "observacoes"),
                    rx.hstack(submit_button("Instalar"), rx.dialog.close(rx.button("Cancelar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                on_submit=s.install_component,
                reset_on_submit=False,
            ),
        ),
    )


def components_tab() -> rx.Component:
    s = EquipmentDetailState

    def row(c, removed: bool):
        cells = [
            rx.table.cell(c["componente"]),
            rx.table.cell(label_of(COMPONENT_TYPE, c["tipo"])),
            rx.table.cell(c["quantidade"]),
            rx.table.cell(c["slot"]),
            rx.table.cell(c["numero_serie_instalado"]),
            rx.table.cell(timestamp_text(c["instalado_em"], "DD/MM/YYYY")),
        ]
        if removed:
            cells.append(rx.table.cell(timestamp_text(c["removido_em"], "DD/MM/YYYY")))
        else:
            cells.append(
                rx.table.cell(
                    rx.cond(
                        s.can_manage_inventory & ~s.is_decommissioned,
                        rx.button("Registrar remoção", size="1", variant="soft", color_scheme="red", on_click=s.remove_component(c["id"])),
                        rx.fragment(),
                    )
                )
            )
        return rx.table.row(*cells)

    def table(rows, removed: bool):
        last = "Removido em" if removed else ""
        return rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in ["Componente", "Tipo", "Qtd.", "Slot", "Série instalada", "Instalado em", last]]
                    )
                ),
                rx.table.body(rx.cond(rows.length() > 0, rx.foreach(rows, lambda c: row(c, removed)), empty_row(7))),
                width="100%",
                size="1",
            ),
            overflow_x="auto",
            width="100%",
        )

    return rx.vstack(
        rx.cond(
            s.can_manage_inventory & ~s.is_decommissioned,
            rx.button(rx.icon("plus", size=16), "Instalar componente", on_click=s.set_component_open(True), size="2"),
            rx.fragment(),
        ),
        rx.heading("Instalados", size="3", as_="h3"),
        table(s.instalados, False),
        rx.heading("Histórico de remoções", size="3", as_="h3"),
        table(s.removidos, True),
        spacing="3",
        width="100%",
        padding_top="1rem",
    )


def history_tab() -> rx.Component:
    s = EquipmentDetailState

    def event_row(ev):
        return rx.table.row(
            # Manutenção ainda não iniciada é datada pela data planejada no calendário: mostrar sem converter fuso
            rx.table.cell(rx.cond(ev["somente_data"], date_text(ev["data_planejada"]), timestamp_text(ev["data"]))),
            rx.table.cell(
                rx.match(
                    ev["categoria"],
                    ("manutencao", rx.text("Manutenção ", label_of(MAINT_TYPE, ev["tipo"]))),
                    ("ocorrencia", rx.text("Ocorrência (", label_of(SEVERITY, ev["tipo"]), ")")),
                    ("componente_instalado", rx.text("Componente instalado")),
                    ("componente_removido", rx.text("Componente removido")),
                    rx.text(ev["categoria"]),
                )
            ),
            rx.table.cell(
                rx.match(
                    ev["categoria"],
                    ("manutencao", badge(MAINT_STATUS, ev["status"])),
                    ("ocorrencia", badge(OCC_STATUS, ev["status"])),
                    rx.text("—"),
                )
            ),
            rx.table.cell(ev["descricao"]),
            rx.table.cell(ev["responsavel"]),
            rx.table.cell(ev["resumo"]),
        )

    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(*[rx.table.column_header_cell(h) for h in ["Data", "Evento", "Situação", "Descrição", "Responsável", "Resumo / motivo"]])
            ),
            rx.table.body(rx.cond(s.historico.length() > 0, rx.foreach(s.historico, event_row), empty_row(6, "Sem eventos registrados."))),
            width="100%",
            size="1",
        ),
        overflow_x="auto",
        width="100%",
        padding_top="1rem",
    )


def equipment_detail_page() -> rx.Component:
    s = EquipmentDetailState
    e = s.equip
    return layout(
        rx.cond(e["nome"], e["nome"].to(str), "Equipamento"),
        error_callout(s.error),
        loading_overlay(s.loading),
        rx.hstack(badge(EQUIP_STATUS, e["status"]), rx.text("Patrimônio ", e["numero_patrimonio"], color_scheme="gray"), align="center"),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Visão geral", value="geral"),
                rx.tabs.trigger("Componentes", value="componentes"),
                rx.tabs.trigger("Histórico", value="historico"),
            ),
            rx.tabs.content(
                rx.grid(
                    info("Categoria", s.categoria_nome),
                    info("Fabricante", s.fabricante_nome),
                    info("Modelo", s.modelo_nome),
                    info("Localização", s.localizacao_nome),
                    info("Número de série", rx.cond(e["numero_serie"], e["numero_serie"].to(str), "—")),
                    info("Ano de fabricação", rx.cond(e["ano_fabricacao"], e["ano_fabricacao"].to(str), "—")),
                    info("Data de aquisição", date_text(e["data_aquisicao"])),
                    info("Valor de aquisição", rx.cond(e["valor_aquisicao"], "R$ " + e["valor_aquisicao"].to(str), "—")),
                    info("Vida útil (anos)", rx.cond(e["vida_util_anos"], e["vida_util_anos"].to(str), "—")),
                    info("Última manutenção", timestamp_text(e["ultima_manutencao"], "DD/MM/YYYY")),
                    info("Próxima manutenção preventiva", date_text(e["proxima_manutencao"])),
                    info("Ocorrências abertas", e["ocorrencias_abertas"].to(str)),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    spacing="4",
                    width="100%",
                    padding_top="1rem",
                ),
                rx.cond(e["observacoes"], rx.box(info("Observações técnicas", e["observacoes"].to(str)), padding_top="1rem"), rx.fragment()),
                rx.hstack(
                    rx.link("Ver manutenções", href="/manutencoes?equipamento_id=" + s.equipment_id.to_string()),
                    rx.link("Ver ocorrências", href="/ocorrencias?equipamento_id=" + s.equipment_id.to_string()),
                    spacing="4",
                    padding_top="1rem",
                ),
                value="geral",
            ),
            rx.tabs.content(components_tab(), value="componentes"),
            rx.tabs.content(history_tab(), value="historico"),
            default_value="geral",
            width="100%",
        ),
        dialogs(),
        actions=detail_actions(),
    )
