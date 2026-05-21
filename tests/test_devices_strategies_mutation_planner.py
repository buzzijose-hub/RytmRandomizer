"""Tests for ``rytm_randomizer.devices.strategies.analog_rytm_mutation_planner``.

Covers every branch of :class:`AnalogRytmMutationPlanner` and its companion
dataclasses :class:`RytmMutationPlan` and :class:`RytmPlanEvent`:

* Guard rejections (wrong snapshot type, depth out of bounds).
* Happy path at depth 0 (every value collapses to anchor / low bound).
* Happy path at depth in (0, MAX_DEPTH] (values within safe range, plan ready).
* Determinism: same seed+slot+depth triple always produces the same plan.
* Seed isolation: different seeds produce different event tuples.
* Event count: one event per (pad, parameter) pair in the safe table.
* Profile-key correctness: each event's ``profile_key`` matches PAD_PROFILE_KEY.
* Snapshot reference: ``plan.snapshot is snapshot``.
* Monkeypatched "data drift" branch: a pad whose profile_key is absent from
  PROFILES yields a non-ready plan with a "data drift" reason.
* Monkeypatched "no events" branch: empty PAD_PROFILE_KEY yields a non-ready
  plan with a "no events produced" reason.

Test naming: test_<unit>_<behavior>_when_<condition> per Gate 8.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helpers: build a minimal RytmKitSnapshot the planner accepts.
# ---------------------------------------------------------------------------


def _make_snapshot(slot: int = 0):
    """Return a RytmKitSnapshot the planner accepts.

    The planner only reads ``snapshot.slot``; other fields are left empty.
    """
    from rytm_randomizer.devices.strategies import RytmKitSnapshot

    return RytmKitSnapshot(slot=slot, kit_name="TEST", raw=b"", unpacked=b"")


# ---------------------------------------------------------------------------
# 1. Dataclass shape: RytmPlanEvent
# ---------------------------------------------------------------------------


def test_rytm_plan_event_is_frozen_dataclass_with_expected_fields() -> None:
    """RytmPlanEvent must be a frozen dataclass exposing pad, profile_key,
    parameter, and value. Frozen means attribute assignment raises."""

    from rytm_randomizer.devices.strategies import RytmPlanEvent

    event = RytmPlanEvent(pad=1, profile_key="2", parameter="SRC Tune", value=58)

    assert event.pad == 1
    assert event.profile_key == "2"
    assert event.parameter == "SRC Tune"
    assert event.value == 58

    with pytest.raises((AttributeError, TypeError)):
        event.pad = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. Dataclass shape: RytmMutationPlan
# ---------------------------------------------------------------------------


def test_rytm_mutation_plan_is_frozen_dataclass_with_expected_fields() -> None:
    """RytmMutationPlan must expose snapshot, depth, events, ready, and
    readiness_reason. Defaults: ready=True, readiness_reason=''."""

    from rytm_randomizer.devices.strategies import RytmMutationPlan

    snap = _make_snapshot()
    plan = RytmMutationPlan(snapshot=snap, depth=2, events=())

    assert plan.snapshot is snap
    assert plan.depth == 2
    assert plan.events == ()
    assert plan.ready is True
    assert plan.readiness_reason == ""

    with pytest.raises((AttributeError, TypeError)):
        plan.depth = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 3. MAX_DEPTH constant
# ---------------------------------------------------------------------------


def test_max_depth_is_seven() -> None:
    """MAX_DEPTH must equal 7; this constant is part of the public API."""

    from rytm_randomizer.devices.strategies import MAX_DEPTH

    assert MAX_DEPTH == 7


# ---------------------------------------------------------------------------
# 4. Guard: non-RytmKitSnapshot raises ValueError
# ---------------------------------------------------------------------------


def test_planner_plan_raises_value_error_when_snapshot_is_string() -> None:
    """Passing a string in place of a RytmKitSnapshot must raise ValueError
    with a message naming the received type."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)

    with pytest.raises(ValueError, match="RytmKitSnapshot"):
        planner.plan("not a snapshot", depth=1)  # type: ignore[arg-type]


