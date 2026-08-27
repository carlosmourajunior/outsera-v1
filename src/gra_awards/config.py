"""Configuracao de origem dos dados."""

from __future__ import annotations

import os
from pathlib import Path

#: Raiz do repositorio: src/gra_awards/config.py -> src/gra_awards -> src -> .
PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: CSV carregado na inicializacao. A variavel de ambiente permite apontar para
#: outro dataset sem alterar codigo - util para a avaliacao, que usara conjuntos
#: de dados diferentes do entregue.
DEFAULT_CSV_PATH = Path(
    os.getenv("GRA_CSV_PATH", PROJECT_ROOT / "data" / "Movielist.csv")
)
