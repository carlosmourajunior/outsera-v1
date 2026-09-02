from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AwardInterval:
    producer: str
    interval: int
    previous_win: int
    following_win: int


@dataclass(frozen=True, slots=True)
class AwardIntervalsResult:

    min: list[AwardInterval]
    max: list[AwardInterval]


def _in_response_order(pairs: Iterable[AwardInterval]) -> list[AwardInterval]:
    return sorted(pairs, key=lambda pair: (pair.previous_win, pair.producer))


def compute_award_intervals(
    wins_by_producer: Mapping[str, Iterable[int]],
) -> AwardIntervalsResult:
    shortest: int | None = None
    longest: int | None = None
    min_pairs: list[AwardInterval] = []
    max_pairs: list[AwardInterval] = []

    for producer, years in wins_by_producer.items():
        award_years = sorted(set(years))

        if len(award_years) < 2:
            continue

        for previous, following in zip(award_years, award_years[1:]):
            pair = AwardInterval(
                producer=producer,
                interval=following - previous,
                previous_win=previous,
                following_win=following,
            )

            if shortest is None or pair.interval < shortest:
                shortest, min_pairs = pair.interval, [pair]
            elif pair.interval == shortest:
                min_pairs.append(pair)

            if longest is None or pair.interval > longest:
                longest, max_pairs = pair.interval, [pair]
            elif pair.interval == longest:
                max_pairs.append(pair)

    return AwardIntervalsResult(
        min=_in_response_order(min_pairs),
        max=_in_response_order(max_pairs),
    )
