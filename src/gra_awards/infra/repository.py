"""Leitura dos anos de vitoria por produtor.

Fronteira deliberadamente estreita: o repositorio devolve dados brutos e nenhuma
regra de dominio. A deduplicacao de anos (`DR-06`) e a formacao dos pares
(`DR-08`) ficam em `domain/intervals.py`, com um unico dono cada.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from collections.abc import Sequence

WIN_YEARS_QUERY = """
SELECT producers.name AS producer,
       movies.year    AS year
FROM producers
JOIN movie_producers ON movie_producers.producer_id = producers.id
JOIN movies          ON movies.id = movie_producers.movie_id
WHERE movies.winner = 1
ORDER BY producers.name, movies.year
"""


def fetch_win_years_by_producer(
    connection: sqlite3.Connection,
) -> dict[str, list[int]]:
    """Mapeia cada produtor vencedor aos anos em que venceu.

    Os anos vem repetidos quando ha mais de uma vitoria no mesmo ano; colapsa-los
    e decisao de dominio, nao da consulta.
    """
    win_years: dict[str, list[int]] = defaultdict(list)

    for row in connection.execute(WIN_YEARS_QUERY):
        win_years[row["producer"]].append(int(row["year"]))

    return dict(win_years)


MOVIE_COLUMNS = """
SELECT movies.id      AS id,
       movies.year    AS year,
       movies.title   AS title,
       movies.studios AS studios,
       movies.winner  AS winner
FROM movies
"""

# `DR-17`: ano, titulo e, como ultimo desempate, o id. O id nao e criterio de
# negocio - esta ali para tornar a ordem **total**. Sem ele, dois filmes de
# mesmo ano e titulo ficam na ordem que o banco resolver devolver, e um item
# pode aparecer em duas paginas ou em nenhuma.
#
# Removendo `movies.id` daqui a suite continua verde, como mostrou o teste de
# mutacao registrado em `docs/ai-log.md` [005]. O motivo e uma particularidade
# do SQLite: toda chave de indice termina no rowid, e `id INTEGER PRIMARY KEY`
# **e** o rowid - entao empates ja saem em ordem de id, com ou sem indice. A
# clausula fica porque essa garantia e do SQLite, nao do SQL: `RNF-03` admite
# qualquer SGBD embarcado, e em outro a ordem dos empates voltaria a ser
# indefinida. Explicito aqui custa tres palavras; implicito custa um bug de
# paginacao que so aparece depois da troca.
MOVIE_ORDER = "ORDER BY movies.year, movies.title, movies.id"

# Ordenado por `rowid` para devolver os produtores na ordem em que o CSV os
# creditou (`DR-16`); `rowid` reflete a ordem de insercao da carga.
PRODUCERS_OF_MOVIES_QUERY = """
SELECT movie_producers.movie_id AS movie_id,
       producers.name           AS producer
FROM movie_producers
JOIN producers ON producers.id = movie_producers.producer_id
WHERE movie_producers.movie_id IN ({placeholders})
ORDER BY movie_producers.rowid
"""


def _movie_filters(
    year: int | None, winner: bool | None
) -> tuple[str, list[int]]:
    """Monta o `WHERE` dos filtros de `DR-18`.

    Filtro ausente nao entra na clausula - e por isso que "sem filtro" nao
    precisa de caso especial. Os valores viajam como parametros ligados, nunca
    interpolados na string: e o que mantem a consulta imune a injecao mesmo com
    a query montada dinamicamente.
    """
    clauses: list[str] = []
    params: list[int] = []

    if year is not None:
        clauses.append("movies.year = ?")
        params.append(year)

    if winner is not None:
        # `winner` e armazenado como 0/1 pelo carregador (`DR-02`).
        clauses.append("movies.winner = ?")
        params.append(int(winner))

    return ("WHERE " + " AND ".join(clauses) if clauses else "", params)


def count_movies(
    connection: sqlite3.Connection,
    *,
    year: int | None = None,
    winner: bool | None = None,
) -> int:
    """Total de filmes que satisfazem os filtros, ignorando paginacao (`DR-19`).

    Contar no banco, e nao medir a lista ja paginada, e o que faz `total`
    descrever o conjunto filtrado inteiro.
    """
    where, params = _movie_filters(year, winner)
    row = connection.execute(
        f"SELECT COUNT(*) AS total FROM movies {where}", params
    ).fetchone()
    return int(row["total"])


def fetch_movies(
    connection: sqlite3.Connection,
    *,
    year: int | None = None,
    winner: bool | None = None,
    limit: int,
    offset: int,
) -> list[sqlite3.Row]:
    """Uma pagina de filmes, filtrada por `DR-18` e ordenada por `DR-17`."""
    where, params = _movie_filters(year, winner)
    return connection.execute(
        f"{MOVIE_COLUMNS} {where} {MOVIE_ORDER} LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()


def fetch_movie(
    connection: sqlite3.Connection, movie_id: int
) -> sqlite3.Row | None:
    """Um filme por id, ou `None` se nao existe - a rota decide o status."""
    return connection.execute(
        f"{MOVIE_COLUMNS} WHERE movies.id = ?", (movie_id,)
    ).fetchone()


def fetch_producers_by_movie(
    connection: sqlite3.Connection, movie_ids: Sequence[int]
) -> dict[int, list[str]]:
    """Produtores de varios filmes em **uma** consulta.

    Uma query por filme seria o N+1 classico: uma pagina de 50 filmes viraria
    51 idas ao banco. O `IN` com um placeholder por id resolve a pagina inteira
    de uma vez, e o numero de placeholders e limitado pelo tamanho maximo de
    pagina, nao pelo tamanho do dataset.
    """
    if not movie_ids:
        # Sem esta guarda o `IN ()` seria sintaxe invalida - e uma pagina alem
        # do fim (`DR-19`) chega aqui exatamente com a lista vazia.
        return {}

    placeholders = ", ".join("?" for _ in movie_ids)
    query = PRODUCERS_OF_MOVIES_QUERY.format(placeholders=placeholders)

    producers: dict[int, list[str]] = defaultdict(list)
    for row in connection.execute(query, tuple(movie_ids)):
        producers[int(row["movie_id"])].append(row["producer"])

    return dict(producers)
