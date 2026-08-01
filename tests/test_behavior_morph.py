"""Branch-complete tests for the passive kit-morph engine."""

from __future__ import annotations

import pytest

from rytm_randomizer.behavior import morph

pytestmark = pytest.mark.fast


def test_interpolate_continuous_linear() -> None:
    assert morph.interpolate_value(10, 20, 0.0, discrete=False) == 10
    assert morph.interpolate_value(10, 20, 0.5, discrete=False) == 15
    assert morph.interpolate_value(10, 20, 1.0, discrete=False) == 20
    # Rounding to nearest integer.
    assert morph.interpolate_value(10, 21, 0.5, discrete=False) == 16


def test_interpolate_discrete_thresholds_at_midpoint() -> None:
    assert morph.interpolate_value(0, 3, 0.49, discrete=True) == 0
    assert morph.interpolate_value(0, 3, 0.5, discrete=True) == 3
    assert morph.interpolate_value(0, 3, 0.9, discrete=True) == 3


def test_interpolate_clamps_amount() -> None:
    assert morph.interpolate_value(10, 20, -1.0, discrete=False) == 10
    assert morph.interpolate_value(10, 20, 2.0, discrete=False) == 20


def test_build_morph_track_from_registry() -> None:
    mt = morph.build_morph_track(1, "1", "3")
    assert mt.track == 1
    assert mt.source_name == "My BD Sharp"
    assert mt.target_name == "My BD Classic"
    assert "SRC Tune" in mt.source
    assert "SRC Tune" in mt.target
    assert "src" in mt.groups


def test_build_morph_track_unknown_key_raises() -> None:
    with pytest.raises(KeyError):
        morph.build_morph_track(1, "1", "nope")


def test_morph_param_moved_property() -> None:
    moved = morph.MorphParam(
        name="x", group="g", source=10, target=20, interpolated=15, discrete=False
    )
    still = morph.MorphParam(
        name="y", group="g", source=10, target=20, interpolated=10, discrete=False
    )
    assert moved.moved is True
    assert still.moved is False


def test_plan_morph_ready_interpolates_and_is_deterministic() -> None:
    mt = morph.build_morph_track(1, "1", "3")
    plan = morph.plan_morph([mt], frozenset({"src", "filter"}), 0.5)
    assert plan.ready is True
    assert plan.readiness_reason == "ready"
    assert plan.amount == 0.5
    assert plan.total_moved > 0
    assert plan == morph.plan_morph([mt], frozenset({"src", "filter"}), 0.5)


def test_plan_morph_no_groups_not_ready() -> None:
    mt = morph.build_morph_track(1, "1", "3")
    plan = morph.plan_morph([mt], frozenset(), 0.5)
    assert plan.ready is False
    assert plan.readiness_reason == "no parameter groups selected"


def test_plan_morph_zero_amount_not_ready() -> None:
    mt = morph.build_morph_track(1, "1", "3")
    plan = morph.plan_morph([mt], frozenset({"src"}), 0.0)
    assert plan.ready is False
    assert plan.readiness_reason == "amount is 0.0 (source unchanged)"


def test_plan_morph_identical_source_target_not_ready() -> None:
    mt = morph.build_morph_track(1, "1", "1")  # source == target profile
    plan = morph.plan_morph([mt], frozenset({"src", "filter"}), 0.5)
    assert plan.ready is False
    assert plan.readiness_reason == "source and target already match in scope"
    assert plan.total_moved == 0


def test_plan_morph_track_unmatched_and_dedupe() -> None:
    mt = morph.MorphTrack(
        track=1,
        source_name="S",
        target_name="T",
        source={"A": 10, "B": 20, "SRC Waveform": 0},
        # "B" missing from target -> unmatched; "C" missing from source -> unmatched.
        target={"A": 30, "C": 40, "SRC Waveform": 3},
        # "A" appears twice across groups -> planned once.
        groups={"g1": ("A", "B", "SRC Waveform", "C"), "g2": ("A",)},
    )
    plan = morph.plan_morph_track(mt, frozenset({"g1", "g2"}), 0.5)
    names = [p.name for p in plan.params]
    assert names == ["A", "SRC Waveform"]
    assert set(plan.unmatched) == {"B", "C"}
    # Discrete waveform thresholds; continuous A blends.
    by_name = {p.name: p for p in plan.params}
    assert by_name["A"].interpolated == 20  # 10 -> 30 at 0.5
    assert by_name["A"].discrete is False
    assert by_name["SRC Waveform"].interpolated == 3  # discrete flips at 0.5
    assert by_name["SRC Waveform"].discrete is True


def test_plan_morph_track_param_absent_from_both_states_ignored() -> None:
    # A group lists a param present in neither source nor target: it is
    # neither morphed nor reported as unmatched (nothing to align).
    mt = morph.MorphTrack(
        track=1,
        source_name="S",
        target_name="T",
        source={"A": 10},
        target={"A": 30},
        groups={"g": ("A", "GHOST")},
    )
    plan = morph.plan_morph_track(mt, frozenset({"g"}), 0.5)
    assert [p.name for p in plan.params] == ["A"]
    assert plan.unmatched == ()


def test_plan_morph_track_out_of_scope_group_ignored() -> None:
    mt = morph.build_morph_track(1, "1", "3")
    plan = morph.plan_morph_track(mt, frozenset({"amp"}), 0.5)
    assert all(p.group == "amp" for p in plan.params)


def test_moved_count_excludes_unchanged_params() -> None:
    mt = morph.MorphTrack(
        track=1,
        source_name="S",
        target_name="T",
        source={"A": 10, "B": 20},
        target={"A": 10, "B": 40},  # A unchanged, B moves
        groups={"g": ("A", "B")},
    )
    plan = morph.plan_morph_track(mt, frozenset({"g"}), 1.0)
    assert plan.moved_count == 1
