"""Painel operacional: todos os números vêm de GET dashboard, calculados no servidor.

Layout: cabeçalho com a data de hoje, quatro indicadores, distribuição por setor, próximas manutenções, alertas
recentes e equipamentos críticos; abaixo, em "Mais detalhes", os filtros de período e as seções anteriores.
"""

import asyncio
import datetime as dt

import reflex as rx

from .. import api
from ..components import (
    EQUIP_STATUS,
    OCC_STATUS,
    SEVERITY,
    STATUS_COLOR,
    badge,
    empty_row,
    label_of,
    layout,
    loading_overlay,
    native_select,
    timestamp_text,
)
from ..options import TZ, OptionsState, to_int

# Quantos itens cada seção do novo layout mostra (as listas completas ficam nas telas de cada área)
LIST_LIMIT = 5
WEEKDAYS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def long_date(day: dt.date) -> str:
    """Data por extenso em português: "Sexta-feira, 9 de outubro de 2026"."""
    return f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]} de {day.year}"


def due_label(planned: str, today: dt.date) -> str:
    """Prazo de uma data de calendário ("YYYY-MM-DD") em relação a hoje, sem conversão de fuso."""
    try:
        days = (dt.date.fromisoformat(planned) - today).days
    except (TypeError, ValueError):
        return ""
    if days < 0:
        return "Atrasada"
    if days == 0:
        return "Hoje"
    if days == 1:
        return "Amanhã"
    return f"Em {days} dias"


