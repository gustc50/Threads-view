"""
Diagnostico da conexao com a Threads API.

Faz uma serie de chamadas isoladas e devolve o resultado CRU de cada uma
(status HTTP + JSON completo, incluindo fbtrace_id/error_subcode), para
identificar a causa real de erros como o code 1 "An unknown error occurred".

Nenhuma chamada aqui usa retry ou mascara o erro: queremos ver tudo.
"""

from __future__ import annotations

import requests

from settings import BASE_URL, ENDPOINT_KEYWORD_SEARCH

TIMEOUT = 30


def _get(caminho: str, params: dict) -> dict:
    """Faz uma chamada e devolve um resumo cru do resultado."""
    url = f"{BASE_URL}{caminho}"
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return {"ok": False, "status": None, "erro_rede": str(exc), "resposta": None}

    try:
        corpo = resp.json()
    except ValueError:
        corpo = {"_raw": resp.text[:500]}

    return {
        "ok": resp.status_code < 400,
        "status": resp.status_code,
        "resposta": corpo,
    }


def _mascara_params(params: dict) -> dict:
    """Nao vaza o token no relatorio."""
    p = dict(params)
    if "access_token" in p:
        p["access_token"] = "***"
    return p


def rodar_diagnostico(access_token: str) -> list[dict]:
    """
    Roda os testes em ordem, do mais basico ao mais completo.
    Retorna uma lista de etapas com o resultado de cada uma.
    """
    if not access_token:
        return [{
            "titulo": "Token ausente",
            "params": {},
            "resultado": {"ok": False, "status": None,
                          "resposta": {"dica": "Salve um token na aba Configuracoes."}},
        }]

    etapas = []

    # 1) Perfil do usuario -> valida o token e a permissao threads_basic
    etapas.append({
        "titulo": "1. Perfil (valida token + threads_basic)",
        "caminho": "/me",
        "params": {"fields": "id,username", "access_token": access_token},
    })

    # 2) keyword_search minimo com TOP (so o id)
    etapas.append({
        "titulo": "2. Busca minima TOP (fields=id)",
        "caminho": ENDPOINT_KEYWORD_SEARCH,
        "params": {"q": "teste", "search_type": "TOP", "fields": "id",
                   "access_token": access_token},
    })

    # 3) keyword_search minimo com RECENT (so o id)
    etapas.append({
        "titulo": "3. Busca minima RECENT (fields=id)",
        "caminho": ENDPOINT_KEYWORD_SEARCH,
        "params": {"q": "teste", "search_type": "RECENT", "fields": "id",
                   "access_token": access_token},
    })

    # 4) keyword_search com todos os campos usados pelo app
    etapas.append({
        "titulo": "4. Busca completa TOP (todos os campos)",
        "caminho": ENDPOINT_KEYWORD_SEARCH,
        "params": {"q": "teste", "search_type": "TOP",
                   "fields": "id,text,username,timestamp,permalink",
                   "access_token": access_token},
    })

    saida = []
    for etapa in etapas:
        resultado = _get(etapa["caminho"], etapa["params"])
        saida.append({
            "titulo": etapa["titulo"],
            "params": _mascara_params(etapa["params"]),
            "resultado": resultado,
        })
    return saida