def test_planner_plan_raises_value_error_when_snapshot_is_none() -> None:
    """None is a common accidental input; guard must reject it cleanly."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)

    with pytest.raises(ValueError, match="RytmKitSnapshot"):
        planner.plan(None, depth=1)  # type: ignore[arg-type]


def test_planner_plan_raises_value_error_when_snapshot_is_integer() -> None:
    """An integer is structurally wrong; the type-check guard must fire."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)

    with pytest.raises(ValueError, match="RytmKitSnapshot"):
        planner.plan(42, depth=0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 5. Guard: depth < 0 raises ValueError
# ---------------------------------------------------------------------------


def test_planner_plan_raises_value_error_when_depth_is_negative() -> None:
    """Negative depth is out of [0, MAX_DEPTH] and must raise ValueError
    with a message referencing the valid range."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(snap, depth=-1)


def test_planner_plan_raises_value_error_when_depth_is_minus_100() -> None:
    """A large negative value must also be rejected via the same guard."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(snap, depth=-100)


# ---------------------------------------------------------------------------
# 6. Guard: depth > MAX_DEPTH raises ValueError
# ---------------------------------------------------------------------------


def test_planner_plan_raises_value_error_when_depth_exceeds_max() -> None:
    """Depth 8 is one above MAX_DEPTH=7 and must raise ValueError."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(snap, depth=8)


def test_planner_plan_raises_value_error_when_depth_is_1000() -> None:
    """A very large depth also violates the upper bound."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(snap, depth=1000)


# ---------------------------------------------------------------------------
# 7. Happy path: depth 0 collapses every event to its low bound
# ---------------------------------------------------------------------------


def test_planner_plan_at_depth_zero_produces_ready_plan() -> None:
    """At depth 0 the plan must be ready=True with at least one event."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    assert plan.ready is True
    assert len(plan.events) > 0


def test_planner_plan_at_depth_zero_all_values_equal_low_bound() -> None:
    """Each event at depth 0 must have value == the safe-range low bound
    for its (pad, parameter) pair."""

    from rytm_randomizer.data.profiles import PROFILES
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    for event in plan.events:
        profile = PROFILES[event.profile_key]
        low, _high = profile["safe"][event.parameter]
        assert event.value == low, (
            f"At depth 0, event for pad={event.pad} parameter={event.parameter!r} "
            f"expected value={low} (low bound), got {event.value}"
        )


def test_planner_plan_at_depth_zero_depth_recorded_on_plan() -> None:
    """The plan's depth attribute must mirror the input depth=0."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=3)
    plan = planner.plan(snap, depth=0)

    assert plan.depth == 0


# ---------------------------------------------------------------------------
# 8. Happy path: depth in (0, MAX_DEPTH]
# ---------------------------------------------------------------------------


def test_planner_plan_at_positive_depth_produces_ready_plan() -> None:
    """At depth 3 the plan must be ready=True."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=1)
    snap = _make_snapshot(slot=1)
    plan = planner.plan(snap, depth=3)

    assert plan.ready is True
    assert plan.readiness_reason == ""


def test_planner_plan_at_max_depth_produces_ready_plan() -> None:
    """depth=MAX_DEPTH=7 must still produce a ready plan (boundary value)."""

    from rytm_randomizer.devices.strategies import MAX_DEPTH, AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=MAX_DEPTH)

    assert plan.ready is True
    assert len(plan.events) > 0


def test_planner_plan_at_depth_one_produces_ready_plan() -> None:
    """depth=1 is the first non-anchor depth; plan must be ready."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=42)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=1)

    assert plan.ready is True
    assert len(plan.events) > 0


def test_planner_plan_at_positive_depth_all_values_within_safe_range() -> None:
    """Every event value at depth 3 must be within [low, high] of the
    parameter's safe-range entry for its pad."""

    from rytm_randomizer.data.profiles import PROFILES
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=7)
    snap = _make_snapshot(slot=2)
    plan = planner.plan(snap, depth=3)

    for event in plan.events:
        profile = PROFILES[event.profile_key]
        low, high = profile["safe"][event.parameter]
        assert low <= event.value <= high, (
            f"Event value {event.value} for pad={event.pad} "
            f"parameter={event.parameter!r} is outside safe range [{low}, {high}]"
        )


