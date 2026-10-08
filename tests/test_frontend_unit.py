"""Local unit tests for the frontend helpers and API client (no backend needed)."""

import asyncio
import json
import re
from pathlib import Path

import httpx
import pytest

from hardware import api
from hardware.options import TZ, local_to_ms, ms_to_local, now_local_input, opt_text, to_float, to_int

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ form value helpers
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
    # Handled after the first submit succeeded and bumped the key
    assert stale_submit({"_form_key": "3"}, 4)
    assert stale_submit({}, 0)


def test_now_local_vars_are_not_cached():
    """A cached dependency-free var is computed once, leaving the pre-filled time stale."""
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
    assert str(TZ)  # tzdata available (required on Windows)


# ------------------------------------------------------------------ API client
def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def mock_transport(monkeypatch):
    """Route api.request through an httpx.MockTransport; returns the list of captured requests."""
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


# ------------------------------------------------------------------ guards and navigation (static)
def test_permission_guard_never_redirects_to_a_guarded_page():
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    guard = state[state.index("async def _guard") : state.index("async def _fetch_all")]
    targets = set(re.findall(r'rx\.redirect\("([^"]+)"\)', guard))
    # /sem-acesso and /trocar-senha require only a session, so redirecting there cannot loop
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
    # flag -> permission it checks
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    flag_perm = dict(re.findall(r"def (can_\w+)\(self\) -> bool:\s+return \"([\w.]+)\" in self\.permissions", state))
    pages = {
        "/": "dashboard.py",
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


# ------------------------------------------------------------------ catalog edit: optional references
def _optional_ref(edit_row: dict, form: dict, key: str, options: list[dict]):
    from types import SimpleNamespace

    from hardware.pages.catalog import CatalogState

    return CatalogState._optional_ref(SimpleNamespace(edit_row=edit_row), form, key, options)


ACTIVE = [{"value": "1", "label": "A"}, {"value": "2", "label": "B"}]


@pytest.mark.parametrize(
    "current,submitted,expected",
    [
        (1, "1", None),  # unchanged: not sent
        (1, "2", 2),  # changed to another active record
        (1, "", 0),  # cleared on purpose: 0 = remove
        (None, "", None),  # nothing before, nothing now
        (None, "2", 2),  # newly set
        (9, "", None),  # current is inactive (not offered): must NOT be silently removed
    ],
)
def test_catalog_edit_optional_reference(current, submitted, expected):
    assert _optional_ref({"parent_id": current}, {"parent_id": submitted}, "parent_id", ACTIVE) == expected


def test_equipment_history_is_shown_oldest_first():
    src = (ROOT / "hardware" / "pages" / "equipment.py").read_text(encoding="utf-8")
    assert "reversed(" not in src and 'self.historico = hist.get("eventos", [])' in src


# ------------------------------------------------------------------ temporary password on first login
def test_temporary_password_routes_to_change_page_before_anything_else():
    state = (ROOT / "hardware" / "state.py").read_text(encoding="utf-8")
    guard = state[state.index("async def _guard") : state.index("async def _fetch_all")]
    # the must-change check comes before the permission check
    assert guard.index("must_change_password") < guard.index("if permissions and")
    assert 'rx.redirect("/trocar-senha" if self.must_change_password else "/")' in state  # after login


def test_change_password_page_never_uses_the_guard():
    """The page must stay reachable while the password change is pending (no redirect loop)."""
    src = (ROOT / "hardware" / "pages" / "change_password.py").read_text(encoding="utf-8")
    assert "_guard(" not in src and "require_login" not in src
    app = (ROOT / "hardware" / "hardware.py").read_text(encoding="utf-8")
    assert re.search(r'route="/trocar-senha".*on_load=ChangePasswordState\.on_load', app)


@pytest.mark.parametrize(
    "nova,ok",
    [("abcdefg1", True), ("abcdefgh", False), ("12345678", False), ("abc1", False)],
)
def test_change_password_client_policy_matches_api(nova, ok):
    """Same rule as the API input filter: min 8 chars, at least one letter and one digit."""
    valid = len(nova) >= 8 and any(c.isalpha() for c in nova) and any(c.isdigit() for c in nova)
    assert valid == ok
    src = (ROOT / "hardware" / "pages" / "change_password.py").read_text(encoding="utf-8")
    assert "len(nova) < 8 or not any(c.isalpha() for c in nova) or not any(c.isdigit() for c in nova)" in src
    api_src = (ROOT / "xano" / "api" / "authentication" / "auth" / "change_password_POST.xs").read_text(encoding="utf-8")
    assert "password nova_senha filters=min:8|minAlpha:1|minDigit:1" in api_src


# ------------------------------------------------------------------ reset links never create sessions
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
    assert "used: true" in xs  # single use


# ------------------------------------------------------------------ one timezone for entry and display
def test_timestamps_display_in_institution_timezone():
    components = (ROOT / "hardware" / "components.py").read_text(encoding="utf-8")
    assert "rx.moment(value, format=fmt, tz=TZ_NAME)" in components
    # every other page goes through timestamp_text/date_text, never rx.moment directly
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
