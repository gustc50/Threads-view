"""
Ponto de entrada do monitor de Threads.

Uso:
    python main.py
    python main.py --tipo RECENT
    python main.py --tipo TOP
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from settings import (
    KEYWORDS_FILE,
    OUTPUT_XLSX,
    SEEN_IDS_FILE,
    load_config,
)
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


def _configurar_log() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def carregar_keywords(path: Path) -> list[str]:
    """Le keywords.txt ignorando comentarios e linhas vazias."""
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de palavras-chave nao encontrado: {path}. "
            "Crie o arquivo com uma palavra-chave por linha."
        )

    palavras: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for linha in fh:
            texto = linha.strip()
            if not texto or texto.startswith("#"):
                continue
            palavras.append(texto)
    return palavras


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Monitor de publicacoes do Threads por palavras-chave."
    )
    p.add_argument(
        "--tipo",
        choices=["RECENT", "TOP"],
        default=None,
        help="Tipo de busca. Sobrepoe o valor de SEARCH_TYPE do .env.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _configurar_log()
    log = logging.getLogger("main")

    args = parse_args(argv)
    cfg = load_config()

    if not cfg.is_valid():
        log.error(
            "Token de acesso nao configurado. "
            "Preencha THREADS_ACCESS_TOKEN no .env ou TEST_ACCESS_TOKEN em settings.py."
        )
        return 2

    search_type = (args.tipo or cfg.search_type).upper()

    try:
        keywords = carregar_keywords(KEYWORDS_FILE)
    except FileNotFoundError as exc:
        log.error(str(exc))
        return 2

    if not keywords:
        log.warning("keywords.txt esta vazio. Nada a fazer.")
        return 0

    seen = load_seen_ids(SEEN_IDS_FILE)
    log.info("Iniciando coleta | tipo=%s | palavras=%d | ids_ja_vistos=%d",
             search_type, len(keywords), len(seen))

    total_novos = 0

    for kw in keywords:
        try:
            posts = list(search_keyword(
                keyword=kw,
                access_token=cfg.access_token,
                search_type=search_type,
                max_pages=cfg.max_pages,
            ))
        except InvalidTokenError as exc:
            log.error("%s", exc)
            return 3
        except RateLimitError as exc:
            log.error("Rate limit persistente para '%s': %s", kw, exc)
            continue
        except ThreadsAPIError as exc:
            log.error("Erro na API para '%s': %s", kw, exc)
            continue

        novos, ids_novos = filter_new_posts(posts, seen)
        linhas = [build_row(kw, p) for p in novos]
        append_rows(OUTPUT_XLSX, linhas)

        seen |= ids_novos
        total_novos += len(novos)

        log.info("'%s': %d publicacoes novas (de %d retornadas)",
                 kw, len(novos), len(posts))

    save_seen_ids(SEEN_IDS_FILE, seen)
    log.info("Coleta finalizada. Total de novas publicacoes: %d", total_novos)
    log.info("Planilha: %s", OUTPUT_XLSX)
    return 0


if __name__ == "__main__":
    sys.exit(main())
