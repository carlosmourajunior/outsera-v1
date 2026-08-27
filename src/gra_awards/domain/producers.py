from __future__ import annotations

import re

_SEPARATORS = re.compile(r",\s*and\s+|\s+and\s+|,")


def split_producers(raw: str) -> list[str]:
    return [name.strip() for name in _SEPARATORS.split(raw) if name.strip()]
