"""Cria dados de demonstração pela API do Xano: localizações, fabricantes, modelos, componentes, equipamentos,
manutenções (concluídas, atrasadas e próximas) e ocorrências (abertas, em andamento e resolvidas).

Tudo é fictício e leva o prefixo DEMO (nomes) ou DEMO- (patrimônio), para ser fácil de achar e desativar depois.
Os cadastros passam pela API, com as mesmas validações e auditoria do aplicativo.

Uso (na pasta do projeto, com uma conta administrator):

    .venv\\Scripts\\python.exe scripts\\seed_demo.py

O e-mail e a senha são pedidos no terminal (a senha não aparece). Também podem vir de HHM_ADMIN_EMAIL e
HHM_ADMIN_PASSWORD. Pode rodar de novo: localizações, fabricantes, modelos, componentes e equipamentos DEMO que já
existem são reaproveitados, e manutenções e ocorrências só são criadas para equipamentos DEMO que ainda não têm
nenhuma. Assim, rodar depois de uma interrupção completa o que falta sem duplicar.

O plano Free do Xano aceita 10 requisições a cada 20 segundos, então o script espera entre as chamadas
(leva alguns minutos).
"""

import datetime as dt
import getpass
import os
import random
import sys
import time

import httpx

BASE = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")
GROUPS = {
    "auth": os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc"),
    "inventory": os.environ.get("XANO_INVENTORY_GROUP", "hhm149197-inventory"),
    "maintenance": os.environ.get("XANO_MAINTENANCE_GROUP", "hhm149197-maintenance"),
}
# Segundos entre requisições: o plano Free aceita 10 por 20 s, contando também as do app aberto no navegador
MIN_INTERVAL = 2.5
TODAY = dt.date.today()

# ------------------------------------------------------------------ dados fictícios
# (nome, localização superior, tipo)
LOCALIZACOES = [
    ("DEMO Bloco A", None, "prédio"),
    ("DEMO Bloco B", None, "prédio"),
    ("DEMO UTI Adulto", "DEMO Bloco A", "unidade"),
    ("DEMO Centro Cirúrgico", "DEMO Bloco A", "unidade"),
    ("DEMO Pronto-Socorro", "DEMO Bloco B", "unidade"),
    ("DEMO Enfermaria 3º andar", "DEMO Bloco B", "unidade"),
    ("DEMO Diagnóstico por Imagem", "DEMO Bloco B", "unidade"),
    ("DEMO Engenharia Clínica", None, "setor"),
]
FABRICANTES = ["DEMO VitalTech", "DEMO RespiraMed", "DEMO InfusaCare", "DEMO CardioSys", "DEMO ImagemPro"]
# (nome, fabricante, categoria, localizações onde costuma ficar)
MODELOS = [
    ("DEMO Monitor VT-12", "DEMO VitalTech", "monitor multiparamétrico", ["DEMO UTI Adulto", "DEMO Pronto-Socorro", "DEMO Centro Cirúrgico"]),
    ("DEMO Ventilador RM-300", "DEMO RespiraMed", "ventilador pulmonar", ["DEMO UTI Adulto", "DEMO Pronto-Socorro"]),
    ("DEMO Bomba IC-2", "DEMO InfusaCare", "bomba de infusão", ["DEMO UTI Adulto", "DEMO Enfermaria 3º andar"]),
    ("DEMO Desfibrilador CS-5", "DEMO CardioSys", "desfibrilador", ["DEMO Pronto-Socorro", "DEMO Centro Cirúrgico"]),
    ("DEMO ECG CS-12", "DEMO CardioSys", "eletrocardiógrafo", ["DEMO Pronto-Socorro", "DEMO Enfermaria 3º andar"]),
    ("DEMO Anestesia RM-A1", "DEMO RespiraMed", "máquina de anestesia", ["DEMO Centro Cirúrgico"]),
    ("DEMO Ultrassom IP-8", "DEMO ImagemPro", "ultrassom", ["DEMO Diagnóstico por Imagem"]),
    ("DEMO Raio-X IP-DR", "DEMO ImagemPro", "raio-X", ["DEMO Diagnóstico por Imagem"]),
    ("DEMO Tomógrafo IP-64", "DEMO ImagemPro", "tomógrafo", ["DEMO Diagnóstico por Imagem"]),
    ("DEMO Oxímetro VT-O2", "DEMO VitalTech", "oxímetro", ["DEMO Enfermaria 3º andar", "DEMO Pronto-Socorro"]),
    ("DEMO Aspirador RM-S", "DEMO RespiraMed", "aspirador hospitalar", ["DEMO Centro Cirúrgico", "DEMO UTI Adulto"]),
]
# (nome, tipo, fabricante)
COMPONENTES = [
    ("DEMO Bateria Li-ion 14,4 V", "battery", "DEMO VitalTech"),
    ("DEMO Sensor de SpO2 adulto", "sensor", "DEMO VitalTech"),
    ("DEMO Placa de comunicação Wi-Fi", "communication_board", None),
    ("DEMO Display LCD 12 pol.", "display", None),
]
PREVENTIVAS = [
    "Inspeção de segurança elétrica e teste funcional",
    "Calibração e verificação de alarmes",
    "Limpeza interna, troca de filtros e teste de bateria",
    "Verificação de parâmetros e atualização de firmware",
]
CHECKLIST = ["Inspeção visual", "Teste de segurança elétrica", "Teste de alarmes", "Registro do resultado"]
# (descrição técnica, severidade)
OCORRENCIAS = [
    ("Alarme de bateria baixa disparando com o equipamento ligado na tomada", "medium"),
    ("Tela pisca e reinicia durante o uso", "high"),
    ("Ruído anormal no motor durante o funcionamento", "medium"),
    ("Equipamento não liga após queda de energia", "critical"),
    ("Mensagem de erro E-04 ao iniciar o autoteste", "high"),
    ("Cabo de alimentação com isolamento danificado", "low"),
    ("Leitura instável no sensor de SpO2", "medium"),
    ("Botão de seleção travando", "low"),
    ("Superaquecimento após uso contínuo", "high"),
    ("Falha na comunicação com a central de monitoramento", "medium"),
]


