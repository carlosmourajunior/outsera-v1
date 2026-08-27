from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from gra_awards.domain.intervals import AwardInterval, AwardIntervalsResult
from gra_awards.domain.studios import split_studios


class AwardIntervalOut(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    producer: str = Field(description="Nome do produtor")
    interval: int = Field(ge=0, description="Anos entre as duas vitorias")
    previous_win: int = Field(
        alias="previousWin", description="Ano da primeira vitoria do par"
    )
    following_win: int = Field(
        alias="followingWin", description="Ano da vitoria consecutiva seguinte"
    )

    @classmethod
    def from_domain(cls, interval: AwardInterval) -> "AwardIntervalOut":
        return cls(
            producer=interval.producer,
            interval=interval.interval,
            previous_win=interval.previous_win,
            following_win=interval.following_win,
        )


class AwardIntervalsOut(BaseModel):

    min: list[AwardIntervalOut] = Field(
        description="Pares com o menor intervalo; vazio se nao ha produtor elegivel"
    )
    max: list[AwardIntervalOut] = Field(
        description="Pares com o maior intervalo; vazio se nao ha produtor elegivel"
    )

    @classmethod
    def from_domain(cls, result: AwardIntervalsResult) -> "AwardIntervalsOut":
        return cls(
            min=[AwardIntervalOut.from_domain(item) for item in result.min],
            max=[AwardIntervalOut.from_domain(item) for item in result.max],
        )


class MovieOut(BaseModel):

    id: int = Field(description="Identificador do filme na execucao corrente")
    year: int = Field(description="Ano da indicacao")
    title: str = Field(description="Titulo do filme")
    studios: list[str] = Field(description="Estudios creditados, na ordem do CSV")
    producers: list[str] = Field(description="Produtores creditados, na ordem do CSV")
    winner: bool = Field(description="Verdadeiro se o filme venceu a categoria")

    @classmethod
    def from_row(cls, row: Mapping[str, Any], producers: list[str]) -> "MovieOut":
        return cls(
            id=int(row["id"]),
            year=int(row["year"]),
            title=row["title"],
            studios=split_studios(row["studios"] or ""),
            producers=producers,
            winner=bool(row["winner"]),
        )


class MoviePageOut(BaseModel):

    items: list[MovieOut] = Field(description="Filmes da pagina corrente")
    page: int = Field(description="Numero da pagina devolvida")
    size: int = Field(description="Tamanho de pagina em vigor")
    total: int = Field(
        description="Total de filmes que satisfazem os filtros, em todas as paginas"
    )
