"""Operational dashboard: all figures come from GET dashboard, computed server-side."""

import reflex as rx

from .. import api
from ..components import timestamp_text, EQUIP_STATUS, SEVERITY, badge, empty_row, layout, loading_overlay, native_select
from ..options import OptionsState, to_int


class DashboardState(OptionsState):
    data: dict = {}
    localizacao_id: str = ""
    janela_dias: str = "30"
    atividade_dias: str = "30"
    loading: bool = False
    error: str = ""

    @rx.event
    async def on_load(self):
        redirect = await self._guard("reports.read")
        if redirect:
            return redirect
        await self._load_options("localizacoes")
        await self._fetch()

    async def _fetch(self):
        self.loading = True
        self.error = ""
        try:
            self.data = await self.call(
                "GET",
                "reports",
                "dashboard",
                params={
                    "localizacao_id": to_int(self.localizacao_id),
                    "janela_dias": to_int(self.janela_dias) or 30,
                    "atividade_dias": to_int(self.atividade_dias) or 30,
                },
            )
        except api.ApiError as err:
            self.error = err.message
        finally:
            self.loading = False

    @rx.event
    async def set_localizacao(self, value: str):
        self.localizacao_id = value
        await self._fetch()

    @rx.event
    async def set_janela(self, value: str):
        self.janela_dias = value
        await self._fetch()

    @rx.event
    async def set_atividade(self, value: str):
        self.atividade_dias = value
        await self._fetch()

    @rx.var
    def status_cards(self) -> list[dict]:
        por_status = self.data.get("por_status", {})
        return [{"status": k, "label": v, "total": por_status.get(k, 0)} for k, v in EQUIP_STATUS.items()]

    @rx.var
    def por_categoria(self) -> list[dict]:
        return [c for c in self.data.get("por_categoria", []) if c.get("total")]

    @rx.var
    def severidades(self) -> list[dict]:
        """Open occurrences per severity, split by status (open / in progress)."""
        por_sev = self.data.get("ocorrencias_abertas", {}).get("por_severidade", {})
        rows = []
        for k in ["critical", "high", "medium", "low"]:
            counts = por_sev.get(k) or {}
            rows.append(
                {
                    "sev": k,
                    "open": counts.get("open", 0),
                    "in_progress": counts.get("in_progress", 0),
                    "total": counts.get("open", 0) + counts.get("in_progress", 0),
                }
            )
        return rows

    @rx.var
    def ocorrencias_status(self) -> dict[str, int]:
        por_status = self.data.get("ocorrencias_abertas", {}).get("por_status", {})
        return {"open": por_status.get("open", 0), "in_progress": por_status.get("in_progress", 0)}

    @rx.var
    def atrasadas(self) -> list[dict]:
        return self.data.get("preventivas_atrasadas", {}).get("itens", [])

    @rx.var
    def proximas(self) -> list[dict]:
        return self.data.get("preventivas_proximas", {}).get("itens", [])

    @rx.var
    def recentes(self) -> list[dict]:
        return self.data.get("manutencoes_recentes", {}).get("itens", [])

    @rx.var
    def total_ativos(self) -> int:
        return self.data.get("equipamentos_ativos", 0)

    @rx.var
    def total_atrasadas(self) -> int:
        return self.data.get("preventivas_atrasadas", {}).get("total", 0) or 0

    @rx.var
    def total_proximas(self) -> int:
        return self.data.get("preventivas_proximas", {}).get("total", 0) or 0

    @rx.var
    def total_ocorrencias(self) -> int:
        return self.data.get("ocorrencias_abertas", {}).get("total", 0) or 0


def stat(label, value, color: str = "gray") -> rx.Component:
    return rx.card(
        rx.vstack(rx.text(label, size="2", color_scheme="gray"), rx.heading(value, size="7", color_scheme=color), spacing="1"),
        width="100%",
    )


def work_table(title: str, rows, empty: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4", as_="h2"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Data"),
                        rx.table.column_header_cell("Equipamento"),
                        rx.table.column_header_cell("Descrição"),
                    )
                ),
                rx.table.body(
                    rx.cond(
                        rows.length() > 0,
                        rx.foreach(
                            rows,
                            lambda m: rx.table.row(
                                rx.table.cell(m["data_planejada"]),
                                rx.table.cell(
                                    rx.link(m["equipamento"], href="/equipamentos/" + m["equipamento_id"].to_string())
                                ),
                                rx.table.cell(m["descricao"]),
                            ),
                        ),
                        empty_row(3, empty),
                    )
                ),
                width="100%",
                size="1",
            ),
            width="100%",
        ),
        width="100%",
    )


def dashboard_page() -> rx.Component:
    return layout(
        "Painel operacional",
        rx.hstack(
            rx.box(
                native_select(
                    "Localização",
                    "dash_localizacao",
                    DashboardState.localizacoes,
                    placeholder="Todas as localizações",
                    value=DashboardState.localizacao_id,
                    on_change=DashboardState.set_localizacao,
                ),
                min_width="16rem",
            ),
            rx.box(
                native_select(
                    "Janela de manutenções futuras",
                    "dash_janela",
                    [("7", "7 dias"), ("30", "30 dias"), ("90", "90 dias")],
                    placeholder="Padrão (30 dias)",
                    value=DashboardState.janela_dias,
                    on_change=DashboardState.set_janela,
                ),
                min_width="12rem",
            ),
            rx.box(
                native_select(
                    "Período da atividade recente",
                    "dash_atividade",
                    [("7", "Últimos 7 dias"), ("30", "Últimos 30 dias"), ("90", "Últimos 90 dias")],
                    placeholder="Padrão (30 dias)",
                    value=DashboardState.atividade_dias,
                    on_change=DashboardState.set_atividade,
                ),
                min_width="12rem",
            ),
            wrap="wrap",
            spacing="4",
        ),
        loading_overlay(DashboardState.loading),
        rx.cond(DashboardState.error != "", rx.callout(DashboardState.error, color_scheme="red", role="alert"), rx.fragment()),
        rx.grid(
            stat("Equipamentos ativos", DashboardState.total_ativos),
            stat("Preventivas atrasadas", DashboardState.total_atrasadas, "red"),
            stat("Preventivas próximas", DashboardState.total_proximas, "blue"),
            stat("Ocorrências abertas", DashboardState.total_ocorrencias, "orange"),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
            width="100%",
        ),
        rx.grid(
            rx.card(
                rx.vstack(
                    rx.heading("Equipamentos por status", size="4", as_="h2"),
                    rx.foreach(
                        DashboardState.status_cards,
                        lambda s: rx.hstack(badge(EQUIP_STATUS, s["status"]), rx.spacer(), rx.text(s["total"], weight="bold"), width="100%"),
                    ),
                    width="100%",
                ),
            ),
            rx.card(
                rx.vstack(
                    rx.heading("Equipamentos ativos por categoria", size="4", as_="h2"),
                    rx.cond(
                        DashboardState.por_categoria.length() > 0,
                        rx.foreach(
                            DashboardState.por_categoria,
                            lambda c: rx.hstack(rx.text(c["categoria"]), rx.spacer(), rx.text(c["total"], weight="bold"), width="100%"),
                        ),
                        rx.text("Nenhum equipamento ativo.", color_scheme="gray"),
                    ),
                    width="100%",
                ),
            ),
            rx.card(
                rx.vstack(
                    rx.heading("Ocorrências abertas por severidade e status", size="4", as_="h2"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Severidade"),
                                rx.table.column_header_cell("Abertas"),
                                rx.table.column_header_cell("Em andamento"),
                                rx.table.column_header_cell("Total"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                DashboardState.severidades,
                                lambda s: rx.table.row(
                                    rx.table.row_header_cell(badge(SEVERITY, s["sev"])),
                                    rx.table.cell(s["open"]),
                                    rx.table.cell(s["in_progress"]),
                                    rx.table.cell(rx.text(s["total"], weight="bold")),
                                ),
                            ),
                            rx.table.row(
                                rx.table.row_header_cell(rx.text("Total", weight="bold")),
                                rx.table.cell(DashboardState.ocorrencias_status["open"]),
                                rx.table.cell(DashboardState.ocorrencias_status["in_progress"]),
                                rx.table.cell(rx.text(DashboardState.total_ocorrencias, weight="bold")),
                            ),
                        ),
                        size="1",
                        width="100%",
                    ),
                    rx.link("Ver ocorrências", href="/ocorrencias", size="2"),
                    width="100%",
                ),
            ),
            columns=rx.breakpoints(initial="1", md="3"),
            spacing="3",
            width="100%",
        ),
        rx.grid(
            work_table("Preventivas atrasadas", DashboardState.atrasadas, "Nenhuma preventiva atrasada."),
            work_table("Preventivas próximas", DashboardState.proximas, "Nenhuma preventiva prevista no período."),
            columns=rx.breakpoints(initial="1", lg="2"),
            spacing="3",
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Atividade de manutenção recente", size="4", as_="h2"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Concluída em"),
                            rx.table.column_header_cell("Equipamento"),
                            rx.table.column_header_cell("Tipo"),
                            rx.table.column_header_cell("Responsável"),
                            rx.table.column_header_cell("Resumo"),
                        )
                    ),
                    rx.table.body(
                        rx.cond(
                            DashboardState.recentes.length() > 0,
                            rx.foreach(
                                DashboardState.recentes,
                                lambda m: rx.table.row(
                                    rx.table.cell(timestamp_text(m["concluida_em"])),
                                    rx.table.cell(m["equipamento"]),
                                    rx.table.cell(rx.cond(m["tipo"] == "preventive", "Preventiva", "Corretiva")),
                                    rx.table.cell(m["responsavel"]),
                                    rx.table.cell(m["resumo_execucao"]),
                                ),
                            ),
                            empty_row(5, "Nenhuma manutenção concluída no período."),
                        )
                    ),
                    width="100%",
                    size="1",
                ),
                width="100%",
            ),
            width="100%",
        ),
    )