# ------------------------------------------------------------------ cliente com ritmo para o plano Free
class Api:
    def __init__(self):
        self.token = ""
        self.last = 0.0
        self.count = 0
        self.http = httpx.Client(timeout=60)

    def req(self, method: str, group: str, path: str, **kwargs):
        for attempt in range(5):
            wait = MIN_INTERVAL - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            try:
                r = self.http.request(method, f"{BASE}/api:{GROUPS[group]}/{path}", headers=headers, **kwargs)
            except httpx.TransportError as err:
                self.count += 1
                if method != "GET":
                    # A gravação pode ter acontecido mesmo sem resposta: repetir poderia duplicar o registro.
                    # Rodar o script de novo reaproveita o que já existe.
                    raise RuntimeError(f"{method} {path} sem resposta do Xano ({type(err).__name__})") from None
                print(f"   (o Xano não respondeu a tempo; tentando de novo em 20 s)")
                time.sleep(20)
                continue
            self.count += 1
            if r.status_code != 429:
                break
            pause = 21 if attempt == 0 else 30
            print(f"   (limite de requisições do Xano; aguardando {pause} s)")
            time.sleep(pause)
        else:
            raise RuntimeError(f"{method} {path}: o Xano não respondeu depois de várias tentativas")
        if r.status_code >= 400:
            try:
                message = r.json().get("message")
            except ValueError:
                message = r.text
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {message}")
        return r.json() if r.content else None

    def items(self, group: str, path: str, **params) -> list[dict]:
        """Lista completa de um GET, aceitando página {"items": ...} ou lista simples."""
        out, page = [], 1
        while True:
            result = self.req("GET", group, path, params=params | {"page": page, "per_page": 100})
            if isinstance(result, list):
                return result
            out += result.get("items") or []
            if result.get("nextPage") is None:
                return out
            page += 1


def ms(day: dt.date, hour: int = 14) -> int:
    """Data e hora local (fuso do computador) em milissegundos, como os formulários do app enviam."""
    return int(dt.datetime(day.year, day.month, day.day, hour).timestamp() * 1000)


