"""Shared runtime narrowing for process and serialization boundaries."""

from __future__ import annotations

from typing import TypeVar

_RuntimeValue = TypeVar("_RuntimeValue")


def require_runtime_type(
    value: object,
    expected_type: type[_RuntimeValue],
    message: str,
) -> _RuntimeValue:
    """Return ``value`` narrowed to ``expected_type`` or fail closed."""

    if not isinstance(value, expected_type):
        raise TypeError(message)
    return value


__all__ = ["require_runtime_type"]
