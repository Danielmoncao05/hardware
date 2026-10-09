"""Avisos de equipamentos que precisam de atenção: consulta GET alertas periodicamente em qualquer página e abre um
pop-up quando um equipamento passa a precisar de atenção ou piora (ex.: de atenção para crítico)."""

import time

import reflex as rx

from . import api
from .state import AuthState

HEALTH = {"critico": "Crítico", "atencao": "Atenção", "ok": "OK"}
HEALTH_COLOR = {"critico": "red", "atencao": "amber", "ok": "green"}
EQUIP_STATUS_LABEL = {"out_of_service": "Fora de serviço", "under_maintenance": "Em manutenção"}
SEVERITY_LABEL = {"low": "baixa", "medium": "média", "high": "alta", "critical": "crítica"}

# Intervalo entre as consultas (ms no navegador) e o menor intervalo aceito no servidor (s). Navegar entre páginas
# remonta o layout e dispara uma consulta; o mínimo evita gastar o limite de requisições do plano Free do Xano.
POLL_INTERVAL_MS = 60_000
MIN_POLL_SECONDS = 30
# Quantos equipamentos o pop-up lista; o resto aparece como "e mais N"
POPUP_LIMIT = 8


def reasons(row: dict) -> str:
    """Por que o equipamento não está OK, em texto curto (mesmas regras dos endpoints)."""
    out = []
    if row.get("status") in EQUIP_STATUS_LABEL:
        out.append(EQUIP_STATUS_LABEL[row["status"]])
    abertas = row.get("ocorrencias_abertas") or 0
    if abertas:
        sev = SEVERITY_LABEL.get(row.get("maior_severidade") or "", "")
        out.append(f"{abertas} ocorrência(s) aberta(s)" + (f", maior severidade {sev}" if sev else ""))
    atrasadas = row.get("preventivas_atrasadas") or 0
    if atrasadas:
        out.append(f"{atrasadas} preventiva(s) atrasada(s)")
    return "; ".join(out)


def new_alerts(rows: list[dict], seen: dict[str, str]) -> list[dict]:
    """Linhas que merecem aviso: equipamento que não estava na última consulta ou cuja situação mudou.
    Críticos primeiro. Um equipamento que volta a ficar OK sai de `seen` e avisa de novo se piorar outra vez."""
    fresh = [r for r in rows if seen.get(str(r["id"])) != signature(r)]
    return sorted(fresh, key=lambda r: (r.get("saude") != "critico", r.get("nome") or ""))


def signature(row: dict) -> str:
    return f"{row.get('saude')}|{reasons(row)}"


def current_list(rows: list[dict]) -> list[dict]:
    """Situação atual para o sino da barra superior: todos os equipamentos que precisam de atenção, críticos primeiro."""
    return new_alerts(rows, {})


class AlertState(AuthState):
    popup_open: bool = False
    popup_items: list[dict] = []
    popup_extra: int = 0
    # Lista completa da última consulta (não só as novidades), mostrada pelo sino da barra superior
    current_items: list[dict] = []

    _seen: dict[str, str] = {}
    _seen_user: int = 0
    _last_poll: float = 0.0

    @rx.event
    async def poll(self, _date=None):
        if not self._token or not self.can_read_reports or self.must_change_password:
            return
        now = time.time()
        if now - self._last_poll < MIN_POLL_SECONDS:
            return
        self._last_poll = now
        if self._seen_user != self.user_id:
            # Outra conta entrou nesta aba: avisa tudo de novo
            self._seen, self._seen_user = {}, self.user_id
        try:
            rows = await self.call("GET", "reports", "alertas")
        except api.ApiError:
            return  # Aviso é complementar: um erro (ex.: limite de requisições) só adia para a próxima consulta
        rows = [r | {"motivos": reasons(r)} for r in rows or []]
        # Atualizada a cada consulta, haja novidade ou não (o pop-up só abre com novidade)
        self.current_items = current_list(rows)
        fresh = new_alerts(rows, self._seen)
        self._seen = {str(r["id"]): signature(r) for r in rows}
        if not fresh:
            return
        if self.popup_open:
            # Pop-up ainda aberto: junta os novos aos que já estão nele
            ids = {r["id"] for r in fresh}
            fresh = new_alerts(fresh + [r for r in self.popup_items if r["id"] not in ids], {})
        self.popup_items = fresh[:POPUP_LIMIT]
        self.popup_extra = max(0, len(fresh) - POPUP_LIMIT)
        self.popup_open = True

    @rx.event
    def set_popup_open(self, value: bool):
        self.popup_open = value

    @rx.event
    def close_popup(self):
        self.popup_open = False


