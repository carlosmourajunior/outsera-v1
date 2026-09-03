from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator

#: `DISTINCT` porque um produtor pode assinar dois vencedores no mesmo ano: sao
#: duas linhas, mas uma unica vitoria para efeito de intervalo (DR-06). Filtrar
#: na origem evita transportar linhas que o dominio so descartaria.
#:
#: O `ORDER BY` nao e cosmetico - e o contrato que permite calcular os
#: intervalos em um unico passe: agrupado por produtor e, dentro do produtor,
#: com os anos em ordem crescente, dois premios consecutivos sao duas linhas
#: adjacentes do resultado.
WIN_YEARS_QUERY = """
SELECT DISTINCT producers.name AS producer,
                movies.year    AS year
FROM producers
JOIN movie_producers ON movie_producers.producer_id = producers.id
JOIN movies          ON movies.id = movie_producers.movie_id
WHERE movies.winner = 1
ORDER BY producers.name, movies.year
"""


def fetch_win_years(connection: sqlite3.Connection) -> Iterator[tuple[str, int]]:
    """Vitorias como `(produtor, ano)`, ordenadas por produtor e ano.

    Devolve o proprio cursor em vez de materializar uma colecao: o dominio
    consome linha a linha, entao nada precisa existir em memoria de uma vez.
    """
    cursor = connection.cursor()
    # O cursor nasce herdando o `row_factory` da conexao (`sqlite3.Row`). Zerar
    # aqui faz o sqlite3 devolver tuplas cruas `(producer, year)` - ja a forma
    # que o dominio espera - eliminando um passe de conversao so para trocar de
    # formato. `year` chega como int porque a coluna e INTEGER.
    cursor.row_factory = None
    return cursor.execute(WIN_YEARS_QUERY)


#: A pagina e materializada numa CTE **antes** do join: `LIMIT/OFFSET` tem de
#: contar filmes, nao linhas do join - um filme com tres produtores nao pode
#: consumir tres posicoes da pagina.
_MOVIE_PAGE_CTE = """
WITH page AS (
    SELECT movies.id      AS id,
           movies.year    AS year,
           movies.title   AS title,
           movies.studios AS studios,
           movies.winner  AS winner
    FROM movies
    {where}
    ORDER BY movies.year, movies.title, movies.id
    LIMIT ? OFFSET ?
)
"""

_MOVIE_ONE_CTE = """
WITH page AS (
    SELECT movies.id      AS id,
           movies.year    AS year,
           movies.title   AS title,
           movies.studios AS studios,
           movies.winner  AS winner
    FROM movies
    WHERE movies.id = ?
)
"""

#: `LEFT JOIN` e nao `JOIN`: um filme sem produtor creditado continua na lista,
#: com `producer` nulo.
#:
#: O `ORDER BY` carrega dois contratos. Os campos de filme mantem a ordenacao
#: deterministica da resposta e, de quebra, garantem que as linhas de um mesmo
#: filme saiam adjacentes - o que permite agrupar em um unico passe.
#: `movie_producers.rowid` preserva a ordem de credito do CSV.
_WITH_PRODUCERS = """
SELECT page.id        AS id,
       page.year      AS year,
       page.title     AS title,
       page.studios   AS studios,
       page.winner    AS winner,
       producers.name AS producer
FROM page
LEFT JOIN movie_producers ON movie_producers.movie_id = page.id
LEFT JOIN producers       ON producers.id = movie_producers.producer_id
ORDER BY page.year, page.title, page.id, movie_producers.rowid
"""

MovieWithProducers = tuple[sqlite3.Row, list[str]]


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


def _group_by_movie(rows: Iterable[sqlite3.Row]) -> Iterator[MovieWithProducers]:
    """Colapsa as linhas do join em um filme por vez, em um unico passe.

    Depende de as linhas de um mesmo filme virem adjacentes - contrato do
    `ORDER BY` de `_WITH_PRODUCERS`. Como e um gerador, o agrupamento acontece
    fundido com a construcao da resposta: nenhum dicionario intermediario de
    produtores e montado.
    """
    current: sqlite3.Row | None = None
    producers: list[str] = []

    for row in rows:
        if current is not None and row["id"] != current["id"]:
            yield current, producers
            producers = []

        current = row
        if row["producer"] is not None:
            producers.append(row["producer"])

    if current is not None:
        yield current, producers


def count_movies(
    connection: sqlite3.Connection,
    *,
    year: int | None = None,
    winner: bool | None = None,
) -> int:
    """Total do conjunto filtrado, em todas as paginas.

    Continua sendo uma consulta propria: e um escalar que precisa existir mesmo
    quando a pagina pedida esta alem do fim e nao devolve nenhuma linha.
    """
    where, params = _movie_filters(year, winner)
    row = connection.execute(
        f"SELECT COUNT(*) AS total FROM movies {where}", params
    ).fetchone()
    return int(row["total"])


def fetch_movies_with_producers(
    connection: sqlite3.Connection,
    *,
    year: int | None = None,
    winner: bool | None = None,
    limit: int,
    offset: int,
) -> Iterator[MovieWithProducers]:
    """Uma pagina de filmes ja com seus produtores, em uma unica consulta."""
    where, params = _movie_filters(year, winner)
    query = _MOVIE_PAGE_CTE.format(where=where) + _WITH_PRODUCERS

    return _group_by_movie(connection.execute(query, [*params, limit, offset]))


def fetch_movie_with_producers(
    connection: sqlite3.Connection, movie_id: int
) -> MovieWithProducers | None:
    """Um filme com seus produtores, ou `None` se o id nao existe."""
    rows = connection.execute(_MOVIE_ONE_CTE + _WITH_PRODUCERS, (movie_id,))

    # Mesmo agrupamento do caso paginado - um grupo so, ou nenhum.
    return next(_group_by_movie(rows), None)
