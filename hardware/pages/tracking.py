"""Acompanhamento por equipamento: saúde (crítico / atenção / OK) calculada no servidor por GET acompanhamento."""

import asyncio
import time

import reflex as rx

from .. import api
from ..alerts import HEALTH, HEALTH_COLOR, health_badge, reasons
from ..components import (
    EQUIP_STATUS,
    badge,
    date_text,
    empty_row,
    error_callout,
    layout,
    loading_overlay,
    native_select,
    pager,
    submit_button,
    text_input,
    timestamp_text,
)
from ..options import OptionsState, ms_to_local, to_int

PAGE_SIZE = 25


class TrackingState(OptionsState):
    items: list[dict] = []
    resumo: dict[str, int] = {}
    total: int = 0
    page: int = 1
    has_next: bool = False
    filters: dict[str, str] = {}
    saude: str = ""
    updated_at: str = ""
    loading: bool = False
    error: str = ""

    @rx.event
    async def on_load(self):
        redirect = await self._guard("reports.read")
        if redirect:
            return redirect
        # Em paralelo: as opções dos filtros não dependem da lista
        await asyncio.gather(self._load_options("localizacoes", "categorias"), self._fetch())

    async def _fetch(self):
        self.loading = True
        self.error = ""
        f = self.filters
        try:
            result = await self.call(
                "GET",
                "reports",
                "acompanhamento",
                params={
                    "q": f.get("q"),
                    "localizacao_id": to_int(f.get("localizacao_id")),
                    "categoria_id": to_int(f.get("categoria_id")),
                    "status": f.get("status") or None,
                    "saude": self.saude or None,
                    "page": self.page,
                    "per_page": PAGE_SIZE,
                },
            )
            self.items = [r | {"motivos": reasons(r)} for r in result.get("items") or []]
            self.resumo = result.get("resumo") or {}
            self.total = result.get("itemsTotal") or len(self.items)
            self.has_next = result.get("nextPage") is not None
            self.updated_at = ms_to_local(time.time() * 1000)
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
    async def set_saude(self, value: str):
        # Clicar de novo na faixa já selecionada volta a mostrar todos
        self.saude = "" if value == self.saude else value
        self.page = 1
        self.loading = True
        yield
        await self._fetch()

    @rx.event
    async def refresh(self):
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

    @rx.var
    def total_geral(self) -> int:
        return sum(self.resumo.get(k, 0) for k in HEALTH)


def health_tile(key: str) -> rx.Component:
    """Total de uma faixa de saúde; o cartão inteiro é um botão que filtra a lista por ela."""
    s = TrackingState
    selected = s.saude == key
    return rx.el.button(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.box(width="0.6rem", height="0.6rem", border_radius="50%", background=rx.color(HEALTH_COLOR[key], 9)),
                    rx.text(HEALTH[key], size="2", color_scheme="gray"),
                    align="center",
                    spacing="2",
                ),
                rx.heading(s.resumo.get(key, 0), size="7", color_scheme=HEALTH_COLOR[key]),
                spacing="1",
                align="start",
            ),
            width="100%",
            border=rx.cond(selected, f"2px solid {rx.color(HEALTH_COLOR[key], 8)}", "2px solid transparent"),
        ),
        on_click=s.set_saude(key),
        type="button",
        aria_pressed=rx.cond(selected, "true", "false"),
        aria_label=f"Filtrar por saúde: {HEALTH[key]}",
        style={"all": "unset", "cursor": "pointer", "display": "block", "width": "100%"},
    )


