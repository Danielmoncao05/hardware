"""Testes unitários locais dos auxiliares do frontend e do cliente da API (sem backend)."""

import asyncio
import datetime as dt
import json
import re
import time
from pathlib import Path

import httpx
import pytest

from hardware import api
from hardware.options import TZ, local_to_ms, ms_to_local, now_local_input, opt_text, to_float, to_int

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ auxiliares de valores de formulário
@pytest.mark.parametrize("value,expected", [("12", 12), (" 7 ", 7), ("", None), (None, None), ("abc", None), ("1.5", None)])
def test_to_int(value, expected):
    assert to_int(value) == expected


@pytest.mark.parametrize("value,expected", [("10,50", 10.5), ("3.25", 3.25), ("", None), ("x", None)])
def test_to_float_accepts_decimal_comma(value, expected):
    assert to_float(value) == expected


def test_opt_text_blank_becomes_none():
    assert opt_text("  ") is None and opt_text(None) is None and opt_text(" a ") == "a"


def test_stale_submit_drops_a_repeated_submit():
    from hardware.components import stale_submit

    assert not stale_submit({"_form_key": "3"}, 3)
    # Tratado depois que o primeiro envio deu certo e incrementou a chave
    assert stale_submit({"_form_key": "3"}, 4)
    assert stale_submit({}, 0)


def test_option_lists_are_reused_within_ttl():
    """Cada troca de página recarregava todas as listas e estourava o limite de requisições do plano Free."""
    from hardware.options import OptionsState

    calls = []

    class Fake:
        _options_at: dict = {}

        async def _fetch_options(self, kind):
            calls.append(kind)
            if kind == "fabricantes" and calls.count(kind) == 1:
                raise api.ApiError(429, "limite")
            return [{"id": 1, "nome": "X"}]

        def _set_options(self, kind, rows):
            self._options_at = self._options_at | {kind: time.time()}

    fake = Fake()
    load = OptionsState._load_options
    _run(load(fake, "categorias", "fabricantes"))
    assert calls == ["categorias", "fabricantes"]
    # categorias está em cache; fabricantes falhou antes e é buscado de novo
    _run(load(fake, "categorias", "fabricantes"))
    assert calls == ["categorias", "fabricantes", "fabricantes"]
    _run(load(fake, "categorias", force=True))
    assert calls[-1] == "categorias" and len(calls) == 4


def test_list_pages_are_cached_and_any_write_clears_them(mock_transport):
    """Voltar a uma aba já vista não chama a API de novo; depois de qualquer alteração, chama."""
    from hardware.state import AuthState

    captured, responses = mock_transport

    class Fake:
        _token = "tok"
        _list_cache: dict = {}

        def _clear_session(self):
            pass

        # call é público, então o Reflex o expõe na classe como EventHandler; .fn é a função original
        call = AuthState.call.fn
        _cached_list = AuthState._cached_list

    fake = Fake()
    responses += [httpx.Response(200, json={"items": [1]}), httpx.Response(200, json={}), httpx.Response(200, json={"items": [2]})]
    assert _run(fake._cached_list("maintenance", "ocorrencias", {"status": "open"})) == {"items": [1]}
    assert _run(fake._cached_list("maintenance", "ocorrencias", {"status": "open"})) == {"items": [1]}
    assert len(captured) == 1
    _run(fake.call("POST", "maintenance", "ocorrencias", json={}))
    assert _run(fake._cached_list("maintenance", "ocorrencias", {"status": "open"})) == {"items": [2]}
    assert len(captured) == 3


