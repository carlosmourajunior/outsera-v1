"""Teste de integracao contra o arquivo padrao (RNF-02).

Garante que os dados retornados pela API batem com o conteudo real de
`data/Movielist.csv` - nao com um fixture sintetico. Os hashes abaixo cobrem o
payload inteiro de cada endpoint, entao qualquer alteracao no arquivo que mude
qualquer aspecto do resultado (um titulo, um ano, um vencedor, a ordem das
linhas) faz o hash calculado divergir e o teste falhar.

Para regenerar os hashes esperados apos uma mudanca intencional no CSV padrao,
rode:

    .venv/Scripts/python.exe scripts/print_dataset_hashes.py

e copie os valores impressos para as constantes abaixo.
"""

from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from gra_awards.app import create_app
from gra_awards.config import DEFAULT_CSV_PATH

EXPECTED_MOVIES_HASH = "8d1963aa05c6b78f16af4797cef03a313528f16d8ff4d647582ebbd75fb6d8e9"
EXPECTED_INTERVALS_HASH = "0b3ae42530902edc7b0790022400d1551c5d671637f1f16ca6ee3bb85dc63a5a"


def _canonical_hash(payload: object) -> str:
    """Hash estavel do conteudo: independe de ordem de chaves ou espacamento."""
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _fetch_all_movies(client: TestClient) -> list[dict]:
    """Concatena todas as paginas de `/movies` (o tamanho maximo por pagina e 100)."""
    items: list[dict] = []
    page = 1
    while True:
        body = client.get("/movies", params={"page": page, "size": 100}).json()
        items.extend(body["items"])
        if len(items) >= body["total"]:
            return items
        page += 1


def test_movies_dataset_matches_default_file() -> None:
    app = create_app(csv_path=DEFAULT_CSV_PATH)
    with TestClient(app) as client:
        actual = _canonical_hash(_fetch_all_movies(client))

    assert actual == EXPECTED_MOVIES_HASH, (
        f"Conteudo de /movies nao bate com o hash esperado para {DEFAULT_CSV_PATH}"
        f" - o arquivo padrao mudou? Hash atual: {actual}"
    )


def test_producer_intervals_matches_default_file() -> None:
    app = create_app(csv_path=DEFAULT_CSV_PATH)
    with TestClient(app) as client:
        body = client.get("/producers/intervals").json()

    actual = _canonical_hash(body)
    assert actual == EXPECTED_INTERVALS_HASH, (
        "Resultado de /producers/intervals nao bate com o hash esperado para "
        f"{DEFAULT_CSV_PATH} - o arquivo padrao mudou? Hash atual: {actual}"
    )
