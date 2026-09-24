"""
Renova o long-lived token da Threads API e atualiza o arquivo .env.

Endpoint oficial:
    GET https://graph.threads.net/refresh_access_token
        ?grant_type=th_refresh_token
        &access_token=<TOKEN_ATUAL>

Referencia: https://developers.facebook.com/docs/threads/get-started/long-lived-tokens
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from settings import ENV_FILE, load_config

REFRESH_URL = "https://graph.threads.net/refresh_access_token"
REQUEST_TIMEOUT = 30

log = logging.getLogger("refresh_token")


def _atualiza_env(path: Path, novo_token: str) -> None:
    """Substitui THREADS_ACCESS_TOKEN dentro do .env, mantendo o resto."""
    linhas: list[str] = []
    achou = False

    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            for linha in fh:
                if linha.strip().startswith("THREADS_ACCESS_TOKEN="):
                    linhas.append(f"THREADS_ACCESS_TOKEN={novo_token}\n")
                    achou = True
                else:
                    linhas.append(linha)

    if not achou:
        linhas.append(f"THREADS_ACCESS_TOKEN={novo_token}\n")

    with path.open("w", encoding="utf-8") as fh:
        fh.writelines(linhas)


def refresh(access_token: str) -> dict:
    """Faz a chamada de refresh e devolve o payload."""
    resp = requests.get(
        REFRESH_URL,
        params={
            "grant_type": "th_refresh_token",
            "access_token": access_token,
        },
        timeout=REQUEST_TIMEOUT,
    )
    payload = {}
    try:
        payload = resp.json()
    except ValueError:
        pass

    if resp.status_code >= 400:
        raise RuntimeError(
            f"Falha no refresh (HTTP {resp.status_code}): {payload}"
        )
    return payload


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = load_config()
    if not cfg.access_token:
        log.error("Nenhum token encontrado para renovar.")
        return 2

    try:
        payload = refresh(cfg.access_token)
    except (requests.RequestException, RuntimeError) as exc:
        log.error("Erro ao renovar token: %s", exc)
        return 1

    novo_token = payload.get("access_token")
    expires_in = payload.get("expires_in")  # em segundos

    if not novo_token:
        log.error("Resposta sem access_token: %s", payload)
        return 1

    _atualiza_env(ENV_FILE, novo_token)
    log.info("Token renovado com sucesso e salvo em %s", ENV_FILE)

    if expires_in:
        expira_em = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        dias = int(expires_in) // 86400
        log.info("Novo token expira em ~%d dias (%s UTC)",
                 dias, expira_em.strftime("%Y-%m-%d %H:%M:%S"))
        if dias < 10:
            log.warning(
                "ATENCAO: faltam menos de 10 dias para expirar. "
                "Rode refresh_token.py de novo antes disso."
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
