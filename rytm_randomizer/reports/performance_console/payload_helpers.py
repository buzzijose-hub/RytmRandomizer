"""Shared helpers for passive performance-console payload rendering."""

from __future__ import annotations

from collections.abc import Mapping


def dict_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    """Return only mapping rows from a JSON-style sequence."""

    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))
