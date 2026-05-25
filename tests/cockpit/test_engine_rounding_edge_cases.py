"""Focused edge-case regression tests for ``_round_half_away_from_zero``.

CODE_REVIEW.md **H5** flagged the
:func:`rytm_randomizer.cockpit.engine.mutate._round_half_away_from_zero`
helper as a Phase-4 firmware-port tripwire: a future C or Rust port that
inlines the rounding logic with a slightly different branch predicate
(e.g. ``f64::is_sign_positive`` in Rust returns ``False`` for ``-0.0``,
unlike Python's ``-0.0 >= 0.0`` which is ``True``) would silently fork
the byte output for a narrow band of inputs near zero.

The broader conformance suite in
:mod:`tests.cockpit.test_engine_conformance_edge_cases` covers a wide
table of values. This file is the **dedicated regression guard** for
exactly the tricky inputs called out in the H5 finding so a future
refactor of that bigger table cannot inadvertently drop them:

* ``-0.0``        — IEEE-754 signed zero; sign bit matters for the C-port.
* ``-0.5`` / ``0.5`` — exact half; ties must go AWAY FROM ZERO (C's
  ``round``), not to even (Python's built-in :func:`round`).
* ``-1.5`` / ``1.5`` — symmetric half; same away-from-zero requirement.

A test failure here is a Phase-4 portability blocker, not a cosmetic
issue: the SysEx output bytes would diverge between the Python cockpit
and the on-device firmware.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rytm_randomizer.cockpit.engine.mutate import _round_half_away_from_zero

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# H5 — the exact tricky inputs called out in CODE_REVIEW.md
# ---------------------------------------------------------------------------


def test_round_half_away_from_zero_negative_zero_returns_integer_zero() -> None:
    """``_round_half_away_from_zero(-0.0)`` returns ``0`` (CODE_REVIEW.md H5).

    The helper's branch predicate is ``value >= 0.0``. IEEE-754 specifies
    ``-0.0 == 0.0``, so ``-0.0 >= 0.0`` is ``True`` — the positive branch
    runs and returns ``int(-0.0 + 0.5) == 0``.

    Python's :class:`int` has no signed-zero representation; the
    return-type contract guarantees the caller receives a plain ``0``.
    A C-port that mirrors the Python branch predicate (``value >= 0.0``)
    agrees here. A Rust port that uses ``f64::is_sign_positive`` does
    NOT — it would take the negative branch and *still* return ``0`` for
    this single input, but diverge across ``(-0.5, 0.0)``. The spec
    pinned here is therefore "the Python branch predicate is the
    portable choice; do not refactor it to a sign-bit check."
    """

    result = _round_half_away_from_zero(-0.0)
    assert result == 0
    assert isinstance(result, int)
    # Python int has no negative zero, but pin the sign-bit assumption
    # the spec depends on at the IEEE-754 level for the C/Rust porter.
    assert (-0.0 >= 0.0) is True


def test_round_half_away_from_zero_at_negative_half_rounds_to_negative_one() -> None:
    """``_round_half_away_from_zero(-0.5)`` returns ``-1`` (CODE_REVIEW.md H5).

    ``-0.5 >= 0.0`` is ``False``, so the negative branch runs:
    ``-int(-(-0.5) + 0.5) == -int(1.0) == -1``. C's ``round(-0.5)`` is
    likewise ``-1.0``. Python's built-in :func:`round` returns ``0`` here
    (round-half-to-even / banker's rounding); we are deliberately NOT
    compatible with it — the C-port behavior is the contract.
    """

    assert _round_half_away_from_zero(-0.5) == -1


def test_round_half_away_from_zero_at_positive_half_rounds_to_one() -> None:
    """``_round_half_away_from_zero(0.5)`` returns ``1`` (CODE_REVIEW.md H5).

    ``0.5 >= 0.0`` is ``True``, so the positive branch runs:
    ``int(0.5 + 0.5) == int(1.0) == 1``. C's ``round(0.5)`` is also
    ``1.0``. Python's :func:`round` returns ``0`` here under banker's
    rounding; again, we deliberately diverge to match the firmware port.
    """

    assert _round_half_away_from_zero(0.5) == 1


def test_round_half_away_from_zero_at_one_point_five_rounds_to_two() -> None:
    """``_round_half_away_from_zero(1.5)`` returns ``2`` (CODE_REVIEW.md H5).

    Half-way between 1 and 2; "away from zero" picks 2. Python's
    :func:`round` returns ``2`` here too (because 2 happens to be even),
    so this row alone cannot distinguish the two conventions — pair it
    with the ``2.5`` case in the larger conformance table where banker's
    rounding picks 2 but away-from-zero picks 3.
    """

    assert _round_half_away_from_zero(1.5) == 2


def test_round_half_away_from_zero_at_negative_one_point_five_rounds_to_negative_two() -> None:
    """``_round_half_away_from_zero(-1.5)`` returns ``-2`` (CODE_REVIEW.md H5).

    Symmetric mirror of the ``1.5`` case. Pins that the helper is exactly
    odd-symmetric about zero: ``round(-v) == -round(v)`` for every
    half-integer ``v``. A signed-magnitude bug in a future C-port (e.g.
    ``return (int)(value + (value >= 0 ? 0.5 : -0.5))`` which actually
    DOES round half-away from zero) would still pass — but a port that
    accidentally uses ``floor(value + 0.5)`` would return ``-1`` here
    instead of ``-2`` and fail.
    """

    assert _round_half_away_from_zero(-1.5) == -2
