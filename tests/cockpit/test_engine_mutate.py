"""Tests for ``rytm_randomizer.cockpit.engine.mutate``.

Covers:

* **Determinism** — same inputs always produce the same `to_dict()` output
  (modulo `candidate_id`, which is a fresh ULID by spec).
* **Variance** — different seeds produce different outputs.
* **Depth scaling** — larger depth produces larger deltas on average.
* **Bias effect** — a pad with a profile mapping gets larger scale than a
  pad without one.
* **Range clamping** — output stays in each manual-backed parameter domain,
  with ``[0, 127]`` retained for unmapped fields.
* **Safety status thresholds** — exclusive lower bound, inclusive upper.
* **`changed_keys` correctness** — only keys whose value actually changed
  appear; the proposed_params dict has every input key.
* **`estimated_midi_msgs` accuracy** — equals the sum of `changed_keys`.
* **Seed normalisation** — `seed=0` is mapped to a valid PRNG state.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.engine.mutate import mutate

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _snapshot(
    *,
    snapshot_id: str = "SNAP1",
    pads: tuple[PadState, ...] | None = None,
) -> Snapshot:
    if pads is None:
        pads = (
            PadState(pad_id=1, machine="bd_classic", params={"tun": 60, "dec": 40}),
            PadState(pad_id=2, machine="sd_classic", params={"tun": 50, "dec": 80}),
        )
    return Snapshot(
        snapshot_id=snapshot_id,
        device="rytm_mk2",
        captured_at=datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc),
        pads=pads,
        scene_slot=None,
        bpm=128.0,
    )


def _profile(
    *,
    profile_id: str = "PROF1",
    traits: tuple[StyleTrait, ...] | None = None,
    pad_mappings: tuple[TraitPadWeight, ...] | None = None,
) -> ProfileModel:
    if traits is None:
        traits = (
            StyleTrait(name="low_end", value=0.8),
            StyleTrait(name="texture", value=0.3),
        )
    if pad_mappings is None:
        pad_mappings = (
            TraitPadWeight(trait="low_end", pad_id=1, weight=0.9),
            TraitPadWeight(trait="texture", pad_id=2, weight=0.5),
        )
    return ProfileModel(
        profile_id=profile_id,
        name="Test Profile",
        kind="user",
        model_version="1.0",
        traits=traits,
        pad_mappings=pad_mappings,
        transition_curve="linear",
        source_summary="unit test fixture",
    )


def _without_candidate_id(d: dict[str, object]) -> dict[str, object]:
    """Return a copy of a MutationCandidate.to_dict() with the non-deterministic
    candidate_id field stripped, for byte-equality comparisons."""

    return {k: v for k, v in d.items() if k != "candidate_id"}


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_mutate_is_deterministic_for_same_inputs() -> None:
    """Same snapshot + profile + depth + seed → byte-equal pad_deltas + meta."""

    snap = _snapshot()
    prof = _profile()
    a = mutate(snap, prof, depth=0.5, seed=42)
    b = mutate(snap, prof, depth=0.5, seed=42)
    assert _without_candidate_id(a.to_dict()) == _without_candidate_id(b.to_dict())


def test_mutate_candidate_id_differs_per_call() -> None:
    """candidate_id is a fresh ULID per call — deterministic in everything else."""

    snap = _snapshot()
    prof = _profile()
    a = mutate(snap, prof, depth=0.5, seed=42)
    b = mutate(snap, prof, depth=0.5, seed=42)
    assert a.candidate_id != b.candidate_id


def test_mutate_copies_snapshot_id_and_profile_id() -> None:
    """source_snapshot_id and profile_id are echoed from the inputs verbatim."""

    snap = _snapshot(snapshot_id="CUSTOM_SNAP")
    prof = _profile(profile_id="CUSTOM_PROF")
    c = mutate(snap, prof, depth=0.5, seed=1)
    assert c.source_snapshot_id == "CUSTOM_SNAP"
    assert c.profile_id == "CUSTOM_PROF"
    assert c.depth == 0.5
    assert c.seed == 1


def test_mutate_explicit_targets_return_only_selected_pad_deltas() -> None:
    snap = _snapshot()
    prof = _profile()

    all_scope = mutate(snap, prof, depth=0.5, seed=42)
    targeted = mutate(
        snap,
        prof,
        depth=0.5,
        seed=42,
        target_pad_ids=frozenset({2}),
    )

    assert {delta.pad_id for delta in targeted.pad_deltas} == {2}
    assert targeted.pad_deltas[0] == all_scope.pad_deltas[1]
    assert targeted.estimated_midi_msgs == len(targeted.pad_deltas[0].changed_keys)


def test_mutate_applies_locks_after_explicit_or_default_targets() -> None:
    snap = _snapshot()
    prof = _profile()

    all_minus_lock = mutate(
        snap,
        prof,
        depth=0.5,
        seed=42,
        locked_pad_ids=frozenset({1}),
    )
    selected_minus_lock = mutate(
        snap,
        prof,
        depth=0.5,
        seed=42,
        target_pad_ids=frozenset({1, 2}),
        locked_pad_ids=frozenset({2}),
    )
    all_locked = mutate(
        snap,
        prof,
        depth=0.5,
        seed=42,
        locked_pad_ids=frozenset({1, 2}),
    )

    assert {delta.pad_id for delta in all_minus_lock.pad_deltas} == {2}
    assert {delta.pad_id for delta in selected_minus_lock.pad_deltas} == {1}
    assert all_locked.pad_deltas == ()
    assert all_locked.estimated_midi_msgs == 0


# ---------------------------------------------------------------------------
# Output pad_delta ordering — pins the engine's "defensive sort" invariant
# (mutate.py line 196-199). CODE_REVIEW.md P6.
# ---------------------------------------------------------------------------


def test_mutate_emits_pad_deltas_sorted_by_pad_id() -> None:
    """``mutate`` MUST emit ``pad_deltas`` sorted ascending by ``pad_id``.

    The engine iterates ``sorted(snapshot.pads, key=lambda p: p.pad_id)``
    so downstream consumers (the WS event serializer, the C port, the
    parity capture) can rely on a stable, pad-id-ordered output regardless
    of any future relaxation in the :class:`Snapshot` constructor's
    ascending-order invariant. Today the constructor enforces it; if a
    refactor ever loosens that contract the defensive sort still holds
    here. This test pins that contract on the output side.

    Three pads with non-adjacent pad_ids (1, 3, 7) exercise more than two
    elements so a "preserved insertion order" implementation would fail
    on the same fixture if the constructor were changed.
    """

    pads = (
        PadState(pad_id=1, machine="bd", params={"k": 64}),
        PadState(pad_id=3, machine="sd", params={"k": 64}),
        PadState(pad_id=7, machine="ch", params={"k": 64}),
    )
    snap = _snapshot(pads=pads)
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    pad_ids = [pd.pad_id for pd in c.pad_deltas]
    assert pad_ids == sorted(pad_ids), f"pad_deltas not sorted by pad_id: {pad_ids}"
    assert pad_ids == [1, 3, 7]


# ---------------------------------------------------------------------------
# Variance — different seeds must produce different outputs
# ---------------------------------------------------------------------------


def test_mutate_different_seeds_produce_different_outputs() -> None:
    """Sampling 5 distinct seeds, the proposed_params dicts must not all be equal."""

    snap = _snapshot()
    prof = _profile()
    outputs = [
        tuple(pd.proposed_params for pd in mutate(snap, prof, depth=0.5, seed=s).pad_deltas)
        for s in (1, 2, 3, 4, 5)
    ]
    # At least two of the five must differ — in practice all five do,
    # but we only need to catch a "PRNG ignored the seed" regression.
    assert len({tuple((k, v) for d in t for k, v in sorted(d.items())) for t in outputs}) > 1


# ---------------------------------------------------------------------------
# Depth scaling
# ---------------------------------------------------------------------------


def test_mutate_depth_scales_delta_magnitude() -> None:
    """At higher depth the average change magnitude grows.

    Run mutate with the same snapshot/profile/seed at depth=0.1 and
    depth=0.9. The mean absolute delta at depth=0.9 must exceed the mean
    at depth=0.1."""

    snap = _snapshot()
    prof = _profile()
    low = mutate(snap, prof, depth=0.1, seed=7)
    high = mutate(snap, prof, depth=0.9, seed=7)

    def total_abs_change(c) -> int:  # type: ignore[no-untyped-def]
        return sum(
            abs(pd.proposed_params[k] - p.params[k])
            for pd, p in zip(c.pad_deltas, sorted(snap.pads, key=lambda x: x.pad_id))
            for k in pd.proposed_params
        )

    assert total_abs_change(high) > total_abs_change(low)


# ---------------------------------------------------------------------------
# Bias effect — a profile mapping on a pad should give it a larger scale
# ---------------------------------------------------------------------------


def test_mutate_bias_amplifies_scale_versus_unmapped_pad() -> None:
    """Two pads with identical params; one is mapped (max bias), one is not.

    Across many seeds, the mapped pad should accumulate strictly more
    absolute change than the unmapped pad."""

    # Two pads with identical starting params at the same value (so the
    # only systemic asymmetry is the bias mapping).
    pads = (
        PadState(pad_id=1, machine="bd", params={"a": 64, "b": 64, "c": 64, "d": 64}),
        PadState(pad_id=2, machine="bd", params={"a": 64, "b": 64, "c": 64, "d": 64}),
    )
    snap = _snapshot(pads=pads)
    # Profile: trait at max, mapped to pad 1 only.
    prof = _profile(
        traits=(StyleTrait(name="bias_max", value=1.0),),
        pad_mappings=(TraitPadWeight(trait="bias_max", pad_id=1, weight=1.0),),
    )

    pad1_total = 0
    pad2_total = 0
    for seed in range(1, 11):
        c = mutate(snap, prof, depth=0.5, seed=seed)
        pad1_total += sum(
            abs(c.pad_deltas[0].proposed_params[k] - 64) for k in c.pad_deltas[0].proposed_params
        )
        pad2_total += sum(
            abs(c.pad_deltas[1].proposed_params[k] - 64) for k in c.pad_deltas[1].proposed_params
        )
    # Bias = 1.0 → scale multiplier = 1.5; bias = 0.0 → multiplier = 0.5.
    # Ratio 3x; with 10 seeds the law of averages is comfortably above 1.
    assert pad1_total > pad2_total


def test_mutate_unmapped_pad_still_mutates() -> None:
    """A pad with no profile mapping still gets a nonzero scale (floor = 0.5)."""

    snap = _snapshot(pads=(PadState(pad_id=3, machine="bd", params={"k1": 64, "k2": 64}),))
    prof = _profile(
        traits=(StyleTrait(name="t", value=0.5),),
        pad_mappings=(TraitPadWeight(trait="t", pad_id=1, weight=0.5),),
        # Mapping references pad 1, but the snapshot only contains pad 3 —
        # so pad 3 has no matching mapping. Verify it still mutates.
    )
    c = mutate(snap, prof, depth=0.9, seed=11)
    assert len(c.pad_deltas) == 1
    pd = c.pad_deltas[0]
    # At depth 0.9 + bias 0.0 + 4 draws, at least one key changes.
    assert len(pd.changed_keys) >= 1


# ---------------------------------------------------------------------------
# Range clamping
# ---------------------------------------------------------------------------


def test_mutate_clamps_to_cc_range() -> None:
    """Even at the upper depth bound, every proposed value is in [0, 127]."""

    # Start at extremes so any positive/negative delta would push out of range.
    pads = (
        PadState(pad_id=1, machine="bd", params={"low": 0, "high": 127, "mid": 64}),
        PadState(pad_id=2, machine="sd", params={"low": 0, "high": 127, "mid": 64}),
    )
    snap = _snapshot(pads=pads)
    prof = _profile()
    for seed in range(1, 21):
        c = mutate(snap, prof, depth=0.9, seed=seed)
        for pd in c.pad_deltas:
            for k, v in pd.proposed_params.items():
                assert 0 <= v <= 127, f"seed={seed} pad={pd.pad_id} key={k} value={v} out of range"


def test_mutate_clamps_manual_backed_selectors_to_semantic_domains() -> None:
    """Known selectors never acquire an invalid raw MIDI-byte value."""

    pads = (
        PadState(
            pad_id=1,
            machine="bd_classic",
            params={
                "filter_type": 3,
                "lfo_mult": 12,
                "lfo_trig": 2,
                "lfo_wave": 3,
                "wav": 1,
            },
        ),
        PadState(
            pad_id=2,
            machine="sy_raw",
            params={"wave": 3, "wave_2": 1},
        ),
    )
    snap = _snapshot(pads=pads)
    prof = _profile()

    for seed in range(1, 30):
        candidate = mutate(snap, prof, depth=0.9, seed=seed)
        pad_1 = candidate.pad_deltas[0].proposed_params
        pad_2 = candidate.pad_deltas[1].proposed_params
        assert 0 <= pad_1["filter_type"] <= 6
        assert 0 <= pad_1["lfo_mult"] <= 23
        assert 0 <= pad_1["lfo_trig"] <= 4
        assert 0 <= pad_1["lfo_wave"] <= 6
        assert 0 <= pad_1["wav"] <= 2
        assert 0 <= pad_2["wave"] <= 6
        assert 0 <= pad_2["wave_2"] <= 1


def test_mutate_clamps_at_lower_bound() -> None:
    """A pad already at 0 may end up at 0 (clamp) or above; never below 0."""

    pads = (PadState(pad_id=1, machine="bd", params={"k": 0}),)
    snap = _snapshot(pads=pads)
    prof = _profile()
    # Many seeds, depth=0.9 — a non-trivial fraction of seeds must produce
    # a downward draw that gets clamped to 0.
    saw_clamp_to_zero = False
    for seed in range(1, 30):
        c = mutate(snap, prof, depth=0.9, seed=seed)
        v = c.pad_deltas[0].proposed_params["k"]
        assert v >= 0
        if v == 0:
            saw_clamp_to_zero = True
    assert saw_clamp_to_zero, "expected at least one seed to clamp to 0"


def test_mutate_clamps_at_upper_bound() -> None:
    """A pad already at 127 may end up at 127 (clamp) or below; never above."""

    pads = (PadState(pad_id=1, machine="bd", params={"k": 127}),)
    snap = _snapshot(pads=pads)
    prof = _profile()
    saw_clamp_to_max = False
    for seed in range(1, 30):
        c = mutate(snap, prof, depth=0.9, seed=seed)
        v = c.pad_deltas[0].proposed_params["k"]
        assert v <= 127
        if v == 127:
            saw_clamp_to_max = True
    assert saw_clamp_to_max, "expected at least one seed to clamp to 127"


# ---------------------------------------------------------------------------
# Safety status thresholds
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "depth, expected",
    [
        (0.10, "safe"),
        (0.20, "safe"),
        (0.29, "safe"),
        (0.30, "armed"),  # inclusive lower bound of armed
        (0.45, "armed"),
        (0.64, "armed"),
        (0.65, "high_risk"),  # inclusive lower bound of high_risk
        (0.80, "high_risk"),
        (0.90, "high_risk"),
    ],
)
def test_safety_status_thresholds(depth: float, expected: str) -> None:
    snap = _snapshot()
    prof = _profile()
    c = mutate(snap, prof, depth=depth, seed=1)
    assert c.safety_status == expected


# ---------------------------------------------------------------------------
# changed_keys + proposed_params shape
# ---------------------------------------------------------------------------


def test_proposed_params_includes_every_input_key() -> None:
    """Every key in pad.params appears in proposed_params (changed or not)."""

    snap = _snapshot()
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    for pd in c.pad_deltas:
        original_pad = next(p for p in snap.pads if p.pad_id == pd.pad_id)
        assert set(pd.proposed_params.keys()) == set(original_pad.params.keys())


def test_changed_keys_only_includes_actually_changed_keys() -> None:
    """A key is in changed_keys iff proposed_params[k] != snapshot.params[k]."""

    snap = _snapshot()
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    for pd in c.pad_deltas:
        original_pad = next(p for p in snap.pads if p.pad_id == pd.pad_id)
        for k, v in pd.proposed_params.items():
            if v != original_pad.params[k]:
                assert k in pd.changed_keys
            else:
                assert k not in pd.changed_keys


def test_changed_keys_can_be_empty_when_nothing_moves() -> None:
    """At extremely low depth + an extremely tight starting value, some draws
    will round to a delta of 0 and produce no change. We force that case by
    setting depth low and a single pad with one key; across many seeds, at
    least one must produce an empty changed_keys."""

    pads = (PadState(pad_id=1, machine="bd", params={"k": 64}),)
    snap = _snapshot(pads=pads)
    prof = _profile()
    saw_no_change = False
    for seed in range(1, 200):
        c = mutate(snap, prof, depth=0.10, seed=seed)
        if not c.pad_deltas[0].changed_keys:
            saw_no_change = True
            break
    assert saw_no_change


# ---------------------------------------------------------------------------
# estimated_midi_msgs
# ---------------------------------------------------------------------------


def test_estimated_midi_msgs_equals_total_changed_keys() -> None:
    snap = _snapshot()
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    assert c.estimated_midi_msgs == sum(len(pd.changed_keys) for pd in c.pad_deltas)


def test_estimated_midi_msgs_is_zero_when_nothing_changes() -> None:
    """A degenerate snapshot with zero pads must produce zero candidate msgs."""

    snap = Snapshot(
        snapshot_id="EMPTY",
        device="rytm_mk2",
        captured_at=datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc),
        pads=(),
        scene_slot=None,
        bpm=None,
    )
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    assert c.pad_deltas == ()
    assert c.estimated_midi_msgs == 0


# ---------------------------------------------------------------------------
# Seed normalisation
# ---------------------------------------------------------------------------


def test_mutate_handles_seed_zero() -> None:
    """seed=0 cannot drive xorshift32 directly; engine maps to a documented
    substitute and must NOT raise."""

    snap = _snapshot()
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=0)
    # The candidate's `seed` field echoes the raw input — the engine's
    # internal normalisation is invisible.
    assert c.seed == 0


def test_mutate_seed_zero_substitute_is_stable() -> None:
    """Two calls with seed=0 produce equal pad_deltas (the substitute is fixed)."""

    snap = _snapshot()
    prof = _profile()
    a = mutate(snap, prof, depth=0.5, seed=0)
    b = mutate(snap, prof, depth=0.5, seed=0)
    assert _without_candidate_id(a.to_dict()) == _without_candidate_id(b.to_dict())


def test_mutate_seed_multiple_of_2_to_32_maps_to_substitute() -> None:
    """Passing 2**32 (mask to 0) must also normalise without raising."""

    snap = _snapshot()
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=1 << 32)
    # echoes raw seed
    assert c.seed == 1 << 32
    # produces same pad_deltas as seed=0 (both normalise to the substitute);
    # the `seed` echo field differs by definition since it stores the raw input.
    z = mutate(snap, prof, depth=0.5, seed=0)
    assert [pd.to_dict() for pd in c.pad_deltas] == [pd.to_dict() for pd in z.pad_deltas]
    assert c.safety_status == z.safety_status
    assert c.estimated_midi_msgs == z.estimated_midi_msgs


# ---------------------------------------------------------------------------
# Output structure / shape
# ---------------------------------------------------------------------------


def test_mutate_emits_pad_deltas_in_pad_id_order() -> None:
    """Even if the caller hands in pads in some order, output is ascending."""

    # Build a snapshot whose pads happen to be in sorted order at construction
    # (the data model requires it), but with non-contiguous pad_ids.
    pads = (
        PadState(pad_id=1, machine="bd", params={"k": 50}),
        PadState(pad_id=4, machine="sd", params={"k": 70}),
        PadState(pad_id=9, machine="hh", params={"k": 30}),
    )
    snap = _snapshot(pads=pads)
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    assert [pd.pad_id for pd in c.pad_deltas] == [1, 4, 9]


def test_mutate_iteration_order_independence_for_dict_input() -> None:
    """Changing dict iteration order at the data-model level must not change
    the engine output. We sort keys explicitly so this should hold.

    Builds two PadStates whose params dict literals declare keys in
    different orders (Python preserves insertion order — the engine must
    NOT)."""

    pads_a = (PadState(pad_id=1, machine="bd", params={"a": 30, "b": 40, "c": 50}),)
    pads_b = (PadState(pad_id=1, machine="bd", params={"c": 50, "a": 30, "b": 40}),)
    snap_a = _snapshot(pads=pads_a)
    snap_b = _snapshot(pads=pads_b)
    prof = _profile()
    a = mutate(snap_a, prof, depth=0.5, seed=42)
    b = mutate(snap_b, prof, depth=0.5, seed=42)
    assert a.pad_deltas[0].proposed_params == b.pad_deltas[0].proposed_params
    assert a.pad_deltas[0].changed_keys == b.pad_deltas[0].changed_keys


# ---------------------------------------------------------------------------
# Bias edge cases
# ---------------------------------------------------------------------------


def test_bias_is_zero_for_pad_with_zero_total_weight() -> None:
    """A pad whose only mapping has weight=0 still yields bias=0 (avoids div by zero)."""

    pads = (PadState(pad_id=1, machine="bd", params={"k": 64}),)
    snap = _snapshot(pads=pads)
    prof = _profile(
        traits=(StyleTrait(name="t", value=1.0),),
        pad_mappings=(TraitPadWeight(trait="t", pad_id=1, weight=0.0),),
    )
    # Should not raise (no divide by zero); output is well-defined.
    c = mutate(snap, prof, depth=0.5, seed=1)
    assert len(c.pad_deltas) == 1


def test_bias_small_weight_uses_floor_divisor() -> None:
    """A weight smaller than the floor (0.001) hits the divisor floor branch."""

    pads = (PadState(pad_id=1, machine="bd", params={"k": 64}),)
    snap = _snapshot(pads=pads)
    prof = _profile(
        traits=(StyleTrait(name="t", value=1.0),),
        pad_mappings=(TraitPadWeight(trait="t", pad_id=1, weight=0.0005),),
    )
    # Hits the `total_weight <= 0.001` branch where the floor takes over.
    c = mutate(snap, prof, depth=0.5, seed=1)
    assert len(c.pad_deltas) == 1


def test_mutate_works_with_pad_with_no_params() -> None:
    """An empty params dict is structurally valid; output is a PadDelta with
    no proposed_params and no changed_keys."""

    pads = (PadState(pad_id=1, machine="bd", params={}),)
    snap = _snapshot(pads=pads)
    prof = _profile()
    c = mutate(snap, prof, depth=0.5, seed=42)
    assert len(c.pad_deltas) == 1
    assert dict(c.pad_deltas[0].proposed_params) == {}
    assert c.pad_deltas[0].changed_keys == frozenset()
    assert c.estimated_midi_msgs == 0
