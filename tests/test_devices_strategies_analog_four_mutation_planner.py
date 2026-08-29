"""Tests for Analog Four mutation planner Strategy."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.snapshot import MutationScope

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=1,
        kit_name="A4",
        raw=b"\x00\x20\x3c\x07" + bytes(32),
        offsets_promoted=offsets_promoted,
    )


def _planner(*, seed: int = 0, track_count: int = 4):
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    return AnalogFourMutationPlanner(track_count=track_count, seed=seed)


def test_plan_returns_not_ready_when_offsets_are_candidate_only() -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    plan = _planner(seed=0).plan(_snapshot(offsets_promoted=False), depth=1)

    assert plan.ready is False
    assert plan.events == ()
    assert "offsets are candidate" in plan.readiness_reason
    assert get_metrics().errors_by_kind["a4_mutation_plan_semantic_offsets_unpromoted"] == 1
    reset_metrics()


def test_plan_returns_ready_events_when_offsets_are_promoted() -> None:
    plan = _planner(seed=0).plan(_snapshot(offsets_promoted=True), depth=1)

    assert plan.ready is True
    assert plan.readiness_reason == ""
    assert len(plan.events) == 4
    assert {event.track for event in plan.events} == {1, 2, 3, 4}


def test_plan_rejects_wrong_snapshot_type() -> None:
    with pytest.raises(ValueError, match="AnalogFourKitSnapshot"):
        _planner().plan("not a snapshot", depth=1)  # type: ignore[arg-type]


def test_plan_rejects_depth_outside_bounds() -> None:
    planner = _planner()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(_snapshot(offsets_promoted=True), depth=-1)
    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(_snapshot(offsets_promoted=True), depth=8)


def test_plan_is_deterministic_for_same_seed_slot_and_depth() -> None:
    planner = _planner(seed=99)
    snap = _snapshot(offsets_promoted=True)

    assert planner.plan(snap, depth=3) == planner.plan(snap, depth=3)


def test_plan_intersects_explicit_track_targets_with_locks_when_promoted() -> None:
    planner = _planner(seed=99)
    plan = planner.plan(
        _snapshot(offsets_promoted=True),
        depth=3,
        scope=MutationScope(
            target_ids=frozenset({1, 3, 4}),
            locked_ids=frozenset({3}),
        ),
    )

    assert plan.ready is True
    assert {event.track for event in plan.events} == {1, 4}
    assert plan.scope.target_ids == frozenset({1, 3, 4})
    assert plan.scope.locked_ids == frozenset({3})


def test_captured_candidate_only_a4_snapshot_stays_fail_closed_with_targets() -> None:
    plan = _planner().plan(
        _snapshot(offsets_promoted=False),
        depth=3,
        scope=MutationScope(target_ids=frozenset({2})),
    )

    assert plan.ready is False
    assert plan.events == ()
    assert "byte offsets" in plan.readiness_reason
    assert "value encodings" in plan.readiness_reason


def test_plan_blocks_when_targets_are_entirely_locked() -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    plan = _planner().plan(
        _snapshot(offsets_promoted=True),
        depth=3,
        scope=MutationScope(
            target_ids=frozenset({2}),
            locked_ids=frozenset({2}),
        ),
    )

    assert plan.ready is False
    assert plan.events == ()
    assert plan.readiness_reason == "no sendable A4 tracks after targets and locks"
    assert get_metrics().errors_by_kind["a4_mutation_plan_no_sendable_tracks"] == 1
    reset_metrics()


def test_plan_rejects_a_missing_promoted_pwm_control(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer.devices.strategies import analog_four_mutation_planner as planner_mod

    pwm_depth = planner_mod.ANALOG_FOUR_SYNTH_TRACK_CC["OSC1 PWM Depth"]
    monkeypatch.setattr(
        planner_mod,
        "ANALOG_FOUR_SYNTH_TRACK_CC",
        {"OSC1 PWM Depth": replace(pwm_depth, cc_msb=None)},
    )

    with pytest.raises(ValueError, match="promoted CC MSB"):
        planner_mod.AnalogFourMutationPlanner(track_count=4).plan(
            _snapshot(offsets_promoted=True),
            depth=1,
        )


def test_plan_uses_injected_track_count() -> None:
    plan = _planner(track_count=2).plan(_snapshot(offsets_promoted=True), depth=1)

    assert {event.track for event in plan.events} == {1, 2}


@pytest.mark.parametrize("track_count", [True, 0, -1, 1.5, "4"])
def test_planner_rejects_invalid_track_count(track_count: object) -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    with pytest.raises(ValueError, match="track_count must be a positive integer"):
        AnalogFourMutationPlanner(track_count=track_count)  # type: ignore[arg-type]