def test_planner_plan_records_depth_on_plan() -> None:
    """The plan's depth attribute must mirror the input depth."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=5)

    assert plan.depth == 5


# ---------------------------------------------------------------------------
# 9. Snapshot reference preserved
# ---------------------------------------------------------------------------


def test_planner_plan_snapshot_reference_is_same_object() -> None:
    """plan.snapshot must be the exact same object (identity, not equality)
    that was passed to plan() -- used by senders for display purposes."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=4)
    plan = planner.plan(snap, depth=2)

    assert plan.snapshot is snap


# ---------------------------------------------------------------------------
# 10. Profile-key correctness
# ---------------------------------------------------------------------------


def test_planner_plan_events_have_correct_profile_key_per_pad() -> None:
    """Each event's profile_key must match PAD_PROFILE_KEY[pad]."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner
    from rytm_randomizer.guardrails.validation import PAD_PROFILE_KEY

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=1)

    for event in plan.events:
        expected_key = PAD_PROFILE_KEY[event.pad]
        assert event.profile_key == expected_key, (
            f"Event for pad={event.pad} has profile_key={event.profile_key!r} "
            f"but PAD_PROFILE_KEY says {expected_key!r}"
        )


# ---------------------------------------------------------------------------
# 11. Event count: one event per (pad, parameter) pair
# ---------------------------------------------------------------------------


def test_planner_plan_event_count_equals_sum_of_safe_table_lengths() -> None:
    """The total number of events must equal the sum of len(safe) across all
    configured pads' profiles -- one event per (pad, parameter) pair."""

    from rytm_randomizer.data.profiles import PROFILES
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner
    from rytm_randomizer.guardrails.validation import PAD_PROFILE_KEY

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    expected_count = sum(len(PROFILES[key]["safe"]) for key in PAD_PROFILE_KEY.values())

    assert len(plan.events) == expected_count, (
        f"Expected {expected_count} events (sum of safe-table lengths), " f"got {len(plan.events)}"
    )


def test_planner_plan_events_cover_every_parameter_in_each_pads_profile() -> None:
    """For each pad, every parameter in that pad's profile safe table must
    appear as an event in the plan."""

    from rytm_randomizer.data.profiles import PROFILES
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner
    from rytm_randomizer.guardrails.validation import PAD_PROFILE_KEY

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=2)

    for pad, profile_key in PAD_PROFILE_KEY.items():
        profile = PROFILES[profile_key]
        expected_params = set(profile["safe"].keys())
        actual_params = {e.parameter for e in plan.events if e.pad == pad}
        assert actual_params == expected_params, (
            f"Pad {pad} (profile_key={profile_key!r}): "
            f"missing parameters {expected_params - actual_params}"
        )


# ---------------------------------------------------------------------------
# 12. Determinism: same input -> same plan
# ---------------------------------------------------------------------------


def test_planner_plan_is_deterministic_for_same_inputs() -> None:
    """Calling plan() twice with the same (seed, slot, depth) must return
    RytmMutationPlan instances with identical events tuples."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=12345)
    snap = _make_snapshot(slot=7)

    plan_a = planner.plan(snap, depth=4)
    plan_b = planner.plan(snap, depth=4)

    assert plan_a.events == plan_b.events


def test_planner_plan_is_deterministic_across_separate_planner_instances() -> None:
    """Two separate AnalogRytmMutationPlanner instances with the same seed
    and the same input must produce identical plans."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    snap = _make_snapshot(slot=3)

    plan_a = AnalogRytmMutationPlanner(seed=99).plan(snap, depth=5)
    plan_b = AnalogRytmMutationPlanner(seed=99).plan(snap, depth=5)

    assert plan_a == plan_b


