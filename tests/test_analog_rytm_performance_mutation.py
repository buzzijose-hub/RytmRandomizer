"""Tests for snapshot-grounded Analog Rytm performance mutation planning."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, cast

import pytest

from conftest import rytm_real_layout_kit_payload
from rytm_randomizer.data.analog_rytm_style_recipes import AnalogRytmRenderedStyleEvent
from rytm_randomizer.devices.strategies import RytmKitSnapshot, RytmPerformanceMutationDepth

pytestmark = pytest.mark.fast


def _snapshot():
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    return AnalogRytmSnapshotDecoder().decode(
        rytm_real_layout_kit_payload(name=b"PERF"),
        slot=0,
    )


def _flow_shift_recipe():
    from rytm_randomizer.data.analog_rytm_style_recipes import get_analog_rytm_style_recipe

    recipe = get_analog_rytm_style_recipe("flow-shift")
    assert recipe is not None
    return recipe


def _parameters(events: Sequence[AnalogRytmRenderedStyleEvent]) -> tuple[str, ...]:
    return tuple(event.parameter for event in events)


def _rendered_event(
    *,
    pad: int = 1,
    machine_key: str = "bd_hard",
    section: str = "FILTER",
    parameter: str = "Filter Frequency",
    value: int = 64,
    source: Literal["machine", "machine_src", "manual"] = "manual",
) -> AnalogRytmRenderedStyleEvent:
    return AnalogRytmRenderedStyleEvent(
        pad=pad,
        channel=pad - 1,
        machine_key=machine_key,
        section=section,
        parameter=parameter,
        cc_msb=74,
        value=value,
        risk="safe",
        mutation_status="validated_runtime",
        source=source,
        intent="coverage probe",
    )


def _event_shape(
    events: Sequence[AnalogRytmRenderedStyleEvent],
) -> tuple[tuple[int, int, str, str, str, int, str], ...]:
    return tuple(
        (
            event.pad,
            event.channel,
            event.machine_key,
            event.section,
            event.parameter,
            event.cc_msb,
            event.source,
        )
        for event in events
    )


def test_performance_plan_live_safe_excludes_machine_switching() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    plan = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
    )

    assert plan.ready is True
    assert plan.mode == "live-safe"
    assert plan.machine_switching_allowed is False
    assert plan.events
    assert "Track Machine Type" not in _parameters(plan.events)
    assert plan.skipped_event_count > 0


def test_performance_plan_live_safe_varies_values_by_seed_without_changing_shape() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    first = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
        seed=101,
    )
    second = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
        seed=202,
    )

    assert _event_shape(first.events) == _event_shape(second.events)
    assert tuple(event.value for event in first.events) != tuple(
        event.value for event in second.events
    )
    assert {event.pad for event in first.events} == set(range(1, 13))


def test_performance_plan_live_safe_keeps_pad_1_bd_hard_tune_punch_safe() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    plan = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
        depth="safe",
        seed=303,
    )

    pad_1_tune_values = [
        event.value
        for event in plan.events
        if event.pad == 1 and event.source == "machine_src" and event.parameter == "Tune"
    ]

    assert pad_1_tune_values
    assert all(58 <= value <= 66 for value in pad_1_tune_values)


def test_performance_plan_live_safe_keeps_pad_1_kick_filter_near_low_anchor() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    plan = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
        depth="safe",
        seed=890002068,
    )

    pad_1_filter_values = [
        event.value
        for event in plan.events
        if event.pad == 1 and event.source == "manual" and event.parameter == "Filter Frequency"
    ]

    assert pad_1_filter_values
    assert all(21 <= value <= 29 for value in pad_1_filter_values)


def test_performance_plan_live_safe_retargets_src_events_to_current_machine() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    plan = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
    )

    pad_1_src_events = [
        event for event in plan.events if event.pad == 1 and event.source == "machine_src"
    ]

    assert pad_1_src_events
    assert {event.machine_key for event in pad_1_src_events} == {"bd_hard"}
    assert {event.parameter for event in pad_1_src_events}.issubset({"Tune", "Decay"})


def test_performance_plan_live_safe_tags_manual_events_with_current_machine_when_known() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    plan = build_rytm_performance_mutation_plan(
        _snapshot(),
        _flow_shift_recipe(),
        mode="live-safe",
    )

    pad_1_manual_events = [
        event for event in plan.events if event.pad == 1 and event.source == "manual"
    ]

    assert pad_1_manual_events
    assert {event.machine_key for event in pad_1_manual_events} == {"bd_hard"}


def test_performance_plan_flow_shift_keeps_full_style_events() -> None:
    from rytm_randomizer.data.analog_rytm_style_recipes import render_analog_rytm_style_recipe
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    recipe = _flow_shift_recipe()
    rendered = render_analog_rytm_style_recipe(recipe)
    plan = build_rytm_performance_mutation_plan(
        _snapshot(),
        recipe,
        mode="flow-shift",
    )

    assert plan.ready is True
    assert plan.mode == "flow-shift"
    assert plan.machine_switching_allowed is True
    assert plan.events == rendered
    assert _parameters(plan.events).count("Track Machine Type") == 12
    assert plan.skipped_event_count == 0


def test_performance_plan_rejects_unknown_mode() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    with pytest.raises(ValueError, match="unknown performance mutation mode"):
        build_rytm_performance_mutation_plan(
            _snapshot(),
            _flow_shift_recipe(),
            mode="panic",  # type: ignore[arg-type]
        )


def test_performance_plan_rejects_non_rytm_snapshot() -> None:
    from rytm_randomizer.devices.strategies import build_rytm_performance_mutation_plan

    bad_snapshot = cast(RytmKitSnapshot, object())
    with pytest.raises(ValueError, match="snapshot must be a RytmKitSnapshot"):
        build_rytm_performance_mutation_plan(
            bad_snapshot,
            _flow_shift_recipe(),
            mode="live-safe",
        )


@pytest.mark.parametrize(
    ("depth", "window", "expected_range", "expected_anchor"),
    (
        ("safe", 6, (1, 2), (63, 65)),
        ("balanced", 14, (3, 4), (62, 66)),
        ("studio", 32, (5, 6), (61, 67)),
    ),
)
def test_performance_guardrail_depth_windows_cover_all_depths(
    depth: RytmPerformanceMutationDepth,
    window: int,
    expected_range: tuple[int, int],
    expected_anchor: tuple[int, int],
) -> None:
    from rytm_randomizer.devices.strategies import analog_rytm_performance_mutation as mutation

    assert mutation._window_for_depth(depth) == window
    assert (
        mutation._range_for_depth(
            depth,
            safe=(1, 2),
            balanced=(3, 4),
            studio=(5, 6),
        )
        == expected_range
    )
    assert (
        mutation._anchor_range(
            64,
            depth,
            safe_window=1,
            balanced_window=2,
            studio_window=3,
        )
        == expected_anchor
    )


def test_performance_guardrail_rejects_unknown_depth() -> None:
    from rytm_randomizer.devices.strategies import analog_rytm_performance_mutation as mutation

    bad_depth = cast(RytmPerformanceMutationDepth, "panic")
    with pytest.raises(ValueError, match="unknown performance mutation depth"):
        mutation._window_for_depth(bad_depth)
    with pytest.raises(ValueError, match="unknown performance mutation depth"):
        mutation._range_for_depth(
            bad_depth,
            safe=(1, 2),
            balanced=(3, 4),
            studio=(5, 6),
        )


@pytest.mark.parametrize(
    ("event", "expected_safe", "expected_studio"),
    (
        (
            _rendered_event(pad=2, section="FILTER", parameter="Filter Resonance", value=28),
            (24, 30),
            (0, 56),
        ),
        (
            _rendered_event(pad=2, section="AMP", parameter="Amp Delay Send", value=40),
            (34, 38),
            (8, 72),
        ),
        (
            _rendered_event(section="AMP", parameter="Amp Pan", value=64),
            (56, 72),
            (28, 100),
        ),
        (
            _rendered_event(section="SRC", parameter="Waveform", value=3, source="machine_src"),
            (1, 5),
            (0, 21),
        ),
        (
            _rendered_event(section="SRC", parameter="Balance", value=64, source="machine_src"),
            (59, 69),
            (36, 92),
        ),
    ),
)
def test_performance_guardrail_parameter_families_have_depth_ranges(
    event: AnalogRytmRenderedStyleEvent,
    expected_safe: tuple[int, int],
    expected_studio: tuple[int, int],
) -> None:
    from rytm_randomizer.devices.strategies import analog_rytm_performance_mutation as mutation

    assert mutation._guardrail_range_for_event(event, "safe") == expected_safe
    assert mutation._guardrail_range_for_event(event, "studio") == expected_studio
