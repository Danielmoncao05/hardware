"""Ocorrências: filas por status, registro técnico, atribuição, resolução e cancelamento."""

import asyncio

import reflex as rx

from .. import api
from ..components import (
    timestamp_text,
    equipment_picker,
    OCC_STATUS,
    SEVERITY,
    badge,
    empty_row,
    error_callout,
    layout,
    loading_overlay,
    native_select,
    no_clinical_notice,
    pager,
    submit_button,
    text_area,
    text_input,
)
from ..options import OptionsState, local_to_ms, now_local_input, page_slice, to_int


class OccurrenceState(OptionsState):
    queue: str = "open"
    equipamento_id: str = ""
    items: list[dict] = []
    page: int = 1
    has_next: bool = False
    loading: bool = False
    error: str = ""

    report_open: bool = False
    action: str = ""  # "iniciar" | "resolver" | "cancelar" | "atribuir"
    target: dict = {}
    form_error: str = ""
    saving: bool = False
    # Todas as ocorrências do filtro de equipamento, quando cabem em uma resposta da API (None = paginar pela API)
    _all: list[dict] | None = None

    @rx.event
    async def on_load(self):
        redirect = await self._guard("operational.read")
        if redirect:
            return redirect
        self.equipamento_id = self._query_param("equipamento_id")
        self.page = 1
        self.report_open = False
        self.action = ""
        # Em paralelo: lista, busca de equipamentos e responsáveis são independentes
        tasks = [self._refresh()]
        if self.can_report_occurrence:
            self.equip_query = ""
            tasks.append(self._search_equipment("", self.equipamento_id))
        if self.can_manage_occurrence:
            tasks.append(self._load_options("responsaveis_ocorrencia"))
        await asyncio.gather(*tasks)

    async def _refresh(self):
        """Recarrega a base (lista completa, quando cabe) e mostra a aba atual."""
        try:
            self._all = await self._load_complete("maintenance", "ocorrencias", {"equipamento_id": to_int(self.equipamento_id)})
        except api.ApiError:
            self._all = None
        await self._fetch()

    def _local_rows(self) -> list[dict]:
        """Filtra a aba atual na lista completa, com as mesmas regras da API (ordem: relatada_em decrescente)."""
        if self.queue == "mine":
            return [o for o in self._all if o.get("responsavel_id") == self.user_id and o.get("status") in ("open", "in_progress")]
        if self.queue == "all":
            return self._all
        return [o for o in self._all if o.get("status") == self.queue]

    async def _fetch(self):
        self.error = ""
        if self._all is not None:
            self.items, self.has_next = page_slice(self._local_rows(), self.page)
            self.loading = False
            return
        self.loading = True
        params = {"equipamento_id": to_int(self.equipamento_id), "page": self.page, "per_page": 25}
        if self.queue == "mine":
            params |= {"minhas": True, "abertas": True}
        elif self.queue != "all":
            params["status"] = self.queue
        try:
            result = await self._cached_list("maintenance", "ocorrencias", params)
            self.items = result["items"]
            self.has_next = result.get("nextPage") is not None
        except api.ApiError as err:
            self.error = err.message
        finally:
            self.loading = False

    # Com a lista completa, trocar de aba/página não chama a API. Sem ela, os handlers devolvem o controle (yield)
    # antes de buscar, para a aba/página mudar na tela na hora, com "Carregando…"
    @rx.event
    async def set_queue(self, value: str):
        self.queue = value
        self.page = 1
        if self._all is None:
            self.loading = True
            yield
        await self._fetch()

    @rx.event
    async def next_page(self):
        self.page += 1
        if self._all is None:
            self.loading = True
            yield
        await self._fetch()

    @rx.event
    async def prev_page(self):
        self.page = max(1, self.page - 1)
        if self._all is None:
            self.loading = True
            yield
        await self._fetch()

    # Sem cache: uma var em cache sem dependências é calculada uma vez só e manteria um horário desatualizado
    @rx.var(cache=False)
    def now_local(self) -> str:
        return now_local_input()

    @rx.event
    def set_report_open(self, value: bool):
        self.report_open = value
        self.form_error = ""

    @rx.event
    async def report(self, form: dict):
        # Os eventos rodam um de cada vez: um segundo envio enfileirado por clique duplo chega depois que o diálogo fechou
        if not self.report_open:
            return
        self.form_error = ""
        payload = {
            "equipamento_id": to_int(form.get("equipamento_id")),
            "descricao_tecnica": (form.get("descricao_tecnica") or "").strip(),
            "severidade": form.get("severidade") or None,
            "relatada_em": local_to_ms(form.get("relatada_em") or ""),
        }
        if not payload["equipamento_id"] or not payload["descricao_tecnica"] or not payload["severidade"]:
            self.form_error = "Informe equipamento, descrição técnica e severidade."
            return
        self.saving = True
        yield
        try:
            await self.call("POST", "maintenance", "ocorrencias", json=payload)
        except api.ApiError as err:
            self.form_error = err.message
            return
        finally:
            self.saving = False
        self.report_open = False
        self.queue = "open"
        self.page = 1
        await self._refresh()
        yield rx.toast.success("Ocorrência registrada.")

    @rx.event
    def open_action(self, action: str, record: dict):
        self.action = action
        self.target = record
        self.form_error = ""

    @rx.event
    def close_action(self, _open: bool = False):
        self.action = ""
        self.form_error = ""

    @rx.event
    async def submit_action(self, form: dict):
        if not self.action:
            return
        self.form_error = ""
        oid = self.target.get("id")
        if self.action == "atribuir":
            method, path = "PATCH", f"ocorrencias/{oid}"
            payload = {"responsavel_id": to_int(form.get("responsavel_id")) or 0}
        else:
            method, path = "POST", f"ocorrencias/{oid}/transicao"
            payload = {"acao": self.action}
            if self.action == "resolver":
                payload |= {
                    "resolvida_em": local_to_ms(form.get("resolvida_em") or ""),
                    "resumo_resolucao": (form.get("resumo_resolucao") or "").strip(),
                }
                if not payload["resolvida_em"] or not payload["resumo_resolucao"]:
                    self.form_error = "Informe a data de resolução e o resumo."
                    return
            elif self.action == "cancelar":
                payload["motivo_cancelamento"] = (form.get("motivo_cancelamento") or "").strip()
                if not payload["motivo_cancelamento"]:
                    self.form_error = "Informe o motivo do cancelamento."
                    return
        self.saving = True
        yield
        try:
            await self.call(method, "maintenance", path, json=payload)
        except api.ApiError as err:
            self.form_error = err.message
            return
        finally:
            self.saving = False
        self.action = ""
        await self._refresh()
        yield rx.toast.success("Ocorrência atualizada.")


