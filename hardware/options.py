"""Loads select options (locations, models, users, ...) shared by several pages."""

import datetime as dt
import os
from zoneinfo import ZoneInfo

import reflex as rx

from . import api
from .state import AuthState


class OptionsState(AuthState):
    localizacoes: list[dict] = []
    categorias: list[dict] = []
    fabricantes: list[dict] = []
    modelos: list[dict] = []
    componentes: list[dict] = []
    # Assignable users, per area (only users whose role can work on that area)
    responsaveis_manutencao: list[dict] = []
    responsaveis_ocorrencia: list[dict] = []

    # Equipment is too large for a fixed option list (up to 10,000+): forms search it instead
    equip_query: str = ""
    equip_options: list[dict] = []
    equip_searching: bool = False

    async def _load_options(self, *kinds: str):
        """Fetch active options as [{value, label}] lists, following pagination so no option is cut off.
        Errors leave the lists empty."""
        try:
            if "localizacoes" in kinds:
                rows = await self.call("GET", "inventory", "localizacoes")
                self.localizacoes = [
                    {"value": str(r["id"]), "label": r["nome"] + (f" ({r['parent']})" if r.get("parent") else "")}
                    for r in rows
                ]
            if "categorias" in kinds:
                rows = await self.call("GET", "inventory", "categorias")
                self.categorias = [{"value": str(r["id"]), "label": r["nome"]} for r in rows]
            if "fabricantes" in kinds:
                rows = await self._fetch_all("inventory", "fabricantes")
                self.fabricantes = [{"value": str(r["id"]), "label": r["nome"]} for r in rows]
            if "modelos" in kinds:
                rows = await self._fetch_all("inventory", "modelos")
                self.modelos = [{"value": str(r["id"]), "label": f"{r['nome']} — {r['fabricante']} / {r['categoria']}"} for r in rows]
            if "componentes" in kinds:
                rows = await self._fetch_all("inventory", "componentes")
                self.componentes = [{"value": str(r["id"]), "label": r["nome"]} for r in rows]
            if "responsaveis_manutencao" in kinds:
                rows = await self.call("GET", "maintenance", "responsaveis", params={"area": "maintenance"})
                self.responsaveis_manutencao = [{"value": str(r["id"]), "label": r["name"]} for r in rows]
            if "responsaveis_ocorrencia" in kinds:
                rows = await self.call("GET", "maintenance", "responsaveis", params={"area": "occurrence"})
                self.responsaveis_ocorrencia = [{"value": str(r["id"]), "label": r["name"]} for r in rows]
        except api.ApiError:
            pass

    async def _search_equipment(self, query: str = "", preselect_id: str = ""):
        """Search active equipment by name, asset or serial number (first 25 matches).
        preselect_id keeps a pre-filtered equipment item selectable even when it is not in the results."""
        self.equip_searching = True
        try:
            page = await self.call("GET", "inventory", "equipamentos", params={"q": query.strip() or None, "per_page": 25})
            options = [{"value": str(e["id"]), "label": f"{e['numero_patrimonio']} — {e['nome']}"} for e in page["items"]]
            if preselect_id and preselect_id not in {o["value"] for o in options}:
                try:
                    e = await self.call("GET", "inventory", f"equipamentos/{preselect_id}")
                    options.insert(0, {"value": str(e["id"]), "label": f"{e['numero_patrimonio']} — {e['nome']}"})
                except api.ApiError:
                    pass
            self.equip_options = options
        except api.ApiError:
            self.equip_options = []
        finally:
            self.equip_searching = False

    @rx.event
    async def search_equipment(self, value: str):
        """Debounced search-as-you-type (no Enter key needed, so it never submits the surrounding form)."""
        self.equip_query = value
        await self._search_equipment(value)


def to_int(value) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def to_float(value) -> float | None:
    try:
        return float(str(value).replace(",", ".")) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def opt_text(value) -> str | None:
    """Form text -> API value: blank becomes None (not sent)."""
    value = (value or "").strip()
    return value or None


# Wall-clock times typed by users are interpreted (and shown) in the institution's timezone
TZ_NAME = os.environ.get("HHM_TIMEZONE", "America/Sao_Paulo")
TZ = ZoneInfo(TZ_NAME)


def local_to_ms(value: str) -> int | None:
    """datetime-local form value (institution wall time) -> epoch ms."""
    if not value:
        return None
    try:
        return int(dt.datetime.fromisoformat(value).replace(tzinfo=TZ).timestamp() * 1000)
    except ValueError:
        return None


def now_local_input() -> str:
    """Current institution time formatted for a datetime-local input."""
    return dt.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M")


def ms_to_local(value) -> str:
    return dt.datetime.fromtimestamp(value / 1000, TZ).strftime("%d/%m/%Y %H:%M") if isinstance(value, (int, float)) else ""