def tracking_page() -> rx.Component:
    s = TrackingState
    return layout(
        "Acompanhamento dos equipamentos",
        rx.text(
            "Crítico: fora de serviço ou com ocorrência crítica aberta. Atenção: em manutenção, com ocorrência aberta "
            "ou com preventiva atrasada. OK: operacional e sem pendências.",
            size="2",
            color_scheme="gray",
        ),
        rx.grid(
            health_tile("critico"),
            health_tile("atencao"),
            health_tile("ok"),
            rx.card(
                rx.vstack(
                    rx.text("Equipamentos ativos", size="2", color_scheme="gray"),
                    rx.heading(s.total_geral, size="7"),
                    spacing="1",
                ),
                width="100%",
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
            width="100%",
        ),
        rx.card(
            rx.form(
                rx.grid(
                    text_input("Buscar (nome, patrimônio ou série)", "q", id_prefix="t"),
                    native_select("Localização", "localizacao_id", s.localizacoes, placeholder="Todas", id_prefix="t"),
                    native_select("Categoria", "categoria_id", s.categorias, placeholder="Todas", id_prefix="t"),
                    native_select("Status", "status", [(k, v) for k, v in EQUIP_STATUS.items() if k != "decommissioned"], placeholder="Todos os ativos", id_prefix="t"),
                    columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    submit_button("Filtrar"),
                    margin_top="0.75rem",
                    width="100%",
                ),
                on_submit=s.apply_filters,
                reset_on_submit=False,
                aria_label="Filtrar acompanhamento",
            ),
            width="100%",
        ),
        error_callout(s.error),
        loading_overlay(s.loading),
        rx.hstack(
            rx.text(
                s.total,
                " equipamento(s)",
                rx.cond(s.saude != "", rx.text.span(" com saúde ", rx.match(s.saude, *HEALTH.items(), "")), rx.fragment()),
                size="2",
                color_scheme="gray",
                role="status",
            ),
            rx.cond(
                s.saude != "",
                rx.button("Limpar filtro de saúde", on_click=s.set_saude(s.saude), variant="ghost", size="1"),
                rx.fragment(),
            ),
            align="center",
            wrap="wrap",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Saúde"),
                        rx.table.column_header_cell("Patrimônio"),
                        rx.table.column_header_cell("Equipamento"),
                        rx.table.column_header_cell("Localização"),
                        rx.table.column_header_cell("Status"),
                        rx.table.column_header_cell("Pendências"),
                        rx.table.column_header_cell("Última manutenção"),
                        rx.table.column_header_cell("Próxima preventiva"),
                    )
                ),
                rx.table.body(
                    rx.cond(
                        s.items.length() > 0,
                        rx.foreach(
                            s.items,
                            lambda e: rx.table.row(
                                rx.table.cell(health_badge(e["saude"])),
                                rx.table.cell(rx.link(e["numero_patrimonio"], href="/equipamentos/" + e["id"].to_string())),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(e["nome"], weight="medium"),
                                        rx.text(e["categoria"], " · ", e["modelo"], size="1", color_scheme="gray"),
                                        spacing="0",
                                    )
                                ),
                                rx.table.cell(e["localizacao"]),
                                rx.table.cell(badge(EQUIP_STATUS, e["status"])),
                                rx.table.cell(
                                    rx.cond(
                                        e["motivos"] != "",
                                        rx.vstack(
                                            rx.text(e["motivos"], size="2"),
                                            rx.cond(
                                                e["preventivas_atrasadas"].to(int) > 0,
                                                rx.text("Atrasada desde ", date_text(e["atrasada_desde"]), size="1", color_scheme="red"),
                                                rx.fragment(),
                                            ),
                                            spacing="0",
                                        ),
                                        rx.text("—", color_scheme="gray"),
                                    )
                                ),
                                rx.table.cell(timestamp_text(e["ultima_manutencao"], "DD/MM/YYYY")),
                                rx.table.cell(date_text(e["proxima_manutencao"])),
                            ),
                        ),
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
        actions=rx.hstack(
            rx.cond(s.updated_at != "", rx.text("Atualizado às ", s.updated_at, size="1", color_scheme="gray"), rx.fragment()),
            rx.button(rx.icon("refresh_cw", size=16), "Atualizar", on_click=s.refresh, loading=s.loading, variant="soft"),
            align="center",
            spacing="3",
        ),
        subtitle="Situação de cada equipamento agora: crítico, atenção ou OK",
    )
