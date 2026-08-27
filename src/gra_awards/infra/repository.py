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

MOVIE_ORDER = "ORDER BY movies.year, movies.title, movies.id"

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
    clauses: list[str] = []
    params: list[int] = []

    if year is not None:
        clauses.append("movies.year = ?")
        params.append(year)

    if winner is not None:
        clauses.append("movies.winner = ?")
        params.append(int(winner))

    return ("WHERE " + " AND ".join(clauses) if clauses else "", params)


def count_movies(
    connection: sqlite3.Connection,
    *,
    year: int | None = None,
    winner: bool | None = None,
) -> int:
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
    where, params = _movie_filters(year, winner)
    return connection.execute(
        f"{MOVIE_COLUMNS} {where} {MOVIE_ORDER} LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()


def fetch_movie(
    connection: sqlite3.Connection, movie_id: int
) -> sqlite3.Row | None:
    return connection.execute(
        f"{MOVIE_COLUMNS} WHERE movies.id = ?", (movie_id,)
    ).fetchone()


def fetch_producers_by_movie(
    connection: sqlite3.Connection, movie_ids: Sequence[int]
) -> dict[int, list[str]]:
    if not movie_ids:
        return {}

    placeholders = ", ".join("?" for _ in movie_ids)
    query = PRODUCERS_OF_MOVIES_QUERY.format(placeholders=placeholders)

    producers: dict[int, list[str]] = defaultdict(list)
    for row in connection.execute(query, tuple(movie_ids)):
        producers[int(row["movie_id"])].append(row["producer"])

    return dict(producers)
