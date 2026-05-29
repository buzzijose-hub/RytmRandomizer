"""Passive SysEx file helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Final

_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7


def extract_sysex_payloads(raw: bytes) -> tuple[bytes, ...]:
    """Return unframed SysEx payloads from ``raw`` bytes."""

    if not raw:
        raise ValueError("SysEx data is empty")

    frames: list[bytes] = []
    cursor = 0
    while cursor < len(raw):
        try:
            start = raw.index(_SYSEX_START, cursor)
        except ValueError:
            break
        try:
            end = raw.index(_SYSEX_END, start + 1)
        except ValueError as exc:
            raise ValueError(
                f"SysEx frame starting at byte {start} is without a closing F7 byte"
            ) from exc
        payload = raw[start + 1 : end]
        if not payload:
            raise ValueError(f"SysEx frame starting at byte {start} has an empty payload")
        frames.append(payload)
        cursor = end + 1

    if frames:
        return tuple(frames)
    if raw[0] == _SYSEX_START or raw[-1] == _SYSEX_END:
        raise ValueError("SysEx framing is incomplete; expected both F0 and F7 bytes")
    return (raw,)


def read_sysex_payloads_from_path(sysex_path: str | Path) -> tuple[bytes, ...]:
    """Read ``sysex_path`` and return unframed SysEx payloads."""

    path = Path(sysex_path)
    if not path.exists():
        raise ValueError(f"SysEx file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"SysEx path is not a file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Could not read SysEx file {path}: {exc}") from exc
    return extract_sysex_payloads(raw)


__all__ = [
    "extract_sysex_payloads",
    "read_sysex_payloads_from_path",
]
