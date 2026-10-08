"""Testes de integração da API entre funcionalidades (tarefa 6.3): integridade referencial, aplicação de perfis,
cobertura da auditoria, cálculos de manutenção/histórico e consistência entre painel e relatórios.

Roda contra um backend publicado (depois de setup/seed_reference_data e setup/migrate_users):

    HHM_TEST_ADMIN_EMAIL=... HHM_TEST_ADMIN_PASSWORD=... [XANO_BASE_URL=...] pytest tests/test_api_integration.py

A suíte cria as próprias contas por perfil e registros de teste, marcados com um id único por execução. O sistema
nunca apaga registros operacionais de vez, então os dados de teste permanecem depois (desativados/descomissionados
quando possível). Rode em um ambiente de teste, não na instituição em produção.
É pulada por completo quando as credenciais de administrador não estão definidas.
"""

import csv
import datetime as dt
import io
import os
import uuid

import httpx
import pytest

ADMIN_EMAIL = os.environ.get("HHM_TEST_ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("HHM_TEST_ADMIN_PASSWORD")

pytestmark = pytest.mark.skipif(not (ADMIN_EMAIL and ADMIN_PASSWORD), reason="HHM_TEST_ADMIN_EMAIL/PASSWORD not set")

BASE = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")
GROUPS = {
    "auth": os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc"),
    "users": os.environ.get("XANO_USERS_GROUP", "hhm149197-users"),
    "inventory": os.environ.get("XANO_INVENTORY_GROUP", "hhm149197-inventory"),
    "maintenance": os.environ.get("XANO_MAINTENANCE_GROUP", "hhm149197-maintenance"),
    "reports": os.environ.get("XANO_REPORTS_GROUP", "hhm149197-reports"),
}
RUN = uuid.uuid4().hex[:8]
PASSWORD = f"Teste{RUN}9"  # senha temporária definida pelo administrador
FINAL_PASSWORD = f"Pessoal{RUN}7"  # escolhida pelo usuário no primeiro acesso
TODAY = dt.date.today()


class Client:
    def __init__(self, token: str = ""):
        self.token = token

    def req(self, method, group, path, **kwargs) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        return httpx.request(method, f"{BASE}/api:{GROUPS[group]}/{path}", headers=headers, timeout=30, **kwargs)

    def ok(self, method, group, path, **kwargs):
        r = self.req(method, group, path, **kwargs)
        assert r.status_code < 400, f"{method} {path} -> {r.status_code} {r.text}"
        return r.json() if r.content else None


def login(email: str, password: str) -> Client:
    r = httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, r.text
    return Client(r.json()["authToken"])


def activate(email: str) -> Client:
    """Primeiro acesso de uma conta criada pelo administrador: troca a senha temporária."""
    client = login(email, PASSWORD)
    client.ok("POST", "auth", "auth/change_password", json={"senha_atual": PASSWORD, "nova_senha": FINAL_PASSWORD, "confirmar_senha": FINAL_PASSWORD})
    return client


# ------------------------------------------------------------------ dados de teste
@pytest.fixture(scope="module")
def admin() -> Client:
    return login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def roles(admin) -> dict[str, int]:
    data = admin.ok("GET", "users", "roles")
    return {r["nome"]: r["id"] for r in data["roles"]}


@pytest.fixture(scope="module")
def accounts(admin, roles) -> dict[str, dict]:
    """Uma conta habilitada para cada perfil que não é administrador, já logada."""
    out = {}
    for role in ("viewer", "technician", "asset_manager"):
        email = f"teste.{role}.{RUN}@example.org"
        user = admin.ok("POST", "users", "users", json={"name": f"Teste {role} {RUN}", "email": email, "password": PASSWORD, "role_id": roles[role]})
        out[role] = {"id": user["id"], "email": email, "client": activate(email)}
    return out


@pytest.fixture(scope="module")
def base(admin) -> dict:
    """Fabricante, categoria, modelo, duas localizações (uma inativa) e um componente."""
    fab = admin.ok("POST", "inventory", "fabricantes", json={"nome": f"Fab {RUN}"})
    cats = admin.ok("GET", "inventory", "categorias")
    cat = next(c for c in cats if c["nome"] == "ultrassom")
    modelo = admin.ok("POST", "inventory", "modelos", json={"nome": f"Modelo {RUN}", "fabricante_id": fab["id"], "categoria_id": cat["id"]})
    loc = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Sala {RUN}"})
    loc2 = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Sala B {RUN}"})
    loc_inativa = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Sala inativa {RUN}"})
    admin.ok("PATCH", "inventory", f"localizacoes/{loc_inativa['id']}", json={"ativo": False})
    comp = admin.ok("POST", "inventory", "componentes", json={"nome": f"Bateria {RUN}", "tipo": "battery"})
    return {"fab": fab, "cat": cat, "modelo": modelo, "loc": loc, "loc2": loc2, "loc_inativa": loc_inativa, "comp": comp}


def new_equipment(client: Client, base: dict, suffix: str, **extra) -> dict:
    payload = {
        "nome": f"Equip {suffix} {RUN}",
        "numero_patrimonio": f"PAT-{RUN}-{suffix}",
        "modelo_id": base["modelo"]["id"],
        "localizacao_id": base["loc"]["id"],
        "status": "operational",
    } | extra
    return client.ok("POST", "inventory", "equipamentos", json=payload)


def audit_events(admin: Client, entidade: str, registro_id: int) -> list[dict]:
    return admin.ok("GET", "reports", "auditoria", params={"entidade": entidade, "registro_id": registro_id})["items"]


# ------------------------------------------------------------------ acesso
def test_public_signup_is_disabled():
    r = httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/signup", json={"name": "x", "email": f"x{RUN}@example.org", "password": PASSWORD}, timeout=30)
    assert r.status_code == 403


@pytest.mark.parametrize(
    "group,path",
    [("inventory", "equipamentos"), ("inventory", "modelos"), ("maintenance", "manutencoes"), ("maintenance", "ocorrencias"), ("reports", "dashboard"), ("users", "users")],
)
def test_unauthenticated_requests_are_denied(group, path):
    r = Client().req("GET", group, path)
    assert r.status_code == 401
    assert "items" not in r.text


def test_viewer_is_read_only(admin, accounts, base):
    viewer = accounts["viewer"]["client"]
    equip = new_equipment(admin, base, "V")
    before = admin.ok("GET", "inventory", f"equipamentos/{equip['id']}")
    attempts = [
        ("POST", "inventory", "equipamentos", {"nome": "x", "numero_patrimonio": f"PAT-{RUN}-VX", "modelo_id": base["modelo"]["id"], "localizacao_id": base["loc"]["id"]}),
        ("PATCH", "inventory", f"equipamentos/{equip['id']}", {"nome": "alterado"}),
        ("POST", "inventory", f"equipamentos/{equip['id']}/status", {"status": "out_of_service", "motivo": "x"}),
        ("POST", "inventory", "fabricantes", {"nome": f"Fab viewer {RUN}"}),
        ("PATCH", "inventory", f"fabricantes/{base['fab']['id']}", {"ativo": False}),
        ("POST", "maintenance", "manutencoes", {"equipamento_id": equip["id"], "tipo": "preventive", "data_planejada": str(TODAY), "descricao": "x", "responsavel_id": accounts["viewer"]["id"]}),
        ("POST", "maintenance", "ocorrencias", {"equipamento_id": equip["id"], "descricao_tecnica": "x", "severidade": "low"}),
        ("POST", "users", "users", {"name": "x", "email": f"y{RUN}@example.org", "password": PASSWORD, "role_id": 1}),
    ]
    for method, group, path, body in attempts:
        r = viewer.req(method, group, path, json=body)
        assert r.status_code == 403, f"{method} {path} -> {r.status_code}"
    after = admin.ok("GET", "inventory", f"equipamentos/{equip['id']}")
    assert after["nome"] == before["nome"] and after["status"] == before["status"]
    assert viewer.req("GET", "reports", "auditoria").status_code == 403


def test_admin_role_change_and_disable_apply_immediately(admin, roles, accounts):
    acc = accounts["viewer"]
    me = acc["client"].ok("GET", "auth", "auth/me")
    assert "inventory.manage" not in me["permissions"]
    admin.ok("PATCH", "users", f"users/{acc['id']}", json={"role_id": roles["asset_manager"]})
    assert "inventory.manage" in acc["client"].ok("GET", "auth", "auth/me")["permissions"]
    admin.ok("PATCH", "users", f"users/{acc['id']}", json={"role_id": roles["viewer"]})
    assert any(e["action"] == "user.updated" for e in audit_events(admin, "user", acc["id"]))

    # Desabilitado: o token existente para de funcionar e o login é recusado
    email = f"teste.disable.{RUN}@example.org"
    user = admin.ok("POST", "users", "users", json={"name": "Desabilitar", "email": email, "password": PASSWORD, "role_id": roles["viewer"]})
    client = activate(email)
    assert client.req("GET", "inventory", "equipamentos").status_code == 200  # funciona antes de desabilitar
    admin.ok("PATCH", "users", f"users/{user['id']}", json={"ativo": False})
    assert client.req("GET", "inventory", "equipamentos").status_code == 403
    r = httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": email, "password": FINAL_PASSWORD}, timeout=30)
    assert r.status_code == 403


# ------------------------------------------------------------------ catálogos e integridade
def test_model_requires_existing_active_references(admin, base):
    r = admin.req("POST", "inventory", "modelos", json={"nome": f"M ruim {RUN}", "fabricante_id": 999999999, "categoria_id": base["cat"]["id"]})
    assert r.status_code == 400 and "fabricante_id" in r.text
    fab = admin.ok("POST", "inventory", "fabricantes", json={"nome": f"Fab inativo {RUN}"})
    admin.ok("PATCH", "inventory", f"fabricantes/{fab['id']}", json={"ativo": False})
    r = admin.req("POST", "inventory", "modelos", json={"nome": f"M inativo {RUN}", "fabricante_id": fab["id"], "categoria_id": base["cat"]["id"]})
    assert r.status_code == 400
    r = admin.req("POST", "inventory", "modelos", json={"nome": base["modelo"]["nome"], "fabricante_id": base["fab"]["id"], "categoria_id": base["cat"]["id"]})
    assert r.status_code == 400, "duplicate (manufacturer, category, name) must be rejected"


def test_equipment_validation_and_derived_catalog(admin, base):
    e = new_equipment(admin, base, "A", numero_serie="  ")
    assert e["fabricante_id"] == base["fab"]["id"] and e["categoria_id"] == base["cat"]["id"]
    assert e["numero_serie"] is None, "blank serial must be stored as null"
    new_equipment(admin, base, "A2", numero_serie="")  # uma segunda série em branco é permitida
    s1 = new_equipment(admin, base, "S1", numero_serie=f"SER-{RUN}")
    cases = [
        {"numero_patrimonio": e["numero_patrimonio"]},  # patrimônio duplicado
        {"numero_serie": f"SER-{RUN}"},  # série duplicada
        {"categoria_id": base["cat"]["id"] + 1000},  # categoria conflitante
        {"modelo_id": 999999999},  # modelo inexistente
        {"localizacao_id": base["loc_inativa"]["id"]},  # localização inativa
        {"data_aquisicao": str(TODAY + dt.timedelta(days=2))},  # aquisição no futuro
        {"valor_aquisicao": -1},
        {"vida_util_anos": 0},
        {"ano_fabricacao": TODAY.year + 1},
    ]
    for i, extra in enumerate(cases):
        r = admin.req("POST", "inventory", "equipamentos", json={"nome": "x", "numero_patrimonio": f"PAT-{RUN}-BAD{i}", "modelo_id": base["modelo"]["id"], "localizacao_id": base["loc"]["id"]} | extra)
        assert r.status_code == 400, f"case {extra} -> {r.status_code}"
    still = admin.ok("GET", "inventory", f"equipamentos/{s1['id']}")
    assert still["numero_serie"] == f"SER-{RUN}"


def test_move_status_decommission_are_audited_and_history_kept(admin, base):
    e = new_equipment(admin, base, "M")
    r = admin.req("POST", "inventory", f"equipamentos/{e['id']}/mover", json={"localizacao_id": base["loc_inativa"]["id"]})
    assert r.status_code == 400
    admin.ok("POST", "inventory", f"equipamentos/{e['id']}/mover", json={"localizacao_id": base["loc2"]["id"]})
    admin.ok("POST", "inventory", f"equipamentos/{e['id']}/status", json={"status": "under_maintenance"})
    events = audit_events(admin, "equipamentos", e["id"])
    status_ev = next(ev for ev in events if ev["action"] == "equipamento.status_changed")
    assert status_ev["metadata"]["antes"]["status"] == "operational"
    assert status_ev["metadata"]["depois"]["status"] == "under_maintenance"
    assert status_ev["user_id"] and status_ev["created_at"]
    assert any(ev["action"] == "equipamento.moved" for ev in events)

    occ = admin.ok("POST", "maintenance", "ocorrencias", json={"equipamento_id": e["id"], "descricao_tecnica": "Tela não liga", "severidade": "high"})
    assert admin.req("POST", "inventory", f"equipamentos/{e['id']}/status", json={"status": "decommissioned"}).status_code == 400  # motivo obrigatório
    admin.ok("POST", "inventory", f"equipamentos/{e['id']}/status", json={"status": "decommissioned", "motivo": "Fim de vida útil"})
    listed = admin.ok("GET", "inventory", "equipamentos", params={"q": e["numero_patrimonio"]})["items"]
    assert not listed, "decommissioned equipment must be hidden from active lists by default"
    hist = admin.ok("GET", "maintenance", f"equipamentos/{e['id']}/historico")
    assert any(ev["categoria"] == "ocorrencia" and ev["registro_id"] == occ["id"] for ev in hist["eventos"])


def test_component_assignment_rules_and_history(admin, base):
    e = new_equipment(admin, base, "C")
    path = f"equipamentos/{e['id']}/componentes"
    assert admin.req("POST", "inventory", path, json={"componente_id": base["comp"]["id"], "quantidade": 0}).status_code == 400
    assert admin.req("POST", "inventory", path, json={"componente_id": 999999999, "quantidade": 1}).status_code == 400
    a1 = admin.ok("POST", "inventory", path, json={"componente_id": base["comp"]["id"], "quantidade": 1, "slot": "A"})
    admin.ok("POST", "inventory", path, json={"componente_id": base["comp"]["id"], "quantidade": 2, "slot": "B"})
    admin.ok("POST", "inventory", f"{path}/{a1['id']}/remover", json={})
    detail = admin.ok("GET", "inventory", f"equipamentos/{e['id']}")
    assert [c["slot"] for c in detail["componentes_instalados"]] == ["B"]
    assert [c["slot"] for c in detail["componentes_removidos"]] == ["A"]
    assert detail["componentes_removidos"][0]["removido_em"]
    hist = admin.ok("GET", "maintenance", f"equipamentos/{e['id']}/historico")["eventos"]
    assert {"componente_instalado", "componente_removido"} <= {ev["categoria"] for ev in hist}


# ------------------------------------------------------------------ manutenções e ocorrências
def test_preventive_schedule_due_views_and_derived_dates(admin, accounts, base):
    tech = accounts["technician"]
    e = new_equipment(admin, base, "P")
    mk = lambda days, desc: admin.ok(  # noqa: E731
        "POST",
        "maintenance",
        "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY + dt.timedelta(days=days)), "descricao": desc, "responsavel_id": tech["id"], "intervalo_recorrencia_dias": 90},
    )
    overdue = mk(-5, "atrasada")
    future_far = mk(40, "futura distante")
    future_near = mk(10, "futura próxima")
    to_cancel = mk(20, "cancelar")

    ids = lambda params: {m["id"] for m in admin.ok("GET", "maintenance", "manutencoes", params=params | {"equipamento_id": e["id"]})["items"]}  # noqa: E731
    assert ids({"situacao": "overdue"}) == {overdue["id"]}
    assert ids({"situacao": "upcoming"}) == {future_far["id"], future_near["id"], to_cancel["id"]}

    detail = admin.ok("GET", "inventory", f"equipamentos/{e['id']}")
    assert detail["ultima_manutencao"] is None
    assert detail["proxima_manutencao"] == future_near["data_planejada"]

    # Conclusão/cancelamento incompleto é recusado e o estado é mantido
    t = tech["client"]
    assert t.req("POST", "maintenance", f"manutencoes/{overdue['id']}/concluir", json={"concluida_em": int(dt.datetime.now().timestamp() * 1000), "resumo_execucao": ""}).status_code == 400
    assert t.req("POST", "maintenance", f"manutencoes/{to_cancel['id']}/cancelar", json={"motivo_cancelamento": ""}).status_code == 400
    assert ids({"status": "planned"}) >= {overdue["id"], to_cancel["id"]}

    done_at = int((dt.datetime.now() - dt.timedelta(hours=1)).timestamp() * 1000)
    done = t.ok("POST", "maintenance", f"manutencoes/{overdue['id']}/concluir", json={"concluida_em": done_at, "resumo_execucao": "Troca de filtro e calibração"})
    assert done["status"] == "completed" and done["proxima_data_sugerida"]
    t.ok("POST", "maintenance", f"manutencoes/{to_cancel['id']}/cancelar", json={"motivo_cancelamento": "Equipamento indisponível"})
    assert to_cancel["id"] not in ids({"situacao": "upcoming"}) and overdue["id"] not in ids({"situacao": "overdue"})

    detail = admin.ok("GET", "inventory", f"equipamentos/{e['id']}")
    assert detail["ultima_manutencao"] == done_at
    hist = admin.ok("GET", "maintenance", f"equipamentos/{e['id']}/historico")["eventos"]
    statuses = {ev["registro_id"]: ev["status"] for ev in hist if ev["categoria"] == "manutencao"}
    assert statuses[overdue["id"]] == "completed" and statuses[to_cancel["id"]] == "canceled"
    dates = [ev["data"] for ev in hist]
    assert dates == sorted(dates), "history must be chronological"
    assert any(ev["action"] == "manutencao.completed" for ev in audit_events(admin, "manutencoes", overdue["id"]))


def test_technician_only_works_on_assigned_maintenance(admin, accounts, base):
    e = new_equipment(admin, base, "T")
    other = admin.ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY), "descricao": "de outro", "responsavel_id": accounts["asset_manager"]["id"]},
    )
    r = accounts["technician"]["client"].req("POST", "maintenance", f"manutencoes/{other['id']}/cancelar", json={"motivo_cancelamento": "x"})
    assert r.status_code == 403
    assert admin.ok("GET", "maintenance", "manutencoes", params={"equipamento_id": e["id"]})["items"][0]["status"] == "planned"


