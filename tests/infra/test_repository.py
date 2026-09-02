from __future__ import annotations

import sqlite3

from gra_awards.infra.repository import (
    count_movies,
    fetch_movie_with_producers,
    fetch_movies_with_producers,
    fetch_win_years,
)


def _page(connection: sqlite3.Connection, **kwargs: object) -> list[tuple]:
    kwargs.setdefault("limit", 100)
    kwargs.setdefault("offset", 0)
    return list(fetch_movies_with_producers(connection, **kwargs))  # type: ignore[arg-type]


def test_count_movies_without_filters(loaded_connection: sqlite3.Connection) -> None:
    assert count_movies(loaded_connection) == 6


def test_count_movies_filtered_by_year(loaded_connection: sqlite3.Connection) -> None:
    assert count_movies(loaded_connection, year=1980) == 2
    assert count_movies(loaded_connection, year=1975) == 0


def test_count_movies_filtered_by_winner(loaded_connection: sqlite3.Connection) -> None:
    assert count_movies(loaded_connection, winner=True) == 4
    assert count_movies(loaded_connection, winner=False) == 2


def test_count_movies_combines_filters(loaded_connection: sqlite3.Connection) -> None:
    assert count_movies(loaded_connection, year=1980, winner=True) == 1
    assert count_movies(loaded_connection, year=1980, winner=False) == 1


def test_fetch_movies_is_ordered_by_year_title_id(
    loaded_connection: sqlite3.Connection,
) -> None:
    titles = [row["title"] for row, _ in _page(loaded_connection)]

    assert titles == [
        "Can't Stop the Music",
        "Cruising",
        "Bonfire of the Vanities",
        "Battlefield Earth",
        "The Adventures of Pluto Nash",
        "Fantastic Four",
    ]


def test_fetch_movies_pagination_counts_movies_not_join_rows(
    loaded_connection: sqlite3.Connection,
) -> None:
    # Battlefield Earth tem tres produtores: se o LIMIT contasse linhas do join
    # em vez de filmes, esta segunda pagina viria truncada.
    first_page = _page(loaded_connection, limit=2, offset=0)
    second_page = _page(loaded_connection, limit=2, offset=2)

    assert [row["title"] for row, _ in first_page] == [
        "Can't Stop the Music",
        "Cruising",
    ]
    assert [row["title"] for row, _ in second_page] == [
        "Bonfire of the Vanities",
        "Battlefield Earth",
    ]
    assert second_page[1][1] == [
        "John Travolta",
        "Jonathan D. Krane",
        "Chris Bender",
    ]


def test_fetch_movies_page_beyond_end_is_empty(
    loaded_connection: sqlite3.Connection,
) -> None:
    assert _page(loaded_connection, limit=50, offset=999) == []


def test_fetch_movies_applies_filters(
    loaded_connection: sqlite3.Connection,
) -> None:
    assert [row["title"] for row, _ in _page(loaded_connection, year=1980)] == [
        "Can't Stop the Music",
        "Cruising",
    ]
    assert all(row["winner"] for row, _ in _page(loaded_connection, winner=True))
    assert [
        row["title"] for row, _ in _page(loaded_connection, year=1980, winner=False)
    ] == ["Cruising"]


def test_fetch_movies_carries_producers_in_csv_order(
    loaded_connection: sqlite3.Connection,
) -> None:
    by_title = {row["title"]: producers for row, producers in _page(loaded_connection)}

    assert by_title["Cruising"] == ["Jerry Weintraub", "Bob Cavallo"]
    assert by_title["Battlefield Earth"] == [
        "John Travolta",
        "Jonathan D. Krane",
        "Chris Bender",
    ]


def test_movie_without_producers_is_not_dropped_by_the_join(
    loaded_connection: sqlite3.Connection,
) -> None:
    # O LEFT JOIN existe para este caso: sem ele, um filme sem produtor
    # creditado sumiria da listagem em vez de aparecer com a lista vazia.
    loaded_connection.execute(
        "INSERT INTO movies (year, title, studios, winner) VALUES (?, ?, ?, ?)",
        (1970, "Orphan Movie", "No Studio", 0),
    )

    by_title = {row["title"]: producers for row, producers in _page(loaded_connection)}

    assert by_title["Orphan Movie"] == []


def test_fetch_movie_found_with_producers(
    loaded_connection: sqlite3.Connection,
) -> None:
    found = fetch_movie_with_producers(loaded_connection, 2)

    assert found is not None
    row, producers = found
    assert row["title"] == "Cruising"
    assert producers == ["Jerry Weintraub", "Bob Cavallo"]


def test_fetch_movie_not_found(loaded_connection: sqlite3.Connection) -> None:
    assert fetch_movie_with_producers(loaded_connection, 9999) is None


def test_fetch_win_years_only_counts_winners(
    loaded_connection: sqlite3.Connection,
) -> None:
    rows = list(fetch_win_years(loaded_connection))
    by_producer: dict[str, list[int]] = {}
    for producer, year in rows:
        by_producer.setdefault(producer, []).append(year)

    # Peter Guber e Jon Peters venceram em 1990 e 2015.
    assert by_producer["Peter Guber"] == [1990, 2015]
    assert by_producer["Jon Peters"] == [1990, 2015]

    # Allan Carr so venceu em 1980; a indicacao de 2000 (Pluto Nash) nao conta.
    assert by_producer["Allan Carr"] == [1980]

    # Jerry Weintraub e Bob Cavallo nunca venceram (Cruising nao ganhou).
    assert "Jerry Weintraub" not in by_producer
    assert "Bob Cavallo" not in by_producer


def test_fetch_win_years_is_ordered_by_producer_then_year(
    loaded_connection: sqlite3.Connection,
) -> None:
    # Contrato consumido por `compute_award_intervals`: sem esta ordenacao o
    # calculo de um passe unico fica errado, entao ela e testada explicitamente.
    rows = list(fetch_win_years(loaded_connection))

    assert rows == sorted(rows)
    assert all(isinstance(producer, str) and isinstance(year, int)
               for producer, year in rows)


def test_fetch_win_years_deduplicates_same_producer_and_year(
    loaded_connection: sqlite3.Connection,
) -> None:
    rows = list(fetch_win_years(loaded_connection))
    assert len(rows) == len(set(rows))
