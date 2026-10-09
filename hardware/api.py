"""Cliente assíncrono enxuto para os grupos de API do Xano.

O frontend nunca acessa a persistência diretamente: toda leitura e escrita passa por estes
endpoints, que aplicam autenticação, permissões, validação e auditoria.
"""

import asyncio
import os
from typing import Any

import httpx

XANO_BASE_URL = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")

# Identificadores canônicos dos grupos de API (ver xano/api/*/api_group.xs e authentication.xs)
GROUPS = {
    "auth": os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc"),
    "users": os.environ.get("XANO_USERS_GROUP", "hhm149197-users"),
    "inventory": os.environ.get("XANO_INVENTORY_GROUP", "hhm149197-inventory"),
    "maintenance": os.environ.get("XANO_MAINTENANCE_GROUP", "hhm149197-maintenance"),
    "reports": os.environ.get("XANO_REPORTS_GROUP", "hhm149197-reports"),
}

TIMEOUT = httpx.Timeout(20.0)

# Conexões com o Xano reaproveitadas entre requisições (keep-alive): abrir TCP + TLS a cada chamada custava
# ~0,4 s; três chamadas seguidas caíam de ~1,8 s para ~0,9 s com a conexão aberta (medido em 2026-10-09).
LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10, keepalive_expiry=30.0)
_client: tuple[asyncio.AbstractEventLoop, httpx.AsyncClient] | None = None


def client() -> httpx.AsyncClient:
    """Cliente HTTP compartilhado do event loop atual (um novo quando o loop muda, por exemplo nos testes)."""
    global _client
    loop = asyncio.get_running_loop()
    if _client is None or _client[0] is not loop or _client[1].is_closed:
        _client = (loop, httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS))
    return _client[1]

# Tratamento do HTTP 429: número de novas tentativas e a maior espera entre elas (segundos)
RATE_LIMIT_RETRIES = 2
RATE_LIMIT_MAX_WAIT = 8.0


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """Respeita o Retry-After quando existe; senão espera 2s, 4s, ...; com limite para a página nunca travar muito."""
    try:
        wait = float(response.headers.get("Retry-After", ""))
    except ValueError:
        wait = 2.0 * (attempt + 1)
    return min(max(wait, 0.5), RATE_LIMIT_MAX_WAIT)


class ApiError(Exception):
    """Resposta de erro da API, com uma mensagem que pode ser mostrada ao usuário."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message

    @property
    def unauthorized(self) -> bool:
        return self.status == 401


def as_page(result: Any, page: int = 1, per_page: int = 25) -> dict:
    """Normaliza a resposta de uma listagem paginada para {"items", "nextPage", "itemsTotal"}.

    O Xano às vezes ignora o bloco de paginação e devolve a lista inteira (sem metadados). Nesse caso a página
    pedida é recortada aqui, para as telas funcionarem igual nos dois formatos."""
    if isinstance(result, dict):
        return result
    rows = list(result or [])
    start = (page - 1) * per_page
    return {
        "items": rows[start : start + per_page],
        "nextPage": page + 1 if len(rows) > start + per_page else None,
        "itemsTotal": len(rows),
    }


def _url(group: str, path: str) -> str:
    return f"{XANO_BASE_URL}/api:{GROUPS[group]}/{path.lstrip('/')}"


def _clean(params: dict[str, Any] | None) -> dict[str, Any]:
    """Remove valores vazios para que filtros opcionais da API fiquem sem valor."""
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None and v != ""}


async def request(
    method: str,
    group: str,
    path: str,
    token: str = "",
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    raw: bool = False,
) -> Any:
    """Chama um endpoint e devolve o JSON decodificado (ou o texto quando raw=True)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    http = client()

    async def send() -> httpx.Response:
        try:
            return await http.request(
                method,
                _url(group, path),
                headers=headers,
                params=_clean(params),
                # None significa "não enviar"; "" é mantido porque a API usa isso para limpar um campo
                json=None if json is None else {k: v for k, v in json.items() if v is not None},
            )
        except (httpx.RemoteProtocolError, httpx.ReadError) as err:
            # Conexão parada fechada pelo servidor: uma leitura pode ser repetida numa conexão nova; uma gravação
            # não (ela pode ter acontecido), então o erro sobe
            if method != "GET":
                raise err
            return await http.request(method, _url(group, path), headers=headers, params=_clean(params))

    try:
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            response = await send()
            if response.status_code != 429 or attempt == RATE_LIMIT_RETRIES:
                break
            # Limite de requisições (o plano permite poucas por janela): espera um pouco e tenta de novo
            await asyncio.sleep(_retry_delay(response, attempt))
    except httpx.HTTPError:
        raise ApiError(0, "Não foi possível contatar o servidor. Tente novamente.") from None

    if response.status_code >= 400:
        message = "Ocorreu um erro inesperado."
        try:
            message = response.json().get("message") or message
        except ValueError:
            pass
        if response.status_code == 429:
            message = "O servidor recebeu muitas requisições em pouco tempo. Aguarde alguns segundos e tente novamente."
        elif response.status_code == 401:
            message = "Sua sessão expirou. Entre novamente."
        elif response.status_code == 403 and message in ("Access denied.", "Ocorreu um erro inesperado."):
            message = "Você não tem permissão para esta ação."
        raise ApiError(response.status_code, message)

    if raw:
        return response.text
    if not response.content:
        return None
    return response.json()
