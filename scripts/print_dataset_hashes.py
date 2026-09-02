"""Gera os hashes esperados pelo teste de integracao contra o arquivo padrao.

Rodar sempre que `data/Movielist.csv` mudar de forma intencional (ex.: troca
oficial do dataset) e colar os valores impressos em
`EXPECTED_MOVIES_HASH`/`EXPECTED_INTERVALS_HASH` em
`tests/integration/test_default_dataset_hash.py`.

Uso:
    .venv/Scripts/python.exe scripts/print_dataset_hashes.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from gra_awards.app import create_app  # noqa: E402
from gra_awards.config import DEFAULT_CSV_PATH  # noqa: E402


def canonical_hash(payload: object) -> str:
    """Hash estavel do conteudo: independe de ordem de chaves ou espacamento."""
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fetch_all_movies(client: TestClient) -> list[dict]:
    """Concatena todas as paginas de `/movies` (o tamanho maximo por pagina e 100)."""
    items: list[dict] = []
    page = 1
    while True:
        body = client.get("/movies", params={"page": page, "size": 100}).json()
        items.extend(body["items"])
        if len(items) >= body["total"]:
            return items
        page += 1


def main() -> None:
    app = create_app(csv_path=DEFAULT_CSV_PATH)
    with TestClient(app) as client:
        movies_hash = canonical_hash(fetch_all_movies(client))
        intervals_hash = canonical_hash(client.get("/producers/intervals").json())

    print(f"Arquivo: {DEFAULT_CSV_PATH}")
    print(f'EXPECTED_MOVIES_HASH = "{movies_hash}"')
    print(f'EXPECTED_INTERVALS_HASH = "{intervals_hash}"')


if __name__ == "__main__":
    main()
