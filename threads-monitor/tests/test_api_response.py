"""Testa o cliente da API com respostas simuladas (mock)."""

from unittest.mock import MagicMock

import pytest

import threads_client
from threads_client import (
    InvalidTokenError,
    RateLimitError,
    ThreadsAPIError,
    search_keyword,
)


class FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


def _sessao_mock(responses):
    """Cria uma session cujo .get() retorna cada FakeResponse em sequencia."""
    sess = MagicMock()
    sess.get.side_effect = responses
    return sess


def test_resposta_vazia_nao_gera_erro():
    sess = _sessao_mock([FakeResponse(200, {"data": []})])

    resultado = list(search_keyword(
        keyword="qualquer",
        access_token="fake",
        max_pages=1,
        session=sess,
    ))

    assert resultado == []
    sess.get.assert_called_once()


def test_data_ausente_e_tratado_como_lista_vazia():
    sess = _sessao_mock([FakeResponse(200, {})])

    resultado = list(search_keyword(
        keyword="x",
        access_token="fake",
        max_pages=1,
        session=sess,
    ))

    assert resultado == []


def test_paginacao_percorre_ate_max_pages():
    respostas = [
        FakeResponse(200, {
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {"next": "https://graph.threads.net/next-page-1"},
        }),
        FakeResponse(200, {
            "data": [{"id": "3"}],
            "paging": {"next": "https://graph.threads.net/next-page-2"},
        }),
        FakeResponse(200, {"data": [{"id": "4"}]}),  # nao deve ser chamada
    ]
    sess = _sessao_mock(respostas)

    resultado = list(search_keyword(
        keyword="x",
        access_token="fake",
        max_pages=2,
        session=sess,
    ))

    assert [p["id"] for p in resultado] == ["1", "2", "3"]
    assert sess.get.call_count == 2


def test_token_invalido_lanca_excecao():
    sess = _sessao_mock([FakeResponse(401, {
        "error": {"code": 190, "message": "Invalid OAuth token"}
    })])

    with pytest.raises(InvalidTokenError):
        list(search_keyword(
            keyword="x",
            access_token="expirado",
            max_pages=1,
            session=sess,
        ))


def test_rate_limit_faz_retry_e_recupera(monkeypatch):
    monkeypatch.setattr(threads_client, "_sleep", lambda s: None)

    respostas = [
        FakeResponse(429, {"error": {"code": 4}}),
        FakeResponse(200, {"data": [{"id": "10"}]}),
    ]
    sess = _sessao_mock(respostas)

    resultado = list(search_keyword(
        keyword="x",
        access_token="fake",
        max_pages=1,
        session=sess,
    ))

    assert [p["id"] for p in resultado] == ["10"]
    assert sess.get.call_count == 2


def test_rate_limit_persistente_lanca_excecao(monkeypatch):
    monkeypatch.setattr(threads_client, "_sleep", lambda s: None)

    respostas = [FakeResponse(429, {"error": {"code": 4}})] * 3
    sess = _sessao_mock(respostas)

    with pytest.raises(RateLimitError):
        list(search_keyword(
            keyword="x",
            access_token="fake",
            max_pages=1,
            session=sess,
        ))


def test_erro_http_generico_e_propagado():
    sess = _sessao_mock([FakeResponse(500, {"error": {"message": "boom"}})])

    with pytest.raises(ThreadsAPIError):
        list(search_keyword(
            keyword="x",
            access_token="fake",
            max_pages=1,
            session=sess,
        ))
