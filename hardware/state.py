"""Session and permission state shared by every page.

The Xano auth token lives only in the backend-only var `_token`: Reflex never sends
underscore vars to the browser. Permission flags below only decide which controls are
shown; the API re-checks every operation.
"""

from typing import Any

import reflex as rx

from . import api


class AuthState(rx.State):
    _token: str = ""

    user_id: int = 0
    user_name: str = ""
    user_email: str = ""
    role: str = ""
    permissions: list[str] = []
    # Account created with a temporary password: the user must replace it before using the system.
    # The API grants no permissions meanwhile; this flag only routes the UI to /trocar-senha.
    must_change_password: bool = False

    login_error: str = ""
    login_loading: bool = False

    # ---- permission flags (UI only) ----
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

    # ---- API helpers for subclasses ----
    async def call(self, method: str, group: str, path: str, **kwargs) -> Any:
        """Call the API with the session token. A 401 clears the session."""
        try:
            return await api.request(method, group, path, token=self._token, **kwargs)
        except api.ApiError as err:
            if err.unauthorized:
                self._clear_session()
            raise

    def _clear_session(self):
        self._token = ""
        self.user_id = 0
        self.user_name = ""
        self.user_email = ""
        self.role = ""
        self.permissions = []
        self.must_change_password = False

    async def _load_me(self):
        me = await api.request("GET", "auth", "auth/me", token=self._token)
        self.user_id = me["id"]
        self.user_name = me.get("name") or ""
        self.user_email = me.get("email") or ""
        self.role = me.get("role") or ""
        self.permissions = me.get("permissions") or []
        self.must_change_password = bool(me.get("deve_trocar_senha"))

    # ---- events ----
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
        yield rx.redirect("/trocar-senha" if self.must_change_password else "/")

    @rx.event
    def logout(self):
        self._clear_session()
        return rx.redirect("/login")

    async def _guard(self, *permissions: str) -> list | None:
        """Page on_load guard. Refreshes the profile (so role, permission, or enabled-state
        changes apply immediately) and returns redirect events when the session is missing or
        none of the given permissions is held; returns None when the page may load."""
        if not self._token:
            self._clear_session()
            return [rx.redirect("/login")]
        try:
            await self._load_me()
        except api.ApiError:
            self._clear_session()
            return [rx.redirect("/login")]
        if self.must_change_password:
            # Temporary password still in place: nothing else is usable until it is replaced
            return [rx.redirect("/trocar-senha")]
        if permissions and not any(p in self.permissions for p in permissions):
            # Never redirect to another guarded page (e.g. "/"): that loops when it is denied too
            return [rx.redirect("/sem-acesso")]
        return None

    async def _fetch_all(self, group: str, path: str, params: dict | None = None, page_size: int = 200, limit: int = 5000) -> list[dict]:
        """Follow pagination until the last page (bounded by limit) so option lists are complete."""
        items: list[dict] = []
        page = 1
        while len(items) < limit:
            result = await self.call("GET", group, path, params=(params or {}) | {"page": page, "per_page": page_size})
            items.extend(result["items"])
            if result.get("nextPage") is None:
                break
            page += 1
        return items

    @rx.event
    async def require_login(self):
        return await self._guard()