def test_occurrence_lifecycle_and_corrective_link(admin, accounts, base):
    tech = accounts["technician"]
    e = new_equipment(admin, base, "O")
    assert tech["client"].req("POST", "maintenance", "ocorrencias", json={"equipamento_id": e["id"], "descricao_tecnica": "", "severidade": "low"}).status_code == 400
    occ = tech["client"].ok("POST", "maintenance", "ocorrencias", json={"equipamento_id": e["id"], "descricao_tecnica": "Alarme de bateria intermitente", "severidade": "medium"})
    assert occ["status"] == "open" and occ["relatada_por"] == tech["id"]

    admin.ok("PATCH", "maintenance", f"ocorrencias/{occ['id']}", json={"responsavel_id": tech["id"]})
    corr = tech["client"].ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "corrective", "data_planejada": str(TODAY), "descricao": "Substituir bateria", "responsavel_id": tech["id"], "ocorrencia_id": occ["id"]},
    )
    path = f"ocorrencias/{occ['id']}/transicao"
    assert tech["client"].req("POST", "maintenance", path, json={"acao": "resolver", "resumo_resolucao": "ok"}).status_code == 400
    assert admin.ok("GET", "maintenance", f"ocorrencias/{occ['id']}")["status"] == "open"
    tech["client"].ok("POST", "maintenance", path, json={"acao": "resolver", "resolvida_em": int(dt.datetime.now().timestamp() * 1000), "resumo_resolucao": "Bateria substituída"})
    detail = admin.ok("GET", "maintenance", f"ocorrencias/{occ['id']}")
    assert detail["status"] == "resolved" and detail["resumo_resolucao"]
    assert [m["id"] for m in detail["manutencoes"]] == [corr["id"]]
    hist = admin.ok("GET", "maintenance", f"equipamentos/{e['id']}/historico")["eventos"]
    assert any(ev["categoria"] == "ocorrencia" and ev["status"] == "resolved" for ev in hist)


