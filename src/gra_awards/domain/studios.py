from __future__ import annotations

STUDIO_SEPARATOR = ","


def split_studios(raw: str) -> list[str]:
    return [name.strip() for name in raw.split(STUDIO_SEPARATOR) if name.strip()]
