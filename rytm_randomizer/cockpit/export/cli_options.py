"""Shared structural option parsing for passive cockpit export CLIs."""

from __future__ import annotations


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


__all__ = ["pop_required_cli_value"]
