"""Tests for curated Analog Rytm full-kit style recipes."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    get_machine_src_mappings,
)
from rytm_randomizer.data.analog_rytm_style_recipes import (
    ANALOG_RYTM_STYLE_RECIPES,
    render_analog_rytm_style_recipe,
)
from rytm_randomizer.data.rytm_machine_catalog import is_machine_allowed_on_pad

EXPECTED_STYLE_NAMES = (
    "banging-warehouse",
    "deeper-rolling",
    "detroit-deep",
    "flow-shift",
    "hard-groove",
    "hypnotic-pressure",
    "mills-drive",
)
EXCLUDED_PARAMETERS = {
    "Amp Volume",
    "Level",
    "LFO Destination",
    "Performance Parameter 1",
    "Performance Parameter 2",
    "Performance Parameter 3",
    "Performance Parameter 4",
    "Performance Parameter 5",
    "Performance Parameter 6",
    "Performance Parameter 7",
    "Performance Parameter 8",
    "Performance Parameter 9",
    "Performance Parameter 10",
    "Performance Parameter 11",
    "Performance Parameter 12",
    "Sample Slot",
    "Sample Level",
    "Track Level",
    "Track Mute (seq. mute)",
    "Track Solo (seq. mute)",
}
EXCLUDED_SECTIONS = {"SAMPLE", "PERFORMANCE"}
MAX_KICK_FILTER_FREQUENCY = 32


def test_style_recipe_registry_contains_initial_curated_styles() -> None:
    assert tuple(sorted(ANALOG_RYTM_STYLE_RECIPES)) == EXPECTED_STYLE_NAMES


def test_each_style_recipe_covers_all_twelve_pads_with_legal_machines() -> None:
    for recipe in ANALOG_RYTM_STYLE_RECIPES.values():
        assert tuple(pad.pad for pad in recipe.pads) == tuple(range(1, 13))
        for pad in recipe.pads:
            assert is_machine_allowed_on_pad(pad.pad, pad.machine_key)
            assert pad.parameters


def test_flow_shift_style_uses_acoustic_kick_and_synth_engine_motion() -> None:
    recipe = ANALOG_RYTM_STYLE_RECIPES["flow-shift"]
    pads_by_pad = {pad.pad: pad for pad in recipe.pads}

    assert pads_by_pad[1].machine_key == "bd_acoustic"
    assert pads_by_pad[3].machine_key == "dual_vco"
    assert pads_by_pad[4].machine_key == "sy_chip"

    events = render_analog_rytm_style_recipe(recipe)
    machine_events = [event for event in events if event.parameter == "Track Machine Type"]

    assert len(machine_events) == 12
    assert any(event.value == 30 for event in machine_events)
    assert any(event.value == 28 for event in machine_events)
    assert any(event.value == 29 for event in machine_events)


def test_rendered_style_events_are_manual_backed_and_cover_every_pad() -> None:
    track_machine = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Machine Type")]

    for recipe in ANALOG_RYTM_STYLE_RECIPES.values():
        events = render_analog_rytm_style_recipe(recipe)
        machine_events = [event for event in events if event.parameter == "Track Machine Type"]
        tone_events = [event for event in events if event.parameter != "Track Machine Type"]

        assert len(machine_events) == 12
        assert {event.pad for event in machine_events} == set(range(1, 13))
        assert {event.pad for event in tone_events} == set(range(1, 13))
        assert all(event.channel == event.pad - 1 for event in events)
        assert all(0 <= event.cc_msb <= 127 for event in events)
        assert all(0 <= event.value <= 127 for event in events)

        for event in machine_events:
            assert event.section == "COMMON"
            assert event.cc_msb == track_machine.cc_msb
            assert event.risk == "high"

        for event in tone_events:
            if event.source == "machine_src":
                source_parameters = {
                    mapping.parameter: mapping
                    for mapping in get_machine_src_mappings(event.machine_key)
                }
                assert event.parameter in source_parameters
                assert event.cc_msb == source_parameters[event.parameter].cc_msb
            else:
                manual_mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[
                    (event.section, event.parameter)
                ]
                assert event.cc_msb == manual_mapping.cc_msb


def test_style_recipes_avoid_samples_macros_and_volume_like_rows() -> None:
    for recipe in ANALOG_RYTM_STYLE_RECIPES.values():
        events = render_analog_rytm_style_recipe(recipe)
        for event in events:
            if event.parameter == "Track Machine Type":
                continue
            assert event.parameter not in EXCLUDED_PARAMETERS
            assert event.section not in EXCLUDED_SECTIONS


def test_style_recipes_keep_kick_filter_frequency_sub_safe() -> None:
    for recipe in ANALOG_RYTM_STYLE_RECIPES.values():
        events = render_analog_rytm_style_recipe(recipe)
        kick_filter_events = [
            event
            for event in events
            if event.machine_key.startswith("bd_")
            and event.section == "FILTER"
            and event.parameter == "Filter Frequency"
        ]

        assert all(
            event.value <= MAX_KICK_FILTER_FREQUENCY for event in kick_filter_events
        ), recipe.name


def test_rendered_style_events_are_deterministic() -> None:
    recipe = ANALOG_RYTM_STYLE_RECIPES["detroit-deep"]

    first = render_analog_rytm_style_recipe(recipe)
    second = render_analog_rytm_style_recipe(recipe)

    assert first == second
    assert len(first) >= 60
    assert [(event.pad, event.parameter, event.cc_msb) for event in first[:3]] == [
        (1, "Track Machine Type", 15),
        (1, "Tune", 17),
        (1, "Decay", 18),
    ]