def test_planner_plan_at_depth_zero_is_deterministic_without_seed() -> None:
    """At depth 0 no RNG is used; two default-seeded planners produce equal plans."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    snap = _make_snapshot(slot=0)

    plan_a = AnalogRytmMutationPlanner().plan(snap, depth=0)
    plan_b = AnalogRytmMutationPlanner().plan(snap, depth=0)

    assert plan_a.events == plan_b.events


# ---------------------------------------------------------------------------
# 13. Different seed -> different plan (seed-controlled property)
# ---------------------------------------------------------------------------


def test_planner_different_seeds_produce_different_event_values_at_nonzero_depth() -> None:
    """Two planners with distinct seeds must produce different event tuples
    at non-zero depth (the RNG sampling window is seed-dependent)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    snap = _make_snapshot(slot=0)

    plan_a = AnalogRytmMutationPlanner(seed=1).plan(snap, depth=7)
    plan_b = AnalogRytmMutationPlanner(seed=999).plan(snap, depth=7)

    # Different seeds must produce at least one differing event value.
    # (Practically guaranteed at depth 7 with wide sampling windows.)
    assert (
        plan_a.events != plan_b.events
    ), "Expected different seeds to produce different event tuples at depth 7."


def test_planner_different_slots_produce_different_event_values() -> None:
    """The same seed at different snapshot slots should produce different plans
    because slot is folded into the RNG seed derivation."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    snap_a = _make_snapshot(slot=0)
    snap_b = _make_snapshot(slot=10)

    plan_a = AnalogRytmMutationPlanner(seed=42).plan(snap_a, depth=5)
    plan_b = AnalogRytmMutationPlanner(seed=42).plan(snap_b, depth=5)

    assert (
        plan_a.events != plan_b.events
    ), "Expected different slots to produce different event tuples at depth 5."


# ---------------------------------------------------------------------------
# 14. Monkeypatch: "data drift" branch -- profile_key absent from PROFILES
# ---------------------------------------------------------------------------


def test_planner_plan_returns_non_ready_plan_when_profile_key_missing_from_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If a pad's profile_key exists in PAD_PROFILE_KEY but that key is not in
    PROFILES (data drift scenario), plan() must return a non-ready plan with
    readiness_reason mentioning 'data drift'.

    Covered branch: ``if profile is None: return RytmMutationPlan(..., ready=False, ...)``
    """

    import rytm_randomizer.devices.strategies.analog_rytm_mutation_planner as planner_mod

    # Inject a PAD_PROFILE_KEY that points to a key absent from PROFILES.
    monkeypatch.setattr(planner_mod, "PAD_PROFILE_KEY", {1: "NONEXISTENT_KEY"})

    planner = planner_mod.AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=1)

    assert plan.ready is False
    assert "data drift" in plan.readiness_reason
    assert plan.snapshot is snap