# ------------------------------------------------------------------ painel e relatórios
def test_dashboard_totals_match_fixture_for_location_filter(admin, base):
    loc = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Sala dashboard {RUN}"})
    for i, status in enumerate(["operational", "operational", "out_of_service"]):
        extra = {"motivo": "Aguardando peça"} if status == "out_of_service" else {}
        new_equipment(admin, base, f"D{i}", localizacao_id=loc["id"], status=status, **extra)
    occ_equip = new_equipment(admin, base, "D9", localizacao_id=loc["id"])
    admin.ok("POST", "maintenance", "ocorrencias", json={"equipamento_id": occ_equip["id"], "descricao_tecnica": "Ruído no motor", "severidade": "critical"})
    d = admin.ok("GET", "reports", "dashboard", params={"localizacao_id": loc["id"]})
    assert d["por_status"] == {"operational": 3, "under_maintenance": 0, "out_of_service": 1, "decommissioned": 0}
    assert d["equipamentos_ativos"] == 4
    assert {c["categoria"]: c["total"] for c in d["por_categoria"]}["ultrassom"] == 4
    assert d["ocorrencias_abertas"]["por_severidade"]["critical"] == {"open": 1, "in_progress": 0}
    assert d["ocorrencias_abertas"]["por_status"] == {"open": 1, "in_progress": 0}
    assert d["ocorrencias_abertas"]["total"] == 1


