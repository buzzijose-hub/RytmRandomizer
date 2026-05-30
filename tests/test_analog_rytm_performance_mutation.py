"""Tests for snapshot-grounded Analog Rytm performance mutation planning."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from conftest import rytm_real_layout_kit_payload
from rytm_randomizer.data.analog_rytm_style_recipes import AnalogRytmRenderedStyleEvent

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
