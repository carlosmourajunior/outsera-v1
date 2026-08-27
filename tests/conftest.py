"""Fixtures compartilhadas pela suite de testes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gra_awards.app import create_app
from gra_awards.infra.csv_loader import load_movies
from gra_awards.infra.database import create_connection

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_CSV_PATH = FIXTURES_DIR / "movies_sample.csv"


@pytest.fixture
def sample_csv_path() -> Path:
    return SAMPLE_CSV_PATH


@pytest.fixture
def connection() -> Iterator[sqlite3.Connection]:
    """Conexao em memoria, com o schema criado mas sem dados."""
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def loaded_connection(connection: sqlite3.Connection) -> sqlite3.Connection:
    """Conexao em memoria, ja populada com `movies_sample.csv`."""
    load_movies(connection, SAMPLE_CSV_PATH)
    return connection


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Cliente HTTP sobre a app real, carregada com `movies_sample.csv`."""
    app = create_app(csv_path=SAMPLE_CSV_PATH)
    with TestClient(app) as test_client:
        yield test_client