def test_csv_export_matches_on_screen_filters(admin, accounts, base):
    params = {"localizacao_id": base["loc"]["id"], "status": "operational"}
    on_screen = admin.ok("GET", "reports", "relatorios/inventario", params=params | {"per_page": 200})
    r = accounts["viewer"]["client"].req("GET", "reports", "relatorios/inventario", params=params | {"formato": "csv"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(r.text.lstrip("\ufeff"))))
    header, data = rows[0], rows[1:]
    assert len(data) == on_screen["itemsTotal"]
    col = header.index("Número de patrimônio")
    assert {row[col] for row in data} == {row["numero_patrimonio"] for row in on_screen["items"]}


def test_overdue_maintenance_report(admin, accounts, base):
    e = new_equipment(admin, base, "R")
    m = admin.ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY - dt.timedelta(days=3)), "descricao": "atrasada", "responsavel_id": accounts["technician"]["id"]},
    )
    params = {"situacao": "overdue", "tipo": "preventive", "de": str(TODAY - dt.timedelta(days=7)), "ate": str(TODAY)}
    rows = admin.ok("GET", "reports", "relatorios/manutencoes", params=params | {"per_page": 200})["items"]
    row = next(r for r in rows if r["id"] == m["id"])
    assert row["status"] == "planned" and row["equipamento"] and row["localizacao"]
    assert all(r["status"] == "planned" and r["data_planejada"] < str(TODAY) for r in rows)


