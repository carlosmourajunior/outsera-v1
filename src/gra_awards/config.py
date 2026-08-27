from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CSV_PATH = Path(
    os.getenv("GRA_CSV_PATH", PROJECT_ROOT / "data" / "Movielist.csv")
)
