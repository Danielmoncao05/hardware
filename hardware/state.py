"""Estado de sessão e permissões compartilhado por todas as páginas.

O token de autenticação do Xano fica só na var exclusiva do backend `_token`: o Reflex nunca envia
vars com sublinhado ao navegador. As flags de permissão abaixo só decidem quais controles são
mostrados; a API verifica de novo toda operação.
"""

import json
import time
from typing import Any

import reflex as rx

from . import api
from .labels import role_label

# Segundos em que o perfil carregado (auth/me) é reaproveitado entre páginas. O plano Free do Xano aceita poucas
# requisições por janela, então consultar o perfil a cada troca de página deixava a navegação lenta.
PROFILE_TTL = 60
# Segundos em que uma página de listagem (ocorrências, manutenções, equipamentos) é reaproveitada
LIST_CACHE_TTL = 30


class AuthState(rx.State):
    _token: str = ""
    _me_loaded_at: float = 0.0
    # chave da consulta -> (momento, resposta); esvaziado por qualquer escrita e ao encerrar a sessão
    _list_cache: dict[str, Any] = {}

    user_id: int = 0
    user_name: str = ""
    user_email: str = ""
    role: str = ""
    permissions: list[str] = []
    # Conta criada com senha temporária: o usuário precisa trocá-la antes de usar o sistema.
    # Enquanto isso a API não concede permissões; esta flag só direciona a interface para /trocar-senha.
    must_change_password: bool = False

    login_error: str = ""
    login_loading: bool = False

    # ---- identificação no menu do usuário ----
    @rx.var
    def display_name(self) -> str:
        """Nome do usuário, ou o e-mail quando a conta não tem nome cadastrado."""
        return self.user_name.strip() or self.user_email

    @rx.var
    def user_initials(self) -> str:
        """Iniciais para o avatar: duas primeiras palavras do nome, ou a primeira letra do e-mail."""
        words = self.user_name.split()
        if words:
            return "".join(w[0] for w in words[:2]).upper()
        return self.user_email[:1].upper() or "?"

    # ---- flags de permissão (só para a interface) ----
    @rx.var
    def logged_in(self) -> bool:
        return self.user_id != 0

    @rx.var
    def can_read_operational(self) -> bool:
        return "operational.read" in self.permissions

    @rx.var
    def can_manage_inventory(self) -> bool:
        return "inventory.manage" in self.permissions

    @rx.var
    def can_manage_maintenance(self) -> bool:
        return "maintenance.manage" in self.permissions

    @rx.var
    def can_work_maintenance(self) -> bool:
        return "maintenance.manage" in self.permissions or "maintenance.manage_assigned" in self.permissions

    @rx.var
    def can_report_occurrence(self) -> bool:
        return "occurrence.report" in self.permissions

    @rx.var
    def can_manage_occurrence(self) -> bool:
        return "occurrence.manage" in self.permissions

    @rx.var
    def can_work_occurrence(self) -> bool:
        return "occurrence.manage" in self.permissions or "occurrence.manage_assigned" in self.permissions

    @rx.var
    def can_read_reports(self) -> bool:
        return "reports.read" in self.permissions

    @rx.var
    def can_read_audit(self) -> bool:
        return "audit.read" in self.permissions

    @rx.var
    def can_manage_users(self) -> bool:
        return "users.manage" in self.permissions

    @rx.var
    def role_label(self) -> str:
        """Perfil do usuário logado em português."""
        return role_label(self.role)

    # ---- auxiliares de API para as subclasses ----
    async def call(self, method: str, group: str, path: str, **kwargs) -> Any:
        """Chama a API com o token da sessão. Um 401 encerra a sessão. Qualquer escrita (método diferente de GET)
        esvazia o cache de listas, para nenhuma tela mostrar dados de antes da alteração."""
        if method != "GET":
            self._list_cache = {}
        try:
            return await api.request(method, group, path, token=self._token, **kwargs)
        except api.ApiError as err:
            if err.unauthorized:
                self._clear_session()
            raise

    async def _cached_list(self, group: str, path: str, params: dict) -> dict:
        """GET de uma página de listagem, reaproveitado por LIST_CACHE_TTL segundos. Voltar a uma aba ou página
        já vista fica instantâneo e economiza requisições do plano Free do Xano. Sempre devolve o formato de
        página {"items", "nextPage", "itemsTotal"} (ver api.as_page)."""
        now = time.time()
        key = f"{group}|{path}|{json.dumps(params, sort_keys=True, default=str)}"
        hit = self._list_cache.get(key)
        if hit and now - hit[0] < LIST_CACHE_TTL:
            return hit[1]
        result = api.as_page(
            await self.call("GET", group, path, params=params), params.get("page", 1), params.get("per_page", 25)
        )
        fresh = {k: v for k, v in self._list_cache.items() if now - v[0] < LIST_CACHE_TTL}
        self._list_cache = fresh | {key: (now, result)}
        return result

    # ---- parâmetros da URL (router.url; router.page foi descontinuado no Reflex 0.8.1) ----
    def _query_param(self, key: str) -> str:
        """Valor de um parâmetro da query string (?chave=valor), ou "" quando ausente."""
        return self.router.url.query_parameters.get(key, "") or ""

    def _path_id(self) -> int | None:
        """O id numérico da rota dinâmica (ex.: /equipamentos/5/editar -> 5), ou None."""
        return next((int(part) for part in self.router.url.path.split("/") if part.isdigit()), None)

    def _clear_session(self):
        self._token = ""
        self.user_id = 0
        self.user_name = ""
        self.user_email = ""
        self.role = ""
        self.permissions = []
        self.must_change_password = False
        self._me_loaded_at = 0.0
        self._list_cache = {}

    async def _load_me(self):
        me = await api.request("GET", "auth", "auth/me", token=self._token)
        self.user_id = me["id"]
        self.user_name = me.get("name") or ""
        self.user_email = me.get("email") or ""
        self.role = me.get("role") or ""
        self.permissions = me.get("permissions") or []
        self.must_change_password = bool(me.get("deve_trocar_senha"))
        self._me_loaded_at = time.time()

    # ---- eventos ----
    @rx.event
    async def login(self, form: dict):
        self.login_error = ""
        email = (form.get("email") or "").strip().lower()
        password = form.get("password") or ""
        if not email or not password:
            self.login_error = "Informe e-mail e senha."
            return
        self.login_loading = True
        yield
        try:
            result = await api.request("POST", "auth", "auth/login", json={"email": email, "password": password})
            self._token = result["authToken"]
            await self._load_me()
        except api.ApiError as err:
            self._clear_session()
            self.login_error = "E-mail ou senha inválidos." if err.status in (401, 403) else err.message
            return
        finally:
            self.login_loading = False
        yield rx.redirect("/trocar-senha" if self.must_change_password else "/painel")

    @rx.event
    def logout(self):
        self._clear_session()
        return rx.redirect("/login")

    async def _guard(self, *permissions: str) -> list | None:
        """Guard do on_load das páginas. Atualiza o perfil quando ele tem mais de PROFILE_TTL segundos (mudanças de
        perfil, permissão ou habilitação aparecem na interface em até esse tempo; a API aplica na hora) e devolve
        eventos de redirecionamento quando não há sessão ou nenhuma das permissões informadas é concedida;
        devolve None quando a página pode carregar."""
        if not self._token:
            self._clear_session()
            return [rx.redirect("/login")]
        if time.time() - self._me_loaded_at > PROFILE_TTL:
            try:
                await self._load_me()
            except api.ApiError:
                self._clear_session()
                return [rx.redirect("/login")]
        if self.must_change_password:
            # Senha temporária ainda ativa: nada mais pode ser usado até ela ser trocada
            return [rx.redirect("/trocar-senha")]
        if permissions and not any(p in self.permissions for p in permissions):
            # Nunca redirecionar para outra página protegida (ex.: "/painel"): isso entra em loop quando ela também é negada
            return [rx.redirect("/sem-acesso")]
        return None

    async def _fetch_all(self, group: str, path: str, params: dict | None = None, page_size: int = 200, limit: int = 5000) -> list[dict]:
        """Segue a paginação até a última página (com limite) para as listas de opções ficarem completas."""
        items: list[dict] = []
        page = 1
        while len(items) < limit:
            result = await self.call("GET", group, path, params=(params or {}) | {"page": page, "per_page": page_size})
            if isinstance(result, list):
                # O Xano ignorou a paginação e devolveu tudo de uma vez (ver api.as_page)
                return result[:limit]
            items.extend(result["items"])
            if result.get("nextPage") is None:
                break
            page += 1
        return items

    @rx.event
    async def require_login(self):
        return await self._guard()
