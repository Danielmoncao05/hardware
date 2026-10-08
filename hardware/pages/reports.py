"""Relatórios operacionais com filtros e exportação CSV, e o log de auditoria exclusivo do administrador.

O CSV é gerado pela API com os mesmos filtros do resultado na tela, então as linhas exportadas
sempre correspondem ao que é mostrado (e ao que o usuário pode ler).
"""

import reflex as rx

from .. import api
from ..components import EQUIP_STATUS, MAINT_STATUS, MAINT_TYPE, OCC_STATUS, SEVERITY, empty_row, error_callout, layout, native_select, pager, submit_button, text_input
from ..options import OptionsState, ms_to_local, to_int

REPORTS = {
    "inventario": {
        "path": "relatorios/inventario",
        "columns": [
            ("numero_patrimonio", "Patrimônio"),
            ("nome", "Nome"),
            ("categoria", "Categoria"),
            ("fabricante", "Fabricante"),
            ("modelo", "Modelo"),
            ("localizacao", "Localização"),
            ("status", "Status"),
            ("numero_serie", "Série"),
        ],
    },
    "manutencoes": {
        "path": "relatorios/manutencoes",
        "columns": [
            ("data_planejada", "Data planejada"),
            ("numero_patrimonio", "Patrimônio"),
            ("equipamento", "Equipamento"),
            ("localizacao", "Localização"),
            ("tipo", "Tipo"),
            ("status", "Status"),
            ("responsavel", "Responsável"),
            ("concluida_em", "Concluída em"),
        ],
    },
    "ocorrencias": {
        "path": "relatorios/ocorrencias",
        "columns": [
            ("relatada_em", "Relatada em"),
            ("numero_patrimonio", "Patrimônio"),
            ("equipamento", "Equipamento"),
            ("localizacao", "Localização"),
            ("severidade", "Severidade"),
            ("status", "Status"),
            ("relatada_por", "Relatada por"),
            ("descricao_tecnica", "Descrição técnica"),
        ],
    },
}
ENUM_LABELS = {**EQUIP_STATUS, **MAINT_STATUS, **MAINT_TYPE, **OCC_STATUS, **SEVERITY}


