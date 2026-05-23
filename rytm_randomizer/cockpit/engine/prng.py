"""Documented PRNG for the cockpit mutation engine.

The engine cannot rely on ``random`` (implementation-defined across
versions), nor on numpy (extra dep + float drift), nor on any
language-level RNG. The C99 / Rust port that lands in Phase 4 must
produce byte-identical output to this Python implementation, so the
PRNG is a small, well-known algorithm with a stable encoding.

Algorithm: **xorshift32** (Marsaglia 2003, "Xorshift RNGs").

State = one 32-bit unsigned integer; never zero (zero is a fixed point
of the shift sequence). Each call returns the next 32-bit pseudo-random
value AND the next state.

Reference sequence (seed=1)::

    state = 1                      → value = 270369,        state = 270369
    state = 270369                 → value = 67634689,      state = 67634689
    state = 67634689               → value = 2647435461,    state = 2647435461
    state = 2647435461             → value = 307599695,     state = 307599695
    state = 307599695              → value = 2398689233,    state = 2398689233
    ...

The reference sequence is locked by
:func:`tests.cockpit.test_engine_prng.test_xorshift32_known_sequence_seed_1`.
A C99 / Rust port must reproduce it bit-for-bit.

Encoding contract for C-port authors:

* State is logically a ``uint32_t``. The Python implementation models it
  with masked Python ``int`` arithmetic (``state & 0xFFFFFFFF`` after
  every left shift, since Python ints are unbounded).
* Shifts and XORs apply in this exact order each call:
  ``state ^= state << 13``, ``state ^= state >> 17``,
  ``state ^= state << 5``. The "left" shifts mask back to 32 bits.
* Zero is invalid input. The caller normalises a 0 seed before calling.
  The engine wrapper (:mod:`.mutate`) uses ``0x12345678`` as the
  documented substitute (chosen for nothing but legibility).
"""

from __future__ import annotations

from typing import Final

_UINT32_MASK: Final[int] = 0xFFFFFFFF
"""32-bit mask applied after every left shift to keep state in ``uint32`` range."""


def xorshift32(state: int) -> tuple[int, int]:
    """Advance an ``xorshift32`` state and return ``(value, new_state)``.

    Args:
        state: A non-zero 32-bit unsigned integer. The caller is
            responsible for normalising 0 to a non-zero seed before the
            first call (xorshift cannot escape the all-zero fixed point).

    Returns:
        A two-tuple ``(value, new_state)`` where both members are
        32-bit unsigned integers. ``value`` is the pseudo-random output;
        ``new_state`` becomes the seed for the next call.

    Raises:
        ValueError: if ``state`` is zero. The all-zero state is a fixed
            point of xorshift — feeding it in would emit zero forever.
            Callers must normalise (see :mod:`.mutate` for the engine's
            convention of mapping seed 0 to ``0x12345678``).
    """

    if state == 0:
        raise ValueError("xorshift32 state must be non-zero (all-zero is a fixed point)")
    state ^= (state << 13) & _UINT32_MASK
    state ^= state >> 17
    state ^= (state << 5) & _UINT32_MASK
    value = state & _UINT32_MASK
    return value, value


__all__ = ["xorshift32"]
