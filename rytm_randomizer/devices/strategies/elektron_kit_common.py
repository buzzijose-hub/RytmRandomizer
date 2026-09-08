"""Shared passive mechanics for typed Elektron saved-Kit codecs.

Device-specific layouts and semantic conversions remain in their respective
strategy and data modules. This module owns only behavior that must be
identical across saved-Kit families: bounded validation errors, fixed-width
ASCII names, recipe input validation, and recipe build metadata.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum

# Compatibility re-exports: recipes retain their public API while all parsing
# is implemented once at the neutral guardrail boundary.
from ...guardrails.input_validation import require_exact_keys as require_exact_keys
from ...guardrails.input_validation import require_float as require_float
from ...guardrails.input_validation import require_int as require_int
from ...guardrails.input_validation import require_object as require_recipe_mapping
from ...guardrails.input_validation import require_recipe_bool as require_recipe_bool
from ...guardrails.input_validation import require_sequence as require_sequence
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


__all__ = [
    "KitRecipeBuildResult",
    "read_fixed_width_ascii",
    "write_fixed_width_ascii",
    "require_recipe_mapping",
    "require_sequence",
    "require_exact_keys",
    "require_int",
    "require_float",
    "require_recipe_bool",
    "require_enum",
    "require_named_index",
]
