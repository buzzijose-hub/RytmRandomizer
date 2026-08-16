"""Shared structural option parsing for passive cockpit export CLIs."""

from __future__ import annotations

from typing import cast


def pop_required_cli_value(
    remaining: list[str],
    *,
    option: str,
    usage: str | None = None,
) -> str:
    """Pop one required option value with consistent command-local guidance."""

    if not remaining:
        message = f"{option} requires a value"
        if usage is not None:
            message += f". {usage}"
        raise ValueError(message)
    return remaining.pop(0)


def parse_bounded_integer(
    value: str,
    *,
    option: str,
    lower: int,
    upper: int,
) -> int:
    """Parse one canonical decimal integer inside an inclusive range."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer from {lower} to {upper}") from exc
    if str(parsed) != value or not lower <= parsed <= upper:
        raise ValueError(f"{option} must be an integer from {lower} to {upper}")
    return parsed


def exception_notes(exc: Exception) -> list[str]:
    """Return string-only exception notes for stable CLI diagnostics."""

    notes = getattr(exc, "__notes__", ())
    if not isinstance(notes, list):
        return []
    return [note for note in cast(list[object], notes) if isinstance(note, str)]


__all__ = ["exception_notes", "parse_bounded_integer", "pop_required_cli_value"]