# ------------------------------------------------------------------ seed, migração, recuperação (tarefas 1.3, 1.4, 2.1)
MATRIX = {
    "administrator": {"operational.read", "inventory.manage", "maintenance.manage", "occurrence.report", "occurrence.manage", "reports.read", "audit.read", "users.manage"},
    "asset_manager": {"operational.read", "inventory.manage", "maintenance.manage", "occurrence.report", "occurrence.manage", "reports.read"},
    "technician": {"operational.read", "maintenance.manage_assigned", "occurrence.report", "occurrence.manage_assigned", "reports.read"},
    "viewer": {"operational.read", "reports.read"},
}
CATEGORIES = [
    "monitor multiparamétrico", "ventilador pulmonar", "bomba de infusão", "desfibrilador", "eletrocardiógrafo",
    "máquina de anestesia", "ultrassom", "raio-X", "tomógrafo", "ressonância magnética", "oxímetro", "aspirador hospitalar",
]


def test_seed_reference_data_matches_approved_matrix(admin):
    data = admin.ok("GET", "users", "roles")
    names = [r["nome"] for r in data["roles"]]
    for role, expected in MATRIX.items():
        assert names.count(role) == 1, role
        granted = set(next(r for r in data["roles"] if r["nome"] == role)["permissions"])
        assert granted == expected, (role, granted ^ expected)
    keys = [p["chave"] for p in data["permissions"]]
    assert len(keys) == len(set(keys)) and set().union(*MATRIX.values()) <= set(keys)
    cats = [c["nome"] for c in admin.ok("GET", "inventory", "categorias", params={"include_inactive": True})]
    for name in CATEGORIES:
        assert cats.count(name) == 1, name


def test_migration_left_every_account_with_role_and_state(admin):
    page, users = 1, []
    while True:
        result = admin.ok("GET", "users", "users", params={"page": page, "per_page": 100})
        users += result["items"]
        if result.get("nextPage") is None:
            break
        page += 1
    assert users
    assert [u["email"] for u in users if u["role_id"] is None] == []
    assert [u["email"] for u in users if u["ativo"] is None] == []


def test_disabled_account_cannot_recover_access(admin, roles):
    email = f"teste.recover.{RUN}@example.org"
    user = admin.ok("POST", "users", "users", json={"name": "Recuperar", "email": email, "password": PASSWORD, "role_id": roles["viewer"]})
    admin.ok("PATCH", "users", f"users/{user['id']}", json={"ativo": False})
    auth = Client()
    disabled = auth.req("GET", "auth", "reset/request-reset-link", params={"email": email})
    unknown = auth.req("GET", "auth", "reset/request-reset-link", params={"email": f"ninguem.{RUN}@example.org"})
    assert disabled.status_code == unknown.status_code == 200
    assert disabled.json() == unknown.json(), "response must not reveal whether the account exists or is enabled"
    r = auth.req(
        "POST", "auth", "reset/confirm",
        json={"magic_token": "x", "email": email, "nova_senha": "Nova12345x", "confirmar_senha": "Nova12345x"},
    )
    assert r.status_code == 403


# ------------------------------------------------------------------ cobertura da auditoria (tarefa 2.3)
def test_audit_covers_catalog_component_and_permission_changes(admin, base):
    fab = admin.ok("POST", "inventory", "fabricantes", json={"nome": f"Fab audit {RUN}"})
    admin.ok("PATCH", "inventory", f"fabricantes/{fab['id']}", json={"site": "https://example.org"})
    events = {e["action"]: e for e in audit_events(admin, "fabricantes", fab["id"])}
    assert {"fabricante.created", "fabricante.updated"} <= set(events)
    upd = events["fabricante.updated"]
    assert upd["user_id"] and upd["created_at"]
    assert upd["metadata"]["antes"]["site"] is None and upd["metadata"]["depois"]["site"]

    e = new_equipment(admin, base, "AU")
    inst = admin.ok("POST", "inventory", f"equipamentos/{e['id']}/componentes", json={"componente_id": base["comp"]["id"], "quantidade": 1})
    assert any(ev["action"] == "componente.installed" for ev in audit_events(admin, "equipamento_componentes", inst["id"]))

    role = admin.ok("POST", "users", "roles", json={"nome": f"auditoria_{RUN}"})
    perm = next(p for p in admin.ok("GET", "users", "roles")["permissions"] if p["chave"] == "reports.read")
    admin.ok("POST", "users", f"roles/{role['id']}/permissions", json={"permission_id": perm["id"]})
    admin.ok("DELETE", "users", f"roles/{role['id']}/permissions/{perm['id']}")
    actions = {ev["action"] for ev in audit_events(admin, "roles", role["id"])}
    assert {"role.created", "role.permission_granted", "role.permission_revoked"} <= actions


def test_unfiltered_audit_view_lists_recent_events(admin):
    """Sem filtros, a tela deve listar todo evento recente (antes ela escondia eventos sem metadata)."""
    fab = admin.ok("POST", "inventory", "fabricantes", json={"nome": f"Fab audit view {RUN}"})
    login(ADMIN_EMAIL, ADMIN_PASSWORD)  # grava um evento "login"
    newest = admin.ok("GET", "reports", "auditoria", params={"per_page": 10})["items"]
    actions = [ev["action"] for ev in newest]
    assert "login" in actions, actions
    assert any(ev["action"] == "fabricante.created" and (ev["metadata"] or {}).get("registro_id") == fab["id"] for ev in newest)
    assert [ev["created_at"] for ev in newest] == sorted((ev["created_at"] for ev in newest), reverse=True)


# ------------------------------------------------------------------ perfis (design: gestão de perfis e permissões)
def test_role_deactivation_guards(admin, roles, accounts):
    assert admin.req("PATCH", "users", f"roles/{roles['administrator']}", json={"ativo": False}).status_code == 400
    assert admin.req("PATCH", "users", f"roles/{roles['technician']}", json={"ativo": False}).status_code == 400  # tem usuários habilitados
    empty = admin.ok("POST", "users", "roles", json={"nome": f"vazio_{RUN}"})
    assert admin.ok("PATCH", "users", f"roles/{empty['id']}", json={"ativo": False})["ativo"] is False
    assert accounts["viewer"]["client"].req("POST", "users", "roles", json={"nome": f"x_{RUN}"}).status_code == 403