def elapsed_label(ms, now: dt.datetime) -> str:
    """Tempo desde um instante (epoch em ms): "agora", "10 min atrás", "2 h atrás", "3 dias atrás"."""
    if not isinstance(ms, (int, float)):
        return ""
    minutes = int((now.timestamp() * 1000 - ms) // 60_000)
    if minutes < 1:
        return "agora"
    if minutes < 60:
        return f"{minutes} min atrás"
    if minutes < 24 * 60:
        return f"{minutes // 60} h atrás"
    days = minutes // (24 * 60)
    return "1 dia atrás" if days == 1 else f"{days} dias atrás"


class DashboardState(OptionsState):
    data: dict = {}
    localizacao_id: str = ""
    janela_dias: str = "30"
    atividade_dias: str = "30"
    loading: bool = False
    error: str = ""

    # Novo layout: calculado a cada busca (datas relativas a "agora")
    hoje: str = ""
    setores: list[dict] = []
    proximas_view: list[dict] = []
    alertas_view: list[dict] = []

    @rx.event
    async def on_load(self):
        redirect = await self._guard("reports.read")
        if redirect:
            return redirect
        # Em paralelo: as opções do filtro não dependem dos dados do painel
        await asyncio.gather(self._load_options("localizacoes"), self._fetch())

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
        self._build_view()

    def _build_view(self):
        now = dt.datetime.now(TZ)
        today = now.date()
        self.hoje = long_date(today)
        self.setores = sorted(self.data.get("por_localizacao") or [], key=lambda s: (-(s.get("total") or 0), s.get("localizacao") or ""))
        self.proximas_view = [m | {"prazo": due_label(m.get("data_planejada"), today)} for m in self.proximas[:LIST_LIMIT]]
        self.alertas_view = [o | {"tempo": elapsed_label(o.get("relatada_em"), now)} for o in (self.data.get("ocorrencias_recentes") or [])[:LIST_LIMIT]]

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

    # ---- indicadores ----
    @rx.var
    def total_ativos(self) -> int:
        return self.data.get("equipamentos_ativos", 0) or 0

    @rx.var
    def total_disponiveis(self) -> int:
        return (self.data.get("por_status") or {}).get("operational", 0) or 0

    @rx.var
    def total_em_manutencao(self) -> int:
        return (self.data.get("por_status") or {}).get("under_maintenance", 0) or 0

    @rx.var
    def criticos(self) -> list[dict]:
        return self.data.get("criticos") or []

    @rx.var
    def total_criticos(self) -> int:
        return len(self.data.get("criticos") or [])

    # ---- seções detalhadas ----
    @rx.var
    def status_cards(self) -> list[dict]:
        por_status = self.data.get("por_status") or {}
        return [{"status": k, "label": v, "total": por_status.get(k, 0)} for k, v in EQUIP_STATUS.items()]

    @rx.var
    def por_categoria(self) -> list[dict]:
        return [c for c in self.data.get("por_categoria") or [] if c.get("total")]

    @rx.var
    def severidades(self) -> list[dict]:
        """Ocorrências abertas por severidade, separadas por status (aberta / em andamento)."""
        por_sev = (self.data.get("ocorrencias_abertas") or {}).get("por_severidade") or {}
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
        por_status = (self.data.get("ocorrencias_abertas") or {}).get("por_status") or {}
        return {"open": por_status.get("open", 0), "in_progress": por_status.get("in_progress", 0)}

    @rx.var
    def atrasadas(self) -> list[dict]:
        return ((self.data.get("preventivas_atrasadas") or {}).get("itens") or [])[:10]

    @rx.var
    def proximas(self) -> list[dict]:
        return (self.data.get("preventivas_proximas") or {}).get("itens") or []

    @rx.var
    def recentes(self) -> list[dict]:
        return ((self.data.get("manutencoes_recentes") or {}).get("itens") or [])[:10]

    @rx.var
    def total_atrasadas(self) -> int:
        return (self.data.get("preventivas_atrasadas") or {}).get("total", 0) or 0

    @rx.var
    def total_ocorrencias(self) -> int:
        return (self.data.get("ocorrencias_abertas") or {}).get("total", 0) or 0


# ------------------------------------------------------------------ novo layout
ENTER_STEP_MS = 60


def enter(child: rx.Component, step: int, **props) -> rx.Component:
    """Envolve um bloco com a animação de entrada (assets/app.css), atrasada conforme a posição."""
    return rx.box(child, class_name="hhm-enter", style={"--hhm-delay": f"{step * ENTER_STEP_MS}ms"}, width="100%", **props)


def section(title: str, *children, icon: str | None = None, extra=None, **props) -> rx.Component:
    header = [rx.heading(title, size="4", as_="h2"), rx.spacer()]
    if extra is not None:
        header.append(extra)
    if icon:
        header.append(rx.icon(icon, size=18, color=rx.color("gray", 10), aria_hidden="true"))
    return rx.card(rx.vstack(rx.hstack(*header, align="center", width="100%"), *children, spacing="3", width="100%"), width="100%", **props)


def stat_card(icon: str, label: str, value, color: str) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.center(rx.icon(icon, size=20), width="2.75rem", height="2.75rem", border_radius="var(--radius-3)", background=rx.color(color, 3), color=rx.color(color, 11), flex_shrink="0"),
            rx.vstack(rx.text(label, size="2", color_scheme="gray"), rx.heading(value, size="7"), spacing="0"),
            align="center",
            spacing="3",
        ),
        width="100%",
    )


def sector_chart() -> rx.Component:
    s = DashboardState
    return section(
        "Distribuição de equipamentos por setor",
        rx.cond(
            s.setores.length() > 0,
            rx.box(
                rx.box(
                    rx.recharts.bar_chart(
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3", vertical=False, stroke=rx.color("gray", 5)),
                        rx.recharts.x_axis(data_key="localizacao", tick={"fontSize": 11}, interval=0, angle=-20, text_anchor="end", height=60),
                        rx.recharts.y_axis(allow_decimals=False, width=32, tick={"fontSize": 11}),
                        rx.recharts.graphing_tooltip(),
                        rx.recharts.bar(data_key="total", name="Equipamentos ativos", fill=rx.color("accent", 9), radius=[4, 4, 0, 0]),
                        data=s.setores,
                        width="100%",
                        height=300,
                    ),
                    aria_hidden="true",
                ),
                # Equivalente em texto do gráfico, lido por leitores de tela
                rx.el.ul(
                    rx.foreach(s.setores, lambda x: rx.el.li(x["localizacao"], ": ", x["total"].to_string(), " equipamento(s)")),
                    class_name="sr-only",
                    aria_label="Equipamentos ativos por setor",
                ),
                width="100%",
            ),
            rx.text("Nenhum equipamento ativo neste filtro.", color_scheme="gray", size="2"),
        ),
        icon="chart_column",
    )


