"""Shared helpers for passive performance-console payload rendering."""

from __future__ import annotations

from collections.abc import Mapping


def dict_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    """Return only mapping rows from a JSON-style sequence."""

    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def payload_text(payload: Mapping[str, object], key: str) -> str:
    """Return a string payload field or an empty string."""

    value = payload.get(key)
    if isinstance(value, str):
        return value
    return ""


def payload_int(payload: Mapping[str, object], key: str) -> int:
    """Return an integer payload field or zero."""

    value = payload.get(key)
    if isinstance(value, int):
        return value
    return 0


def payload_text_list(payload: Mapping[str, object], key: str) -> list[str]:
    """Return string-only list payload fields."""

    value = payload.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
