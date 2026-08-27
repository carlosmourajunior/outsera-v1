"""Calculo dos intervalos entre premios consecutivos (`DR-06` a `DR-12`).

Funcoes puras: recebem os anos de vitoria ja lidos do banco e nao conhecem
SQL nem HTTP. E aqui que vivem as regras de dominio - a camada de infra apenas
entrega dados brutos.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AwardInterval:
    """Um par de vitorias consecutivas de um mesmo produtor."""

    producer: str
    interval: int
    previous_win: int
    following_win: int


@dataclass(frozen=True, slots=True)
class AwardIntervalsResult:
    """Extremos globais: todos os pares empatados em cada ponta (`DR-09`)."""

    min: list[AwardInterval]
    max: list[AwardInterval]


def _in_response_order(pairs: Iterable[AwardInterval]) -> list[AwardInterval]:
    """Ordena por ano anterior e, no empate, por produtor (`DR-12`)."""
    return sorted(pairs, key=lambda pair: (pair.previous_win, pair.producer))


def compute_award_intervals(
    wins_by_producer: Mapping[str, Iterable[int]],
) -> AwardIntervalsResult:
    """Calcula os extremos de intervalo entre premios consecutivos.

    `wins_by_producer` mapeia o nome do produtor aos anos em que venceu, na
    forma bruta - com repeticoes, se houver.
    """
    pairs: list[AwardInterval] = []

    for producer, years in wins_by_producer.items():
        # `set` implementa `DR-06`: duas vitorias no mesmo ano sao a mesma
        # edicao, nao dois premios consecutivos. A deduplicacao mora aqui, e nao
        # em um `DISTINCT` no SQL, para que a regra tenha um unico dono.
        award_years = sorted(set(years))

        if len(award_years) < 2:
            # DR-07 explicitado. Removendo esta guarda o resultado nao muda - o
            # `zip` abaixo ja nao produz par algum com menos de dois anos, como
            # confirmou o teste de mutacao em `docs/ai-log.md` [004]. Ela fica
            # porque a elegibilidade e uma regra do dominio, e uma regra que so
            # existe como efeito colateral de outra e invisivel a quem le.
            continue

        # DR-08: um par por vitoria consecutiva, nao apenas o extremo do
        # produtor - o menor par global pode pertencer a quem tambem detem o
        # maior, e reduzir cedo demais perderia um dos dois.
        pairs.extend(
            AwardInterval(
                producer=producer,
                interval=following - previous,
                previous_win=previous,
                following_win=following,
            )
            for previous, following in zip(award_years, award_years[1:])
        )

    if not pairs:
        return AwardIntervalsResult(min=[], max=[])  # DR-11

    shortest = min(pair.interval for pair in pairs)
    longest = max(pair.interval for pair in pairs)

    # Os dois filtros sao independentes: com um unico par, ele satisfaz ambos e
    # aparece nas duas listas (`DR-10`).
    return AwardIntervalsResult(
        min=_in_response_order(p for p in pairs if p.interval == shortest),
        max=_in_response_order(p for p in pairs if p.interval == longest),
    )
