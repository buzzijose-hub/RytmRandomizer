"""Tests for Analog Four front-panel display metadata."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_bipolar_display_values_map_center_to_midi_64() -> None:
    from rytm_randomizer.data.analog_four_display import (
        midi_to_a4_signed_screen,
        signed_screen_to_a4_midi,
    )

    assert signed_screen_to_a4_midi(-64) == 0
    assert signed_screen_to_a4_midi(0) == 64
    assert signed_screen_to_a4_midi(63) == 127
    assert midi_to_a4_signed_screen(0) == -64
    assert midi_to_a4_signed_screen(64) == 0
    assert midi_to_a4_signed_screen(127) == 63


@pytest.mark.parametrize("screen_value", [-65, 64])
def test_bipolar_display_rejects_out_of_range_screen_values(screen_value: int) -> None:
    from rytm_randomizer.data.analog_four_display import signed_screen_to_a4_midi

    with pytest.raises(ValueError, match="screen value must be in"):
        signed_screen_to_a4_midi(screen_value)


def test_display_metadata_covers_user_called_out_a4_parameters() -> None:
    from rytm_randomizer.data.analog_four_display import ANALOG_FOUR_PARAMETER_DISPLAY

    expected = {
        "OSC1 Pulsewidth",
        "Filter Overdrive",
        "Filter2 Type",
        "Filter2 Resonance",
        "EnvA Env Shape",
        "EnvF Release Time",
        "EnvF Env Shape",
        "LFO1 Speed Multiplier",
        "LFO1 Waveform",
        "LFO1 Destination A",
        "LFO1 Depth A",
    }

    assert expected <= set(ANALOG_FOUR_PARAMETER_DISPLAY)
    assert ANALOG_FOUR_PARAMETER_DISPLAY["Filter Overdrive"].display_scale == "bipolar"
    assert ANALOG_FOUR_PARAMETER_DISPLAY["OSC1 Pulsewidth"].display_scale == "bipolar"
    assert ANALOG_FOUR_PARAMETER_DISPLAY["Filter2 Type"].label_for_value(4) == "HP2"
    assert ANALOG_FOUR_PARAMETER_DISPLAY["EnvA Env Shape"].label_for_value(0) == "triangle"


def test_patch_value_for_bipolar_filter_overdrive_includes_screen_and_transport() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value("Filter Overdrive", screen_target=10)

    assert value.parameter == "Filter Overdrive"
    assert value.section == "FILTERS"
    assert value.encoder == "C"
    assert value.screen_value == "+10"
    assert value.midi_value == 74
    assert value.cc_msb == 86
    assert value.nrpn_address == (1, 42)
    assert value.transport_status == "cc-ready"
    assert value.dial_direction == "turn right from OFF/0"


def test_patch_value_for_filter_overdrive_center_uses_off_label() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value("Filter Overdrive", screen_target=0)

    assert value.screen_value == "OFF/0"
    assert value.midi_value == 64
    assert value.dial_direction == "leave at OFF/0"


def test_patch_value_for_validated_nrpn_destination_is_transport_ready() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value(
        "LFO1 Destination A",
        screen_target="Filter1 Frequency",
    )

    assert value.parameter == "LFO1 Destination A"
    assert value.cc_msb is None
    assert value.midi_value == 34
    assert value.nrpn_address == (1, 86)
    assert value.transport_status == "nrpn-ready"
    assert value.screen_value == "Filter1 Frequency"


@pytest.mark.parametrize(
    ("parameter", "screen_target", "midi_value", "nrpn_address"),
    [
        ("EnvF Gate Length", "NOTE", 0, (1, 65)),
        ("EnvF Destination A", "OFF", 96, (1, 66)),
        ("EnvF Destination B", "OFF", 96, (1, 68)),
        ("LFO1 Destination B", "OFF", 96, (1, 88)),
    ],
)
def test_patch_value_uses_validated_overbridge_enum_ordinals(
    parameter: str,
    screen_target: str,
    midi_value: int,
    nrpn_address: tuple[int, int],
) -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value(parameter, screen_target=screen_target)

    assert value.midi_value == midi_value
    assert value.nrpn_address == nrpn_address
    assert value.transport_status == "nrpn-ready"


def test_patch_value_for_unknown_destination_label_fails_closed() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value(
        "LFO1 Destination A",
        screen_target="Unvalidated Destination",
    )

    assert value.midi_value is None
    assert value.nrpn_address == (1, 86)
    assert value.transport_status == "screen-only-nrpn"


def test_patch_value_for_nrpn_enum_can_accept_explicit_transport_value() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value(
        "Filter2 Type",
        screen_target="HP2",
        transport_value=4,
    )

    assert value.screen_value == "HP2"
    assert value.midi_value == 4
    assert value.transport_status == "nrpn-ready"
    assert value.dial_direction == "select HP2"


def test_patch_value_rejects_invalid_screen_target_shapes() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    with pytest.raises(ValueError, match="MIDI value must be in"):
        make_a4_patch_value("OSC1 Level", screen_target=128)
    with pytest.raises(ValueError, match="MIDI value must be in"):
        make_a4_patch_value("Filter2 Type", screen_target="HP2", transport_value=128)
    with pytest.raises(TypeError, match="screen_target must be"):
        make_a4_patch_value("OSC1 Level", screen_target=object())  # type: ignore[arg-type]


def test_display_transport_fallbacks_for_unmapped_manual_rows() -> None:
    from rytm_randomizer.data.analog_four_display import (
        DISPLAY_SCALE_ENUM,
        TRANSPORT_SCREEN_ONLY,
        AnalogFourDisplaySpec,
        _dial_direction,
        _nrpn_address,
        _transport_status,
    )
    from rytm_randomizer.data.analog_four_midi import AnalogFourCcMapping

    mapping = AnalogFourCcMapping(
        parameter="Manual-only",
        section="TEST",
        encoder="-",
        cc_msb=None,
        cc_lsb=None,
        nrpn_msb=None,
        nrpn_lsb=None,
    )

    assert _nrpn_address(mapping) is None
    assert _transport_status(mapping, None) == TRANSPORT_SCREEN_ONLY
    assert (
        _dial_direction(
            10,
            spec=AnalogFourDisplaySpec(DISPLAY_SCALE_ENUM),
            midi_value=None,
        )
        == "set to 10"
    )


def test_patch_value_rejects_unknown_parameter() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    with pytest.raises(KeyError, match="Unknown Analog Four parameter"):
        make_a4_patch_value("Imaginary Parameter", screen_target=0)
