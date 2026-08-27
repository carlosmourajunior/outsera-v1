"""Separacao do campo livre `studios` do CSV em nomes individuais (`DR-15`)."""

from __future__ import annotations

STUDIO_SEPARATOR = ","


def split_studios(raw: str) -> list[str]:
    """Devolve os estudios listados em um campo `studios` do CSV.

    Deliberadamente mais restrito que `split_producers`: aqui **so** a virgula
    separa. Em lista de pessoas o `and` e conjuncao gramatical; em razao social
    de empresa ele costuma ser parte do nome - "Barnum and Bailey Pictures" e um
    estudio, nao dois. Aplicar a regra de `DR-03` aqui inventaria uma empresa a
    cada razao social com conjuncao, e o dataset entregue confirma que a virgula
    basta: 44 registros tem virgula em `studios` e nenhum tem ` and `.

    A ordem de origem e preservada - a ordem dos creditos e informacao, e
    ordenar alfabeticamente a destruiria (`DR-16`).
    """
    return [name.strip() for name in raw.split(STUDIO_SEPARATOR) if name.strip()]
