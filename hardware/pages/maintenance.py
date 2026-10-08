"""Maintenance: due/overdue/all lists, a month calendar, scheduling, and state transitions."""

import calendar
import datetime as dt
from typing import TypedDict

import reflex as rx

from .. import api
from ..components import (
    equipment_picker,
    MAINT_STATUS,
    MAINT_TYPE,
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
from ..options import TZ, OptionsState, local_to_ms, now_local_input, opt_text, to_int

class CalItem(TypedDict):
    id: int
    label: str
    status: str


class CalDay(TypedDict):
    day: int
    iso: str
    in_month: bool
    items: list[CalItem]


VIEWS = {
    "upcoming": {"situacao": "upcoming"},
    "overdue": {"situacao": "overdue"},
    "mine": {"minhas": True},
    "all": {},
}
MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


class MaintenanceState(OptionsState):
    view: str = "upcoming"
    equipamento_id: str = ""
    items: list[dict] = []
    page: int = 1
    has_next: bool = False
    loading: bool = False
    error: str = ""

    # calendar
    mode: str = "list"
    cal_year: int = 0
    cal_month: int = 0
    cal_items: list[dict] = []

    # dialogs
    create_open: bool = False
    transition: str = ""  # "iniciar" | "concluir" | "cancelar"
    target: dict = {}
    form_error: str = ""
    saving: bool = False
    # Corrective maintenance opened from an occurrence (/manutencoes?ocorrencia_id=...): type, equipment
    # and the occurrence link are fixed and sent automatically.
    ocorrencia: dict = {}
    responsavel_padrao: str = ""

    @rx.event
    async def on_load(self):
        redirect = await self._guard("operational.read")
        if redirect:
            return redirect
        equipamento_id = self.router.page.params.get("equipamento_id", "") or ""
        if equipamento_id != self.equipamento_id:
            # Entering a filter shows every record of the equipment; clearing it returns to the default queue
            self.view = "all" if equipamento_id else "upcoming"
        self.equipamento_id = equipamento_id
        self.page = 1
        today = dt.datetime.now(TZ).date()
        self.cal_year = self.cal_year or today.year
        self.cal_month = self.cal_month or today.month
        self.create_open = False
        self.transition = ""
        self.ocorrencia = {}
        self.responsavel_padrao = ""
        await self._fetch()
        if self.can_work_maintenance:
            await self._load_options("responsaveis_manutencao")
            self.equip_query = ""
            await self._search_equipment("", self.equipamento_id)
            ocorrencia_id = to_int(self.router.page.params.get("ocorrencia_id"))
            if ocorrencia_id:
                await self._open_corrective(ocorrencia_id)

    async def _open_corrective(self, ocorrencia_id: int):
        """Open the create form pre-filled from an open/in-progress occurrence."""
        try:
            occ = await self.call("GET", "maintenance", f"ocorrencias/{ocorrencia_id}")
        except api.ApiError as err:
            self.error = err.message
            return
        if occ.get("status") not in ("open", "in_progress"):
            self.error = "A ocorrência já foi encerrada; não é possível abrir manutenção corretiva para ela."
            return
        self.ocorrencia = {
            "id": occ["id"],
            "equipamento_id": occ["equipamento_id"],
            "equipamento": f"{occ['equipamento']['numero_patrimonio']} — {occ['equipamento']['nome']}",
            "descricao_tecnica": occ.get("descricao_tecnica") or "",
        }
        # Managers default to the occurrence's responsible user; technicians can only assign themselves
        if self.can_manage_maintenance:
            self.responsavel_padrao = str(occ.get("responsavel_id") or "")
        else:
            self.responsavel_padrao = str(self.user_id)
        self.form_error = ""
        self.create_open = True

    @rx.var
    def from_occurrence(self) -> bool:
        return bool(self.ocorrencia)

    async def _fetch(self):
        self.loading = True
        self.error = ""
        try:
            if self.mode == "calendar":
                first = dt.date(self.cal_year, self.cal_month, 1)
                last = dt.date(self.cal_year, self.cal_month, calendar.monthrange(self.cal_year, self.cal_month)[1])
                # All records of the month (paginated), so busy months are not truncated
                self.cal_items = await self._fetch_all(
                    "maintenance",
                    "manutencoes",
                    params={"de": first.isoformat(), "ate": last.isoformat(), "equipamento_id": to_int(self.equipamento_id)},
                    page_size=100,
                )
            else:
                result = await self.call(
                    "GET",
                    "maintenance",
                    "manutencoes",
                    params=VIEWS[self.view] | {"equipamento_id": to_int(self.equipamento_id), "page": self.page, "per_page": 25},
                )
                self.items = result["items"]
                self.has_next = result.get("nextPage") is not None
        except api.ApiError as err:
            self.error = err.message
        finally:
            self.loading = False

    @rx.event
    async def set_view(self, value: str):
        self.view = value
        self.page = 1
        await self._fetch()

    @rx.event
    async def set_mode(self, value: str | list[str]):
        self.mode = value if isinstance(value, str) else (value[0] if value else "list")
        await self._fetch()

    @rx.event
    async def shift_month(self, delta: int):
        month = self.cal_month + delta
        self.cal_year += (month - 1) // 12
        self.cal_month = (month - 1) % 12 + 1
        await self._fetch()

    @rx.event
    async def next_page(self):
        self.page += 1
        await self._fetch()

    @rx.event
    async def prev_page(self):
        self.page = max(1, self.page - 1)
        await self._fetch()

    @rx.var
    def month_label(self) -> str:
        return f"{MONTHS[self.cal_month - 1]} de {self.cal_year}" if self.cal_month else ""

    @rx.var
    def weeks(self) -> list[list[CalDay]]:
        """Month grid (Sunday first); each day lists its maintenance records."""
        if not self.cal_month:
            return []
        by_day: dict[str, list[CalItem]] = {}
        for m in self.cal_items:
            by_day.setdefault(m["data_planejada"], []).append(
                {"id": m["id"], "label": f"{m['numero_patrimonio']} · {MAINT_TYPE.get(m['tipo'], m['tipo'])}", "status": m["status"]}
            )
        weeks = []
        for week in calendar.Calendar(firstweekday=6).monthdatescalendar(self.cal_year, self.cal_month):
            weeks.append(
                [
                    {
                        "day": d.day,
                        "iso": d.isoformat(),
                        "in_month": d.month == self.cal_month,
                        "items": by_day.get(d.isoformat(), []),
                    }
                    for d in week
                ]
            )
        return weeks

    # ---- create ----
    @rx.event
    def set_create_open(self, value: bool):
        self.create_open = value
        self.form_error = ""
        if not value:
            self.ocorrencia = {}
            self.responsavel_padrao = ""

    @rx.event
    async def create(self, form: dict):
        # Events run one at a time: a second submit queued by a double click arrives after the dialog closed
        if not self.create_open:
            return
        self.form_error = ""
        if self.ocorrencia:
            # Fixed by the occurrence; never taken from editable form fields
            form = form | {"tipo": "corrective", "equipamento_id": str(self.ocorrencia["equipamento_id"]), "ocorrencia_id": str(self.ocorrencia["id"])}
        tipo = form.get("tipo") or ""
        payload = {
            "equipamento_id": to_int(form.get("equipamento_id")),
            "tipo": tipo,
            "data_planejada": opt_text(form.get("data_planejada")),
            "descricao": (form.get("descricao") or "").strip(),
            "responsavel_id": to_int(form.get("responsavel_id")),
            "intervalo_recorrencia_dias": to_int(form.get("intervalo_recorrencia_dias")) if tipo == "preventive" else None,
            "ocorrencia_id": to_int(form.get("ocorrencia_id")) if tipo == "corrective" else None,
        }
        checklist = [line.strip() for line in (form.get("checklist") or "").splitlines() if line.strip()]
        if checklist:
            payload["checklist"] = [{"item": line, "feito": False} for line in checklist]
        missing = [k for k in ("equipamento_id", "tipo", "data_planejada", "descricao", "responsavel_id") if not payload.get(k)]
        if missing:
            self.form_error = "Preencha equipamento, tipo, data planejada, descrição e responsável."
            return
        self.saving = True
        yield
        try:
            await self.call("POST", "maintenance", "manutencoes", json=payload)
        except api.ApiError as err:
            self.form_error = err.message
            return
        finally:
            self.saving = False
        linked = bool(self.ocorrencia)
        self.create_open = False
        self.ocorrencia = {}
        self.responsavel_padrao = ""
        await self._fetch()
        yield rx.toast.success("Manutenção corretiva registrada e vinculada à ocorrência." if linked else "Manutenção registrada.")

    # ---- transitions ----
    @rx.event
    def open_transition(self, action: str, record: dict):
        self.transition = action
        self.target = record
        self.form_error = ""

    @rx.event
    def close_transition(self, _open: bool = False):
        self.transition = ""
        self.form_error = ""

    @rx.event
    async def submit_transition(self, form: dict):
        if not self.transition:
            return
        self.form_error = ""
        mid = self.target.get("id")
        action = self.transition
        if action == "iniciar":
            payload = {"colocar_equipamento_em_manutencao": form.get("colocar_equipamento_em_manutencao") == "on"}
        elif action == "concluir":
            payload = {
                "concluida_em": local_to_ms(form.get("concluida_em") or ""),
                "resumo_execucao": (form.get("resumo_execucao") or "").strip(),
                "status_equipamento": form.get("status_equipamento") or None,
                "motivo_status": opt_text(form.get("motivo_status")),
            }
            if not payload["concluida_em"] or not payload["resumo_execucao"]:
                self.form_error = "Informe a data de conclusão e o resumo do serviço executado."
                return
            if payload["status_equipamento"] == "out_of_service" and not payload["motivo_status"]:
                self.form_error = "Informe o motivo para deixar o equipamento fora de serviço."
                return
        else:
            payload = {"motivo_cancelamento": (form.get("motivo_cancelamento") or "").strip()}
            if not payload["motivo_cancelamento"]:
                self.form_error = "Informe o motivo do cancelamento."
                return
        self.saving = True
        yield
        try:
            result = await self.call("POST", "maintenance", f"manutencoes/{mid}/{action}", json=payload)
        except api.ApiError as err:
            self.form_error = err.message
            return
        finally:
            self.saving = False
        self.transition = ""
        await self._fetch()
        messages = {"iniciar": "Manutenção iniciada.", "concluir": "Manutenção concluída.", "cancelar": "Manutenção cancelada."}
        yield rx.toast.success(messages[action])
        if action == "concluir" and result and result.get("proxima_data_sugerida"):
            yield rx.toast.info(f"Manutenção recorrente: próxima data sugerida {result['proxima_data_sugerida']}.")

    # Not cached: a dependency-free cached var is computed once and would keep a stale time
    @rx.var(cache=False)
    def now_local(self) -> str:
        return now_local_input()


def row_actions(m) -> rx.Component:
    s = MaintenanceState
    open_states = (m["status"] == "planned") | (m["status"] == "in_progress")
    allowed = s.can_manage_maintenance | (s.can_work_maintenance & (m["responsavel_id"] == s.user_id))
    return rx.cond(
        allowed & open_states,
        rx.hstack(
            rx.cond(
                m["status"] == "planned",
                rx.button("Iniciar", size="1", variant="soft", on_click=s.open_transition("iniciar", m)),
                rx.fragment(),
            ),
            rx.button("Concluir", size="1", variant="soft", color_scheme="green", on_click=s.open_transition("concluir", m)),
            rx.button("Cancelar", size="1", variant="soft", color_scheme="red", on_click=s.open_transition("cancelar", m)),
            spacing="1",
        ),
        rx.fragment(),
    )


def list_view() -> rx.Component:
    s = MaintenanceState
    return rx.vstack(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Preventivas próximas", value="upcoming"),
                rx.tabs.trigger("Preventivas atrasadas", value="overdue"),
                rx.tabs.trigger("Atribuídas a mim", value="mine"),
                rx.tabs.trigger("Todas", value="all"),
            ),
            value=s.view,
            on_change=s.set_view,
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[
                            rx.table.column_header_cell(h)
                            for h in ["Data planejada", "Equipamento", "Localização", "Tipo", "Status", "Responsável", "Descrição", "Ações"]
                        ]
                    )
                ),
                rx.table.body(
                    rx.cond(
                        s.items.length() > 0,
                        rx.foreach(
                            s.items,
                            lambda m: rx.table.row(
                                rx.table.cell(m["data_planejada"]),
                                rx.table.cell(rx.link(m["numero_patrimonio"], " — ", m["equipamento"], href="/equipamentos/" + m["equipamento_id"].to_string())),
                                rx.table.cell(m["localizacao"]),
                                rx.table.cell(label_of(MAINT_TYPE, m["tipo"])),
                                rx.table.cell(badge(MAINT_STATUS, m["status"])),
                                rx.table.cell(m["responsavel"]),
                                rx.table.cell(m["descricao"]),
                                rx.table.cell(row_actions(m)),
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
        width="100%",
        spacing="3",
    )


def calendar_view() -> rx.Component:
    s = MaintenanceState
    weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    return rx.vstack(
        rx.hstack(
            rx.icon_button(rx.icon("chevron_left"), variant="soft", on_click=s.shift_month(-1), aria_label="Mês anterior"),
            rx.heading(s.month_label, size="4", as_="h2", aria_live="polite"),
            rx.icon_button(rx.icon("chevron_right"), variant="soft", on_click=s.shift_month(1), aria_label="Próximo mês"),
            align="center",
        ),
        rx.box(
            rx.grid(
                *[rx.text(d, weight="bold", size="2", text_align="center") for d in weekdays],
                rx.foreach(
                    s.weeks,
                    lambda week: rx.foreach(
                        week,
                        lambda day: rx.box(
                            rx.text(day["day"], size="1", weight="bold", color_scheme=rx.cond(day["in_month"], "gray", "gray"), opacity=rx.cond(day["in_month"], "1", "0.4")),
                            rx.foreach(
                                day["items"],
                                lambda it: rx.badge(it["label"], color_scheme=rx.cond(it["status"] == "completed", "green", rx.cond(it["status"] == "canceled", "gray", "blue")), variant="soft", size="1", white_space="normal"),
                            ),
                            min_height="5.5rem",
                            padding="0.25rem",
                            border=f"1px solid {rx.color('gray', 5)}",
                            border_radius="var(--radius-2)",
                        ),
                    ),
                ),
                columns="7",
                spacing="1",
                min_width="42rem",
            ),
            overflow_x="auto",
            width="100%",
        ),
        width="100%",
    )


def create_dialog() -> rx.Component:
    s = MaintenanceState
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(rx.cond(s.from_occurrence, "Nova manutenção corretiva", "Nova manutenção")),
            rx.form(
                rx.vstack(
                    error_callout(s.form_error),
                    rx.cond(
                        s.from_occurrence,
                        rx.callout(
                            rx.vstack(
                                rx.text("Vinculada à ocorrência #", s.ocorrencia["id"].to(str), weight="bold"),
                                rx.text("Equipamento: ", s.ocorrencia["equipamento"].to(str)),
                                rx.text(s.ocorrencia["descricao_tecnica"].to(str), size="1"),
                                spacing="1",
                            ),
                            icon="link",
                            size="1",
                        ),
                        rx.fragment(
                            equipment_picker(s, s.equipamento_id),
                            native_select("Tipo", "tipo", list(MAINT_TYPE.items()), required=True),
                        ),
                    ),
                    text_input("Data planejada", "data_planejada", type_="date", required=True),
                    native_select("Responsável", "responsavel_id", s.responsaveis_manutencao, required=True, default_value=s.responsavel_padrao),
                    text_area("Descrição do serviço", "descricao", required=True),
                    text_area("Checklist (um item por linha)", "checklist"),
                    rx.cond(
                        s.from_occurrence,
                        rx.fragment(),
                        text_input("Recorrência (dias) — somente preventiva", "intervalo_recorrencia_dias", type_="number", min="1"),
                    ),
                    rx.hstack(submit_button("Salvar", loading=s.saving), rx.dialog.close(rx.button("Cancelar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                key=s.ocorrencia["id"].to(str),
                on_submit=s.create,
                reset_on_submit=False,
            ),
            max_width="36rem",
        ),
        open=s.create_open,
        on_open_change=s.set_create_open,
    )


def transition_dialog() -> rx.Component:
    s = MaintenanceState
    t = s.target
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.match(s.transition, ("iniciar", "Iniciar manutenção"), ("concluir", "Concluir manutenção"), ("cancelar", "Cancelar manutenção"), "")
            ),
            rx.text(t["numero_patrimonio"], " — ", t["equipamento"], " · ", t["data_planejada"], size="2", color_scheme="gray"),
            rx.form(
                rx.vstack(
                    error_callout(s.form_error),
                    rx.match(
                        s.transition,
                        (
                            "iniciar",
                            # Equipment status changes require inventory.manage (decision 20)
                            rx.cond(
                                s.can_manage_inventory,
                                rx.el.label(
                                    rx.hstack(rx.checkbox(name="colocar_equipamento_em_manutencao", id="f-em-manutencao", default_checked=True), rx.text("Colocar o equipamento em “Em manutenção”", size="2")),
                                    html_for="f-em-manutencao",
                                ),
                                rx.text("A manutenção passará para “Em andamento”. O status do equipamento é alterado pela gestão de inventário.", size="2"),
                            ),
                        ),
                        (
                            "concluir",
                            rx.vstack(
                                text_input("Data e hora de conclusão", "concluida_em", type_="datetime-local", required=True, default_value=s.now_local),
                                text_area("Resumo do serviço executado", "resumo_execucao", required=True),
                                rx.cond(
                                    s.can_manage_inventory,
                                    rx.vstack(
                                        native_select(
                                            "Status do equipamento após o serviço",
                                            "status_equipamento",
                                            [("operational", "Operacional"), ("out_of_service", "Fora de serviço")],
                                            placeholder="Manter status atual",
                                        ),
                                        text_input("Motivo do status", "motivo_status", hint="Obrigatório para “Fora de serviço”."),
                                        spacing="3",
                                        width="100%",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                        ),
                        text_area("Motivo do cancelamento", "motivo_cancelamento", required=True),
                    ),
                    rx.hstack(submit_button("Confirmar", loading=s.saving), rx.dialog.close(rx.button("Voltar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                on_submit=s.submit_transition,
                reset_on_submit=False,
            ),
            max_width="32rem",
        ),
        open=s.transition != "",
        on_open_change=s.close_transition,
    )


def maintenance_page() -> rx.Component:
    s = MaintenanceState
    return layout(
        "Manutenções",
        rx.cond(
            s.equipamento_id != "",
            rx.hstack(rx.text("Filtrado por equipamento #", s.equipamento_id, size="2"), rx.link("Limpar filtro", href="/manutencoes", size="2")),
            rx.fragment(),
        ),
        rx.segmented_control.root(
            rx.segmented_control.item("Lista", value="list"),
            rx.segmented_control.item("Calendário", value="calendar"),
            value=s.mode,
            on_change=s.set_mode,
            aria_label="Modo de visualização",
        ),
        error_callout(s.error),
        loading_overlay(s.loading),
        rx.cond(s.mode == "calendar", calendar_view(), list_view()),
        create_dialog(),
        transition_dialog(),
        actions=rx.cond(
            s.can_work_maintenance,
            rx.button(rx.icon("plus", size=16), "Nova manutenção", on_click=s.set_create_open(True)),
            rx.fragment(),
        ),
    )
