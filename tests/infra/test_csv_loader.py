from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from gra_awards.infra.csv_loader import CsvFormatError, load_movies
from gra_awards.infra.repository import fetch_movie_with_producers


def test_load_movies_returns_the_number_of_rows_inserted(
    connection: sqlite3.Connection, sample_csv_path: Path
) -> None:
    count = load_movies(connection, sample_csv_path)
    assert count == 6

    total = connection.execute("SELECT COUNT(*) AS total FROM movies").fetchone()
    assert total["total"] == 6


def test_load_movies_populates_studios_and_winner_flag(
    connection: sqlite3.Connection, sample_csv_path: Path
) -> None:
    load_movies(connection, sample_csv_path)

    row = connection.execute(
        "SELECT title, studios, winner FROM movies WHERE title = ?",
        ("Can't Stop the Music",),
    ).fetchone()

    assert row["studios"] == "Associated Film Distribution"
    assert row["winner"] == 1


@pytest.mark.parametrize(
    ("raw_flag", "expected"),
    [("yes", 1), ("YES", 1), (" Yes ", 1), ("no", 0), ("", 0), ("maybe", 0)],
)
def test_winner_flag_parsing_is_case_and_whitespace_insensitive(
    tmp_path: Path, connection: sqlite3.Connection, raw_flag: str, expected: int
) -> None:
    csv_path = tmp_path / "flag.csv"
    csv_path.write_text(
        f"year;title;studios;producers;winner\n1999;Movie;Studio;Producer;{raw_flag}\n",
        encoding="utf-8",
    )

    load_movies(connection, csv_path)

    row = connection.execute("SELECT winner FROM movies").fetchone()
    assert row["winner"] == expected


def test_load_movies_raises_on_missing_required_column(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text(
        "year;title;studios;producers\n1999;Movie;Studio;Producer\n",
        encoding="utf-8",
    )

    with pytest.raises(CsvFormatError):
        load_movies(connection, csv_path)


def test_load_movies_raises_on_invalid_year(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    csv_path = tmp_path / "bad_year.csv"
    csv_path.write_text(
        "year;title;studios;producers;winner\n"
        "1999;Good Movie;Studio;Producer;yes\n"
        "not-a-year;Bad Movie;Studio;Producer;no\n",
        encoding="utf-8",
    )

    with pytest.raises(CsvFormatError, match="not-a-year"):
        load_movies(connection, csv_path)


def test_load_movies_handles_utf8_bom(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    csv_path = tmp_path / "with_bom.csv"
    csv_path.write_text(
        "year;title;studios;producers;winner\n1999;Movie;Studio;Producer;yes\n",
        encoding="utf-8-sig",
    )

    count = load_movies(connection, csv_path)
    assert count == 1


def test_producer_credited_twice_in_same_movie_is_linked_only_once(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    csv_path = tmp_path / "duplicate_credit.csv"
    csv_path.write_text(
        "year;title;studios;producers;winner\n"
        "1999;Movie;Studio;Allan Carr, Allan Carr;yes\n",
        encoding="utf-8",
    )

    load_movies(connection, csv_path)

    movie_id = connection.execute("SELECT id FROM movies").fetchone()["id"]
    found = fetch_movie_with_producers(connection, movie_id)

    assert found is not None
    assert found[1] == ["Allan Carr"]
