"""Shared passive mechanics for typed Elektron saved-Kit codecs.

Device-specific layouts and semantic conversions remain in their respective
strategy and data modules. This module owns only behavior that must be
identical across saved-Kit families: bounded validation errors, fixed-width
ASCII names, recipe input validation, and recipe build metadata.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import cast

from ...observability.errors import ElektronKitFieldError
from ...snapshot import ElektronNativeObjectMessage


@dataclass(frozen=True, slots=True)
class KitRecipeBuildResult:
    """Common output contract for conservative saved-Kit recipe compilers."""

    message: ElektronNativeObjectMessage
    changed_payload_offsets: tuple[int, ...]
    changed_outside_declared_edit_regions: tuple[int, ...]

    @property
    def changed_payload_byte_count(self) -> int:
        return len(self.changed_payload_offsets)


def read_fixed_width_ascii(data: bytes | bytearray, *, offset: int, length: int) -> str:
    """Read one NUL-padded ASCII field from a native payload."""

    raw = bytes(data[offset : offset + length])
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace").rstrip()


def write_fixed_width_ascii(
    data: bytearray,
    *,
    offset: int,
    storage_length: int,
    visible_length: int,
    value: str,
    nul_terminated: bool,
) -> None:
    """Write a bounded ASCII field while preserving its storage contract."""

    if visible_length > storage_length:
        raise ElektronKitFieldError("visible name length cannot exceed storage length")
    if nul_terminated and visible_length >= storage_length:
        raise ElektronKitFieldError("NUL-terminated names require one storage byte")
    try:
        encoded = value.encode("ascii", errors="strict")
    except UnicodeEncodeError as exc:
        raise ElektronKitFieldError("saved-Kit names must contain ASCII characters") from exc
    visible = encoded[:visible_length]
    if nul_terminated:
        stored = (visible + b"\x00").ljust(storage_length, b"\x00")
    else:
        stored = visible.ljust(storage_length, b"\x00")
    data[offset : offset + storage_length] = stored


def require_recipe_mapping(
    value: object,
    label: str,
    error_type: type[ValueError],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise error_type(f"{label} must be an object")
    raw = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise error_type(f"{label} keys must be strings")
    return {str(key): item for key, item in raw.items()}


def require_sequence(
    value: object,
    label: str,
    error_type: type[ValueError],
) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise error_type(f"{label} must be an array")
    return cast(Sequence[object], value)


def require_exact_keys(
    mapping: Mapping[str, object],
    expected: frozenset[str],
    label: str,
    error_type: type[ValueError],
) -> None:
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


def require_int(value: object, label: str, error_type: type[ValueError]) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise error_type(f"{label} must be an integer")
    return value


def require_float(value: object, label: str, error_type: type[ValueError]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise error_type(f"{label} must be numeric")
    return float(value)


def require_recipe_bool(value: object, label: str, error_type: type[ValueError]) -> int:
    if not isinstance(value, bool):
        raise error_type(f"{label} must be true or false")
    return int(value)


def require_enum(
    field: str,
    value: object,
    enum_type: type[IntEnum],
    error_type: type[ValueError],
) -> int:
    if isinstance(value, str):
        try:
            return int(enum_type[value])
        except KeyError as exc:
            names = ", ".join(member.name for member in enum_type)
            raise error_type(
                f"unknown {field} enum name {value!r}; expected one of: {names}"
            ) from exc
    numeric = require_int(value, field, error_type)
    try:
        return int(enum_type(numeric))
    except (TypeError, ValueError) as exc:
        raise error_type(f"invalid numeric enum value {value!r} for {field}") from exc


def require_named_index(
    field: str,
    value: object,
    choices: Mapping[str, int],
    error_type: type[ValueError],
) -> int:
    if isinstance(value, str):
        key = value.upper()
        try:
            return choices[key]
        except KeyError as exc:
            raise error_type(
                f"unknown {field} value {value!r}; expected one of: {', '.join(choices)}"
            ) from exc
    numeric = require_int(value, field, error_type)
    if numeric not in choices.values():
        raise error_type(
            f"invalid {field} index {numeric}; expected one of: {sorted(set(choices.values()))}"
        )
    return numeric
