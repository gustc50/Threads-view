"""
Logica de coleta compartilhada entre a CLI (main.py) e o app web (app.py).

A funcao run_collection aceita um callback de log (log_fn) para que a
interface possa acompanhar o progresso em tempo real.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from settings import Config, OUTPUT_XLSX, SEEN_IDS_FILE
from storage import (
    append_rows,
    build_row,
    filter_new_posts,
    load_seen_ids,
    save_seen_ids,
)
from threads_client import (
    InvalidTokenError,
    RateLimitError,
    ThreadsAPIError,
    search_keyword,
)

LogFn = Callable[[str], None]


def run_collection(
    cfg: Config,
    keywords: list[str],
    search_type: str,
    log_fn: LogFn | None = None,
    output_xlsx: Path = OUTPUT_XLSX,
    seen_ids_file: Path = SEEN_IDS_FILE,
) -> dict:
    """
    Executa a coleta para todas as palavras-chave.

    Retorna um resumo:
        {
          "total_novos": int,
          "por_palavra": {kw: qtd_novos, ...},
          "erros": [str, ...],
          "token_invalido": bool,
        }
    """
    def log(msg: str) -> None:
        if log_fn:
            log_fn(msg)

    resumo = {
        "total_novos": 0,
        "por_palavra": {},
        "erros": [],
        "token_invalido": False,
    }

    seen = load_seen_ids(seen_ids_file)
    log(f"Iniciando coleta | tipo={search_type} | "
        f"palavras={len(keywords)} | ids_ja_vistos={len(seen)}")

    for kw in keywords:
        try:
            posts = list(search_keyword(
                keyword=kw,
                access_token=cfg.access_token,
                search_type=search_type,
                max_pages=cfg.max_pages,
            ))
        except InvalidTokenError as exc:
            log(f"ERRO: {exc}")
            resumo["erros"].append(str(exc))
            resumo["token_invalido"] = True
            break
        except RateLimitError as exc:
            msg = f"Rate limit persistente para '{kw}': {exc}"
            log(f"ERRO: {msg}")
            resumo["erros"].append(msg)
            continue
        except ThreadsAPIError as exc:
            msg = f"Erro na API para '{kw}': {exc}"
            log(f"ERRO: {msg}")
            resumo["erros"].append(msg)
            continue

        novos, ids_novos = filter_new_posts(posts, seen)
        linhas = [build_row(kw, p) for p in novos]
        append_rows(output_xlsx, linhas)

        seen |= ids_novos
        resumo["total_novos"] += len(novos)
        resumo["por_palavra"][kw] = len(novos)

        log(f"'{kw}': {len(novos)} publicacoes novas (de {len(posts)} retornadas)")

    save_seen_ids(seen_ids_file, seen)
    log(f"Coleta finalizada. Total de novas publicacoes: {resumo['total_novos']}")
    return resumo
