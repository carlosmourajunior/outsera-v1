from __future__ import annotations

import pytest

from gra_awards.domain.studios import split_studios


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Warner Bros.", ["Warner Bros."]),
        (
            "Lorimar Productions,United Artists",
            ["Lorimar Productions", "United Artists"],
        ),
        # "and" e parte da razao social, nao um separador aqui.
        ("Barnum and Bailey Pictures", ["Barnum and Bailey Pictures"]),
        # A ordem de origem e preservada, sem ordenacao alfabetica.
        (
            "United Artists,Lorimar Productions",
            ["United Artists", "Lorimar Productions"],
        ),
        ("A,,B", ["A", "B"]),
        ("A,", ["A"]),
        ("", []),
        ("   ", []),
        ("  Warner Bros.  ,  MGM  ", ["Warner Bros.", "MGM"]),
    ],
)
def test_split_studios(raw: str, expected: list[str]) -> None:
    assert split_studios(raw) == expected
