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

from collector import run_collection
from settings import (
    KEYWORDS_FILE,
    OUTPUT_XLSX,
    load_config,
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

    resumo = run_collection(
        cfg=cfg,
        keywords=keywords,
        search_type=search_type,
        log_fn=log.info,
    )

    log.info("Planilha: %s", OUTPUT_XLSX)
    if resumo["token_invalido"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
