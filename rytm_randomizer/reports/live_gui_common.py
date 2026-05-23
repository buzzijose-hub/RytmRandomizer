"""Shared helpers for passive live-GUI report modules."""

from __future__ import annotations

from collections.abc import Sequence

from .formatter import powershell_literal_arg


def format_cli_error(exc: Exception) -> str:
    """Return the standard passive live-GUI CLI error line."""

    return f"Error: {exc}"


def pop_option_value(remaining: list[str], *, usage: str) -> str:
    """Pop the next CLI option value or raise the command usage text."""

    if not remaining:
        raise ValueError(usage)
    return remaining.pop(0)


def status_severity(status: str) -> str:
    """Map passive readiness status to report severity."""

    if status == "blocked":
        return "critical"
    if status == "review-needed":
        return "warning"
    return "info"


def replace_replay_command(
    command: str,
    *,
    source_command: str,
    target_command: str,
    extra_options: Sequence[tuple[str, str]],
) -> str | None:
    """Rewrite a passive replay command and append quoted option values."""

    if source_command not in command:
        return None
    suffix = "".join(
        f" {option} {powershell_literal_arg(value)}" for option, value in extra_options
    )
    return command.replace(source_command, target_command, 1) + suffix
