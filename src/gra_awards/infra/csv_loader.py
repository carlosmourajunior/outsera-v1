from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from gra_awards.domain.producers import split_producers

CSV_DELIMITER = ";"

REQUIRED_COLUMNS = frozenset({"year", "title", "studios", "producers", "winner"})

WINNER_FLAG = "yes"

class CsvFormatError(ValueError):
    """CSV ilegivel: cabecalho ausente ou linha malformada."""


def _is_winner(raw_value: str | None) -> bool:
    return (raw_value or "").strip().lower() == WINNER_FLAG


def load_movies(connection: sqlite3.Connection, csv_path: Path) -> int:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=CSV_DELIMITER)

        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(
            reader.fieldnames
        ):
            raise CsvFormatError(
                f"{csv_path}: cabecalho deve conter as colunas "
                f"{sorted(REQUIRED_COLUMNS)}, encontrado {reader.fieldnames}"
            )

        producer_ids: dict[str, int] = {}
        movie_count = 0

        for row in reader:
            movie_count += 1
            movie_id = _insert_movie(connection, row, reader.line_num, csv_path)

            for name in split_producers(row.get("producers") or ""):
                producer_id = producer_ids.get(name)
                if producer_id is None:
                    producer_id = _insert_producer(connection, name)
                    producer_ids[name] = producer_id

                connection.execute(
                    "INSERT OR IGNORE INTO movie_producers (movie_id, producer_id) "
                    "VALUES (?, ?)",
                    (movie_id, producer_id),
                )

    connection.commit()
    return movie_count


def _insert_movie(
    connection: sqlite3.Connection,
    row: dict[str, str | None],
    line_num: int,
    csv_path: Path,
) -> int:
    try:
        year = int((row.get("year") or "").strip())
    except ValueError as error:
        raise CsvFormatError(
            f"{csv_path}:{line_num}: ano invalido {row.get('year')!r}"
        ) from error

    cursor = connection.execute(
        "INSERT INTO movies (year, title, studios, winner) VALUES (?, ?, ?, ?)",
        (
            year,
            (row.get("title") or "").strip(),
            (row.get("studios") or "").strip(),
            int(_is_winner(row.get("winner"))),
        ),
    )
    return int(cursor.lastrowid)


def _insert_producer(connection: sqlite3.Connection, name: str) -> int:
    connection.execute("INSERT OR IGNORE INTO producers (name) VALUES (?)", (name,))
    row = connection.execute(
        "SELECT id FROM producers WHERE name = ?", (name,)
    ).fetchone()
    return int(row["id"])