def test_local_tabs_follow_api_rules():
    """Com a lista completa, as abas são filtradas no app; as regras precisam ser as mesmas da API."""
    from types import SimpleNamespace

    from hardware.options import page_slice
    from hardware.pages.maintenance import MaintenanceState
    from hardware.pages.occurrences import OccurrenceState

    occ = [
        {"id": 1, "status": "open", "responsavel_id": 7},
        {"id": 2, "status": "in_progress", "responsavel_id": 8},
        {"id": 3, "status": "resolved", "responsavel_id": 7},
    ]
    rows = lambda queue: [o["id"] for o in OccurrenceState._local_rows(SimpleNamespace(_all=occ, queue=queue, user_id=7))]  # noqa: E731
    assert rows("open") == [1] and rows("resolved") == [3] and rows("all") == [1, 2, 3]
    assert rows("mine") == [1]  # só as abertas/em andamento atribuídas a mim

    today = dt.datetime.now(dt.timezone.utc).date()
    past, future = str(today - dt.timedelta(days=3)), str(today + dt.timedelta(days=3))
    man = [
        {"id": 1, "tipo": "preventive", "status": "planned", "data_planejada": past, "responsavel_id": 7},
        {"id": 2, "tipo": "corrective", "status": "planned", "data_planejada": past, "responsavel_id": 8},
        {"id": 3, "tipo": "preventive", "status": "planned", "data_planejada": future, "responsavel_id": 8},
        {"id": 4, "tipo": "preventive", "status": "completed", "data_planejada": past, "responsavel_id": 7},
    ]
    views = lambda view: [m["id"] for m in MaintenanceState._local_rows(SimpleNamespace(_all=man, view=view, user_id=7))]  # noqa: E731
    assert views("overdue") == [1]  # corretiva e concluída ficam de fora
    assert views("upcoming") == [3]
    assert views("mine") == [1, 4]
    assert views("all") == [1, 2, 3, 4]

    assert page_slice(list(range(30)), 1) == (list(range(25)), True)
    assert page_slice(list(range(30)), 2) == (list(range(25, 30)), False)


def test_as_page_accepts_a_plain_list():
    """O Xano às vezes ignora a paginação e devolve a lista inteira; as telas quebravam com TypeError."""
    page = {"items": [1], "nextPage": 2, "itemsTotal": 30}
    assert api.as_page(page) is page
    rows = list(range(30))
    assert api.as_page(rows, 1, 25) == {"items": list(range(25)), "nextPage": 2, "itemsTotal": 30}
    assert api.as_page(rows, 2, 25) == {"items": list(range(25, 30)), "nextPage": None, "itemsTotal": 30}
    assert api.as_page(None) == {"items": [], "nextPage": None, "itemsTotal": 0}


def test_now_local_vars_are_not_cached():
    """Uma var em cache sem dependências é calculada uma vez só, deixando desatualizado o horário pré-preenchido."""
    from hardware.pages.maintenance import MaintenanceState
    from hardware.pages.occurrences import OccurrenceState

    for state in (MaintenanceState, OccurrenceState):
        assert not state.computed_vars["now_local"]._cache


def test_local_time_round_trip_uses_institution_timezone():
    ms = local_to_ms("2026-03-10T14:30")
    assert ms is not None
    assert ms_to_local(ms) == "10/03/2026 14:30"
    assert local_to_ms("") is None and local_to_ms("not a date") is None
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", now_local_input())
    assert str(TZ)  # tzdata disponível (obrigatório no Windows)


# ------------------------------------------------------------------ cliente da API
def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def mock_transport(monkeypatch):
    """Faz api.request passar por um httpx.MockTransport; devolve a lista de requisições capturadas."""
    captured: list[httpx.Request] = []
    responses: list[httpx.Response] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return responses.pop(0)

    real_client = httpx.AsyncClient
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    return captured, responses


def test_request_drops_none_keeps_empty_string_and_sends_token(mock_transport):
    captured, responses = mock_transport
    responses.append(httpx.Response(200, json={"ok": True}))
    _run(api.request("PATCH", "inventory", "equipamentos/1", token="tok", params={"a": None, "b": "", "c": 1}, json={"x": None, "y": "", "z": 2}))
    req = captured[0]
    assert req.headers["Authorization"] == "Bearer tok"
    assert dict(req.url.params) == {"c": "1"}
    assert json.loads(req.content) == {"y": "", "z": 2}
    assert "/api:hhm149197-inventory/equipamentos/1" in str(req.url)


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (401, {"message": "Unauthorized"}, "Sua sessão expirou. Entre novamente."),
        (403, {"message": "Access denied."}, "Você não tem permissão para esta ação."),
        (400, {"message": "numero_patrimonio is already in use."}, "numero_patrimonio is already in use."),
        (500, {}, "Ocorreu um erro inesperado."),
    ],
)
def test_request_maps_errors(mock_transport, status, body, expected):
    _, responses = mock_transport
    responses.append(httpx.Response(status, json=body))
    with pytest.raises(api.ApiError) as exc:
        _run(api.request("GET", "inventory", "equipamentos"))
    assert exc.value.status == status and exc.value.message == expected
    assert exc.value.unauthorized == (status == 401)


