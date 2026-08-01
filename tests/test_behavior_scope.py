"""Branch-complete tests for the passive scoped-randomization engine."""

from __future__ import annotations

import pytest

from rytm_randomizer.behavior import scope

pytestmark = pytest.mark.fast


def _sharp_scope(track: int = 1) -> scope.TrackScope:
    return scope.build_track_scope(track, "1")


def test_build_track_scope_from_profile_registry() -> None:
    ts = _sharp_scope()
    assert ts.track == 1
    assert ts.profile_name == "My BD Sharp"
    assert "SRC Tune" in ts.anchor
    assert ts.safe["SRC Tune"] == (56, 62)
    assert "src" in ts.groups


def test_build_track_scope_unknown_key_raises() -> None:
    with pytest.raises(KeyError):
        scope.build_track_scope(1, "nope")


def test_scope_mask_track_range_validation() -> None:
    scope.ScopeMask(tracks=frozenset({1, 12}), groups=frozenset())
    with pytest.raises(ValueError, match="out of range"):
        scope.ScopeMask(tracks=frozenset({0}), groups=frozenset())
    with pytest.raises(ValueError, match="out of range"):
        scope.ScopeMask(tracks=frozenset({13}), groups=frozenset())


def test_scope_mask_membership_helpers() -> None:
    mask = scope.ScopeMask(tracks=frozenset({1, 3}), groups=frozenset({"src"}))
    assert mask.includes_track(1) is True
    assert mask.includes_track(2) is False
    assert mask.includes_group("src") is True
    assert mask.includes_group("filter") is False


def test_param_delta_signed_delta() -> None:
    up = scope.ParamDelta(name="x", group="g", anchor=10, planned=15)
    down = scope.ParamDelta(name="y", group="g", anchor=10, planned=4)
    assert up.delta == 5
    assert down.delta == -6


def test_plan_scope_ready_moves_continuous_params() -> None:
    ts = _sharp_scope()
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"src", "filter"}))
    plan = scope.plan_scope([ts], mask, 0.5)
    assert plan.ready is True
    assert plan.readiness_reason == "ready"
    assert plan.depth == 0.5
    assert plan.total_changed > 0
    assert len(plan.track_plans) == 1
    (track_plan,) = plan.track_plans
    assert track_plan.track == 1
    assert track_plan.changed_count == track_plan.changed_count  # property callable
    # Deterministic: same inputs -> identical plan.
    assert scope.plan_scope([ts], mask, 0.5) == plan


def test_plan_scope_only_selected_tracks_included() -> None:
    tracks = [scope.build_track_scope(1, "1"), scope.build_track_scope(2, "6")]
    mask = scope.ScopeMask(tracks=frozenset({2}), groups=frozenset({"src"}))
    plan = scope.plan_scope(tracks, mask, 0.5)
    assert [tp.track for tp in plan.track_plans] == [2]


def test_plan_scope_no_tracks_not_ready() -> None:
    ts = _sharp_scope()
    mask = scope.ScopeMask(tracks=frozenset(), groups=frozenset({"src"}))
    plan = scope.plan_scope([ts], mask, 0.5)
    assert plan.ready is False
    assert plan.readiness_reason == "no tracks selected"


def test_plan_scope_no_groups_not_ready() -> None:
    ts = _sharp_scope()
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset())
    plan = scope.plan_scope([ts], mask, 0.5)
    assert plan.ready is False
    assert plan.readiness_reason == "no parameter groups selected"


def test_plan_scope_zero_depth_not_ready() -> None:
    ts = _sharp_scope()
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"src"}))
    plan = scope.plan_scope([ts], mask, 0.0)
    assert plan.ready is False
    assert plan.readiness_reason == "depth is 0.0 (no movement)"
    # Zero depth still lists the track but moves nothing.
    assert plan.total_changed == 0


def test_plan_scope_group_with_no_reachable_params_not_ready() -> None:
    # A track whose only in-scope group holds a single discrete selector: no
    # continuous param can move -> not ready ("no reachable").
    ts = scope.TrackScope(
        track=1,
        profile_name="Synthetic",
        anchor={"SRC Waveform": 1},
        safe={"SRC Waveform": (0, 3)},
        groups={"osc": ("SRC Waveform",)},
    )
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"osc"}))
    plan = scope.plan_scope([ts], mask, 0.5)
    assert plan.ready is False
    assert plan.readiness_reason == "mask selects no reachable continuous parameters"
    assert plan.total_changed == 0


def test_plan_track_scope_skips_missing_bound_and_dedupes() -> None:
    ts = scope.TrackScope(
        track=1,
        profile_name="Synthetic",
        anchor={"A": 10, "B": 50, "SRC Waveform": 1},
        # "A" has no safe bound -> skipped; "B" reachable; waveform discrete.
        safe={"B": (0, 100), "SRC Waveform": (0, 3)},
        # "B" appears in two groups -> planned once (dedupe).
        groups={"g1": ("A", "B", "SRC Waveform"), "g2": ("B",)},
    )
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"g1", "g2"}))
    plan = scope.plan_track_scope(ts, mask, 1.0)
    names = [d.name for d in plan.deltas]
    assert names == ["B"]  # A skipped (no bound), waveform skipped (discrete)
    (delta,) = plan.deltas
    # anchor 50, safe (0,100): up=50, down=50, tie -> up wins, full depth -> 100
    assert delta.planned == 100


def test_plan_track_scope_out_of_scope_group_ignored() -> None:
    ts = _sharp_scope()
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"amp"}))
    plan = scope.plan_track_scope(ts, mask, 0.5)
    # Only amp-group params planned; src/filter untouched.
    assert all(d.group == "amp" for d in plan.deltas)


def test_reach_prefers_wider_side_and_down_direction() -> None:
    ts = scope.TrackScope(
        track=1,
        profile_name="Synthetic",
        # anchor 90 in (0,100): up=10, down=90 -> down wins -> negative reach.
        anchor={"P": 90},
        safe={"P": (0, 100)},
        groups={"g": ("P",)},
    )
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"g"}))
    plan = scope.plan_track_scope(ts, mask, 1.0)
    (delta,) = plan.deltas
    assert delta.planned == 0  # full downward reach
    assert delta.delta == -90


def test_plan_track_scope_clamps_anchor_outside_safe_range() -> None:
    ts = scope.TrackScope(
        track=1,
        profile_name="Synthetic",
        anchor={"P": 200},  # above the safe high edge
        safe={"P": (0, 100)},
        groups={"g": ("P",)},
    )
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"g"}))
    plan = scope.plan_track_scope(ts, mask, 1.0)
    (delta,) = plan.deltas
    # clamped anchor 100: up=0, down=100 -> down wins -> planned 0.
    assert delta.anchor == 200  # original anchor reported
    assert delta.planned == 0


def test_depth_is_clamped_into_range() -> None:
    ts = _sharp_scope()
    mask = scope.ScopeMask(tracks=frozenset({1}), groups=frozenset({"src"}))
    over = scope.plan_scope([ts], mask, 5.0)
    under = scope.plan_scope([ts], mask, -1.0)
    assert over.depth == scope.DEPTH_MAX
    assert under.depth == scope.DEPTH_MIN
    assert under.ready is False  # clamped to 0 -> no movement