class ReportsState(OptionsState):
    report: str = "inventario"
    filters: dict[str, str] = {}
    rows: list[list[str]] = []
    total: int = 0
    page: int = 1
    has_next: bool = False
    error: str = ""
    loading: bool = False
    exporting: bool = False
    form_key: int = 0

    audit_rows: list[dict] = []
    audit_page: int = 1
    audit_has_next: bool = False
    audit_filters: dict[str, str] = {}

    @rx.event
    async def on_load(self):
        redirect = await self._guard("reports.read")
        if redirect:
            return redirect
        await self._load_options("localizacoes", "categorias", "fabricantes")
        await self._fetch()
        if self.can_read_audit:
            await self._fetch_audit()

    def _params(self) -> dict:
        f = self.filters
        common = {"localizacao_id": to_int(f.get("localizacao_id")), "status": f.get("status") or None}
        if self.report == "inventario":
            return common | {
                "categoria_id": to_int(f.get("categoria_id")),
                "fabricante_id": to_int(f.get("fabricante_id")),
                "include_decommissioned": f.get("include_decommissioned") == "on",
            }
        if self.report == "manutencoes":
            return common | {
                "situacao": f.get("situacao") or None,
                "tipo": f.get("tipo") or None,
                "de": f.get("de") or None,
                "ate": f.get("ate") or None,
            }
        return common | {"severidade": f.get("severidade") or None, "abertas": f.get("abertas") == "on"}

    @rx.var
    def headers(self) -> list[str]:
        return [label for _, label in REPORTS[self.report]["columns"]]

    async def _fetch(self):
        self.loading = True
        self.error = ""
        try:
            result = await self._cached_list("reports", REPORTS[self.report]["path"], self._params() | {"page": self.page, "per_page": 50})
            items = result["items"]
            self.total = result.get("itemsTotal") or len(items)
            self.has_next = result.get("nextPage") is not None
            keys = [k for k, _ in REPORTS[self.report]["columns"]]
            self.rows = [[self._fmt(k, item.get(k)) for k in keys] for item in items]
        except api.ApiError as err:
            self.error = err.message
            self.rows = []
        finally:
            self.loading = False

    @staticmethod
    def _fmt(key: str, value) -> str:
        if value is None:
            return ""
        if key in ("status", "tipo", "severidade"):
            return ENUM_LABELS.get(value, value)
        if key in ("relatada_em", "concluida_em"):
            return ms_to_local(value)
        return str(value)

    @rx.event
    async def set_report(self, value: str):
        self.report = value
        self.filters = {}
        self.page = 1
        self.form_key += 1
        await self._fetch()

    @rx.event
    async def apply_filters(self, form: dict):
        self.filters = {k: str(v) for k, v in form.items()}
        self.page = 1
        await self._fetch()

    @rx.event
    async def next_page(self):
        self.page += 1
        await self._fetch()

    @rx.event
    async def prev_page(self):
        self.page = max(1, self.page - 1)
        await self._fetch()

    @rx.event
    async def export_csv(self):
        self.exporting = True
        yield
        try:
            csv = await self.call("GET", "reports", REPORTS[self.report]["path"], params=self._params() | {"formato": "csv"}, raw=True)
        except api.ApiError as err:
            self.exporting = False
            yield rx.toast.error(err.message)
            return
        self.exporting = False
        # BOM para que planilhas reconheçam os acentos em UTF-8
        yield rx.download(data="﻿" + csv, filename=f"relatorio_{self.report}.csv", mime_type="text/csv")

    # ---- auditoria ----
    async def _fetch_audit(self):
        f = self.audit_filters
        try:
            result = api.as_page(
                await self.call(
                    "GET",
                    "reports",
                    "auditoria",
                    params={
                        "action": f.get("action") or None,
                        "entidade": f.get("entidade") or None,
                        "registro_id": to_int(f.get("registro_id")),
                        "page": self.audit_page,
                        "per_page": 50,
                    },
                ),
                self.audit_page,
                50,
            )
            self.audit_rows = [
                {
                    "quando": self._fmt("relatada_em", r.get("created_at")),
                    "ator": r.get("ator") or "sistema",
                    "acao": r.get("action") or "",
                    "registro": f"{(r.get('metadata') or {}).get('entidade', '')} #{(r.get('metadata') or {}).get('registro_id', '')}",
                    "detalhes": str({k: v for k, v in (r.get("metadata") or {}).items() if k in ("antes", "depois")}),
                }
                for r in result["items"]
            ]
            self.audit_has_next = result.get("nextPage") is not None
        except api.ApiError as err:
            self.error = err.message

    @rx.event
    async def apply_audit_filters(self, form: dict):
        self.audit_filters = {k: str(v) for k, v in form.items()}
        self.audit_page = 1
        await self._fetch_audit()

    @rx.event
    async def audit_next(self):
        self.audit_page += 1
        await self._fetch_audit()

    @rx.event
    async def audit_prev(self):
        self.audit_page = max(1, self.audit_page - 1)
        await self._fetch_audit()