def health_badge(value) -> rx.Component:
    return rx.badge(
        rx.match(value, *[(k, v) for k, v in HEALTH.items()], value),
        color_scheme=rx.match(value, *[(k, c) for k, c in HEALTH_COLOR.items()], "gray"),
        variant="solid",
    )


def alerts_bell() -> rx.Component:
    """Sino da barra superior: contagem e lista atual dos equipamentos que precisam de atenção (da última consulta,
    sem requisição extra). Só para quem pode ler relatórios, a mesma permissão de GET alertas."""
    s = AlertState
    count = s.current_items.length()
    label = rx.cond(count > 0, "Alertas: " + count.to_string() + " equipamento(s) precisam de atenção", "Alertas: nenhum equipamento precisa de atenção")
    return rx.cond(
        AuthState.can_read_reports,
        rx.popover.root(
            rx.popover.trigger(
                rx.box(
                    rx.icon_button(rx.icon("bell", size=18), variant="ghost", color_scheme="gray", aria_label=label, title=label),
                    rx.cond(
                        count > 0,
                        rx.badge(count, color_scheme="red", variant="solid", radius="full", size="1", position="absolute", top="-0.35rem", right="-0.35rem", aria_hidden="true"),
                        rx.fragment(),
                    ),
                    position="relative",
                ),
            ),
            rx.popover.content(
                rx.vstack(
                    rx.text("Precisam de atenção", weight="bold", size="2"),
                    rx.cond(
                        count > 0,
                        rx.vstack(
                            rx.foreach(
                                s.current_items[:POPUP_LIMIT],
                                lambda e: rx.hstack(
                                    health_badge(e["saude"]),
                                    rx.vstack(
                                        rx.link(e["numero_patrimonio"], " — ", e["nome"], href="/equipamentos/" + e["id"].to_string(), size="2", weight="medium"),
                                        rx.text(e["localizacao"], " · ", e["motivos"], size="1", color_scheme="gray"),
                                        spacing="0",
                                    ),
                                    align="start",
                                    spacing="2",
                                    width="100%",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                            role="list",
                        ),
                        rx.text("Nenhum equipamento precisa de atenção agora.", size="2", color_scheme="gray"),
                    ),
                    rx.link("Ver acompanhamento", href="/acompanhamento", size="2"),
                    spacing="3",
                    width="100%",
                ),
                width="22rem",
                max_width="calc(100vw - 2rem)",
            ),
        ),
        rx.fragment(),
    )


def alert_watcher() -> rx.Component:
    """Relógio invisível que dispara a consulta, mais o pop-up. Vai no layout das páginas autenticadas."""
    s = AlertState
    return rx.fragment(
        rx.moment(interval=POLL_INTERVAL_MS, on_change=s.poll, display="none", aria_hidden="true"),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.hstack(rx.icon("triangle_alert", color=rx.color("red", 10)), "Equipamentos precisam de atenção", align="center", spacing="2")),
                rx.dialog.description("Situação nova ou que piorou desde a última verificação.", size="2", color_scheme="gray"),
                rx.vstack(
                    rx.foreach(
                        s.popup_items,
                        lambda e: rx.hstack(
                            health_badge(e["saude"]),
                            rx.vstack(
                                rx.link(
                                    e["numero_patrimonio"], " — ", e["nome"],
                                    href="/equipamentos/" + e["id"].to_string(),
                                    on_click=s.close_popup,
                                    weight="medium",
                                ),
                                rx.text(e["localizacao"], " · ", e["motivos"], size="1", color_scheme="gray"),
                                spacing="0",
                            ),
                            align="start",
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    rx.cond(s.popup_extra > 0, rx.text("e mais ", s.popup_extra, " equipamento(s).", size="2", color_scheme="gray"), rx.fragment()),
                    spacing="3",
                    margin_y="1rem",
                    width="100%",
                    role="list",
                ),
                rx.hstack(
                    rx.dialog.close(rx.button("Fechar", variant="soft", color_scheme="gray")),
                    rx.link(rx.button("Ver acompanhamento"), href="/acompanhamento", on_click=s.close_popup),
                    justify="end",
                    spacing="3",
                ),
                max_width="34rem",
            ),
            open=s.popup_open,
            on_open_change=s.set_popup_open,
        ),
    )
