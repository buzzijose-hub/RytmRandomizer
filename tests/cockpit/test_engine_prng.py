"""Tests for ``rytm_randomizer.cockpit.engine.prng``.

The xorshift32 PRNG is the byte-frozen, language-portable random source
for the mutation engine. These tests lock its behavior against the
published reference sequence (Marsaglia 2003) so a future C99 / Rust
port can be validated mechanically.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.engine.prng import xorshift32

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Known-value tests against the reference sequence
# ---------------------------------------------------------------------------


def test_xorshift32_known_sequence_seed_1() -> None:
    """The first 10 outputs for seed=1 are byte-frozen.

    Locking this sequence is the *only* way to detect a regression in the
    PRNG implementation; everything downstream in the mutation engine
    depends on it being bit-identical to the spec.

    The values below were computed from the canonical implementation in
    ``spec.md`` §3 and are the same values an embedded C99 implementation
    must reproduce.
    """

    expected = [
        270369,
        67634689,
        2647435461,
        307599695,
        2398689233,
        745495504,
        632435482,
        435756210,
        2005365029,
        2916098932,
    ]
    state = 1
    actual = []
    for _ in range(10):
        value, state = xorshift32(state)
        actual.append(value)
    assert actual == expected


def test_xorshift32_state_threads_through_calls() -> None:
    """The new_state returned must equal the value returned."""

    value, new_state = xorshift32(1)
    assert value == new_state
    assert value == 270369


def test_xorshift32_known_sequence_seed_42() -> None:
    """Lock a non-canonical seed too, to defend against accidental "fixes" that
    happen to leave the seed=1 sequence intact while breaking other seeds."""

    state = 42
    values: list[int] = []
    for _ in range(5):
        value, state = xorshift32(state)
        values.append(value)
    # Values computed from the reference implementation.
    expected = [
        11355432,
        2836018348,
        476557059,
        3648046016,
        3759983556,
    ]
    assert values == expected


# ---------------------------------------------------------------------------
# Output range invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 7, 42, 0xDEADBEEF, 0x12345678, 0xFFFFFFFF])
def test_xorshift32_output_fits_in_uint32(seed: int) -> None:
    """Every output must be a valid 32-bit unsigned integer."""

    state = seed
    for _ in range(100):
        value, state = xorshift32(state)
        assert 0 <= value <= 0xFFFFFFFF
        assert 0 <= state <= 0xFFFFFFFF


def test_xorshift32_period_is_not_trivially_short() -> None:
    """A first-million-step sanity check: xorshift32 cannot fall back to seed 1
    within the first million steps. (Its period is 2^32 - 1.) This is a smoke
    test that catches an obvious "masked the wrong bits" regression."""

    state = 1
    seen_starting_state = False
    for _ in range(1_000_000):
        _, state = xorshift32(state)
        if state == 1:
            seen_starting_state = True
            break
    assert not seen_starting_state


# ---------------------------------------------------------------------------
# Zero-state rejection (xorshift32 cannot escape the all-zero fixed point)
# ---------------------------------------------------------------------------


def test_xorshift32_rejects_zero_state() -> None:
    """The all-zero state is invalid; callers must normalise before calling."""

    with pytest.raises(ValueError, match="non-zero"):
        xorshift32(0)