# ------------------------------------------------------------------ atribuição e limites do técnico
def test_assignee_must_be_able_to_work_on_the_area(admin, accounts, base):
    e = new_equipment(admin, base, "AS")
    r = admin.req(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY), "descricao": "x", "responsavel_id": accounts["viewer"]["id"]},
    )
    assert r.status_code == 400 and "responsavel_id" in r.text
    occ = admin.ok("POST", "maintenance", "ocorrencias", json={"equipamento_id": e["id"], "descricao_tecnica": "Falha no display", "severidade": "low"})
    assert admin.req("PATCH", "maintenance", f"ocorrencias/{occ['id']}", json={"responsavel_id": accounts["viewer"]["id"]}).status_code == 400
    listed = {u["id"] for u in admin.ok("GET", "maintenance", "responsaveis", params={"area": "maintenance"})}
    assert accounts["technician"]["id"] in listed and accounts["viewer"]["id"] not in listed


def test_technician_occurrence_limits(admin, accounts, base):
    tech = accounts["technician"]["client"]
    e = new_equipment(admin, base, "TO")
    occ = admin.ok("POST", "maintenance", "ocorrencias", json={"equipamento_id": e["id"], "descricao_tecnica": "Bip contínuo", "severidade": "medium"})
    assert tech.req("PATCH", "maintenance", f"ocorrencias/{occ['id']}", json={"responsavel_id": accounts["technician"]["id"]}).status_code == 403
    path = f"ocorrencias/{occ['id']}/transicao"
    assert tech.req("POST", "maintenance", path, json={"acao": "cancelar", "motivo_cancelamento": "x"}).status_code == 403
    assert admin.ok("GET", "maintenance", f"ocorrencias/{occ['id']}")["status"] == "open"


# ------------------------------------------------------------------ regras de status do equipamento
def test_initial_status_rules(admin, base):
    payload = {"nome": "x", "modelo_id": base["modelo"]["id"], "localizacao_id": base["loc"]["id"]}
    r = admin.req("POST", "inventory", "equipamentos", json=payload | {"numero_patrimonio": f"PAT-{RUN}-IS1", "status": "decommissioned"})
    assert r.status_code == 400
    r = admin.req("POST", "inventory", "equipamentos", json=payload | {"numero_patrimonio": f"PAT-{RUN}-IS2", "status": "out_of_service"})
    assert r.status_code == 400 and "motivo" in r.text
    e = new_equipment(admin, base, "IS3", status="out_of_service", motivo="Aguardando calibração")
    created = next(ev for ev in audit_events(admin, "equipamentos", e["id"]) if ev["action"] == "equipamento.created")
    assert created["metadata"]["depois"]["motivo"] == "Aguardando calibração"


def test_decommissioned_equipment_is_read_only(admin, base):
    e = new_equipment(admin, base, "RO")
    inst = admin.ok("POST", "inventory", f"equipamentos/{e['id']}/componentes", json={"componente_id": base["comp"]["id"], "quantidade": 1})
    admin.ok("POST", "inventory", f"equipamentos/{e['id']}/status", json={"status": "decommissioned", "motivo": "Substituído"})
    assert admin.req("PATCH", "inventory", f"equipamentos/{e['id']}", json={"nome": "novo nome"}).status_code == 400
    assert admin.req("POST", "inventory", f"equipamentos/{e['id']}/componentes/{inst['id']}/remover", json={}).status_code == 400
    assert admin.req("POST", "inventory", f"equipamentos/{e['id']}/mover", json={"localizacao_id": base["loc2"]["id"]}).status_code == 400
    detail = admin.ok("GET", "inventory", f"equipamentos/{e['id']}")
    assert detail["nome"] == e["nome"] and [c["id"] for c in detail["componentes_instalados"]] == [inst["id"]]


def test_inactive_component_cannot_be_assigned(admin, base):
    comp = admin.ok("POST", "inventory", "componentes", json={"nome": f"Sensor inativo {RUN}", "tipo": "sensor"})
    admin.ok("PATCH", "inventory", f"componentes/{comp['id']}", json={"ativo": False})
    e = new_equipment(admin, base, "IC")
    r = admin.req("POST", "inventory", f"equipamentos/{e['id']}/componentes", json={"componente_id": comp["id"], "quantidade": 1})
    assert r.status_code == 400
    assert admin.ok("GET", "inventory", f"equipamentos/{e['id']}")["componentes_instalados"] == []


def test_overdue_means_planned_preventive_everywhere(admin, accounts, base):
    e = new_equipment(admin, base, "OD")
    past = str(TODAY - dt.timedelta(days=4))
    tech_id = accounts["technician"]["id"]
    prev = admin.ok("POST", "maintenance", "manutencoes", json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": past, "descricao": "prev", "responsavel_id": tech_id})
    corr = admin.ok("POST", "maintenance", "manutencoes", json={"equipamento_id": e["id"], "tipo": "corrective", "data_planejada": past, "descricao": "corr", "responsavel_id": tech_id})
    params = {"situacao": "overdue", "equipamento_id": e["id"]}
    listed = {m["id"] for m in admin.ok("GET", "maintenance", "manutencoes", params=params)["items"]}
    report = {m["id"] for m in admin.ok("GET", "reports", "relatorios/manutencoes", params=params)["items"]}
    assert listed == report == {prev["id"]}
    assert corr["id"] not in listed


# ------------------------------------------------------------------ decisões da revisão (2026-10-08)
def test_old_audit_events_hold_no_credentials(admin):
    """Decisão 4: os eventos são mantidos, mas nenhuma metadata de auditoria guarda hash de senha ou de token de redefinição."""
    for action in ("login", "signup", "get_auth_user", "login_for_password_reset", "reset_password"):
        for ev in admin.ok("GET", "reports", "auditoria", params={"action": action, "per_page": 200})["items"]:
            meta = ev.get("metadata") or {}
            assert meta.get("password") is None, ev["id"]
            assert (meta.get("password_reset") or {}).get("token") is None, ev["id"]


def test_technician_cannot_change_equipment_status_through_maintenance(admin, accounts, base):
    """Decisão 20: mudar o status do equipamento exige inventory.manage, inclusive ao iniciar/concluir."""
    tech = accounts["technician"]
    e = new_equipment(admin, base, "TS")
    m = admin.ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY), "descricao": "x", "responsavel_id": tech["id"]},
    )
    t = tech["client"]
    r = t.req("POST", "maintenance", f"manutencoes/{m['id']}/iniciar", json={"colocar_equipamento_em_manutencao": True})
    assert r.status_code == 403
    assert admin.ok("GET", "inventory", f"equipamentos/{e['id']}")["status"] == "operational"
    t.ok("POST", "maintenance", f"manutencoes/{m['id']}/iniciar", json={})  # o trabalho em si pode começar
    done = {"concluida_em": int(dt.datetime.now().timestamp() * 1000), "resumo_execucao": "ok"}
    r = t.req("POST", "maintenance", f"manutencoes/{m['id']}/concluir", json=done | {"status_equipamento": "operational"})
    assert r.status_code == 403
    states = {x["id"]: x["status"] for x in admin.ok("GET", "maintenance", "manutencoes", params={"equipamento_id": e["id"]})["items"]}
    assert states[m["id"]] == "in_progress", "a refused request must not complete the maintenance"


