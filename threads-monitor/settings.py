"""
=========================================================
 ABA DE CONFIGURACOES
=========================================================
Este arquivo centraliza todas as configuracoes do projeto.

Prioridade de leitura:
    1. Variaveis definidas no arquivo .env (recomendado).
    2. Valores colocados manualmente logo abaixo (uteis para
       testes rapidos sem precisar mexer no .env).

>>>>> COLOQUE AQUI O CODIGO/TOKEN DA API PARA TESTAR <<<<<
Basta preencher a variavel TEST_ACCESS_TOKEN abaixo.
Se ela estiver preenchida, sera usada mesmo sem .env.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------
# >>> AREA DE TESTE RAPIDO (opcional) <<<
# Preencha para testar sem precisar criar o .env.
# Deixe vazio ("") em producao e use o .env.
# ---------------------------------------------------------
TEST_ACCESS_TOKEN: str = ""   # ex.: "THAA...seu_token..."
TEST_APP_ID: str = ""         # ex.: "1234567890"
TEST_APP_SECRET: str = ""     # ex.: "abcdef..."

# ---------------------------------------------------------
# Constantes do projeto
# ---------------------------------------------------------
BASE_URL = "https://graph.threads.net/v1.0"
ENDPOINT_KEYWORD_SEARCH = "/keyword_search"

# Campos padrao a serem retornados pela API para cada post
DEFAULT_FIELDS = "id,text,username,timestamp,permalink"

# Arquivos usados pela aplicacao
ROOT_DIR = Path(__file__).resolve().parent
KEYWORDS_FILE = ROOT_DIR / "keywords.txt"
SEEN_IDS_FILE = ROOT_DIR / "seen_ids.json"
OUTPUT_XLSX = ROOT_DIR / "resultados.xlsx"
ENV_FILE = ROOT_DIR / ".env"

# ---------------------------------------------------------
# Carrega variaveis do .env (se existir)
# ---------------------------------------------------------
load_dotenv(dotenv_path=ENV_FILE)


@dataclass
class Config:
    """Configuracoes efetivas usadas pelo programa."""
    access_token: str
    app_id: str
    app_secret: str
    max_pages: int
    search_type: str

    def is_valid(self) -> bool:
        return bool(self.access_token)


def _pick(env_key: str, fallback: str) -> str:
    """Le do ambiente ou usa o valor de teste como fallback."""
    value = os.getenv(env_key, "").strip()
    return value or fallback.strip()


def load_config() -> Config:
    """Constroi o objeto Config combinando .env e valores de teste."""
    max_pages_raw = os.getenv("MAX_PAGES", "3").strip() or "3"
    search_type = (os.getenv("SEARCH_TYPE", "RECENT").strip() or "RECENT").upper()

    try:
        max_pages = int(max_pages_raw)
    except ValueError:
        max_pages = 3

    if search_type not in ("RECENT", "TOP"):
        search_type = "RECENT"

    return Config(
        access_token=_pick("THREADS_ACCESS_TOKEN", TEST_ACCESS_TOKEN),
        app_id=_pick("THREADS_APP_ID", TEST_APP_ID),
        app_secret=_pick("THREADS_APP_SECRET", TEST_APP_SECRET),
        max_pages=max_pages,
        search_type=search_type,
    )


# ---------------------------------------------------------
# Helpers usados pela interface web para persistir mudancas
# ---------------------------------------------------------
_ENV_KEYS = (
    "THREADS_ACCESS_TOKEN",
    "THREADS_APP_ID",
    "THREADS_APP_SECRET",
    "MAX_PAGES",
    "SEARCH_TYPE",
)


def save_env(valores: dict[str, str]) -> None:
    """
    Grava/atualiza chaves no arquivo .env, preservando linhas nao
    relacionadas. Recarrega o ambiente em seguida.
    """
    existentes: dict[str, str] = {}
    outras_linhas: list[str] = []

    if ENV_FILE.exists():
        for linha in ENV_FILE.read_text(encoding="utf-8").splitlines():
            crua = linha.strip()
            if not crua or crua.startswith("#") or "=" not in crua:
                outras_linhas.append(linha)
                continue
            chave, _, valor = crua.partition("=")
            chave = chave.strip()
            if chave in _ENV_KEYS:
                existentes[chave] = valor
            else:
                outras_linhas.append(linha)

    for chave, valor in valores.items():
        if chave in _ENV_KEYS and valor is not None:
            existentes[chave] = str(valor)

    linhas = list(outras_linhas)
    for chave in _ENV_KEYS:
        if chave in existentes:
            linhas.append(f"{chave}={existentes[chave]}")

    ENV_FILE.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    # Recarrega para refletir imediatamente na mesma execucao
    load_dotenv(dotenv_path=ENV_FILE, override=True)


def load_keywords() -> list[str]:
    """Le keywords.txt ignorando comentarios e linhas vazias."""
    if not KEYWORDS_FILE.exists():
        return []
    palavras: list[str] = []
    for linha in KEYWORDS_FILE.read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#"):
            continue
        palavras.append(texto)
    return palavras


def save_keywords(palavras: list[str]) -> None:
    """Grava a lista de palavras-chave (uma por linha)."""
    linhas = [p.strip() for p in palavras if p.strip()]
    KEYWORDS_FILE.write_text("\n".join(linhas) + "\n", encoding="utf-8")