def row_actions(o) -> rx.Component:
    s = OccurrenceState
    is_open = (o["status"] == "open") | (o["status"] == "in_progress")
    can_work = s.can_manage_occurrence | (s.can_work_occurrence & (o["responsavel_id"] == s.user_id))
    return rx.cond(
        is_open & can_work,
        rx.hstack(
            rx.cond(s.can_manage_occurrence, rx.button("Atribuir", size="1", variant="soft", on_click=s.open_action("atribuir", o)), rx.fragment()),
            rx.cond(o["status"] == "open", rx.button("Iniciar", size="1", variant="soft", on_click=s.open_action("iniciar", o)), rx.fragment()),
            rx.button("Resolver", size="1", variant="soft", color_scheme="green", on_click=s.open_action("resolver", o)),
            rx.button("Cancelar", size="1", variant="soft", color_scheme="red", on_click=s.open_action("cancelar", o)),
            # Abre o formulário de manutenção preenchido como corretiva e vinculado a esta ocorrência.
            # Técnicos só podem fazer isso em ocorrências atribuídas a eles (mesma regra da API).
            rx.cond(
                s.can_manage_maintenance | (s.can_work_maintenance & (o["responsavel_id"] == s.user_id)),
                rx.link(
                    rx.button(rx.icon("wrench", size=14), "Abrir manutenção corretiva", size="1", variant="soft", color_scheme="teal"),
                    href="/manutencoes?equipamento_id=" + o["equipamento_id"].to_string() + "&ocorrencia_id=" + o["id"].to_string(),
                ),
                rx.fragment(),
            ),
            spacing="1",
            wrap="wrap",
        ),
        rx.fragment(),
    )