def test_out_of_service_on_completion_requires_reason(admin, accounts, base):
    """Decisão 21a: a regra do motivo vale para todos os caminhos, inclusive concluir manutenção."""
    e = new_equipment(admin, base, "CR")
    m = admin.ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "corrective", "data_planejada": str(TODAY), "descricao": "x", "responsavel_id": accounts["asset_manager"]["id"]},
    )
    done = {"concluida_em": int(dt.datetime.now().timestamp() * 1000), "resumo_execucao": "Peça indisponível", "status_equipamento": "out_of_service"}
    assert admin.req("POST", "maintenance", f"manutencoes/{m['id']}/concluir", json=done).status_code == 400
    admin.ok("POST", "maintenance", f"manutencoes/{m['id']}/concluir", json=done | {"motivo_status": "Aguardando placa"})
    ev = next(x for x in audit_events(admin, "equipamentos", e["id"]) if x["action"] == "equipamento.status_changed")
    assert ev["metadata"]["depois"] == {"status": "out_of_service", "motivo": "Aguardando placa"}


def test_decommissioning_is_final(admin, base):
    """Decisão 21b."""
    e = new_equipment(admin, base, "DF")
    admin.ok("POST", "inventory", f"equipamentos/{e['id']}/status", json={"status": "decommissioned", "motivo": "Fim de vida"})
    for status in ("operational", "out_of_service", "under_maintenance"):
        r = admin.req("POST", "inventory", f"equipamentos/{e['id']}/status", json={"status": status, "motivo": "x"})
        assert r.status_code == 400, status
    assert admin.ok("GET", "inventory", f"equipamentos/{e['id']}")["status"] == "decommissioned"


def test_recurrence_only_suggests_next_date(admin, accounts, base):
    """Decisão 21c: concluir um trabalho recorrente não cria um novo registro de manutenção."""
    e = new_equipment(admin, base, "RC")
    m = admin.ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY), "descricao": "x", "responsavel_id": accounts["asset_manager"]["id"], "intervalo_recorrencia_dias": 30},
    )
    done = admin.ok("POST", "maintenance", f"manutencoes/{m['id']}/concluir", json={"concluida_em": int(dt.datetime.now().timestamp() * 1000), "resumo_execucao": "ok"})
    assert done["proxima_data_sugerida"] == str(TODAY + dt.timedelta(days=30))
    assert len(admin.ok("GET", "maintenance", "manutencoes", params={"equipamento_id": e["id"]})["items"]) == 1


def test_location_filter_excludes_sub_locations(admin, base):
    """Decisão 21d."""
    parent = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Prédio {RUN}"})
    child = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Sala filha {RUN}", "parent_id": parent["id"]})
    new_equipment(admin, base, "LF", localizacao_id=child["id"])
    assert admin.ok("GET", "inventory", "equipamentos", params={"localizacao_id": parent["id"]})["items"] == []
    assert admin.ok("GET", "reports", "dashboard", params={"localizacao_id": parent["id"]})["equipamentos_ativos"] == 0


def test_catalog_edit_rules(admin, base):
    """Decisão 18: edições passam pela API existente, com a validação dela."""
    fab = admin.ok("POST", "inventory", "fabricantes", json={"nome": f"Fab edit {RUN}"})
    assert admin.req("PATCH", "inventory", f"fabricantes/{fab['id']}", json={"nome": base["fab"]["nome"]}).status_code == 400
    assert admin.ok("PATCH", "inventory", f"fabricantes/{fab['id']}", json={"nome": f"Fab editado {RUN}", "site": ""})["nome"] == f"Fab editado {RUN}"
    parent = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Bloco {RUN}"})
    child = admin.ok("POST", "inventory", "localizacoes", json={"nome": f"Ala {RUN}", "parent_id": parent["id"]})
    assert admin.req("PATCH", "inventory", f"localizacoes/{parent['id']}", json={"parent_id": child["id"]}).status_code == 400  # ciclo
    assert admin.ok("PATCH", "inventory", f"localizacoes/{child['id']}", json={"parent_id": 0})["parent_id"] is None