def main():
    rnd = random.Random(2026)
    api = Api()

    email = os.environ.get("HHM_ADMIN_EMAIL") or input("E-mail do administrador: ").strip()
    password = os.environ.get("HHM_ADMIN_PASSWORD") or getpass.getpass("Senha (não aparece ao digitar): ")
    api.token = api.req("POST", "auth", "auth/login", json={"email": email, "password": password})["authToken"]
    me = api.req("GET", "auth", "auth/me")
    if "inventory.manage" not in me.get("permissions", []) or "maintenance.manage" not in me.get("permissions", []):
        sys.exit("Esta conta precisa do perfil administrator (ou asset_manager). Rode o setup do Xano se for o caso.")
    print(f"Conectado como {me.get('name') or me.get('email')} ({me.get('role')}).")

    # ---- categorias (criadas pelo setup do Xano)
    categorias = {c["nome"].lower(): c["id"] for c in api.items("inventory", "categorias")}
    faltando = {m[2].lower() for m in MODELOS} - set(categorias)
    if faltando:
        sys.exit(f"Categorias ausentes: {sorted(faltando)}. Rode antes: xano function run \"setup/run_deployment_setup\"")

    # ---- localizações
    print("Localizações...")
    locs = {l["nome"]: l["id"] for l in api.items("inventory", "localizacoes", include_inactive=True)}
    for nome, parent, tipo in LOCALIZACOES:
        if nome not in locs:
            locs[nome] = api.req("POST", "inventory", "localizacoes", json={"nome": nome, "tipo": tipo, "parent_id": locs.get(parent)} if parent else {"nome": nome, "tipo": tipo})["id"]

    # ---- fabricantes, modelos e componentes
    print("Fabricantes, modelos e componentes...")
    fabs = {f["nome"]: f["id"] for f in api.items("inventory", "fabricantes", include_inactive=True)}
    for nome in FABRICANTES:
        if nome not in fabs:
            fabs[nome] = api.req("POST", "inventory", "fabricantes", json={"nome": nome, "observacoes": "Fabricante fictício (dados de demonstração)"})["id"]
    modelos = {m["nome"]: m["id"] for m in api.items("inventory", "modelos", include_inactive=True)}
    for nome, fab, cat, _ in MODELOS:
        if nome not in modelos:
            modelos[nome] = api.req("POST", "inventory", "modelos", json={"nome": nome, "fabricante_id": fabs[fab], "categoria_id": categorias[cat.lower()]})["id"]
    comps = {c["nome"]: c["id"] for c in api.items("inventory", "componentes", include_inactive=True)}
    for nome, tipo, fab in COMPONENTES:
        if nome not in comps:
            payload = {"nome": nome, "tipo": tipo} | ({"fabricante_id": fabs[fab]} if fab else {})
            comps[nome] = api.req("POST", "inventory", "componentes", json=payload)["id"]

    # ---- equipamentos (os que já existem são pulados)
    print("Equipamentos...")
    demo = [e for e in api.items("inventory", "equipamentos", q="DEMO-", include_decommissioned=True) if e["numero_patrimonio"].startswith("DEMO-")]
    existentes = {e["numero_patrimonio"] for e in demo}
    novos = []
    numero = 0
    for nome_modelo, _, cat, lugares in MODELOS:
        for _ in range(3 if cat in ("monitor multiparamétrico", "bomba de infusão", "oxímetro") else 2):
            numero += 1
            patrimonio = f"DEMO-{numero:04d}"
            if patrimonio in existentes:
                continue
            ano = rnd.randint(2016, TODAY.year - 1)
            aquisicao = dt.date(ano, rnd.randint(1, 12), rnd.randint(1, 28))
            payload = {
                "nome": f"{cat.capitalize()} {numero:02d}",
                "numero_patrimonio": patrimonio,
                "numero_serie": f"SN-DEMO-{rnd.randint(100000, 999999)}",
                "modelo_id": modelos[nome_modelo],
                "localizacao_id": locs[rnd.choice(lugares)],
                "status": "operational",
                "ano_fabricacao": ano,
                "data_aquisicao": str(aquisicao),
                "valor_aquisicao": round(rnd.uniform(4000, 380000 if cat in ("tomógrafo", "raio-X") else 90000), 2),
                "vida_util_anos": rnd.choice([8, 10, 12]),
                "observacoes": "Equipamento fictício (dados de demonstração)",
            }
            novos.append(api.req("POST", "inventory", "equipamentos", json=payload))
            print(f"   {patrimonio} {payload['nome']}")

    # Eventos só para equipamentos DEMO que ainda não têm nenhuma manutenção nem ocorrência: rodar de novo depois
    # de uma interrupção completa o que falta sem duplicar
    com_eventos = {m["equipamento_id"] for m in api.items("maintenance", "manutencoes")}
    com_eventos |= {o["equipamento_id"] for o in api.items("maintenance", "ocorrencias")}
    novos = sorted(
        [e for e in demo + novos if e["id"] not in com_eventos], key=lambda e: e["numero_patrimonio"]
    )
    if not novos:
        print(f"Nada a criar: os equipamentos DEMO já têm manutenções e ocorrências. Requisições feitas: {api.count}.")
        return
    print(f"{len(novos)} equipamento(s) sem manutenções nem ocorrências; criando os eventos...")

    # ---- componentes instalados
    print("Componentes instalados...")
    for e in novos[::3]:
        api.req("POST", "inventory", f"equipamentos/{e['id']}/componentes", json={"componente_id": comps["DEMO Bateria Li-ion 14,4 V"], "quantidade": 1, "slot": "Compartimento traseiro"})
    for e in novos[1::5]:
        api.req("POST", "inventory", f"equipamentos/{e['id']}/componentes", json={"componente_id": comps["DEMO Sensor de SpO2 adulto"], "quantidade": 2})

    # ---- manutenções preventivas: histórico concluído, atrasadas e próximas
    print("Manutenções...")
    resp = me["id"]

    def preventiva(e, dia: dt.date, recorrencia: int | None = 180):
        return api.req("POST", "maintenance", "manutencoes", json={
            "equipamento_id": e["id"], "tipo": "preventive", "data_planejada": str(dia), "descricao": rnd.choice(PREVENTIVAS),
            "responsavel_id": resp, "checklist": [{"item": i, "feito": False} for i in CHECKLIST],
        } | ({"intervalo_recorrencia_dias": recorrencia} if recorrencia else {}))

    for e in novos[::2]:  # histórico: preventiva concluída há alguns meses
        dia = TODAY - dt.timedelta(days=rnd.randint(60, 200))
        m = preventiva(e, dia)
        api.req("POST", "maintenance", f"manutencoes/{m['id']}/concluir", json={
            "concluida_em": ms(dia + dt.timedelta(days=1)), "resumo_execucao": "Serviço executado conforme checklist; equipamento aprovado nos testes.",
        })
    for e in novos[:6]:  # atrasadas
        preventiva(e, TODAY - dt.timedelta(days=rnd.randint(3, 40)))
    for e in novos[6:18]:  # próximas (nos próximos 60 dias)
        preventiva(e, TODAY + dt.timedelta(days=rnd.randint(1, 60)))

    # ---- ocorrências e manutenções corretivas
    print("Ocorrências...")
    alvos = rnd.sample(novos, min(len(OCORRENCIAS), len(novos)))
    for i, ((descricao, severidade), e) in enumerate(zip(OCORRENCIAS, alvos)):
        # Pelo menos 3 dias atrás: a resolução (relato + 1 dia) nunca cai no futuro, que a API recusa
        relato = TODAY - dt.timedelta(days=rnd.randint(3, 25))
        occ = api.req("POST", "maintenance", "ocorrencias", json={
            "equipamento_id": e["id"], "descricao_tecnica": descricao, "severidade": severidade, "relatada_em": ms(relato, 9),
        })
        if i < 3:  # resolvidas
            api.req("POST", "maintenance", f"ocorrencias/{occ['id']}/transicao", json={
                "acao": "resolver", "resolvida_em": ms(relato + dt.timedelta(days=1), 16),
                "resumo_resolucao": "Componente substituído e equipamento testado; funcionamento normal.",
            })
        elif i < 6:  # em andamento, com manutenção corretiva iniciada (equipamento fica "em manutenção")
            api.req("POST", "maintenance", f"ocorrencias/{occ['id']}/transicao", json={"acao": "iniciar"})
            corr = api.req("POST", "maintenance", "manutencoes", json={
                "equipamento_id": e["id"], "tipo": "corrective", "data_planejada": str(TODAY), "descricao": f"Corretiva: {descricao.lower()}",
                "responsavel_id": resp, "ocorrencia_id": occ["id"],
            })
            api.req("POST", "maintenance", f"manutencoes/{corr['id']}/iniciar", json={"colocar_equipamento_em_manutencao": True})
        # as demais ficam abertas

    print(f"\nPronto: {len(novos)} equipamentos com manutenções e ocorrências. Requisições feitas: {api.count}.")
    print("Abra o painel do app para ver os números.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as err:
        sys.exit(f"\nErro da API: {err}\nO que já foi criado continua lá; rode de novo para completar.")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido. Rode de novo para completar o que falta.")
