"""Thin async client for the Xano API groups.

The frontend never touches persistence directly: every read and write goes through these
endpoints, which enforce authentication, permissions, validation, and auditing.
"""

import asyncio
import os
from typing import Any

import httpx

XANO_BASE_URL = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")

# API group canonicals (see xano/api/*/api_group.xs and authentication.xs)
GROUPS = {
    "auth": os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc"),
    "users": os.environ.get("XANO_USERS_GROUP", "hhm149197-users"),
    "inventory": os.environ.get("XANO_INVENTORY_GROUP", "hhm149197-inventory"),
    "maintenance": os.environ.get("XANO_MAINTENANCE_GROUP", "hhm149197-maintenance"),
    "reports": os.environ.get("XANO_REPORTS_GROUP", "hhm149197-reports"),
}

TIMEOUT = httpx.Timeout(20.0)

# HTTP 429 handling: retries and the longest wait between them (seconds)
RATE_LIMIT_RETRIES = 2
RATE_LIMIT_MAX_WAIT = 8.0


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """Honor Retry-After when present, otherwise back off 2s, 4s, ...; capped so a page never hangs long."""
    try:
        wait = float(response.headers.get("Retry-After", ""))
    except ValueError:
        wait = 2.0 * (attempt + 1)
    return min(max(wait, 0.5), RATE_LIMIT_MAX_WAIT)


class ApiError(Exception):
    """An error response from the API, carrying a user-presentable message."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message

    @property
    def unauthorized(self) -> bool:
        return self.status == 401


def _url(group: str, path: str) -> str:
    return f"{XANO_BASE_URL}/api:{GROUPS[group]}/{path.lstrip('/')}"


def _clean(params: dict[str, Any] | None) -> dict[str, Any]:
    """Drop empty values so optional API filters stay unset."""
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
    """Call an endpoint and return its decoded JSON (or text when raw=True)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for attempt in range(RATE_LIMIT_RETRIES + 1):
                response = await client.request(
                    method,
                    _url(group, path),
                    headers=headers,
                    params=_clean(params),
                    # None means "not sent"; "" is kept because the API uses it to clear a field
                    json=None if json is None else {k: v for k, v in json.items() if v is not None},
                )
                if response.status_code != 429 or attempt == RATE_LIMIT_RETRIES:
                    break
                # Rate limited (the plan allows a few requests per window): wait briefly and retry
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