# ------------------------------------------------------------------ senha temporária no primeiro acesso
def test_temporary_password_must_be_changed_before_use(admin, roles):
    email = f"teste.temp.{RUN}@example.org"
    created = admin.ok("POST", "users", "users", json={"name": "Temporária", "email": email, "password": PASSWORD, "role_id": roles["asset_manager"]})
    assert created["deve_trocar_senha"] is True

    r = httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": email, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200 and r.json()["deve_trocar_senha"] is True
    client = Client(r.json()["authToken"])
    me = client.ok("GET", "auth", "auth/me")
    assert me["deve_trocar_senha"] is True and me["permissions"] == []
    # Toda operação protegida é recusada até a senha ser trocada
    assert client.req("GET", "inventory", "equipamentos").status_code == 403
    assert client.req("POST", "inventory", "fabricantes", json={"nome": f"Fab temp {RUN}"}).status_code == 403

    change = lambda body: client.req("POST", "auth", "auth/change_password", json=body)  # noqa: E731
    assert change({"senha_atual": "errada123", "nova_senha": FINAL_PASSWORD, "confirmar_senha": FINAL_PASSWORD}).status_code == 400
    assert change({"senha_atual": PASSWORD, "nova_senha": PASSWORD, "confirmar_senha": PASSWORD}).status_code == 400  # mesma senha
    assert change({"senha_atual": PASSWORD, "nova_senha": "curta1", "confirmar_senha": "curta1"}).status_code == 400  # política
    assert change({"senha_atual": PASSWORD, "nova_senha": FINAL_PASSWORD, "confirmar_senha": "outra123"}).status_code == 400
    assert client.ok("GET", "auth", "auth/me")["deve_trocar_senha"] is True  # nada mudou ainda

    assert change({"senha_atual": PASSWORD, "nova_senha": FINAL_PASSWORD, "confirmar_senha": FINAL_PASSWORD}).status_code == 200
    me = client.ok("GET", "auth", "auth/me")
    assert me["deve_trocar_senha"] is False and "inventory.manage" in me["permissions"]
    assert client.req("GET", "inventory", "equipamentos").status_code == 200

    old = httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": email, "password": PASSWORD}, timeout=30)
    assert old.status_code == 403
    new = httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": email, "password": FINAL_PASSWORD}, timeout=30)
    assert new.status_code == 200 and new.json()["deve_trocar_senha"] is False

    events = audit_events(admin, "user", created["id"])
    changed = next(ev for ev in events if ev["action"] == "user.password_changed")
    assert changed["metadata"]["depois"] == {"deve_trocar_senha": False}
    assert "password" not in str(changed["metadata"]).replace("password_changed", "")


def test_administrator_cannot_set_an_existing_users_password(admin, accounts):
    acc = accounts["viewer"]
    r = admin.req("PATCH", "users", f"users/{acc['id']}", json={"password": "Admin1234x"})
    assert r.status_code in (200, 400)  # o endpoint não aceita esse campo
    assert httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": acc["email"], "password": "Admin1234x"}, timeout=30).status_code == 403
    assert httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": acc["email"], "password": FINAL_PASSWORD}, timeout=30).status_code == 200
    # Recriar o mesmo e-mail (uma redefinição disfarçada) também é recusado
    r = admin.req("POST", "users", "users", json={"name": "x", "email": acc["email"], "password": "Admin1234x", "role_id": 1})
    assert r.status_code == 400
    # change_password só altera a senha de quem chama
    r = admin.req("POST", "auth", "auth/change_password", json={"senha_atual": "x", "nova_senha": "Admin1234x", "confirmar_senha": "Admin1234x", "user_id": acc["id"]})
    assert r.status_code == 400
    assert httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": acc["email"], "password": FINAL_PASSWORD}, timeout=30).status_code == 200


# ------------------------------------------------------------------ fluxo de redefinição (sem sessões de redefinição)
def test_reset_links_never_create_sessions(accounts):
    """O fluxo antigo em dois passos devolvia uma sessão completa para o link de redefinição; os dois endpoints dele estão desativados."""
    anon = Client()
    r = anon.req("POST", "auth", "reset/magic-link-login", json={"magic_token": "x", "email": accounts["viewer"]["email"]})
    assert r.status_code == 403 and "authToken" not in r.text
    # Uma sessão normal não consegue mais definir senha sem informar a atual
    viewer = accounts["viewer"]["client"]
    r = viewer.req("POST", "auth", "reset/update_password", json={"password": "Tomada123x", "confirm_password": "Tomada123x"})
    assert r.status_code == 403
    assert httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": accounts["viewer"]["email"], "password": "Tomada123x"}, timeout=30).status_code == 403


def test_reset_confirm_rejects_bad_links_identically(accounts):
    anon = Client()
    body = {"nova_senha": "Nova12345x", "confirmar_senha": "Nova12345x"}
    known = anon.req("POST", "auth", "reset/confirm", json=body | {"magic_token": "nao-existe", "email": accounts["viewer"]["email"]})
    unknown = anon.req("POST", "auth", "reset/confirm", json=body | {"magic_token": "nao-existe", "email": f"ninguem.{RUN}@example.org"})
    assert known.status_code == unknown.status_code == 403
    assert known.json().get("message") == unknown.json().get("message"), "must not reveal whether the account exists"
    mismatch = anon.req("POST", "auth", "reset/confirm", json={"magic_token": "x", "email": accounts["viewer"]["email"], "nova_senha": "Nova12345x", "confirmar_senha": "Outra12345x"})
    assert mismatch.status_code == 400
    # A conta continua funcionando com a própria senha
    assert httpx.post(f"{BASE}/api:{GROUPS['auth']}/auth/login", json={"email": accounts["viewer"]["email"], "password": FINAL_PASSWORD}, timeout=30).status_code == 200


def test_history_marks_planned_only_events_as_dates(admin, accounts, base):
    """Item 5: eventos datados por uma data planejada de calendário são marcados para os clientes não converterem o fuso."""
    e = new_equipment(admin, base, "HD")
    m = admin.ok(
        "POST", "maintenance", "manutencoes",
        json={"equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(TODAY + dt.timedelta(days=3)), "descricao": "x", "responsavel_id": accounts["asset_manager"]["id"]},
    )
    ev = next(x for x in admin.ok("GET", "maintenance", f"equipamentos/{e['id']}/historico")["eventos"] if x["registro_id"] == m["id"])
    assert ev["somente_data"] is True and ev["data_planejada"] == m["data_planejada"]
