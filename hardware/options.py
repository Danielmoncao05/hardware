"""Carrega as opções dos selects (localizações, modelos, usuários, ...) compartilhadas por várias páginas."""

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
    # Usuários atribuíveis, por área (só usuários cujo perfil pode atuar nessa área)
    responsaveis_manutencao: list[dict] = []
    responsaveis_ocorrencia: list[dict] = []

    # Há equipamentos demais para uma lista fixa de opções (10.000+): os formulários fazem busca
    equip_query: str = ""
    equip_options: list[dict] = []
    equip_searching: bool = False

    async def _load_options(self, *kinds: str):
        """Busca as opções ativas como listas [{value, label}], seguindo a paginação para nenhuma opção ficar de fora.
        Em caso de erro, as listas ficam vazias."""
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
        """Busca equipamentos ativos por nome, patrimônio ou número de série (primeiros 25 resultados).
        preselect_id mantém selecionável um equipamento pré-filtrado mesmo que ele não esteja nos resultados."""
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
        """Busca enquanto digita, com debounce (dispensa o Enter, então nunca envia o formulário em volta)."""
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
