"""Edge-case conformance tests for the cockpit mutation engine (CR PR15).

These tests pin two cross-implementation tripwires that the existing
:mod:`tests.cockpit.test_engine_mutate` and :mod:`.test_engine_conformance`
suites do not cover explicitly:

1. **Rounding around the zero / half boundary.** The Phase 4 hardware
   runtime ports :func:`rytm_randomizer.cockpit.engine.mutate.mutate` to
   C99 / Rust. The private helper ``_round_half_away_from_zero`` is the
   single point where IEEE-754 sign quirks (``-0.0 >= 0.0`` is ``True``
   in Python and C; ``f64::is_sign_positive(-0.0)`` is ``False`` in
   Rust) can silently fork the byte output. This file locks the helper's
   behavior at the ±0.0, ±0.5, ±0.49999, ±0.50001, ±1.0, ±1.5 and a
   handful of larger magnitudes so any port that diverges fails CI here
   before it reaches the conformance corpus.

2. **The defensive sort over ``snapshot.pads`` (P6).** ``mutate`` calls
   ``sorted(snapshot.pads, key=lambda p: p.pad_id)`` with a comment that
   reads *"The data model enforces ascending order at construction;
   re-sorting defensively keeps the algorithm portable if that contract
   ever loosens."* But until this commit nothing pinned that the
   data-layer's contract actually holds — a defensive sort without a
   guard test is vestigial. The :class:`~rytm_randomizer.cockpit.data.Snapshot`
   ``__post_init__`` raises on unsorted pads (locked here), so the
   defensive sort is provably redundant; for symmetry we also pin that
   the engine output is invariant under ``ProfileModel.pad_mappings``
   ordering, since float summation in :func:`_pad_bias` is the obvious
   non-associative-sum tripwire.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.engine.mutate import (
    _round_half_away_from_zero,
    mutate,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers — kept tiny so the test bodies stay readable
# ---------------------------------------------------------------------------


_FIXED_CAPTURED_AT = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


def _snapshot(pads: tuple[PadState, ...], snapshot_id: str = "SNAP1") -> Snapshot:
    return Snapshot(
        snapshot_id=snapshot_id,
        device="rytm_mk2",
        captured_at=_FIXED_CAPTURED_AT,
        pads=pads,
        scene_slot=None,
        bpm=128.0,
    )


def _profile(
    *,
    traits: tuple[StyleTrait, ...],
    pad_mappings: tuple[TraitPadWeight, ...],
    profile_id: str = "PROF1",
) -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name="Edge Case Profile",
        kind="user",
        model_version="1.0",
        traits=traits,
        pad_mappings=pad_mappings,
        transition_curve="linear",
        source_summary="edge-case test fixture",
    )


def _without_candidate_id(d: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in d.items() if k != "candidate_id"}


# ---------------------------------------------------------------------------
# Rounding: negative-zero / negative-half boundary (H5)
# ---------------------------------------------------------------------------


def test_round_half_away_from_zero_for_negative_zero() -> None:
    """``_round_half_away_from_zero(-0.0)`` returns ``0`` (integer, no sign).

    This pins the **Python/C-port branch predicate** used in the helper
    (``value >= 0.0``). In IEEE-754, ``-0.0 == 0.0`` is ``True`` and so
    ``-0.0 >= 0.0`` is ``True`` — the helper takes the positive branch and
    returns ``int(-0.0 + 0.5) == 0``. A Rust port that naively writes
    ``if value.is_sign_positive()`` would take the **negative** branch
    instead (Rust's ``is_sign_positive(-0.0)`` is ``false``), still return
    0 here, but diverge for inputs in ``(-0.5, 0.0)``. The spec calls this
    out explicitly; see ``engine/spec.md`` §"Rounding & Negative Zero".
    """

    result = _round_half_away_from_zero(-0.0)
    assert result == 0
    # Pin the Python-level quirk the spec depends on: -0.0 is not less than 0.0.
    assert (-0.0 >= 0.0) is True


def test_round_half_away_from_zero_at_exactly_negative_half() -> None:
    """``_round_half_away_from_zero(-0.5)`` returns ``-1`` (matches C's ``round(-0.5)``).

    ``-0.5 >= 0.0`` is ``False``, so the helper takes the negative branch:
    ``-int(-(-0.5) + 0.5) == -int(1.0) == -1``. C's ``round(-0.5)`` is
    likewise ``-1.0``. Python's built-in :func:`round` returns ``0`` here
    (banker's rounding); we are deliberately NOT compatible with it.
    """

    assert _round_half_away_from_zero(-0.5) == -1


def test_round_half_away_from_zero_at_exactly_positive_half() -> None:
    """``_round_half_away_from_zero(0.5)`` returns ``1`` (matches C's ``round(0.5)``).

    ``0.5 >= 0.0`` is ``True`` → ``int(0.5 + 0.5) == int(1.0) == 1``. C's
    ``round(0.5)`` is also ``1.0``. Python's :func:`round` returns ``0``
    (banker's rounding); again, we deliberately diverge.
    """

    assert _round_half_away_from_zero(0.5) == 1


@pytest.mark.parametrize(
    "value, expected",
    [
        # Zero boundary
        (0.0, 0),
        (-0.0, 0),
        # Just-below-half (truncates toward zero in both directions)
        (0.49999, 0),
        (-0.49999, 0),
        # Exact half — ties go away from zero
        (0.5, 1),
        (-0.5, -1),
        # Just-above-half (rounds away)
        (0.50001, 1),
        (-0.50001, -1),
        # Unit magnitude
        (1.0, 1),
        (-1.0, -1),
        # 1.5 — ties go away from zero
        (1.5, 2),
        (-1.5, -2),
        # 2.5 — would be 2 under banker's, must be 3 here
        (2.5, 3),
        (-2.5, -3),
        # Mid-range realistic engine outputs
        (32.4, 32),
        (-32.4, -32),
        (32.5, 33),
        (-32.5, -33),
        (63.6, 64),
        (-63.6, -64),
        # Engine clamp ceiling
        (127.49, 127),
        (-127.49, -127),
        (127.5, 128),  # clamp upstream in mutate; helper itself just rounds
        (-127.5, -128),
        # Large magnitudes — still purely round-half-away-from-zero
        (1000.5, 1001),
        (-1000.5, -1001),
    ],
)
def test_round_half_away_from_zero_boundary_table(value: float, expected: int) -> None:
    """Table-driven matrix of ±0.0, ±0.5±epsilon, ±1.5, ±2.5, and engine-range values.

    Every row is a C-port tripwire: an implementation that uses
    ``floor(value + 0.5)`` (wrong for negatives), banker's rounding, or
    ``f64::is_sign_positive`` as the branch predicate will diverge on
    at least one row here.
    """

    assert _round_half_away_from_zero(value) == expected


def test_round_half_away_from_zero_is_symmetric_about_zero() -> None:
    """For every ``v`` tested, ``round(-v) == -round(v)``. Pins the "away-from-zero" half."""

    for v in (0.5, 1.5, 2.5, 0.49999, 0.50001, 32.4, 32.5, 127.49, 1000.5):
        pos = _round_half_away_from_zero(v)
        neg = _round_half_away_from_zero(-v)
        assert pos == -neg, f"asymmetric: round({v}) = {pos}, round({-v}) = {neg}"


# ---------------------------------------------------------------------------
# PRNG reachability of the -0.0 / -0.5 boundary
# ---------------------------------------------------------------------------


def test_mutate_reaches_negative_zero_via_prng() -> None:
    """Document and pin: through the engine's PRNG path, ``delta`` cannot land on
    exactly ``-0.0`` or exactly ``-0.5``.

    Reasoning (locked here so a future spec change re-evaluates this):

    * ``raw = xorshift32(state)`` is in ``[1, 2**32 - 1]`` for non-zero
      ``state``; xorshift32 cannot escape ``state == 0``. So ``raw != 0``,
      i.e. ``r = raw / 2**32`` is in ``(0.0, 1.0)`` — strictly open on
      both sides.
    * ``r - 0.5`` is therefore in ``(-0.5, 0.5)`` — ``-0.5`` is NOT
      reachable at the unit level.
    * ``(r - 0.5) * 2.0`` is in ``(-1.0, 1.0)``. The product with any
      ``scale > 0`` (which holds in the cockpit: ``depth >= 0.10`` and
      ``0.5 + bias >= 0.5`` ⇒ ``scale >= 6.35``) yields a magnitude
      ``< scale``, so the only way for the product to be ``-0.0`` is
      IEEE-754 underflow — and the minimum non-zero magnitude
      ``|(r - 0.5)*2|`` is ``2 / 2**32 = 2**-31``, with ``scale >= 6.35``
      that gives a magnitude no smaller than ``2**-31 * 6.35 ≈ 2**-28``,
      vastly above the subnormal threshold ``2**-1074``.

    We assert reachability by scanning ~150k PRNG draws across multiple
    seeds and verifying delta never equals ``-0.0`` or ``-0.5`` exactly.
    The helper still has to handle these inputs correctly (a C-port that
    inlines the formula and somehow produces ``-0.0`` is portable iff
    the helper agrees), which is what the direct table-driven test above
    pins. This test pins the *upstream* claim that the helper's
    boundary cases are unreachable through the normal mutation path.
    """

    # Import the same module-level constants the engine uses so this test
    # is invalidated automatically if any of them shift.
    from rytm_randomizer.cockpit.engine.mutate import (
        _BIAS_FLOOR,
        _CC_RANGE,
        _PRNG_NORMALIZER,
    )
    from rytm_randomizer.cockpit.engine.prng import xorshift32

    # Smallest realistic scale = depth_min(0.10) * 127 * (0.5 + bias_min(0.0))
    min_scale = 0.10 * _CC_RANGE * _BIAS_FLOOR
    assert min_scale >= 1.0, "spec invariant: minimum scale exceeds 1.0"

    scales = [
        0.10 * _CC_RANGE * 0.5,
        0.10 * _CC_RANGE * 1.5,
        0.50 * _CC_RANGE * 0.5,
        0.50 * _CC_RANGE * 1.5,
        0.90 * _CC_RANGE * 0.5,
        0.90 * _CC_RANGE * 1.5,
    ]

    seeds = [1, 7, 42, 0x12345678, 999, 31337]
    draws_per_seed = 25_000
    neg_zero_count = 0
    neg_half_count = 0
    seen_neg_unit = False  # sanity: we DO see negative unit-deltas

    for seed in seeds:
        state = seed if seed != 0 else 0x12345678
        # 8-step warm-up matches the engine
        for _ in range(8):
            _, state = xorshift32(state)
        for _ in range(draws_per_seed):
            raw, state = xorshift32(state)
            r = raw / _PRNG_NORMALIZER
            unit = (r - 0.5) * 2.0
            if unit < 0.0:
                seen_neg_unit = True
            for sc in scales:
                delta = unit * sc
                if delta == 0.0 and math.copysign(1.0, delta) == -1.0:
                    neg_zero_count += 1
                if delta == -0.5:
                    neg_half_count += 1

    # Sanity: we exercised the negative-delta branch many times.
    assert seen_neg_unit, "scan produced no negative deltas — PRNG / scaling broken"
    # Pin: the documented unreachable cases stayed unreachable.
    assert (
        neg_zero_count == 0
    ), f"engine produced delta=-0.0 ({neg_zero_count}x); spec assumption broken"
    assert (
        neg_half_count == 0
    ), f"engine produced delta=-0.5 ({neg_half_count}x); spec assumption broken"


# ---------------------------------------------------------------------------
# Defensive sort guard (P6)
# ---------------------------------------------------------------------------


def test_snapshot_rejects_non_ascending_pads_at_construction() -> None:
    """The data-layer contract the engine's defensive sort *defends against* is
    actually enforced at construction — proving the defensive sort is
    superseded by ``Snapshot.__post_init__``.

    If this test ever starts failing, the data-layer contract has been
    loosened and the engine's defensive sort comment (``mutate.py:182-184``)
    is no longer vestigial — re-instate / strengthen it consciously.
    """

    pad_low = PadState(pad_id=1, machine="bd", params={"k": 64})
    pad_high = PadState(pad_id=2, machine="sd", params={"k": 64})
    with pytest.raises(ValueError, match="ascending"):
        # Reversed pad order — must raise.
        Snapshot(
            snapshot_id="SNAP_BAD",
            device="rytm_mk2",
            captured_at=_FIXED_CAPTURED_AT,
            pads=(pad_high, pad_low),
            scene_slot=None,
            bpm=128.0,
        )


def test_engine_output_invariant_under_profile_mapping_shuffle() -> None:
    """Shuffling ``ProfileModel.pad_mappings`` declaration order does not change
    engine output for any (snapshot, profile, depth, seed).

    Float summation in ``_pad_bias`` is the obvious non-associative-sum
    risk: the helper does ``weighted_sum += trait_values[trait] * weight``
    in declaration order. For the small magnitudes involved here (every
    trait value and weight is in ``[0, 1]``) the catastrophic-cancellation
    surface is empty, but pinning the invariant explicitly protects a
    future refactor (e.g. adding wider-range weights or trait values)
    from a silently order-dependent bias.

    This is the *positive* counterpart to the test above: where pads are
    locked to ascending order at construction, mapping order is NOT, so
    shuffling is a meaningful threat that needs an active guard.
    """

    snapshot = _snapshot(
        pads=(
            PadState(pad_id=1, machine="bd", params={"tun": 60, "dec": 40, "lev": 100}),
            PadState(pad_id=2, machine="sd", params={"tun": 50, "dec": 80, "lev": 95}),
            PadState(pad_id=3, machine="sy", params={"tun": 70, "dec": 30, "lev": 105}),
        ),
    )

    traits = (
        StyleTrait(name="low_end", value=0.8),
        StyleTrait(name="texture", value=0.3),
        StyleTrait(name="brightness", value=0.6),
    )

    # Canonical ordering: pad 1 first, then 2, then 3; multiple mappings per pad.
    canonical_mappings = (
        TraitPadWeight(trait="low_end", pad_id=1, weight=0.9),
        TraitPadWeight(trait="texture", pad_id=1, weight=0.4),
        TraitPadWeight(trait="brightness", pad_id=2, weight=0.5),
        TraitPadWeight(trait="low_end", pad_id=2, weight=0.2),
        TraitPadWeight(trait="brightness", pad_id=3, weight=0.7),
        TraitPadWeight(trait="texture", pad_id=3, weight=0.3),
    )
    # Shuffled: deliberately interleaves pad_ids and traits.
    shuffled_mappings = (
        canonical_mappings[4],  # brightness@3
        canonical_mappings[0],  # low_end@1
        canonical_mappings[3],  # low_end@2
        canonical_mappings[5],  # texture@3
        canonical_mappings[1],  # texture@1
        canonical_mappings[2],  # brightness@2
    )

    prof_canonical = _profile(traits=traits, pad_mappings=canonical_mappings, profile_id="PROF_CAN")
    prof_shuffled = _profile(traits=traits, pad_mappings=shuffled_mappings, profile_id="PROF_SHUF")

    # Run across multiple seeds and depths to make sure invariance holds
    # uniformly, not just for one lucky (seed, depth) coincidence.
    for depth in (0.1, 0.3, 0.5, 0.7, 0.9):
        for seed in (1, 7, 42, 0xDEADBEEF):
            cand_canonical = mutate(snapshot, prof_canonical, depth=depth, seed=seed)
            cand_shuffled = mutate(snapshot, prof_shuffled, depth=depth, seed=seed)

            # The two profile_ids differ by design; compare the rest of the
            # output (and exclude candidate_id — see test_engine_mutate).
            canonical_dict = _without_candidate_id(cand_canonical.to_dict())
            shuffled_dict = _without_candidate_id(cand_shuffled.to_dict())
            canonical_dict.pop("profile_id")
            shuffled_dict.pop("profile_id")

            assert canonical_dict == shuffled_dict, (
                f"engine output diverged after pad_mappings shuffle "
                f"(depth={depth}, seed={seed})"
            )


def test_engine_pad_iteration_order_is_pad_id_ascending() -> None:
    """``mutate`` emits ``pad_deltas`` in strictly ascending ``pad_id`` order.

    Direct lock on the spec's iteration rule (§4 of ``engine/spec.md``).
    The data layer already enforces this at the snapshot level, so this
    test verifies the engine preserves the order on the output as well —
    the defensive sort would catch a mid-engine swap that the data layer
    cannot see.
    """

    snapshot = _snapshot(
        pads=(
            PadState(pad_id=1, machine="bd", params={"k": 64}),
            PadState(pad_id=2, machine="sd", params={"k": 64}),
            PadState(pad_id=4, machine="cb", params={"k": 64}),  # gap is fine
            PadState(pad_id=7, machine="sy", params={"k": 64}),
        ),
    )
    prof = _profile(
        traits=(StyleTrait(name="t", value=0.5),),
        pad_mappings=(TraitPadWeight(trait="t", pad_id=1, weight=0.5),),
    )
    cand = mutate(snapshot, prof, depth=0.5, seed=42)
    pad_ids = [pd.pad_id for pd in cand.pad_deltas]
    assert pad_ids == sorted(pad_ids), f"pad_deltas not sorted: {pad_ids}"
    assert pad_ids == [1, 2, 4, 7]
