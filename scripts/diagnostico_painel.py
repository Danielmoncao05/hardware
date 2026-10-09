"""Diagnóstico (somente leitura) do painel: resume a resposta de GET dashboard e mede o tempo de resposta.

Uso, na pasta do projeto:

    .venv\\Scripts\\python.exe scripts\\diagnostico_painel.py

Pede e-mail e senha de administrador (a senha não aparece). Não grava nada.
"""

import getpass
import os
import sys
import time

import httpx

BASE = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")
AUTH = os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc")
REPORTS = os.environ.get("XANO_REPORTS_GROUP", "hhm149197-reports")


def main():
    email = input("E-mail do administrador: ").strip()
    password = getpass.getpass("Senha (não aparece ao digitar): ")
    with httpx.Client(timeout=60) as http:
        r = http.post(f"{BASE}/api:{AUTH}/auth/login", json={"email": email, "password": password})
        if r.status_code != 200:
            sys.exit(f"Login falhou: HTTP {r.status_code}")
        headers = {"Authorization": f"Bearer {r.json()['authToken']}"}

        tempos = []
        data = None
        for _ in range(3):
            time.sleep(2.5)  # limite do plano Free
            t0 = time.perf_counter()
            resp = http.get(f"{BASE}/api:{REPORTS}/dashboard", headers=headers)
            tempos.append(time.perf_counter() - t0)
            if resp.status_code != 200:
                sys.exit(f"GET dashboard: HTTP {resp.status_code} {resp.text[:300]}")
            data = resp.json()

        def n(value):
            return len(value) if isinstance(value, list) else value

        por_status = data.get("por_status") or {}
        setores = data.get("por_localizacao") or []
        print("\n=== Indicadores")
        print(f"ativos={data.get('equipamentos_ativos')}  disponiveis={por_status.get('operational')}  "
              f"em_manutencao={por_status.get('under_maintenance')}  fora_de_servico={por_status.get('out_of_service')}  "
              f"criticos={n(data.get('criticos'))}")
        print(f"\n=== Por setor (soma {sum(s.get('total') or 0 for s in setores)})")
        for s in setores:
            print(f"   {s.get('localizacao')}: {s.get('total')}")
        prox = data.get("preventivas_proximas") or {}
        atr = data.get("preventivas_atrasadas") or {}
        rec = data.get("manutencoes_recentes") or {}
        print(f"\n=== Listas")
        print(f"preventivas_proximas: total={prox.get('total')} itens={n(prox.get('itens'))} "
              f"primeiro_setor={((prox.get('itens') or [{}])[0]).get('localizacao')}")
        print(f"preventivas_atrasadas: total={atr.get('total')} itens={n(atr.get('itens'))}")
        print(f"manutencoes_recentes: total={rec.get('total')} itens={n(rec.get('itens'))}")
        print(f"ocorrencias_recentes: {n(data.get('ocorrencias_recentes'))}")
        print("\n=== Críticos")
        for c in data.get("criticos") or []:
            print(f"   {c.get('numero_patrimonio')} {c.get('equipamento')} [{c.get('status')}] ocorrência={c.get('ocorrencia_id')}")
        print(f"\n=== Tempo de GET dashboard: {', '.join(f'{t:.2f} s' for t in tempos)} (maior: {max(tempos):.2f} s)")

        # Acompanhamento: sem filtro e com o filtro de saúde "critico" (o caso do "Carregando..." demorado)
        for saude in (None, "critico"):
            tempos_acomp = []
            for _ in range(2):
                time.sleep(2.5)
                params = {"page": 1, "per_page": 25} | ({"saude": saude} if saude else {})
                t0 = time.perf_counter()
                resp = http.get(f"{BASE}/api:{REPORTS}/acompanhamento", headers=headers, params=params)
                tempos_acomp.append(time.perf_counter() - t0)
                if resp.status_code != 200:
                    sys.exit(f"GET acompanhamento: HTTP {resp.status_code} {resp.text[:300]}")
            body = resp.json()
            com_datas = sum(1 for r in body.get("items") or [] if r.get("proxima_manutencao") or r.get("ultima_manutencao"))
            print(f"=== Tempo de GET acompanhamento (saude={saude or 'todas'}): "
                  f"{', '.join(f'{t:.2f} s' for t in tempos_acomp)} | linhas={len(body.get('items') or [])} "
                  f"com datas de manutenção={com_datas} | resumo={body.get('resumo')}")


if __name__ == "__main__":
    main()