def upcoming_list() -> rx.Component:
    s = DashboardState
    return section(
        "Próximas manutenções",
        rx.cond(
            s.proximas_view.length() > 0,
            rx.vstack(
                rx.foreach(
                    s.proximas_view,
                    lambda m: rx.hstack(
                        rx.center(rx.icon("wrench", size=16), width="2.25rem", height="2.25rem", border_radius="full", background=rx.color("accent", 3), color=rx.color("accent", 11), flex_shrink="0"),
                        rx.vstack(
                            rx.link(m["equipamento"], href="/equipamentos/" + m["equipamento_id"].to_string(), size="2", weight="medium"),
                            rx.text(m["localizacao"], " • ", m["numero_patrimonio"], size="1", color_scheme="gray"),
                            spacing="0",
                            min_width="0",
                        ),
                        rx.spacer(),
                        rx.text(m["prazo"], size="1", weight="medium", white_space="nowrap"),
                        align="center",
                        spacing="3",
                        width="100%",
                        padding="0.5rem",
                        border=f"1px solid {rx.color('gray', 5)}",
                        border_radius="var(--radius-3)",
                    ),
                ),
                spacing="2",
                width="100%",
                role="list",
            ),
            rx.text("Nenhuma preventiva prevista no período.", color_scheme="gray", size="2"),
        ),
        rx.link(rx.button("Ver todas", variant="outline", size="2", width="100%"), href="/manutencoes", width="100%"),
        icon="calendar_days",
    )


def severity_alert(o) -> rx.Component:
    return rx.badge(
        rx.icon("triangle_alert", size=12),
        rx.text(label_of(SEVERITY, o["severidade"]), ": ", o["descricao_tecnica"], white_space="normal"),
        color_scheme=rx.match(o["severidade"], *[(k, STATUS_COLOR[k]) for k in SEVERITY], "gray"),
        variant="soft",
        size="1",
        max_width="22rem",
    )


def recent_alerts() -> rx.Component:
    s = DashboardState
    return section(
        "Alertas recentes",
        rx.box(
            rx.table.root(
                rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Equipamento", "Setor", "Alerta", "Tempo"]])),
                rx.table.body(
                    rx.cond(
                        s.alertas_view.length() > 0,
                        rx.foreach(
                            s.alertas_view,
                            lambda o: rx.table.row(
                                rx.table.cell(rx.link(o["equipamento"], href="/equipamentos/" + o["equipamento_id"].to_string())),
                                rx.table.cell(o["localizacao"]),
                                rx.table.cell(severity_alert(o)),
                                rx.table.cell(rx.text(o["tempo"], white_space="nowrap", size="1", color_scheme="gray")),
                            ),
                        ),
                        empty_row(4, "Nenhuma ocorrência aberta."),
                    )
                ),
                size="1",
                width="100%",
            ),
            overflow_x="auto",
            width="100%",
        ),
        rx.link("Ver ocorrências", href="/ocorrencias", size="2"),
    )