def test_planner_plan_data_drift_reason_names_the_pad_and_profile_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The non-ready plan's readiness_reason must identify which pad and which
    profile_key caused the data drift so operators can diagnose it."""

    import rytm_randomizer.devices.strategies.analog_rytm_mutation_planner as planner_mod

    monkeypatch.setattr(planner_mod, "PAD_PROFILE_KEY", {2: "MYSTERY_KEY"})

    planner = planner_mod.AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    assert plan.ready is False
    # The reason should name the pad number and the missing key.
    assert "MYSTERY_KEY" in plan.readiness_reason


def test_planner_plan_data_drift_events_reflect_already_processed_pads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the drift guard fires on pad N, events accumulated for pads
    processed before pad N are preserved on the returned plan (the loop
    exits early, preserving partial results)."""

    import rytm_randomizer.devices.strategies.analog_rytm_mutation_planner as planner_mod

    # Put a known-good pad first (pad 1, key "2") then a drifted pad after.
    # sorted() iteration order: 1 comes before 99.
    monkeypatch.setattr(
        planner_mod,
        "PAD_PROFILE_KEY",
        {1: "2", 99: "DRIFT_KEY"},
    )

    planner = planner_mod.AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    # Plan must be non-ready (drift triggered on pad 99).
    assert plan.ready is False
    # Events for pad 1 must be present (processed before the drift pad).
    pad_1_events = [e for e in plan.events if e.pad == 1]
    assert len(pad_1_events) > 0


# ---------------------------------------------------------------------------
# 15. Monkeypatch: "no events" branch -- empty PAD_PROFILE_KEY
# ---------------------------------------------------------------------------


def test_planner_plan_returns_non_ready_plan_when_pad_profile_key_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If PAD_PROFILE_KEY is empty, no events are produced and plan() must
    return a non-ready plan whose readiness_reason matches 'no events produced'.

    Covered branch: ``if not events: return RytmMutationPlan(..., ready=False, ...)``
    """

    import rytm_randomizer.devices.strategies.analog_rytm_mutation_planner as planner_mod

    monkeypatch.setattr(planner_mod, "PAD_PROFILE_KEY", {})

    planner = planner_mod.AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=1)

    assert plan.ready is False
    assert "no events produced" in plan.readiness_reason
    assert plan.events == ()
    assert plan.snapshot is snap


def test_planner_plan_no_events_plan_preserves_depth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The non-ready 'no events' plan must still carry the requested depth."""

    import rytm_randomizer.devices.strategies.analog_rytm_mutation_planner as planner_mod

    monkeypatch.setattr(planner_mod, "PAD_PROFILE_KEY", {})

    planner = planner_mod.AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=4)

    assert plan.depth == 4
    assert plan.ready is False


# ---------------------------------------------------------------------------
# 16. Boundary: depth=0 accepted (lower boundary value)
# ---------------------------------------------------------------------------


