"""ULID-style id generator built on stdlib ``uuid`` + ``time`` (no new dep).

A real `Universally Unique Lexicographically Sortable Identifier (ULID)
<https://github.com/ulid/spec>`_ is a 128-bit value split into:

* a 48-bit UNIX-time-in-milliseconds prefix, and
* an 80-bit random suffix,

encoded as 26 ASCII characters of `Crockford base32
<https://www.crockford.com/base32.html>`_ (alphabet ``0-9A-HJKMNP-TV-Z`` —
the ambiguous letters ``I``, ``L``, ``O``, ``U`` are omitted).

The cockpit data model never re-parses an id; the prefix is here purely so
in-process collections of ids sort in roughly chronological order, which
makes UIs (history strips, debug logs) feel correct without an extra
``captured_at`` lookup.

The implementation deliberately stays in pure stdlib (``time`` for the
millisecond clock, ``secrets`` for the random suffix). No ``ulid``,
``python-ulid``, or ``uuid7`` dependency.
"""

from __future__ import annotations

import secrets
import time
from typing import Final

_CROCKFORD_ALPHABET: Final[str] = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
"""Crockford base32 alphabet — 32 chars, excludes I, L, O, U."""

_ULID_BITS: Final[int] = 128
_TIMESTAMP_BITS: Final[int] = 48
_RANDOM_BITS: Final[int] = 80
_ULID_CHARS: Final[int] = 26
_MAX_TIMESTAMP_MS: Final[int] = (1 << _TIMESTAMP_BITS) - 1
_MAX_RANDOM_BITS: Final[int] = (1 << _RANDOM_BITS) - 1


def encode(*, timestamp_ms: int, random_bits: int) -> str:
    """Encode a 48-bit timestamp + 80-bit random integer as a 26-char ULID.

    Both arguments are validated for range; this function is pure (same
    inputs always produce the same string) so it can be exercised in tests
    without monkey-patching the clock or ``secrets``.

    Args:
        timestamp_ms: UNIX time in milliseconds. 0 <= value < 2**48.
        random_bits: 80-bit random integer. 0 <= value < 2**80.

    Returns:
        The 26-character Crockford-base32 ULID string.

    Raises:
        ValueError: if either input falls outside its bit range.
    """

    if timestamp_ms < 0 or timestamp_ms > _MAX_TIMESTAMP_MS:
        raise ValueError(
            f"timestamp_ms must fit in 48 bits (0..{_MAX_TIMESTAMP_MS}); got {timestamp_ms}"
        )
    if random_bits < 0 or random_bits > _MAX_RANDOM_BITS:
        raise ValueError(
            f"random_bits must fit in 80 bits (0..{_MAX_RANDOM_BITS}); got {random_bits}"
        )

    value = (timestamp_ms << _RANDOM_BITS) | random_bits
    # 128 bits / 5 bits per base32 char = 25.6 → pad to 26 chars by emitting
    # 130 bits and discarding the high 2 (always zero given the bit budgets).
    chars: list[str] = []
    for _ in range(_ULID_CHARS):
        chars.append(_CROCKFORD_ALPHABET[value & 0x1F])
        value >>= 5
    chars.reverse()
    return "".join(chars)


def new_ulid() -> str:
    """Generate a fresh ULID using the current wall clock + 80 random bits.

    Convenience wrapper around :func:`encode`. The clock comes from
    ``time.time_ns()`` (monotonic-ish; same source the stdlib ``uuid7``
    proposal uses); the random suffix comes from :func:`secrets.randbits`
    so the value is cryptographically random and safe to use as an opaque
    handle even if a future iteration of the cockpit exposes ids over the
    wire.
    """

    timestamp_ms = time.time_ns() // 1_000_000
    random_bits = secrets.randbits(_RANDOM_BITS)
    return encode(timestamp_ms=timestamp_ms, random_bits=random_bits)


__all__ = ["encode", "new_ulid"]
