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
    pairs: list[AwardInterval] = []

    for producer, years in wins_by_producer.items():
        award_years = sorted(set(years))

        if len(award_years) < 2:
            continue
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

    return AwardIntervalsResult(
        min=_in_response_order(p for p in pairs if p.interval == shortest),
        max=_in_response_order(p for p in pairs if p.interval == longest),
    )
