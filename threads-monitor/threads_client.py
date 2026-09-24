"""
Cliente HTTP para o endpoint de Keyword Search da Threads API.

Documentacao oficial (Meta):
    https://developers.facebook.com/docs/threads/keyword-search

Regras aplicadas:
    - timeout em toda chamada;
    - trata rate limit (HTTP 429 ou codigos Meta 4/17/32/613) com espera
      e ate 3 tentativas;
    - percorre paginacao via paging.next respeitando MAX_PAGES;
    - erros de token/rede sao propagados como excecoes claras.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Iterator

import requests

from settings import BASE_URL, DEFAULT_FIELDS, ENDPOINT_KEYWORD_SEARCH

log = logging.getLogger(__name__)

# Codigos que a Meta usa para sinalizar limite de requisicoes
RATE_LIMIT_CODES = {4, 17, 32, 613}
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # segundos


class ThreadsAPIError(Exception):
    """Erro generico devolvido pela API do Threads."""


class InvalidTokenError(ThreadsAPIError):
    """Token expirado ou invalido."""


class RateLimitError(ThreadsAPIError):
    """Rate limit persistente apos as tentativas."""


def _sleep(seconds: float) -> None:
    """Wrapper para permitir monkeypatch em testes."""
    time.sleep(seconds)


def _is_rate_limited(status_code: int, payload: dict) -> bool:
    if status_code == 429:
        return True
    err = (payload or {}).get("error", {})
    return err.get("code") in RATE_LIMIT_CODES


def _is_invalid_token(status_code: int, payload: dict) -> bool:
    if status_code not in (400, 401):
        return False
    err = (payload or {}).get("error", {})
    # Meta usa code=190 para OAuth token invalido/expirado
    return err.get("code") == 190 or "OAuthException" in str(err.get("type", ""))


def _do_request(
    url: str,
    params: dict | None,
    session: requests.Session,
) -> dict:
    """Executa uma chamada HTTP com retry para rate limit."""
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            last_error = exc
            wait = 2 ** attempt
            log.warning("Erro de rede (%s). Tentativa %d/%d. Aguardando %ds...",
                        exc, attempt, MAX_RETRIES, wait)
            _sleep(wait)
            continue

        try:
            payload = resp.json()
        except ValueError:
            payload = {}

        if _is_invalid_token(resp.status_code, payload):
            raise InvalidTokenError(
                "Token invalido ou expirado. Rode refresh_token.py "
                "ou gere um novo token no painel da Meta."
            )

        if _is_rate_limited(resp.status_code, payload):
            wait = 30 * attempt  # 30s, 60s, 90s
            log.warning(
                "Rate limit atingido (status=%s). Tentativa %d/%d. Aguardando %ds...",
                resp.status_code, attempt, MAX_RETRIES, wait,
            )
            _sleep(wait)
            last_error = RateLimitError(str(payload))
            continue

        if resp.status_code >= 400:
            raise ThreadsAPIError(
                f"HTTP {resp.status_code} ao chamar {url}: {payload}"
            )

        return payload

    if isinstance(last_error, RateLimitError):
        raise last_error
    raise ThreadsAPIError(f"Falha apos {MAX_RETRIES} tentativas: {last_error}")


def search_keyword(
    keyword: str,
    access_token: str,
    search_type: str = "RECENT",
    max_pages: int = 3,
    fields: str = DEFAULT_FIELDS,
    session: requests.Session | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> Iterator[dict]:
    """
    Faz a busca por palavra-chave e itera por todas as paginas ate
    max_pages. Retorna um iterador de dicts (cada item = 1 post).
    """
    if sleep_fn is not None:
        global _sleep
        _sleep = sleep_fn  # facilita testes

    sess = session or requests.Session()
    url = f"{BASE_URL}{ENDPOINT_KEYWORD_SEARCH}"
    params = {
        "q": keyword,
        "search_type": search_type,
        "fields": fields,
        "access_token": access_token,
    }

    pages = 0
    while url and pages < max_pages:
        payload = _do_request(url, params, sess)
        pages += 1

        for item in payload.get("data", []) or []:
            yield item

        # A partir da segunda pagina o "next" ja carrega tudo na URL
        next_url = (payload.get("paging") or {}).get("next")
        if not next_url:
            break
        url = next_url
        params = None
