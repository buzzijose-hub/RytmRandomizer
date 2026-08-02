"""Passive command-formatting helpers for the operator console."""

from __future__ import annotations

from typing import Final

_POWERSHELL_BARE_ARG_CHARS: Final[frozenset[str]] = frozenset(
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "-_./\\:+=,@%"
)


def powershell_literal_arg(value: str) -> str:
    """Return a PowerShell-safe literal command argument."""

    if value and all(char in _POWERSHELL_BARE_ARG_CHARS for char in value):
        return value
    return "'" + value.replace("'", "''") + "'"


__all__ = ["powershell_literal_arg"]
