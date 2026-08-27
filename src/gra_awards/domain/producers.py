"""Separacao do campo livre `producers` do CSV em nomes individuais (`DR-03`)."""

from __future__ import annotations

import re

# Tres alternativas, cada uma cobrindo um formato presente no dataset:
#
#   `,\s*and\s+`  virgula de Oxford  -> "Eric Fellner, and Tom Hooper"
#   `\s+and\s+`   conjuncao          -> "Ted Field and Robert W. Cort"
#   `,`           enumeracao simples -> "Jerry Weintraub, Bob Cavallo"
#
# A primeira alternativa e, a rigor, redundante: sem ela a virgula e o ` and `
# seriam consumidos em duas separacoes seguidas, deixando um trecho vazio entre
# as duas - que o filtro de vazios em `split_producers` descarta. Ela fica por
# ser explicita: depender do descarte de vazios faria a virgula de Oxford
# funcionar por acidente, e um acidente nao sobrevive a proxima refatoracao.
#
# Os `\s+` ao redor de `and` sao carga estrutural, nao estilo. O dataset contem
# "Roland Emmerich", "Adam Sandler", "Alexander Salkind" e "Sandra Bullock" -
# todos com a sequencia de letras "and" dentro do nome. Separar por `and` sem
# exigir os espacos quebraria cada um deles ao meio.
_SEPARATORS = re.compile(r",\s*and\s+|\s+and\s+|,")


def split_producers(raw: str) -> list[str]:
    """Devolve os produtores listados em um campo `producers` do CSV.

    Nomes sao normalizados por remocao de espacos nas pontas e nomes vazios -
    resultado de virgulas duplicadas, campo em branco ou de duas separacoes
    adjacentes - sao descartados.
    """
    return [name.strip() for name in _SEPARATORS.split(raw) if name.strip()]
