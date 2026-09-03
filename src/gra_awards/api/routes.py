from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from gra_awards.api.schemas import AwardIntervalsOut, MovieOut, MoviePageOut
from gra_awards.domain.intervals import compute_award_intervals
from gra_awards.infra.repository import (
    count_movies,
    fetch_movie_with_producers,
    fetch_movies_with_producers,
    fetch_win_years,
)

#: Limites de paginacao de `API-05`. O maximo existe para que o tamanho da
#: resposta seja decidido pela aplicacao, e nao pelo cliente: sem teto, um
#: `size` arbitrario transforma a paginacao em enfeite.
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def get_connection(request: Request) -> sqlite3.Connection:
    """Conexao criada no `lifespan` e guardada no estado da aplicacao.

    Injetar por dependencia - em vez de ler `app.state` dentro da rota - mantem
    o handler testavel e explicito sobre o que consome.
    """
    return request.app.state.connection


Connection = Annotated[sqlite3.Connection, Depends(get_connection)]

router = APIRouter()


@router.get(
    "/producers/intervals",
    response_model=AwardIntervalsOut,
    tags=["producers"],
    summary="Intervalos entre premios consecutivos",
    description=(
        "Retorna o produtor com o maior intervalo entre dois premios "
        "consecutivos e o que obteve dois premios mais rapido. Empates "
        "produzem multiplos elementos; ausencia de produtor elegivel produz "
        "listas vazias com status 200."
    ),
)
async def read_award_intervals(connection: Connection) -> AwardIntervalsOut:

    return AwardIntervalsOut.from_domain(
        compute_award_intervals(fetch_win_years(connection))
    )


@router.get(
    "/movies",
    response_model=MoviePageOut,
    tags=["movies"],
    summary="Lista de indicados e vencedores",
    description=(
        "Lista os filmes indicados e vencedores da categoria Pior Filme. "
        "Aceita filtro por ano e por condicao de vitoria, combinaveis, e "
        "devolve o resultado paginado com o total do conjunto filtrado."
    ),
)
async def list_movies(
    connection: Connection,
    year: Annotated[
        int | None, Query(description="Filtra pelo ano da indicacao")
    ] = None,
    winner: Annotated[
        bool | None,
        Query(description="`true` so vencedores, `false` so nao vencedores"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Pagina desejada")] = DEFAULT_PAGE,
    size: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Itens por pagina")
    ] = DEFAULT_PAGE_SIZE,
) -> MoviePageOut:
    total = count_movies(connection, year=year, winner=winner)

    items = [
        MovieOut.from_row(row, producers)
        for row, producers in fetch_movies_with_producers(
            connection,
            year=year,
            winner=winner,
            limit=size,
            offset=(page - 1) * size,
        )
    ]

    return MoviePageOut(items=items, page=page, size=size, total=total)


@router.get(
    "/movies/{movie_id}",
    response_model=MovieOut,
    tags=["movies"],
    summary="Filme individual",
    responses={404: {"description": "Nenhum filme com esse identificador"}},
)
async def read_movie(
    connection: Connection,
    movie_id: Annotated[int, Path(description="Identificador do filme")],
) -> MovieOut:
    found = fetch_movie_with_producers(connection, movie_id)

    if found is None:
        raise HTTPException(status_code=404, detail="Filme nao encontrado")

    row, producers = found
    return MovieOut.from_row(row, producers)
