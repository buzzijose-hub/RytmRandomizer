"""``mutate(snapshot, profile, depth, seed) -> MutationCandidate``.

The single public entry point of the cockpit mutation engine. Pure
function: same inputs → same outputs, no side effects (except
``candidate_id`` which is a fresh ULID — the candidate identity is the
only non-deterministic field, and excluded from conformance fixtures).

See :doc:`spec.md <./spec>` for the normative algorithm. Hard rules:

* Iterate ``snapshot.pads`` in ``pad_id`` order. The data model already
  enforces ascending ``pad_id``; we re-sort defensively so a future
  relaxation cannot silently break determinism.
* Iterate each pad's ``params`` in ``sorted(key)`` order. Python dict
  insertion-order is portable today, but ``sorted()`` is portable across
  *any* language. The C-port author iterates a sorted key array.
* PRNG is :func:`.prng.xorshift32`. No ``random``, no numpy, no
  language-level RNG.
* Float arithmetic uses IEEE-754 double precision (Python's ``float``,
  C's ``double``). The formula is encoded to avoid catastrophic
  cancellation; see spec §"Arithmetic" for the rationale.
* Clamp output to ``[0, 127]`` (Rytm MIDI CC value range).
* Emit a key into ``proposed_params`` for **every** input key
  (unchanged or not); record only **actually-changed** keys in
  ``changed_keys`` so callers can compute the MIDI send list cheaply.
"""

from __future__ import annotations

from typing import Final

from ...observability.logging import get_logger
from ..data import (
    MutationCandidate,
    PadDelta,
    ProfileModel,
    Snapshot,
    Status,
    new_ulid,
)
from ..mutation_targets import MutationTargets
from .prng import xorshift32

_logger = get_logger(__name__)
"""Module logger for the cockpit mutation engine. Bound here so future
structured log calls (per-mutation telemetry, sampled-DEBUG candidate
audit lines) can land in the package's structured stream without
touching this file's imports. See ``OBSERVABILITY_REVIEW.md`` Phase 5."""

_CC_MIN: Final[int] = 0
"""Minimum Rytm CC value."""

_CC_MAX: Final[int] = 127
"""Maximum Rytm CC value."""

_CC_RANGE: Final[int] = 127
"""Full Rytm CC dynamic range used as the depth scaling factor."""

_BIAS_FLOOR: Final[float] = 0.5
"""Bias multiplier additive term. A pad with no profile mapping still mutates."""

_TOTAL_WEIGHT_FLOOR: Final[float] = 0.001
"""Divisor floor in the bias formula. Avoids divide-by-zero without changing the unmapped case."""

_PRNG_SEED_FOR_ZERO: Final[int] = 0x12345678
"""Substitute seed when the caller passes 0 (xorshift32 cannot escape an all-zero state)."""

_PRNG_WARMUP_STEPS: Final[int] = 8
"""Discard the first 8 xorshift32 outputs to mix small seeds before sampling.

Small seeds (e.g. 1, 7, 42) feed xorshift32 a state whose first 1-2 outputs
are dominated by the low-order bits and produce r-values in [0, 0.02). This
biases the first draw heavily negative; spinning 8 times mixes the state.
The C port must perform the same 8 discards before the first sampled draw."""

_PRNG_NORMALIZER: Final[float] = float(1 << 32)
"""Divisor that maps a 32-bit xorshift32 output to the half-open interval ``[0.0, 1.0)``."""

_DEPTH_SAFE_CEIL: Final[float] = 0.30
"""Strictly below this depth the candidate is ``safe``."""

_DEPTH_ARMED_CEIL: Final[float] = 0.65
"""Strictly below this depth the candidate is ``armed``; above-or-equal is ``high_risk``."""


def _classify_safety(depth: float) -> Status:
    """Map a depth value to the canonical ``Status`` literal.

    Thresholds (matching ``spec.md`` §"Safety status"):

    * ``depth < 0.30`` → ``"safe"``
    * ``0.30 <= depth < 0.65`` → ``"armed"``
    * ``depth >= 0.65`` → ``"high_risk"``

    Return type is the :data:`Status` literal alias so the caller does not
    need a ``# type: ignore[arg-type]`` to feed the result into
    :class:`MutationCandidate.safety_status`; the literal narrowing is
    earned by the branching here (each return statement returns a value
    that is statically a member of :data:`Status`).
    """

    if depth < _DEPTH_SAFE_CEIL:
        return "safe"
    if depth < _DEPTH_ARMED_CEIL:
        return "armed"
    return "high_risk"


def _pad_bias(profile: ProfileModel, pad_id: int) -> float:
    """Compute the per-pad bias as the trait-weight-weighted average trait value.

    Iterates ``profile.pad_mappings`` in declaration order (the order the
    profile author chose). For each mapping whose ``pad_id`` matches,
    looks up the trait value via the dict built once below. Returns the
    weighted mean in ``[0.0, 1.0]``, or ``0.0`` if no mapping targets
    the pad.

    The divisor floors at :data:`_TOTAL_WEIGHT_FLOOR` (``0.001``) so the
    zero-mapping case returns exactly ``0.0`` without a branch — but a
    pad with at least one ``weight > 0.001`` mapping is unaffected.

    ``ProfileModel.__post_init__`` already enforces that every mapping's
    trait name exists in ``profile.traits``, so the dict lookup below is
    total (no missing-key branch reachable from a valid profile).
    """

    trait_values = {trait.name: trait.value for trait in profile.traits}
    total_weight = 0.0
    weighted_sum = 0.0
    for mapping in profile.pad_mappings:
        if mapping.pad_id != pad_id:
            continue
        weighted_sum += trait_values[mapping.trait] * mapping.weight
        total_weight += mapping.weight
    if total_weight == 0.0:
        return 0.0
    divisor = total_weight if total_weight > _TOTAL_WEIGHT_FLOOR else _TOTAL_WEIGHT_FLOOR
    return weighted_sum / divisor


