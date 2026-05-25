"""Small helpers for passive report JSON and line sections."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass


def _identity(value: object) -> object:
    return value


def _text(value: object) -> str:
    return str(value)


@dataclass(frozen=True)
class PassiveJsonField:
    """One dataclass attribute to expose in report JSON."""

    key: str
    attr: str
    transform: Callable[[object], object] = _identity


@dataclass(frozen=True)
class PassiveLineField:
    """One dataclass attribute to expose in text report lines."""

    label: str
    attr: str
    formatter: Callable[[object], str] = _text


def passive_dataclass_json(
    value: object,
    fields: Sequence[PassiveJsonField],
) -> dict[str, object]:
    """Return a deterministic JSON dict from a field spec."""

    return {field.key: field.transform(getattr(value, field.attr)) for field in fields}


def passive_section_lines(
    header: str,
    value: object,
    fields: Sequence[PassiveLineField],
) -> list[str]:
    """Return a passive report section from a field spec."""

    return [
        header,
        *[f"  {field.label}: {field.formatter(getattr(value, field.attr))}" for field in fields],
    ]


__all__ = [
    "PassiveJsonField",
    "PassiveLineField",
    "passive_dataclass_json",
    "passive_section_lines",
]
