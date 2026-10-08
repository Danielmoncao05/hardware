"""Carrega as opções dos selects (localizações, modelos, usuários, ...) compartilhadas por várias páginas."""

import datetime as dt
import os
import time
from zoneinfo import ZoneInfo

import reflex as rx

from . import api
from .state import AuthState

# Segundos em que uma lista de opções carregada é reaproveitada entre páginas
OPTIONS_TTL = 300


class OptionsState(AuthState):
    localizacoes: list[dict] = []
    categorias: list[dict] = []
    fabricantes: list[dict] = []
    modelos: list[dict] = []
    componentes: list[dict] = []
    # Usuários atribuíveis, por área (só usuários cujo perfil pode atuar nessa área)
    responsaveis_manutencao: list[dict] = []
    responsaveis_ocorrencia: list[dict] = []

    # Há equipamentos demais para uma lista fixa de opções (10.000+): os formulários fazem busca
    equip_query: str = ""
    equip_options: list[dict] = []
    equip_searching: bool = False

    # Momento (time.time) em que cada lista de opções foi carregada; listas com menos de OPTIONS_TTL segundos
    # são reaproveitadas entre páginas para poupar requisições ao Xano
    _options_at: dict[str, float] = {}

    async def _fetch_options(self, kind: str) -> list[dict]:
        """Linhas ativas de um tipo de opção, seguindo a paginação para nenhuma opção ficar de fora."""
        if kind in ("localizacoes", "categorias"):
            return await self.call("GET", "inventory", kind)
        if kind in ("fabricantes", "modelos", "componentes"):
            return await self._fetch_all("inventory", kind)
        area = "maintenance" if kind == "responsaveis_manutencao" else "occurrence"
        return await self.call("GET", "maintenance", "responsaveis", params={"area": area})

    def _set_options(self, kind: str, rows: list[dict]):
        """Converte as linhas em [{value, label}] e marca a lista como recém-carregada."""
        if kind == "localizacoes":
            options = [{"value": str(r["id"]), "label": r["nome"] + (f" ({r['parent']})" if r.get("parent") else "")} for r in rows]
        elif kind == "modelos":
            options = [{"value": str(r["id"]), "label": f"{r['nome']} — {r['fabricante']} / {r['categoria']}"} for r in rows]
        elif kind.startswith("responsaveis"):
            options = [{"value": str(r["id"]), "label": r["name"]} for r in rows]
        else:
            options = [{"value": str(r["id"]), "label": r["nome"]} for r in rows]
        setattr(self, kind, options)
        self._options_at = self._options_at | {kind: time.time()}

    async def _load_options(self, *kinds: str, force: bool = False):
        """Carrega as listas de opções pedidas, reaproveitando as que têm menos de OPTIONS_TTL segundos
        (force=True sempre busca de novo). Um erro deixa só a lista daquele tipo como estava."""
        now = time.time()
        for kind in kinds:
            if not force and now - self._options_at.get(kind, 0.0) < OPTIONS_TTL:
                continue
            try:
                self._set_options(kind, await self._fetch_options(kind))
            except api.ApiError:
                pass

    async def _load_complete(self, group: str, path: str, params: dict) -> list[dict] | None:
        """Todos os registros da consulta quando cabem em uma página da API (até 100); senão None.
        Com a lista completa em mãos, as abas e a paginação são filtradas aqui, sem novas requisições."""
        result = await self._cached_list(group, path, params | {"page": 1, "per_page": 100})
        return result["items"] if result.get("nextPage") is None else None

    async def _search_equipment(self, query: str = "", preselect_id: str = ""):
        """Busca equipamentos ativos por nome, patrimônio ou número de série (primeiros 25 resultados).
        preselect_id mantém selecionável um equipamento pré-filtrado mesmo que ele não esteja nos resultados."""
        self.equip_searching = True
        try:
            page = api.as_page(await self.call("GET", "inventory", "equipamentos", params={"q": query.strip() or None, "per_page": 25}))
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
        """Busca enquanto digita, com debounce (dispensa o Enter, então nunca envia o formulário em volta)."""
        self.equip_query = value
        await self._search_equipment(value)


def page_slice(rows: list[dict], page: int, size: int = 25) -> tuple[list[dict], bool]:
    """Uma página de uma lista já carregada: (itens da página, se existe próxima)."""
    start = (page - 1) * size
    return rows[start : start + size], len(rows) > start + size


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
    """Texto do formulário -> valor da API: vazio vira None (não é enviado)."""
    value = (value or "").strip()
    return value or None


# Horários digitados pelos usuários são interpretados (e exibidos) no fuso da instituição
TZ_NAME = os.environ.get("HHM_TIMEZONE", "America/Sao_Paulo")
TZ = ZoneInfo(TZ_NAME)


def local_to_ms(value: str) -> int | None:
    """Valor de um campo datetime-local (horário local da instituição) -> epoch em ms."""
    if not value:
        return None
    try:
        return int(dt.datetime.fromisoformat(value).replace(tzinfo=TZ).timestamp() * 1000)
    except ValueError:
        return None


def now_local_input() -> str:
    """Horário atual da instituição, formatado para um campo datetime-local."""
    return dt.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M")


def ms_to_local(value) -> str:
    return dt.datetime.fromtimestamp(value / 1000, TZ).strftime("%d/%m/%Y %H:%M") if isinstance(value, (int, float)) else ""