def test_request_retries_when_rate_limited(mock_transport, monkeypatch):
    captured, responses = mock_transport
    waits = []

    async def fake_sleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr(api.asyncio, "sleep", fake_sleep)
    responses += [httpx.Response(429, headers={"Retry-After": "3"}, json={"message": "Whoa there!"}), httpx.Response(200, json={"ok": True})]
    assert _run(api.request("GET", "inventory", "equipamentos")) == {"ok": True}
    assert len(captured) == 2 and waits == [3.0]


def test_request_rate_limit_message_is_user_presentable(mock_transport, monkeypatch):
    captured, responses = mock_transport

    async def fake_sleep(seconds):
        pass

    monkeypatch.setattr(api.asyncio, "sleep", fake_sleep)
    responses += [httpx.Response(429, json={"message": "Whoa there!"}) for _ in range(api.RATE_LIMIT_RETRIES + 1)]
    with pytest.raises(api.ApiError) as exc:
        _run(api.request("GET", "inventory", "equipamentos"))
    assert exc.value.status == 429 and "Aguarde" in exc.value.message
    assert len(captured) == api.RATE_LIMIT_RETRIES + 1


def test_request_network_failure_is_user_presentable(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("boom")

    real_client = httpx.AsyncClient
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(api.ApiError) as exc:
        _run(api.request("GET", "inventory", "equipamentos"))
    assert exc.value.status == 0 and "servidor" in exc.value.message


# ------------------------------------------------------------------ guards e navegação (estático)
def test_permission_guard_never_redirects_to_a_guarded_page():
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    guard = state[state.index("async def _guard") : state.index("async def _fetch_all")]
    targets = set(re.findall(r'rx\.redirect\("([^"]+)"\)', guard))
    # /sem-acesso e /trocar-senha só exigem sessão, então redirecionar para lá não entra em loop
    assert targets == {"/login", "/sem-acesso", "/trocar-senha"}, targets


def test_no_access_page_requires_only_a_session():
    app = (ROOT / "hardware" / "hardware.py").read_text(encoding="utf-8")
    assert re.search(r'route="/sem-acesso".*on_load=AuthState\.require_login', app)
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    assert re.search(r"async def require_login\(self\):\s+return await self\._guard\(\)", state)


def test_every_nav_link_is_gated_by_its_page_permission():
    components = (ROOT / "hardware" / "components.py").read_text(encoding="utf-8")
    nav = re.findall(r'\("([^"]+)", "(/[^"]*)", "[^"]+", (None|"\w+")\)', components)
    assert nav and all(flag != "None" for _, _, flag in nav), nav
    # flag -> permissão que ela verifica
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    flag_perm = dict(re.findall(r"def (can_\w+)\(self\) -> bool:\s+return \"([\w.]+)\" in self\.permissions", state))
    pages = {
        "/": "dashboard.py",
        "/acompanhamento": "tracking.py",
        "/equipamentos": "equipment.py",
        "/manutencoes": "maintenance.py",
        "/ocorrencias": "occurrences.py",
        "/catalogos": "catalog.py",
        "/relatorios": "reports.py",
        "/usuarios": "users.py",
    }
    for _, route, flag in nav:
        src = (ROOT / "hardware" / "pages" / pages[route]).read_text(encoding="utf-8")
        guarded = re.findall(r'_guard\("([\w.]+)"\)', src)
        assert flag_perm[flag.strip('"')] in guarded, (route, flag, guarded)


def test_light_theme_is_the_default():
    rxconfig = (ROOT / "rxconfig.py").read_text(encoding="utf-8")
    assert 'default_color_mode="light"' in rxconfig
    # appearance fixo no tema raiz travaria o modo e anularia a alternância
    assert "appearance" not in rxconfig


def test_theme_toggle_switches_mode_with_portuguese_labels():
    from hardware.components import theme_toggle

    rendered = str(theme_toggle().render())
    assert "toggleColorMode" in rendered
    assert "Ativar tema escuro" in rendered and "Ativar tema claro" in rendered


def test_theme_toggle_is_in_sidebar_and_top_bar():
    components = (ROOT / "hardware" / "components.py").read_text(encoding="utf-8")
    body = components[components.index("def layout(") : components.index("def loading_overlay")]
    assert body.count("theme_toggle(") == 2


# ------------------------------------------------------------------ edição de catálogo: referências opcionais
def _optional_ref(edit_row: dict, form: dict, key: str, options: list[dict]):
    from types import SimpleNamespace

    from hardware.pages.catalog import CatalogState

    return CatalogState._optional_ref(SimpleNamespace(edit_row=edit_row), form, key, options)


ACTIVE = [{"value": "1", "label": "A"}, {"value": "2", "label": "B"}]


@pytest.mark.parametrize(
    "current,submitted,expected",
    [
        (1, "1", None),  # inalterado: não é enviado
        (1, "2", 2),  # trocado por outro registro ativo
        (1, "", 0),  # limpo de propósito: 0 = remover
        (None, "", None),  # nada antes, nada agora
        (None, "2", 2),  # definido agora
        (9, "", None),  # o atual está inativo (não é oferecido): NÃO pode ser removido sem aviso
    ],
)
def test_catalog_edit_optional_reference(current, submitted, expected):
    assert _optional_ref({"parent_id": current}, {"parent_id": submitted}, "parent_id", ACTIVE) == expected


def test_equipment_history_is_shown_oldest_first():
    src = (ROOT / "hardware" / "pages" / "equipment.py").read_text(encoding="utf-8")
    assert "reversed(" not in src and 'self.historico = hist.get("eventos", [])' in src


# ------------------------------------------------------------------ senha temporária no primeiro acesso
def test_temporary_password_routes_to_change_page_before_anything_else():
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    guard = state[state.index("async def _guard") : state.index("async def _fetch_all")]
    # a verificação de troca obrigatória vem antes da verificação de permissão
    assert guard.index("must_change_password") < guard.index("if permissions and")
    assert 'rx.redirect("/trocar-senha" if self.must_change_password else "/")' in state  # depois do login


def test_change_password_page_never_uses_the_guard():
    """A página precisa continuar acessível enquanto a troca de senha está pendente (sem loop de redirecionamento)."""
    src = (ROOT / "hardware" / "pages" / "change_password.py").read_text(encoding="utf-8")
    assert "_guard(" not in src and "require_login" not in src
    app = (ROOT / "hardware" / "hardware.py").read_text(encoding="utf-8")
    assert re.search(r'route="/trocar-senha".*on_load=ChangePasswordState\.on_load', app)


@pytest.mark.parametrize(
    "nova,ok",
    [("abcdefg1", True), ("abcdefgh", False), ("12345678", False), ("abc1", False)],
)
def test_change_password_client_policy_matches_api(nova, ok):
    """Mesma regra do filtro de entrada da API: mínimo de 8 caracteres, com pelo menos uma letra e um número."""
    valid = len(nova) >= 8 and any(c.isalpha() for c in nova) and any(c.isdigit() for c in nova)
    assert valid == ok
    src = (ROOT / "hardware" / "pages" / "change_password.py").read_text(encoding="utf-8")
    assert "len(nova) < 8 or not any(c.isalpha() for c in nova) or not any(c.isdigit() for c in nova)" in src
    api_src = (ROOT / "xano" / "api" / "authentication" / "auth" / "change_password_POST.xs").read_text(encoding="utf-8")
    assert "password nova_senha filters=min:8|minAlpha:1|minDigit:1" in api_src


# ------------------------------------------------------------------ links de redefinição nunca criam sessão
def test_reset_page_uses_single_step_confirm():
    src = (ROOT / "hardware" / "pages" / "login.py").read_text(encoding="utf-8")
    assert '"reset/confirm"' in src
    assert "magic-link-login" not in src and "update_password" not in src


@pytest.mark.parametrize("name", ["magic_link_login_POST.xs", "update_password_POST.xs"])
def test_session_based_reset_endpoints_are_disabled(name):
    xs = (ROOT / "xano" / "api" / "authentication" / "reset" / name).read_text(encoding="utf-8")
    stack = xs[xs.index("stack {") :]
    assert 'name = "accessdenied"' in stack
    assert "create_auth_token" not in xs and "db.edit" not in xs


def test_reset_confirm_creates_no_session():
    xs = (ROOT / "xano" / "api" / "authentication" / "reset" / "confirm_POST.xs").read_text(encoding="utf-8")
    assert "create_auth_token" not in xs
    assert "password nova_senha filters=min:8|minAlpha:1|minDigit:1" in xs
    assert "used: true" in xs  # uso único


# ------------------------------------------------------------------ um só fuso para entrada e exibição
def test_timestamps_display_in_institution_timezone():
    components = (ROOT / "hardware" / "components.py").read_text(encoding="utf-8")
    assert "rx.moment(value, format=fmt, tz=TZ_NAME)" in components
    # todas as outras páginas passam por timestamp_text/date_text, nunca rx.moment diretamente
    for page in (ROOT / "hardware" / "pages").glob("*.py"):
        assert "rx.moment(" not in page.read_text(encoding="utf-8"), page.name
    from hardware.options import TZ, TZ_NAME

    assert str(TZ) == TZ_NAME


def test_calendar_dates_are_never_timezone_converted():
    components = (ROOT / "hardware" / "components.py").read_text(encoding="utf-8")
    date_fn = components[components.index("def date_text") : components.index("def badge")]
    assert "tz=" not in date_fn
    equipment = (ROOT / "hardware" / "pages" / "equipment.py").read_text(encoding="utf-8")
    assert 'date_text(e["data_aquisicao"])' in equipment and 'date_text(e["proxima_manutencao"])' in equipment
    assert 'rx.cond(ev["somente_data"], date_text(ev["data_planejada"])' in equipment


# ------------------------------------------------------------------ acompanhamento: motivos da saúde
@pytest.mark.parametrize(
    "row,expected",
    [
        ({"status": "operational", "ocorrencias_abertas": 0, "preventivas_atrasadas": 0}, ""),
        ({"status": "out_of_service"}, "Fora de serviço"),
        (
            {"status": "under_maintenance", "ocorrencias_abertas": 2, "maior_severidade": "high", "preventivas_atrasadas": 1},
            "Em manutenção; 2 ocorrência(s) aberta(s), maior severidade alta; 1 preventiva(s) atrasada(s)",
        ),
    ],
)
def test_tracking_reasons(row, expected):
    from hardware.pages.tracking import reasons

    assert reasons(row) == expected


# ------------------------------------------------------------------ avisos: só o que é novo ou piorou
def test_alerts_only_new_or_changed_and_critical_first():
    from hardware.alerts import new_alerts, signature

    a = {"id": 1, "nome": "B", "saude": "atencao", "status": "operational", "preventivas_atrasadas": 1}
    b = {"id": 2, "nome": "A", "saude": "atencao", "status": "under_maintenance"}
    c = {"id": 3, "nome": "C", "saude": "critico", "status": "out_of_service"}
    # Primeira consulta: tudo é novo, críticos primeiro e depois por nome
    assert [r["id"] for r in new_alerts([a, b, c], {})] == [3, 2, 1]
    seen = {str(r["id"]): signature(r) for r in (a, b, c)}
    # Nada mudou: nenhum aviso
    assert new_alerts([a, b, c], seen) == []
    # Piorou (ocorrência crítica aberta): avisa de novo
    a2 = a | {"saude": "critico", "ocorrencias_abertas": 1, "maior_severidade": "critical"}
    assert [r["id"] for r in new_alerts([a2, b, c], seen)] == [1]
