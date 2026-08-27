from __future__ import annotations

import sqlite3

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
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection
