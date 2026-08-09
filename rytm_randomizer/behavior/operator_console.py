"""Passive command-formatting helpers for the operator console."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

_POWERSHELL_BARE_ARG_CHARS: Final[frozenset[str]] = frozenset(
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "-_./\\:+=@%"
)


def powershell_literal_arg(value: str, *, always_quote: bool = False) -> str:
    """Return a PowerShell-safe literal command argument."""

    if (
        not always_quote
        and value
        and not value.startswith("@")
        and all(char in _POWERSHELL_BARE_ARG_CHARS for char in value)
    ):
        return value
    return "'" + value.replace("'", "''") + "'"


def powershell_command(argv: Sequence[str]) -> str:
    """Render ``argv`` as one copy-pasteable PowerShell command line.

    The executable (``argv[0]``) is always single-quoted and invoked through
    the ``&`` call operator, because a quoted string at command position is
    otherwise just an expression in PowerShell; every later element is
    quoted only when :func:`powershell_literal_arg` requires it.

    NOTE for consolidators: ``reports/cockpit_export_rehearsal.py`` and
    ``reports/live_gui_common.py`` still hand-assemble replay commands in a
    different shape (no ``&`` operator, bare executable). Their outputs are
    byte-frozen by the report goldens, so converging them onto this builder
    is a deliberate golden-regeneration change, not a drive-by refactor.
    """

    return "& " + " ".join(
        powershell_literal_arg(value, always_quote=index == 0) for index, value in enumerate(argv)
    )


__all__ = ["powershell_command", "powershell_literal_arg"]