def critical_card(c) -> rx.Component:
    s = DashboardState
    has_occ = c["ocorrencia_id"].to(int) > 0
    return rx.box(
        rx.hstack(
            rx.center(rx.icon("shield_alert", size=18), width="2.25rem", height="2.25rem", border_radius="full", background=rx.color("red", 9), color="white", flex_shrink="0"),
            rx.vstack(
                rx.hstack(
                    rx.link(c["equipamento"], " (", c["numero_patrimonio"], ")", href="/equipamentos/" + c["equipamento_id"].to_string(), size="2", weight="bold"),
                    rx.spacer(),
                    rx.cond(
                        has_occ,
                        badge(OCC_STATUS, c["ocorrencia_status"]),
                        badge(EQUIP_STATUS, c["status"]),
                    ),
                    width="100%",
                    align="center",
                    wrap="wrap",
                ),
                rx.text(c["localizacao"], size="1", color_scheme="gray"),
                rx.text(rx.cond(has_occ, c["descricao_tecnica"].to(str), "Equipamento fora de serviço."), size="2"),
                rx.hstack(
                    rx.cond(
                        has_occ & s.can_manage_maintenance,
                        rx.link(
                            rx.button(rx.icon("wrench", size=14), "Abrir manutenção corretiva", size="1", color_scheme="red"),
                            href="/manutencoes?equipamento_id=" + c["equipamento_id"].to_string() + "&ocorrencia_id=" + c["ocorrencia_id"].to_string(),
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        has_occ,
                        rx.link(rx.button("Ver ocorrências", size="1", variant="outline", color_scheme="gray"), href="/ocorrencias?equipamento_id=" + c["equipamento_id"].to_string()),
                        rx.link(rx.button("Ver equipamento", size="1", variant="outline", color_scheme="gray"), href="/equipamentos/" + c["equipamento_id"].to_string()),
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="1",
                width="100%",
                min_width="0",
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        padding="0.75rem",
        border=f"1px solid {rx.color('red', 6)}",
        background=rx.color("red", 2),
        border_radius="var(--radius-3)",
        width="100%",
        role="listitem",
    )


def critical_list() -> rx.Component:
    s = DashboardState
    return section(
        "Equipamentos com problemas críticos",
        rx.cond(
            s.criticos.length() > 0,
            rx.vstack(rx.foreach(s.criticos, critical_card), spacing="2", width="100%", role="list"),
            rx.text("Nenhum equipamento com problema crítico.", color_scheme="gray", size="2"),
        ),
        icon="shield_alert",
        border_top=f"3px solid {rx.color('red', 9)}",
    )


# ------------------------------------------------------------------ seções detalhadas (conteúdo anterior)
def work_table(title: str, rows, empty: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4", as_="h3"),
            rx.box(
                rx.table.root(
                    rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Data", "Equipamento", "Descrição"]])),
                    rx.table.body(
                        rx.cond(
                            rows.length() > 0,
                            rx.foreach(
                                rows,
                                lambda m: rx.table.row(
                                    rx.table.cell(m["data_planejada"]),
                                    rx.table.cell(rx.link(m["equipamento"], href="/equipamentos/" + m["equipamento_id"].to_string())),
                                    rx.table.cell(m["descricao"]),
                                ),
                            ),
                            empty_row(3, empty),
                        )
                    ),
                    width="100%",
                    size="1",
                ),
                overflow_x="auto",
                width="100%",
            ),
            width="100%",
        ),
        width="100%",
    )


def details() -> rx.Component:
    s = DashboardState
    return rx.el.details(
        rx.el.summary(rx.text("Mais detalhes", weight="bold", size="3", as_="span"), cursor="pointer", padding_y="0.5rem"),
        rx.vstack(
            rx.hstack(
                rx.box(
                    native_select(
                        "Janela de manutenções futuras",
                        "dash_janela",
                        [("7", "7 dias"), ("30", "30 dias"), ("90", "90 dias")],
                        placeholder="Padrão (30 dias)",
                        value=s.janela_dias,
                        on_change=s.set_janela,
                    ),
                    min_width="12rem",
                ),
                rx.box(
                    native_select(
                        "Período da atividade recente",
                        "dash_atividade",
                        [("7", "Últimos 7 dias"), ("30", "Últimos 30 dias"), ("90", "Últimos 90 dias")],
                        placeholder="Padrão (30 dias)",
                        value=s.atividade_dias,
                        on_change=s.set_atividade,
                    ),
                    min_width="12rem",
                ),
                wrap="wrap",
                spacing="4",
            ),
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.heading("Equipamentos por status", size="4", as_="h3"),
                        rx.foreach(s.status_cards, lambda x: rx.hstack(badge(EQUIP_STATUS, x["status"]), rx.spacer(), rx.text(x["total"], weight="bold"), width="100%")),
                        width="100%",
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("Equipamentos ativos por categoria", size="4", as_="h3"),
                        rx.cond(
                            s.por_categoria.length() > 0,
                            rx.foreach(s.por_categoria, lambda c: rx.hstack(rx.text(c["categoria"]), rx.spacer(), rx.text(c["total"], weight="bold"), width="100%")),
                            rx.text("Nenhum equipamento ativo.", color_scheme="gray"),
                        ),
                        width="100%",
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("Ocorrências abertas por severidade e status", size="4", as_="h3"),
                        rx.table.root(
                            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Severidade", "Abertas", "Em andamento", "Total"]])),
                            rx.table.body(
                                rx.foreach(
                                    s.severidades,
                                    lambda x: rx.table.row(
                                        rx.table.row_header_cell(badge(SEVERITY, x["sev"])),
                                        rx.table.cell(x["open"]),
                                        rx.table.cell(x["in_progress"]),
                                        rx.table.cell(rx.text(x["total"], weight="bold")),
                                    ),
                                ),
                                rx.table.row(
                                    rx.table.row_header_cell(rx.text("Total", weight="bold")),
                                    rx.table.cell(s.ocorrencias_status["open"]),
                                    rx.table.cell(s.ocorrencias_status["in_progress"]),
                                    rx.table.cell(rx.text(s.total_ocorrencias, weight="bold")),
                                ),
                            ),
                            size="1",
                            width="100%",
                        ),
                        width="100%",
                    ),
                ),
                columns=rx.breakpoints(initial="1", md="3"),
                spacing="3",
                width="100%",
            ),
            rx.grid(
                work_table("Preventivas atrasadas", s.atrasadas, "Nenhuma preventiva atrasada."),
                work_table("Preventivas próximas", s.proximas[:10], "Nenhuma preventiva prevista no período."),
                columns=rx.breakpoints(initial="1", lg="2"),
                spacing="3",
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.heading("Atividade de manutenção recente", size="4", as_="h3"),
                    rx.box(
                        rx.table.root(
                            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in ["Concluída em", "Equipamento", "Tipo", "Responsável", "Resumo"]])),
                            rx.table.body(
                                rx.cond(
                                    s.recentes.length() > 0,
                                    rx.foreach(
                                        s.recentes,
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
                        overflow_x="auto",
                        width="100%",
                    ),
                    width="100%",
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
            padding_top="0.5rem",
        ),
        open=True,
        width="100%",
    )


def dashboard_page() -> rx.Component:
    s = DashboardState
    return layout(
        "Painel",
        rx.box(
            native_select(
                "Localização",
                "dash_localizacao",
                s.localizacoes,
                placeholder="Todas as localizações",
                value=s.localizacao_id,
                on_change=s.set_localizacao,
            ),
            max_width="20rem",
            width="100%",
        ),
        loading_overlay(s.loading),
        rx.cond(s.error != "", rx.callout(s.error, color_scheme="red", role="alert"), rx.fragment()),
        rx.grid(
            enter(stat_card("monitor", "Total de equipamentos", s.total_ativos, "blue"), 0),
            enter(stat_card("circle_check", "Equipamentos disponíveis", s.total_disponiveis, "green"), 1),
            enter(stat_card("wrench", "Em manutenção", s.total_em_manutencao, "amber"), 2),
            enter(stat_card("circle_alert", "Com problemas críticos", s.total_criticos, "red"), 3),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
            width="100%",
        ),
        rx.grid(
            enter(sector_chart(), 4, grid_column=rx.breakpoints(initial="auto", lg="span 2")),
            enter(upcoming_list(), 5),
            columns=rx.breakpoints(initial="1", lg="3"),
            spacing="3",
            width="100%",
        ),
        rx.grid(
            enter(recent_alerts(), 6),
            enter(critical_list(), 7),
            columns=rx.breakpoints(initial="1", lg="2"),
            spacing="3",
            width="100%",
        ),
        enter(details(), 8),
        subtitle="Resumo operacional do parque de equipamentos",
        actions=rx.badge(rx.icon("calendar", size=14), s.hoje, variant="soft", color_scheme="gray", size="2"),
    )