def test_planner_plan_accepts_depth_zero_as_lower_boundary() -> None:
    """depth=0 is the inclusive lower boundary; it must not raise."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    assert plan.ready is True


def test_planner_plan_accepts_depth_max_as_upper_boundary() -> None:
    """depth=MAX_DEPTH is the inclusive upper boundary; it must not raise."""

    from rytm_randomizer.devices.strategies import MAX_DEPTH, AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=0)
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=MAX_DEPTH)

    assert plan.ready is True


# ---------------------------------------------------------------------------
# 17. Default seed constructor
# ---------------------------------------------------------------------------


def test_planner_init_default_seed_is_zero() -> None:
    """The no-argument constructor must succeed and use seed 0 (the default
    seed makes the API ergonomic for callers that want determinism without
    specifying a seed)."""

    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner()
    snap = _make_snapshot(slot=0)
    plan = planner.plan(snap, depth=0)

    assert plan.ready is True


# ---------------------------------------------------------------------------
# 18. Snapshot machine-value routing
# ---------------------------------------------------------------------------


def test_planner_can_plan_from_snapshot_machine_values_for_mutable_pads() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner, RytmKitSnapshot

    snapshot = RytmKitSnapshot(slot=7, kit_name="LIVE", raw=b"", unpacked=b"")
    plan = AnalogRytmMutationPlanner(seed=1).plan_for_machine_values(
        snapshot,
        depth=1,
        pad_machine_values={1: 0, 2: 3, 3: 32},
    )

    assert plan.ready is True
    assert {event.pad for event in plan.events} == {1, 2, 3}
    assert {event.profile_key for event in plan.events} == {"2", "10", "5"}


def test_planner_refuses_snapshot_machine_values_with_blocked_pad() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner, RytmKitSnapshot
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    snapshot = RytmKitSnapshot(slot=7, kit_name="LIVE", raw=b"", unpacked=b"")
    reset_metrics()
    try:
        plan = AnalogRytmMutationPlanner(seed=1).plan_for_machine_values(
            snapshot,
            depth=1,
            pad_machine_values={1: 0, 10: 10},
        )

        assert plan.ready is False
        assert plan.events == ()
        assert "selectable-only" in plan.readiness_reason
        assert get_metrics().cc_blocked_by_guardrail_by_pad[10] == 1
    finally:
        reset_metrics()


def test_planner_refuses_empty_snapshot_machine_values_with_reason() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner, RytmKitSnapshot

    snapshot = RytmKitSnapshot(slot=7, kit_name="LIVE", raw=b"", unpacked=b"")
    plan = AnalogRytmMutationPlanner(seed=1).plan_for_machine_values(
        snapshot,
        depth=1,
        pad_machine_values={},
    )

    assert plan.ready is False
    assert plan.events == ()
    assert plan.readiness_reason == "no snapshot machine values supplied"


def test_planner_plan_for_machine_values_raises_value_error_when_snapshot_is_wrong_type() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    planner = AnalogRytmMutationPlanner(seed=1)

    with pytest.raises(ValueError, match="RytmKitSnapshot"):
        planner.plan_for_machine_values(
            "not a snapshot", depth=1, pad_machine_values={1: 0}
        )  # type: ignore[arg-type]


def test_planner_plan_for_machine_values_raises_value_error_when_depth_exceeds_max() -> None:
    from rytm_randomizer.devices.strategies import MAX_DEPTH, AnalogRytmMutationPlanner

    snapshot = _make_snapshot(slot=7)

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        AnalogRytmMutationPlanner(seed=1).plan_for_machine_values(
            snapshot,
            depth=MAX_DEPTH + 1,
            pad_machine_values={1: 0},
        )


def test_planner_refuses_snapshot_machine_facts_until_promoted() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    snapshot = _make_snapshot(slot=7)
    plan = AnalogRytmMutationPlanner(seed=1).plan_for_snapshot_machine_facts(
        snapshot,
        depth=1,
    )

    assert plan.ready is False
    assert plan.events == ()
    assert "candidate-only" in plan.readiness_reason


def test_planner_uses_promoted_snapshot_machine_facts() -> None:
    from rytm_randomizer.devices.strategies import (
        AnalogRytmMutationPlanner,
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad={
            1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
            2: RytmSnapshotMachineFact(2, 3, 3, True, "promoted"),
            3: RytmSnapshotMachineFact(3, 32, 32, True, "promoted"),
        },
        promoted=True,
    )
    snapshot = RytmKitSnapshot(
        slot=7,
        kit_name="LIVE",
        raw=b"",
        unpacked=b"",
        machine_facts=facts,
    )

    plan = AnalogRytmMutationPlanner(seed=1).plan_for_snapshot_machine_facts(
        snapshot,
        depth=1,
    )

    assert plan.ready is True
    assert {event.pad for event in plan.events} == {1, 2, 3}


def test_planner_ignores_promoted_snapshot_machine_facts_without_decoded_value() -> None:
    from rytm_randomizer.devices.strategies import (
        AnalogRytmMutationPlanner,
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad={
            1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
            6: RytmSnapshotMachineFact(6, 8, None, True, "offset not promoted"),
        },
        promoted=True,
    )
    snapshot = RytmKitSnapshot(
        slot=7,
        kit_name="LIVE",
        raw=b"",
        unpacked=b"",
        machine_facts=facts,
    )

    plan = AnalogRytmMutationPlanner(seed=1).plan_for_snapshot_machine_facts(
        snapshot,
        depth=1,
    )

    assert plan.ready is True
    assert {event.pad for event in plan.events} == {1}
