"""Tests for ``rytm_randomizer.cockpit.data.ulid`` — ULID-style id generator.

The cockpit data model uses string ids for ``Snapshot.snapshot_id``,
``ProfileModel.profile_id``, ``MutationCandidate.candidate_id``, and
``HistoryEntry`` parent links. They must be:

* **opaque** — callers never parse them,
* **sortable-ish** — ULIDs are commonly used because the encoded timestamp
  sorts lexicographically in roughly chronological order,
* **stdlib-only** — no new dependency (per WS-A scope).

We approximate ULID with: 48-bit millisecond timestamp + 80 random bits,
Crockford base32-encoded into 26 ASCII chars (uppercase, no padding).
"""

from __future__ import annotations

import re

import pytest

from rytm_randomizer.cockpit.data import ulid as ulid_mod

pytestmark = pytest.mark.fast


_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
"""Crockford base32 alphabet (excludes I, L, O, U) — 26 chars total."""


# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------


def test_new_ulid_returns_26_char_crockford_base32_string() -> None:
    """``new_ulid()`` must return a 26-char Crockford-base32 uppercase string."""

    token = ulid_mod.new_ulid()
    assert isinstance(token, str)
    assert len(token) == 26
    assert _ULID_RE.fullmatch(token) is not None, token


def test_repeated_calls_produce_distinct_ids() -> None:
    """Sequential calls produce a different id every time (random tail)."""

    seen = {ulid_mod.new_ulid() for _ in range(100)}
    assert len(seen) == 100


def test_alphabet_excludes_ambiguous_characters() -> None:
    """Crockford base32 drops I, L, O, U to avoid visual ambiguity."""

    forbidden = set("ILOU")
    for _ in range(50):
        token = ulid_mod.new_ulid()
        assert not (forbidden & set(token)), token


# ---------------------------------------------------------------------------
# Encoder primitive — exercise both with and without an explicit timestamp.
# ---------------------------------------------------------------------------


def test_encode_with_explicit_timestamp_is_deterministic_in_prefix() -> None:
    """``encode(ms, random_bits)`` must be a pure function of its inputs."""

    a = ulid_mod.encode(timestamp_ms=0, random_bits=0)
    b = ulid_mod.encode(timestamp_ms=0, random_bits=0)
    assert a == b
    assert _ULID_RE.fullmatch(a) is not None


def test_encode_with_max_inputs_still_26_chars() -> None:
    """Edge-case inputs at the top of each bit range still produce 26 chars.

    128 bits / 5 bits per base32 char = 25.6 chars; we always emit 26, so
    the leading char only ever carries the top 3 bits of the 128-bit
    value. With both timestamp + random saturated the value is
    ``(1<<128) - 1``, whose top 3 bits are ``0b111`` = ``7`` in the
    Crockford alphabet; the remaining 25 chars are all ``Z`` (``0b11111``).
    """

    token = ulid_mod.encode(
        timestamp_ms=(1 << 48) - 1,
        random_bits=(1 << 80) - 1,
    )
    assert len(token) == 26
    assert token == "7" + "Z" * 25


def test_encode_with_zero_inputs_is_all_zero_char() -> None:
    """All-zero inputs produce the lexicographically smallest ULID."""

    token = ulid_mod.encode(timestamp_ms=0, random_bits=0)
    assert token == "0" * 26


def test_encode_rejects_negative_timestamp() -> None:
    with pytest.raises(ValueError, match="timestamp_ms"):
        ulid_mod.encode(timestamp_ms=-1, random_bits=0)


def test_encode_rejects_timestamp_exceeding_48_bits() -> None:
    with pytest.raises(ValueError, match="timestamp_ms"):
        ulid_mod.encode(timestamp_ms=1 << 48, random_bits=0)


def test_encode_rejects_negative_random_bits() -> None:
    with pytest.raises(ValueError, match="random_bits"):
        ulid_mod.encode(timestamp_ms=0, random_bits=-1)


def test_encode_rejects_random_bits_exceeding_80_bits() -> None:
    with pytest.raises(ValueError, match="random_bits"):
        ulid_mod.encode(timestamp_ms=0, random_bits=1 << 80)


# ---------------------------------------------------------------------------
# Timestamp prefix sorts chronologically.
# ---------------------------------------------------------------------------


def test_later_timestamp_sorts_after_earlier_timestamp() -> None:
    """Two ULIDs with different timestamps sort by their timestamp prefix."""

    earlier = ulid_mod.encode(timestamp_ms=1_000, random_bits=0)
    later = ulid_mod.encode(timestamp_ms=2_000, random_bits=0)
    assert earlier < later
