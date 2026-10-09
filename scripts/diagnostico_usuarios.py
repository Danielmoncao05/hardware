"""Diagnóstico (somente leitura) da tela de usuários: mostra o que o Xano responde para auth/me, users e roles.

Uso, na pasta do projeto:

    .venv\\Scripts\\python.exe scripts\\diagnostico_usuarios.py

Pede e-mail e senha de administrador (a senha não aparece). Não grava nada.
"""

import getpass
import json
import os
import sys

import httpx

BASE = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")
AUTH = os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc")
USERS = os.environ.get("XANO_USERS_GROUP", "hhm149197-users")


def show(label: str, r: httpx.Response):
    try:
        body = r.json()
    except ValueError:
        body = r.text
    if isinstance(body, dict) and "authToken" in body:
        body = {**body, "authToken": "(oculto)"}
    text = json.dumps(body, ensure_ascii=False, indent=2) if not isinstance(body, str) else body
    kind = type(body).__name__
    print(f"\n=== {label}: HTTP {r.status_code}, resposta do tipo {kind}")
    print(text[:1500] + ("\n... (cortado)" if len(text) > 1500 else ""))


def main():
    email = input("E-mail do administrador: ").strip()
    password = getpass.getpass("Senha (não aparece ao digitar): ")
    with httpx.Client(timeout=60) as http:
        r = http.post(f"{BASE}/api:{AUTH}/auth/login", json={"email": email, "password": password})
        if r.status_code != 200:
            show("login", r)
            sys.exit("Login falhou.")
        headers = {"Authorization": f"Bearer {r.json()['authToken']}"}
        show("auth/me", http.get(f"{BASE}/api:{AUTH}/auth/me", headers=headers))
        show("users (como o app pede)", http.get(f"{BASE}/api:{USERS}/users", headers=headers, params={"page": 1, "per_page": 100}))
        show("users (sem parâmetros)", http.get(f"{BASE}/api:{USERS}/users", headers=headers))
        # Hipótese: o Xano trata o filtro bool? ativo ausente como false
        show("users com ativo=true", http.get(f"{BASE}/api:{USERS}/users", headers=headers, params={"ativo": "true"}))
        show("users com ativo=false", http.get(f"{BASE}/api:{USERS}/users", headers=headers, params={"ativo": "false"}))


if __name__ == "__main__":
    main()
