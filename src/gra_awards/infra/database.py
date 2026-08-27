"""Banco embarcado em memoria (`RNF-03`).

SQLite via `sqlite3` da biblioteca padrao: nenhuma dependencia externa e nenhuma
instalacao, exatamente o que o requisito pede.
"""

from __future__ import annotations

import sqlite3

#: Esquema normalizado. `producers` e uma tabela propria - e nao uma coluna de
#: texto em `movies` - porque a unica consulta do sistema agrupa por produtor;
#: manter os nomes concatenados obrigaria a separa-los a cada leitura.
SCHEMA = """
CREATE TABLE movies (
    id      INTEGER PRIMARY KEY,
    year    INTEGER NOT NULL,
    title   TEXT    NOT NULL,
    studios TEXT    NOT NULL,
    winner  INTEGER NOT NULL CHECK (winner IN (0, 1))
);

CREATE TABLE producers (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE movie_producers (
    movie_id    INTEGER NOT NULL REFERENCES movies(id),
    producer_id INTEGER NOT NULL REFERENCES producers(id),
    PRIMARY KEY (movie_id, producer_id)
);

CREATE INDEX idx_movies_winner ON movies(winner);
"""


def create_connection() -> sqlite3.Connection:
    """Abre a conexao em memoria e cria o esquema.

    `check_same_thread=False` e necessario porque a conexao e criada no
    `lifespan` da aplicacao e usada no atendimento das requisicoes, que o
    servidor pode despachar em outra thread. E seguro aqui: o modulo `sqlite3`
    desta instalacao reporta `threadsafety == 3` (modo serializado), ou seja, a
    propria biblioteca serializa os acessos concorrentes.
    """
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    # Nomes de coluna nas linhas: as consultas ficam legiveis por chave em vez
    # de por indice posicional.
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection
