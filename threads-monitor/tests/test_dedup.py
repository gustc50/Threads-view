"""Testa a deduplicacao pelos ids ja vistos."""

from storage import filter_new_posts, load_seen_ids, save_seen_ids


def _post(pid: str, texto: str = "oi") -> dict:
    return {
        "id": pid,
        "text": texto,
        "username": "user",
        "timestamp": "2026-01-01T00:00:00Z",
        "permalink": f"https://threads.net/post/{pid}",
    }


def test_filter_new_posts_ignora_ids_ja_vistos():
    posts = [_post("1"), _post("2"), _post("3")]
    seen = {"2"}

    novos, novos_ids = filter_new_posts(posts, seen)

    assert [p["id"] for p in novos] == ["1", "3"]
    assert novos_ids == {"1", "3"}


def test_filter_new_posts_remove_duplicatas_no_mesmo_lote():
    posts = [_post("10"), _post("10"), _post("11")]

    novos, novos_ids = filter_new_posts(posts, set())

    assert [p["id"] for p in novos] == ["10", "11"]
    assert novos_ids == {"10", "11"}


def test_filter_new_posts_ignora_posts_sem_id():
    posts = [
        {"id": "1", "text": "ok"},
        {"text": "sem id"},
        {"id": "", "text": "id vazio"},
    ]

    novos, novos_ids = filter_new_posts(posts, set())

    assert [p["id"] for p in novos] == ["1"]
    assert novos_ids == {"1"}


def test_seen_ids_roundtrip(tmp_path):
    path = tmp_path / "seen.json"
    save_seen_ids(path, {"a", "b", "c"})
    lido = load_seen_ids(path)
    assert lido == {"a", "b", "c"}


def test_load_seen_ids_arquivo_inexistente(tmp_path):
    assert load_seen_ids(tmp_path / "nao_existe.json") == set()


def test_load_seen_ids_arquivo_corrompido(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text("isso nao e json", encoding="utf-8")
    assert load_seen_ids(path) == set()