def filters_form() -> rx.Component:
    s = ReportsState
    return rx.form(
        rx.vstack(
            rx.grid(
                native_select("Localização", "localizacao_id", s.localizacoes, placeholder="Todas"),
                rx.match(
                    s.report,
                    (
                        "inventario",
                        rx.fragment(
                            native_select("Categoria", "categoria_id", s.categorias, placeholder="Todas"),
                            native_select("Fabricante", "fabricante_id", s.fabricantes, placeholder="Todos"),
                            native_select("Status", "status", list(EQUIP_STATUS.items()), placeholder="Todos os ativos"),
                        ),
                    ),
                    (
                        "manutencoes",
                        rx.fragment(
                            native_select("Situação", "situacao", [("overdue", "Preventivas atrasadas"), ("upcoming", "Preventivas próximas")], placeholder="Todas (histórico)"),
                            native_select("Tipo", "tipo", list(MAINT_TYPE.items()), placeholder="Todos"),
                            native_select("Status", "status", list(MAINT_STATUS.items()), placeholder="Todos"),
                            text_input("Planejada a partir de", "de", type_="date"),
                            text_input("Planejada até", "ate", type_="date"),
                        ),
                    ),
                    rx.fragment(
                        native_select("Severidade", "severidade", list(SEVERITY.items()), placeholder="Todas"),
                        native_select("Status", "status", list(OCC_STATUS.items()), placeholder="Todos"),
                    ),
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="3",
                width="100%",
            ),
            rx.match(
                s.report,
                (
                    "inventario",
                    rx.el.label(rx.hstack(rx.checkbox(name="include_decommissioned", id="f-rel-decom"), rx.text("Incluir descomissionados", size="2")), html_for="f-rel-decom"),
                ),
                (
                    "ocorrencias",
                    rx.el.label(rx.hstack(rx.checkbox(name="abertas", id="f-rel-abertas"), rx.text("Somente abertas e em andamento", size="2")), html_for="f-rel-abertas"),
                ),
                rx.fragment(),
            ),
            rx.hstack(
                submit_button("Aplicar filtros"),
                rx.button(rx.icon("download", size=16), "Exportar CSV", type="button", variant="soft", loading=s.exporting, on_click=s.export_csv),
                spacing="3",
            ),
            spacing="3",
            width="100%",
        ),
        key=s.form_key,
        on_submit=s.apply_filters,
        reset_on_submit=False,
        aria_label="Filtros do relatório",
    )


def report_tab() -> rx.Component:
    s = ReportsState
    return rx.vstack(
        rx.box(
            native_select(
                "Relatório",
                "relatorio",
                [("inventario", "Inventário, status e localização"), ("manutencoes", "Manutenções (histórico, próximas, atrasadas)"), ("ocorrencias", "Ocorrências")],
                placeholder="Selecione…",
                value=s.report,
                on_change=s.set_report,
            ),
            max_width="28rem",
            width="100%",
        ),
        rx.card(filters_form(), width="100%"),
        error_callout(s.error),
        rx.text(s.total, " registro(s)", size="2", color_scheme="gray", role="status"),
        rx.box(
            rx.table.root(
                rx.table.header(rx.table.row(rx.foreach(s.headers, lambda h: rx.table.column_header_cell(h)))),
                rx.table.body(
                    rx.cond(
                        s.rows.length() > 0,
                        rx.foreach(s.rows, lambda r: rx.table.row(rx.foreach(r, lambda c: rx.table.cell(c)))),
                        empty_row(8),
                    )
                ),
                width="100%",
                size="1",
            ),
            overflow_x="auto",
            width="100%",
        ),
        pager(s.page, s.has_next, s.prev_page, s.next_page),
        spacing="3",
        width="100%",
        padding_top="1rem",
    )


def audit_tab() -> rx.Component:
    s = ReportsState
    return rx.vstack(
        rx.form(
            rx.hstack(
                text_input("Ação (ex.: equipamento.status_changed)", "action"),
                text_input("Entidade (ex.: equipamentos)", "entidade"),
                text_input("ID do registro", "registro_id", type_="number"),
                submit_button("Filtrar"),
                align="end",
                wrap="wrap",
                spacing="3",
            ),
            on_submit=s.apply_audit_filters,
            reset_on_submit=False,
            aria_label="Filtrar auditoria",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Quando", "Usuário", "Ação", "Registro", "Antes / depois"]])),
                rx.table.body(
                    rx.cond(
                        s.audit_rows.length() > 0,
                        rx.foreach(
                            s.audit_rows,
                            lambda r: rx.table.row(
                                rx.table.cell(r["quando"]),
                                rx.table.cell(r["ator"]),
                                rx.table.cell(rx.code(r["acao"])),
                                rx.table.cell(r["registro"]),
                                rx.table.cell(rx.text(r["detalhes"], size="1", font_family="monospace", word_break="break-all")),
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
        pager(s.audit_page, s.audit_has_next, s.audit_prev, s.audit_next),
        spacing="3",
        width="100%",
        padding_top="1rem",
    )


def reports_page() -> rx.Component:
    s = ReportsState
    return layout(
        "Relatórios",
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Relatórios operacionais", value="relatorios"),
                rx.cond(s.can_read_audit, rx.tabs.trigger("Auditoria", value="auditoria"), rx.fragment()),
            ),
            rx.tabs.content(report_tab(), value="relatorios"),
            rx.tabs.content(rx.cond(s.can_read_audit, audit_tab(), rx.fragment()), value="auditoria"),
            default_value="relatorios",
            width="100%",
        ),
    )