def report_dialog() -> rx.Component:
    s = OccurrenceState
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Registrar ocorrência"),
            rx.form(
                rx.vstack(
                    no_clinical_notice(),
                    error_callout(s.form_error),
                    equipment_picker(s, s.equipamento_id),
                    native_select("Severidade", "severidade", list(SEVERITY.items()), required=True),
                    text_input("Data e hora do relato", "relatada_em", type_="datetime-local", default_value=s.now_local),
                    text_area(
                        "Descrição técnica",
                        "descricao_tecnica",
                        required=True,
                        hint="Descreva o comportamento do equipamento (sintomas, mensagens de erro, condições de uso).",
                    ),
                    rx.hstack(submit_button("Registrar", loading=s.saving), rx.dialog.close(rx.button("Cancelar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                on_submit=s.report,
                reset_on_submit=False,
            ),
            max_width="34rem",
        ),
        open=s.report_open,
        on_open_change=s.set_report_open,
    )


def action_dialog() -> rx.Component:
    s = OccurrenceState
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.match(
                    s.action,
                    ("atribuir", "Atribuir responsável"),
                    ("iniciar", "Iniciar atendimento"),
                    ("resolver", "Resolver ocorrência"),
                    ("cancelar", "Cancelar ocorrência"),
                    "",
                )
            ),
            rx.text(s.target["numero_patrimonio"], " — ", s.target["equipamento"], size="2", color_scheme="gray"),
            rx.form(
                rx.vstack(
                    error_callout(s.form_error),
                    rx.match(
                        s.action,
                        ("atribuir", native_select("Responsável", "responsavel_id", s.responsaveis_ocorrencia, placeholder="Sem responsável")),
                        ("iniciar", rx.text("A ocorrência passará para “Em andamento”.", size="2")),
                        (
                            "resolver",
                            rx.vstack(
                                text_input("Data e hora da resolução", "resolvida_em", type_="datetime-local", required=True, default_value=s.now_local),
                                text_area("Resumo da resolução", "resumo_resolucao", required=True),
                                no_clinical_notice(),
                                spacing="3",
                                width="100%",
                            ),
                        ),
                        text_area("Motivo do cancelamento", "motivo_cancelamento", required=True),
                    ),
                    rx.hstack(submit_button("Confirmar", loading=s.saving), rx.dialog.close(rx.button("Voltar", type="button", variant="soft", color_scheme="gray"))),
                    spacing="3",
                ),
                on_submit=s.submit_action,
                reset_on_submit=False,
            ),
            max_width="32rem",
        ),
        open=s.action != "",
        on_open_change=s.close_action,
    )


def occurrences_page() -> rx.Component:
    s = OccurrenceState
    return layout(
        "Ocorrências",
        rx.cond(
            s.equipamento_id != "",
            rx.hstack(rx.text("Filtrado por equipamento #", s.equipamento_id, size="2"), rx.link("Limpar filtro", href="/ocorrencias", size="2")),
            rx.fragment(),
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Abertas", value="open"),
                rx.tabs.trigger("Em andamento", value="in_progress"),
                rx.tabs.trigger("Resolvidas", value="resolved"),
                rx.tabs.trigger("Canceladas", value="canceled"),
                rx.tabs.trigger("Atribuídas a mim", value="mine"),
                rx.tabs.trigger("Todas", value="all"),
            ),
            value=s.queue,
            on_change=s.set_queue,
        ),
        error_callout(s.error),
        loading_overlay(s.loading),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(*[rx.table.column_header_cell(h) for h in ["Relatada em", "Equipamento", "Localização", "Severidade", "Status", "Descrição técnica", "Ações"]])
                ),
                rx.table.body(
                    rx.cond(
                        s.items.length() > 0,
                        rx.foreach(
                            s.items,
                            lambda o: rx.table.row(
                                rx.table.cell(timestamp_text(o["relatada_em"])),
                                rx.table.cell(rx.link(o["numero_patrimonio"], " — ", o["equipamento"], href="/equipamentos/" + o["equipamento_id"].to_string())),
                                rx.table.cell(o["localizacao"]),
                                rx.table.cell(badge(SEVERITY, o["severidade"])),
                                rx.table.cell(badge(OCC_STATUS, o["status"])),
                                rx.table.cell(o["descricao_tecnica"]),
                                rx.table.cell(row_actions(o)),
                            ),
                        ),
                        empty_row(7),
                    )
                ),
                width="100%",
                size="1",
            ),
            overflow_x="auto",
            width="100%",
        ),
        pager(s.page, s.has_next, s.prev_page, s.next_page),
        report_dialog(),
        action_dialog(),
        actions=rx.cond(
            s.can_report_occurrence,
            rx.button(rx.icon("plus", size=16), "Registrar ocorrência", on_click=s.set_report_open(True)),
            rx.fragment(),
        ),
    )
