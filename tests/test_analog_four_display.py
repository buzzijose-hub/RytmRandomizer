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


def test_patch_value_for_physically_disproved_nrpn_destination_fails_closed() -> None:
    from rytm_randomizer.data.analog_four_display import (
        A4_PHYSICAL_ENUM_CALIBRATION_REQUIRED,
        make_a4_patch_value,
    )

    value = make_a4_patch_value(
        "LFO1 Destination A",
        screen_target="Filter1 Frequency",
    )

    assert value.parameter == "LFO1 Destination A"
    assert value.cc_msb is None
    assert value.midi_value is None
    assert value.nrpn_address == (1, 86)
    assert value.transport_status == "screen-only-nrpn"
    assert value.screen_value == "Filter1 Frequency"
    assert value.transport_blocking_reason == A4_PHYSICAL_ENUM_CALIBRATION_REQUIRED


@pytest.mark.parametrize(
    ("parameter", "screen_target", "nrpn_address"),
    [
        ("EnvF Gate Length", "NOTE", (1, 65)),
        ("EnvF Destination A", "OFF", (1, 66)),
        ("EnvF Destination B", "OFF", (1, 68)),
        ("LFO1 Speed Multiplier", "x1", (1, 81)),
        ("LFO1 Destination A", "Filter1 Frequency", (1, 86)),
        ("LFO1 Destination B", "OFF", (1, 88)),
    ],
)
def test_patch_value_keeps_physically_disproved_enum_ordinals_manual(
    parameter: str,
    screen_target: str,
    nrpn_address: tuple[int, int],
) -> None:
    from rytm_randomizer.data.analog_four_display import (
        A4_PHYSICAL_ENUM_CALIBRATION_REQUIRED,
        make_a4_patch_value,
    )

    value = make_a4_patch_value(parameter, screen_target=screen_target)

    assert value.midi_value is None
    assert value.nrpn_address == nrpn_address
    assert value.transport_status == "screen-only-nrpn"
    assert value.transport_blocking_reason == A4_PHYSICAL_ENUM_CALIBRATION_REQUIRED


@pytest.mark.parametrize(
    ("parameter", "disproved_raw_value"),
    [
        ("EnvF Gate Length", 0),
        ("EnvF Destination A", 96),
        ("EnvF Destination B", 96),
        ("LFO1 Speed Multiplier", 64),
        ("LFO1 Destination A", 34),
        ("LFO1 Destination B", 96),
    ],
)
def test_disproved_raw_enum_values_do_not_render_as_semantic_labels(
    parameter: str,
    disproved_raw_value: int,
) -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value(parameter, screen_target=disproved_raw_value)

    assert value.screen_value == str(disproved_raw_value)
    assert value.midi_value is None


def test_lfo2_multiplier_keeps_its_independently_verified_x1_label() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value("LFO2 Speed Multiplier", screen_target=64)

    assert value.screen_value == "x1"
    assert value.midi_value == 64
    assert value.transport_status == "cc-ready"


@pytest.mark.parametrize(
    ("screen_target", "transport_value"),
    [("Filter1 Frequency", 34), (34, None)],
)
def test_physically_disproved_enum_cannot_be_reenabled_by_explicit_raw_value(
    screen_target: int | str,
    transport_value: int | None,
) -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    value = make_a4_patch_value(
        "LFO1 Destination A",
        screen_target=screen_target,
        transport_value=transport_value,
    )

    assert value.midi_value is None
    assert value.transport_status == "screen-only-nrpn"


def test_patch_value_for_unknown_destination_label_fails_closed() -> None:
    from rytm_randomizer.data.analog_four_display import make_a4_patch_value

    unverified_destination = make_a4_patch_value(
        "LFO1 Destination A",
        screen_target="Unvalidated Destination",
    )
    unknown_ready_enum = make_a4_patch_value(
        "Filter2 Type",
        screen_target="Unvalidated Filter Type",
    )

    assert unverified_destination.midi_value is None
    assert unverified_destination.nrpn_address == (1, 86)
    assert unverified_destination.transport_status == "screen-only-nrpn"
    assert unknown_ready_enum.midi_value is None
    assert unknown_ready_enum.transport_status == "screen-only-nrpn"


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
    with pytest.raises(ValueError, match="MIDI value must be in"):
        make_a4_patch_value(
            "LFO1 Destination A",
            screen_target="Filter1 Frequency",
            transport_value=128,
        )
    with pytest.raises(ValueError, match="MIDI value must be in"):
        make_a4_patch_value("LFO1 Destination A", screen_target=128)
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
