"""Strict device-neutral input primitives shared by recipes and wire schemas.

Callers choose the exception type at their boundary; the type checks and JSON
encoding have one implementation. No domain state, logging, or I/O lives here.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Final, Literal, cast

SequenceKind = Literal["sequence", "array", "list"]
_FILENAME_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def require_object(
    value: object, label: str, error_type: type[Exception] = TypeError
) -> Mapping[str, object]:
    """Require an object whose every key is already a string."""
    if not isinstance(value, Mapping):
        raise error_type(f"{label} must be an object")
    raw = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise error_type(f"{label} keys must be strings")
    return cast(Mapping[str, object], raw)


def require_sequence(
    value: object,
    label: str,
    error_type: type[Exception] = TypeError,
    *,
    kind: SequenceKind = "sequence",
) -> Sequence[object]:
    """Require a sequence, a JSON-compatible array, or a wire-only list."""
    if kind == "list":
        valid = isinstance(value, list)
    elif kind == "array":
        valid = isinstance(value, (list, tuple))
    else:
        valid = isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
    if not valid:
        raise error_type(f"{label} must be an array")
    return cast(Sequence[object], value)


def require_exact_keys(
    mapping: Mapping[str, object],
    expected: frozenset[str],
    label: str,
    error_type: type[Exception] = ValueError,
) -> None:
    """Reject missing and unknown schema fields."""
    supplied = set(mapping)
    missing = expected - supplied
    extra = supplied - expected
    if not missing and not extra:
        return
    parts: list[str] = []
    if missing:
        parts.append(f"missing {sorted(missing)}")
    if extra:
        parts.append(f"unknown {sorted(extra)}")
    raise error_type(f"{label} is incomplete: " + "; ".join(parts))


def require_int(value: object, label: str, error_type: type[Exception] = TypeError) -> int:
    """Require an actual integer, never a boolean or a numeric coercion."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise error_type(f"{label} must be an integer")
    return value


def require_float(value: object, label: str, error_type: type[Exception] = TypeError) -> float:
    """Require an integer or float without accepting boolean coercion."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise error_type(f"{label} must be numeric")
    return float(value)


def require_text(value: object, label: str, error_type: type[Exception] = TypeError) -> str:
    """Require text without coercing other JSON values."""
    if not isinstance(value, str):
        raise error_type(f"{label} must be a string")
    return value


def require_boolean(value: object, label: str, error_type: type[Exception] = TypeError) -> bool:
    """Require a JSON boolean, never an integer equivalent."""
    if not isinstance(value, bool):
        raise error_type(f"{label} must be a boolean")
    return value


def require_recipe_bool(value: object, label: str, error_type: type[Exception]) -> int:
    """Preserve the existing recipe API's boolean-to-byte conversion."""
    try:
        return int(require_boolean(value, label, error_type))
    except error_type as exc:
        raise error_type(f"{label} must be true or false") from exc


def require_text_field(data: Mapping[str, object], key: str, label: str) -> str:
    """Read one required schema text field."""
    return require_text(data[key], f"{label}.{key}")


def require_integer_field(data: Mapping[str, object], key: str, label: str) -> int:
    """Read one required strict schema integer field."""
    return require_int(data[key], f"{label}.{key}")


def require_finite_number_field(data: Mapping[str, object], key: str, label: str) -> float:
    """Read a numeric schema field that must be finite."""
    value = require_float(data[key], f"{label}.{key}")
    if not math.isfinite(value):
        raise ValueError(f"{label}.{key} must be finite")
    return value


def require_text_tuple(
    value: object,
    label: str,
    error_type: type[Exception] = TypeError,
    *,
    kind: SequenceKind = "array",
) -> tuple[str, ...]:
    """Read an immutable text array under the caller's container policy."""
    return tuple(
        require_text(item, label, error_type)
        for item in require_sequence(value, label, error_type, kind=kind)
    )


def require_integer_tuple(
    value: object,
    label: str,
    error_type: type[Exception] = TypeError,
    *,
    kind: SequenceKind = "array",
) -> tuple[int, ...]:
    """Read an immutable strict integer array under the container policy."""
    return tuple(
        require_int(item, label, error_type)
        for item in require_sequence(value, label, error_type, kind=kind)
    )


def validate_filename_id(value: str, label: str, *, maximum: int) -> None:
    """Validate one bounded lowercase identifier, distinct from a path."""
    if len(value) > maximum or _FILENAME_ID_RE.fullmatch(value) is None:
        raise ValueError(
            f"{label} must be a lowercase filename-safe id of at most {maximum} characters"
        )


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    """Encode deterministic UTF-8 JSON with one final newline and no NaN."""
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    ).encode("utf-8")
