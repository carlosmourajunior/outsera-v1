from __future__ import annotations

import pytest

from gra_awards.domain.producers import split_producers


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Allan Carr", ["Allan Carr"]),
        ("Jerry Weintraub, Bob Cavallo", ["Jerry Weintraub", "Bob Cavallo"]),
        ("Peter Guber and Jon Peters", ["Peter Guber", "Jon Peters"]),
        (
            "John Travolta, Jonathan D. Krane, and Chris Bender",
            ["John Travolta", "Jonathan D. Krane", "Chris Bender"],
        ),
        # Nomes que contem a sequencia "and" nao podem ser quebrados ao meio.
        ("Roland Emmerich", ["Roland Emmerich"]),
        ("Roland Emmerich and Adam Sandler", ["Roland Emmerich", "Adam Sandler"]),
        # Virgulas duplicadas/finais e campo vazio nao geram nomes vazios.
        ("Jerry Weintraub,, Bob Cavallo", ["Jerry Weintraub", "Bob Cavallo"]),
        ("Jerry Weintraub,", ["Jerry Weintraub"]),
        ("", []),
        ("   ", []),
        # Espacos nas pontas de cada nome sao removidos.
        ("  Allan Carr  ,  Bob Cavallo  ", ["Allan Carr", "Bob Cavallo"]),
    ],
)
def test_split_producers(raw: str, expected: list[str]) -> None:
    assert split_producers(raw) == expected