def _clamp_cc(value: int) -> int:
    """Clamp ``value`` to the inclusive ``[0, 127]`` Rytm CC range."""

    if value < _CC_MIN:
        return _CC_MIN
    if value > _CC_MAX:
        return _CC_MAX
    return value


def mutate(
    snapshot: Snapshot,
    profile: ProfileModel,
    depth: float,
    seed: int,
    target_pad_ids: frozenset[int] = frozenset(),
) -> MutationCandidate:
    """Generate a ``MutationCandidate`` from a snapshot, profile, depth, seed.

    Pure function; deterministic given the four inputs (modulo
    ``candidate_id``, which is a fresh ULID excluded from conformance
    fixtures).

    Args:
        snapshot: The device's current parameter state.
        profile: The operator-curated taste model. The ``transition_curve``
            field is intentionally not consumed by this implementation —
            it is reserved for the Phase 2 progressive-mutation extension
            and the existing single-shot mutation behaves as the
            ``"linear"`` curve.
        depth: Mutation amplitude in the closed interval ``[0.10, 0.90]``
            (the UI's snap range). Lower = subtler delta; higher = larger
            delta. ``MutationCandidate.__post_init__`` enforces the
            bounds.
        seed: 32-bit unsigned integer used to seed ``xorshift32``. Same
            seed + same other inputs = identical output. ``0`` is mapped
            to a documented substitute (xorshift cannot escape zero).
        target_pad_ids: Explicit pad include-list. Empty preserves the
            historical all-pad behavior. Untargeted pads still consume their
            deterministic PRNG draws so a selected pad's proposed values do
            not change merely because the surrounding include-list changes.

    Returns:
        A fully-formed ``MutationCandidate`` with one ``PadDelta`` per
        pad in ``snapshot``. ``safety_status`` derives from ``depth``;
        ``estimated_midi_msgs`` is the total ``changed_keys`` count.
    """

    explicit_targets = MutationTargets(rytm_pad_targets=target_pad_ids).rytm_pad_targets
    state = _PRNG_SEED_FOR_ZERO if seed == 0 else (seed & 0xFFFFFFFF)
    # xorshift32 cannot escape state==0; the masking step above lets
    # callers pass any Python int and have it normalised to uint32.
    if state == 0:
        state = _PRNG_SEED_FOR_ZERO

    # Discard the first N draws to break the small-seed bias. See
    # _PRNG_WARMUP_STEPS docstring for the rationale.
    for _ in range(_PRNG_WARMUP_STEPS):
        _, state = xorshift32(state)

    pad_deltas: list[PadDelta] = []
    total_changed = 0

    # Iterate in pad_id order. The data model enforces ascending order at
    # construction; re-sorting defensively keeps the algorithm portable
    # if that contract ever loosens.
    for pad in sorted(snapshot.pads, key=lambda p: p.pad_id):
        bias = _pad_bias(profile, pad.pad_id)
        scale = depth * _CC_RANGE * (_BIAS_FLOOR + bias)

        proposed: dict[str, int] = {}
        changed: set[str] = set()

        for key in sorted(pad.params.keys()):
            value = pad.params[key]
            raw, state = xorshift32(state)
            # raw is a 32-bit unsigned int; r is in [0.0, 1.0).
            r = raw / _PRNG_NORMALIZER
            delta = (r - 0.5) * 2.0 * scale
            # round-half-away-from-zero is the spec'd rounding; Python's
            # built-in round() does banker's rounding, which is locale-
            # independent but disagrees with C's round() on half-values.
            # The spec docs the choice; C-port authors implement
            # round-half-away-from-zero explicitly.
            new_value = _clamp_cc(value + _round_half_away_from_zero(delta))
            proposed[key] = new_value
            if new_value != value:
                changed.add(key)

        if not explicit_targets or pad.pad_id in explicit_targets:
            pad_deltas.append(
                PadDelta(
                    pad_id=pad.pad_id,
                    proposed_params=proposed,
                    changed_keys=frozenset(changed),
                )
            )
            total_changed += len(changed)

    safety_status = _classify_safety(depth)

    return MutationCandidate(
        candidate_id=new_ulid(),
        source_snapshot_id=snapshot.snapshot_id,
        profile_id=profile.profile_id,
        depth=depth,
        seed=seed,
        pad_deltas=tuple(pad_deltas),
        safety_status=safety_status,
        estimated_midi_msgs=total_changed,
    )


def _round_half_away_from_zero(value: float) -> int:
    """Round ``value`` to the nearest integer, ties going away from zero.

    Python's built-in :func:`round` uses banker's rounding (round-half-to-
    even), which disagrees with C's ``round()`` on exact-half values
    (``round(0.5) == 0`` in Python, ``round(0.5) == 1`` in C). The C-port
    implementation uses C's behavior; this helper mirrors it so the two
    implementations stay byte-identical.
    """

    if value >= 0.0:
        return int(value + 0.5)
    return -int(-value + 0.5)


__all__ = ["mutate"]
