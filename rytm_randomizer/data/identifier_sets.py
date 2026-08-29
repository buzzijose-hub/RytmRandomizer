"""Shared validation for positive identifier sets.

The base rule is device-neutral: identifiers are positive integers and booleans
are never accepted as integers. Callers may inject a stricter device-domain
predicate while retaining one normalization and error-reporting path.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable


def validated_id_set(
    values: Iterable[object],
    *,
    field_name: str,
    is_allowed: Callable[[int], bool] | None = None,
    expected: str = "positive integer ids",
) -> frozenset[int]:
    """Normalize ``values`` and reject non-positive or disallowed identifiers."""

    invalid: list[object] = []
    valid: set[int] = set()
    for value in values:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 1
            or (is_allowed is not None and not is_allowed(value))
        ):
            invalid.append(value)
        else:
            valid.add(value)
    if invalid:
        rendered = sorted(repr(value) for value in invalid)
        raise ValueError(f"{field_name} must contain {expected}; got {rendered}")
    return frozenset(valid)


__all__ = ["validated_id_set"]
