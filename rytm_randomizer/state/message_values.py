"""Shared value coercion helpers for passive MIDI observation state."""

from __future__ import annotations


def coerce_int(value: object) -> int:
    if isinstance(value, int):
        return value
    return -1
