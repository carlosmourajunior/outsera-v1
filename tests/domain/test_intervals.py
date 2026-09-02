from __future__ import annotations

from gra_awards.domain.intervals import AwardInterval, compute_award_intervals



def test_single_producer_two_wins_appears_in_both_extremes() -> None:
    result = compute_award_intervals([("Producer A", 2000), ("Producer A", 2002)])

    expected = [AwardInterval("Producer A", 2, 2000, 2002)]
    assert result.min == expected
    assert result.max == expected


def test_producer_with_less_than_two_distinct_wins_is_excluded() -> None:
    empty = compute_award_intervals([])

    # Uma unica vitoria nao forma par.
    assert compute_award_intervals([("Producer A", 1990)]) == empty
    # Duas vitorias no mesmo ano contam como uma so (DR-06).
    assert (
        compute_award_intervals([("Producer A", 1990), ("Producer A", 1990)]) == empty
    )


def test_no_eligible_producer_returns_empty_lists() -> None:
    result = compute_award_intervals([])
    assert result.min == []
    assert result.max == []


def test_producer_with_three_wins_produces_one_pair_per_consecutive_win() -> None:
    # DR-08: nao reduz cedo para o extremo do produtor, gera os dois pares.
    result = compute_award_intervals(
        [("Producer A", 1990), ("Producer A", 1991), ("Producer A", 2000)]
    )

    assert result.min == [AwardInterval("Producer A", 1, 1990, 1991)]
    assert result.max == [AwardInterval("Producer A", 9, 1991, 2000)]


def test_ties_produce_multiple_elements_ordered_by_previous_win_then_producer() -> None:
    result = compute_award_intervals(
        [
            # Producer A: pares de interval 1 e 9.
            ("Producer A", 1990),
            ("Producer A", 1991),
            ("Producer A", 2000),
            # Producer B: interval 1, empata com o primeiro par de A.
            ("Producer B", 1985),
            ("Producer B", 1986),
        ]
    )

    assert result.min == [
        AwardInterval("Producer B", 1, 1985, 1986),
        AwardInterval("Producer A", 1, 1990, 1991),
    ]
    assert result.max == [AwardInterval("Producer A", 9, 1991, 2000)]


def test_last_win_of_a_producer_does_not_pair_with_first_of_the_next() -> None:
    result = compute_award_intervals(
        [
            ("Producer A", 1990),
            ("Producer A", 2000),
            ("Producer B", 1985),
            ("Producer B", 1999),
        ]
    )

    assert result.min == [AwardInterval("Producer A", 10, 1990, 2000)]
    assert result.max == [AwardInterval("Producer B", 14, 1985, 1999)]


def test_tie_with_same_previous_win_orders_by_producer_name() -> None:
    result = compute_award_intervals(
        [
            ("Apple Studio", 1980),
            ("Apple Studio", 1990),
            ("Zebra Films", 1980),
            ("Zebra Films", 1990),
        ]
    )

    # Mesmo interval (10) e mesmo previous_win (1980): desempate por nome.
    assert result.min == [
        AwardInterval("Apple Studio", 10, 1980, 1990),
        AwardInterval("Zebra Films", 10, 1980, 1990),
    ]
    assert result.min == result.max
