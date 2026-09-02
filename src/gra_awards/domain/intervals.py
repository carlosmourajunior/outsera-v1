from __future__ import annotations

from collections.abc import Iterable
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
    wins: Iterable[tuple[str, int]],
) -> AwardIntervalsResult:

    shortest: int | None = None
    longest: int | None = None
    min_pairs: list[AwardInterval] = []
    max_pairs: list[AwardInterval] = []


    current_producer: str | None = None
    previous_win = 0

    for producer, year in wins:
        if producer != current_producer:
            current_producer, previous_win = producer, year
            continue

        if year == previous_win:
            continue

        pair = AwardInterval(
            producer=producer,
            interval=year - previous_win,
            previous_win=previous_win,
            following_win=year,
        )
        previous_win = year

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
