from __future__ import annotations

import sqlite3

from gra_awards.infra.repository import (
    count_movies,
    fetch_movie,
    fetch_movies,
    fetch_producers_by_movie,
    fetch_win_years_by_producer,
)


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
    rows = fetch_movies(loaded_connection, limit=100, offset=0)
    titles = [row["title"] for row in rows]

    assert titles == [
        "Can't Stop the Music",
        "Cruising",
        "Bonfire of the Vanities",
        "Battlefield Earth",
        "The Adventures of Pluto Nash",
        "Fantastic Four",
    ]


def test_fetch_movies_pagination(loaded_connection: sqlite3.Connection) -> None:
    first_page = fetch_movies(loaded_connection, limit=2, offset=0)
    second_page = fetch_movies(loaded_connection, limit=2, offset=2)

    assert [row["title"] for row in first_page] == ["Can't Stop the Music", "Cruising"]
    assert [row["title"] for row in second_page] == [
        "Bonfire of the Vanities",
        "Battlefield Earth",
    ]


def test_fetch_movies_page_beyond_end_is_empty(
    loaded_connection: sqlite3.Connection,
) -> None:
    rows = fetch_movies(loaded_connection, limit=50, offset=999)
    assert rows == []


def test_fetch_movie_found(loaded_connection: sqlite3.Connection) -> None:
    row = fetch_movie(loaded_connection, 1)
    assert row is not None
    assert row["title"] == "Can't Stop the Music"


def test_fetch_movie_not_found(loaded_connection: sqlite3.Connection) -> None:
    assert fetch_movie(loaded_connection, 9999) is None


def test_fetch_producers_by_movie_empty_input_returns_empty_dict(
    loaded_connection: sqlite3.Connection,
) -> None:
    assert fetch_producers_by_movie(loaded_connection, []) == {}


def test_fetch_producers_by_movie_batches_multiple_movies(
    loaded_connection: sqlite3.Connection,
) -> None:
    # id 2 = Cruising (Jerry Weintraub, Bob Cavallo); id 4 = Battlefield Earth
    # (John Travolta, Jonathan D. Krane, Chris Bender), na ordem do CSV.
    producers = fetch_producers_by_movie(loaded_connection, [2, 4])

    assert producers[2] == ["Jerry Weintraub", "Bob Cavallo"]
    assert producers[4] == ["John Travolta", "Jonathan D. Krane", "Chris Bender"]


def test_fetch_win_years_by_producer_only_counts_winners(
    loaded_connection: sqlite3.Connection,
) -> None:
    win_years = fetch_win_years_by_producer(loaded_connection)

    # Peter Guber e Jon Peters venceram em 1990 e 2015.
    assert sorted(win_years["Peter Guber"]) == [1990, 2015]
    assert sorted(win_years["Jon Peters"]) == [1990, 2015]

    # Allan Carr so venceu em 1980; a indicacao de 2000 (Pluto Nash) nao conta.
    assert win_years["Allan Carr"] == [1980]

    # Jerry Weintraub e Bob Cavallo nunca venceram (Cruising nao ganhou).
    assert "Jerry Weintraub" not in win_years
    assert "Bob Cavallo" not in win_years
