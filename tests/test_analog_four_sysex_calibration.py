"""Tests for promoted Analog Four SysEx calibration facts."""

from __future__ import annotations

from decimal import localcontext
from fractions import Fraction

import pytest

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("precision", [1, 2, 28])
def test_filter1_frequency_formatter_is_exact_across_its_complete_domain(precision: int) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")
    with localcontext() as context:
        context.prec = precision
        for raw in range(calibration.native_raw_max + 1):
            screen_value = calibration.format_native_screen_value(raw)
            assert Fraction(screen_value) == Fraction(raw, 256)
            assert "." not in screen_value or not screen_value.endswith("0")
        assert calibration.format_native_screen_value(0) == "0"
        assert calibration.format_native_screen_value(0x3F80) == "63.5"
        assert calibration.format_native_screen_value(0x4001) == "64.00390625"
        assert calibration.format_native_screen_value(0x7F00) == "127"


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_filter1_frequency_formatter_rejects_non_integer_inputs(value: object) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")
    with pytest.raises(TypeError, match="must be an integer"):
        calibration.format_native_screen_value(value)


@pytest.mark.parametrize("value", [-1, 0x7F01, 0xFFFF])
def test_filter1_frequency_formatter_rejects_unpromoted_range(value: int) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")
    with pytest.raises(ValueError, match="0x0000..0x7F00"):
        calibration.format_native_screen_value(value)


def test_filter1_frequency_calibration_records_promoted_track_stride() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")

    assert calibration.parameter == "Filter1 Frequency"
    assert calibration.status == A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED
    assert calibration.offline_saved_kit_mutation_validated is True
    assert calibration.hardware_send_validated is False
    assert calibration.native_encoding == "unsigned-big-endian-q8.8"
    assert (calibration.native_raw_min, calibration.native_raw_max) == (
        0x0000,
        0x7F00,
    )
    assert [calibration.native_offset_for_track(track) for track in range(1, 5)] == [
        128,
        478,
        828,
        1178,
    ]
    assert calibration.native_field == "filter1_frequency"
    assert calibration.native_scale == 256
    assert calibration.native_width == 2
    assert calibration.screen_min == "0.00"
    assert calibration.screen_mid == "63.50"
    assert calibration.screen_max == "127.00"
    assert calibration.primary_raw_values == {
        "0.00": 0x00,
        "63.50": 0x3F,
        "127.00": 0x7F,
    }
    assert calibration.track_raw_stride == 400
    assert calibration.track_unpacked_stride == 350
    assert [calibration.primary_raw_offset_for_track(track) for track in range(1, 5)] == [
        156,
        556,
        956,
        1356,
    ]
    assert [calibration.raw_group_range_for_track(track) for track in range(1, 5)] == [
        (152, 160),
        (552, 560),
        (952, 960),
        (1352, 1360),
    ]
    assert [calibration.unpacked_group_range_for_track(track) for track in range(1, 5)] == [
        (130, 140),
        (480, 490),
        (830, 840),
        (1180, 1190),
    ]


def test_filter1_frequency_calibration_keeps_capture_evidence_compact() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")

    assert {
        (row.track, row.screen_value, row.primary_raw_value) for row in calibration.evidence
    } == {
        (1, "0.00", 0x00),
        (1, "63.50", 0x3F),
        (1, "127.00", 0x7F),
        (2, "0.00", 0x00),
        (2, "63.50", 0x3F),
        (2, "127.00", 0x7F),
        (3, "0.00", 0x00),
        (4, "0.00", 0x00),
    }
    assert {
        (
            row.screen_value,
            row.source_file,
            row.payload_fingerprint,
        )
        for row in calibration.evidence
        if row.track == 1
    } == {
        ("0.00", "filter1_freq_000_expected.syx", "3834839047939f0a"),
        ("63.50", "filter1_freq_063_50_expected.syx", "89569c28ad1c6d3a"),
        ("127.00", "filter1_freq_127_source.syx", "ca77b13a6131a513"),
    }
    assert {row.kit_name for row in calibration.evidence} == {"KIT 1", "KIT 20"}
    assert all(len(row.payload_fingerprint) == 16 for row in calibration.evidence)


def test_only_filter1_frequency_has_offline_saved_kit_mutation_authority() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
        ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
    )

    offline_parameters = {
        parameter
        for parameter, calibration in ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.items()
        if calibration.status == A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED
    }

    assert offline_parameters == {"Filter1 Frequency"}
    assert (
        ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS["Filter1 Frequency"].hardware_send_validated is False
    )


def test_filter1_resonance_calibration_records_promoted_track_stride() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Resonance")

    assert calibration.parameter == "Filter1 Resonance"
    assert calibration.status == A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED
    assert calibration.screen_min == "0"
    assert calibration.screen_mid == "20"
    assert calibration.screen_max == "127"
    assert calibration.primary_raw_values == {
        "0": 0x00,
        "20": 0x14,
        "127": 0x7F,
    }
    assert calibration.track_raw_stride == 400
    assert calibration.track_unpacked_stride == 350
    assert [calibration.primary_raw_offset_for_track(track) for track in range(1, 5)] == [
        158,
        558,
        958,
        1358,
    ]
    assert [calibration.raw_group_range_for_track(track) for track in range(1, 5)] == [
        (156, 164),
        (556, 564),
        (956, 964),
        (1356, 1364),
    ]
    assert [calibration.unpacked_group_range_for_track(track) for track in range(1, 5)] == [
        (133, 140),
        (483, 490),
        (833, 840),
        (1183, 1190),
    ]


def test_filter1_resonance_calibration_keeps_capture_evidence_compact() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Resonance")

    assert {
        (row.track, row.screen_value, row.primary_raw_value) for row in calibration.evidence
    } == {
        (1, "0", 0x00),
        (1, "20", 0x14),
        (1, "127", 0x7F),
        (2, "0", 0x00),
        (3, "0", 0x00),
        (4, "0", 0x00),
    }
    assert {row.kit_name for row in calibration.evidence} == {"KIT 1"}
    assert {row.payload_fingerprint for row in calibration.evidence} == {
        "9a5da29b4ad37008",
        "67a43e126f4d0f85",
        "9f4535115136f4ec",
        "950e8f5b65253fbb",
        "cc64427123887f89",
        "6818388c34db01b9",
    }
    assert all(row.source_file.endswith("_Kit.syx") for row in calibration.evidence)


def test_filter2_frequency_calibration_records_promoted_track_stride() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter2 Frequency")

    assert calibration.parameter == "Filter2 Frequency"
    assert calibration.status == A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED
    assert calibration.screen_min == "0.00"
    assert calibration.screen_mid == "63.50"
    assert calibration.screen_max == "127.00"
    assert calibration.primary_raw_values == {
        "0.00": 0x00,
        "63.50": 0x3F,
        "127.00": 0x7F,
    }
    assert calibration.track_raw_stride == 400
    assert calibration.track_unpacked_stride == 350
    assert [calibration.primary_raw_offset_for_track(track) for track in range(1, 5)] == [
        167,
        567,
        967,
        1367,
    ]
    assert [calibration.raw_group_range_for_track(track) for track in range(1, 5)] == [
        (160, 172),
        (560, 572),
        (960, 972),
        (1360, 1372),
    ]
    assert [calibration.unpacked_group_range_for_track(track) for track in range(1, 5)] == [
        (137, 144),
        (487, 494),
        (837, 844),
        (1187, 1194),
    ]


def test_filter2_frequency_calibration_keeps_capture_evidence_compact() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter2 Frequency")

    assert {
        (row.track, row.screen_value, row.primary_raw_value) for row in calibration.evidence
    } == {
        (1, "0.00", 0x00),
        (1, "63.50", 0x3F),
        (1, "127.00", 0x7F),
        (2, "127.00", 0x7F),
        (3, "127.00", 0x7F),
        (4, "127.00", 0x7F),
    }
    assert {row.kit_name for row in calibration.evidence} == {"KIT 1"}
    assert {row.payload_fingerprint for row in calibration.evidence} == {
        "6818388c34db01b9",
        "82c03587679c6ddc",
        "9497709f8562f1ef",
        "1f15e21e281ce000",
        "fabeab5b95ed53e0",
        "a52174e811260978",
    }
    assert all(row.source_file.endswith("_Kit.syx") for row in calibration.evidence)


def test_filter2_resonance_calibration_records_promoted_track_stride() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter2 Resonance")

    assert calibration.parameter == "Filter2 Resonance"
    assert calibration.status == A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED
    assert calibration.hardware_send_validated is True
    assert calibration.offline_saved_kit_mutation_validated is False
    assert calibration.screen_min == "0"
    assert calibration.screen_mid == "20"
    assert calibration.screen_max == "127"
    assert calibration.primary_raw_values == {
        "0": 0x00,
        "20": 0x14,
        "127": 0x7F,
    }
    assert calibration.track_raw_stride == 400
    assert calibration.track_unpacked_stride == 350
    assert [calibration.primary_raw_offset_for_track(track) for track in range(1, 5)] == [
        170,
        570,
        970,
        1370,
    ]
    assert [calibration.raw_group_range_for_track(track) for track in range(1, 5)] == [
        (168, 176),
        (568, 576),
        (968, 976),
        (1368, 1376),
    ]
    assert [calibration.unpacked_group_range_for_track(track) for track in range(1, 5)] == [
        (144, 151),
        (494, 501),
        (844, 851),
        (1194, 1201),
    ]


def test_filter2_resonance_calibration_keeps_capture_evidence_compact() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter2 Resonance")

    assert {
        (
            row.track,
            row.screen_value,
            row.primary_raw_value,
            row.source_file,
            row.payload_fingerprint,
        )
        for row in calibration.evidence
    } == {
        (
            1,
            "0",
            0x00,
            "A4_Test1_T1_Filter2Res_000_Kit.syx",
            "4ec91a917cfaeab0",
        ),
        (
            1,
            "20",
            0x14,
            "A4_Test1_T1_Filter2Res_020_Kit.syx",
            "ccf0acb6bb32e1b3",
        ),
        (
            1,
            "127",
            0x7F,
            "A4_Test1_T1_Filter2Res_127_Kit.syx",
            "c842a01f81f1eaa8",
        ),
        (
            2,
            "127",
            0x7F,
            "A4_Test1_T2_Filter2Res_127_Kit.syx",
            "8de0161d9ffd0798",
        ),
        (
            3,
            "127",
            0x7F,
            "A4_Test1_T3_Filter2Res_127_Kit.syx",
            "640e4443acf81ee4",
        ),
        (
            4,
            "127",
            0x7F,
            "A4_Test1_T4_Filter2Res_127_Kit.syx",
            "1f2160541d4204b0",
        ),
    }
    assert {row.kit_name for row in calibration.evidence} == {"KIT 1"}


def test_filter2_resonance_records_hardware_write_validation_evidence() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
    )

    evidence = ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS["Filter2 Resonance"]

    assert [row.expected_track_values for row in evidence] == [
        ((1, "127"),),
        ((1, "64"),),
        ((1, "16"), (2, "48"), (3, "80"), (4, "112")),
    ]
    assert [row.generated_sha256 for row in evidence] == [
        "5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b",
        "2fee1aa93c98e0221dbe7bac296c51268360c5c61e11c8eea77fd091cbbd94f7",
        "0e88aa6f15fd49c36696d5b8e09bda18ce5eeb8562c1a44ce46683c6deef819b",
    ]
    assert evidence[0].matched_reference_file == "A4_Test1_T1_Filter2Res_127_Kit.syx"
    assert evidence[1].matched_reference_file is None
    assert evidence[2].operator_confirmed is True


def test_filter2_resonance_calibration_converts_novel_integer_screen_values() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    resonance = analog_four_sysex_calibration_for("Filter2 Resonance")
    frequency = analog_four_sysex_calibration_for("Filter2 Frequency")

    assert frequency.primary_raw_value_for_screen("63.50") == 0x3F
    assert resonance.primary_raw_value_for_screen("64") == 64
    with pytest.raises(ValueError, match="unsupported screen value"):
        resonance.primary_raw_value_for_screen("loud")
    with pytest.raises(ValueError, match="unsupported screen value"):
        resonance.primary_raw_value_for_screen("064")
    with pytest.raises(ValueError, match="unsupported screen value"):
        resonance.primary_raw_value_for_screen("128")
    with pytest.raises(ValueError, match="unsupported screen value"):
        frequency.primary_raw_value_for_screen("64.00")


def test_hardware_write_validation_status_requires_confirmed_hashed_evidence() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
        ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
        ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
    )

    validated_parameters = {
        parameter
        for parameter, calibration in ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.items()
        if calibration.status == A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED
    }

    assert validated_parameters == set(ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS)
    for parameter in validated_parameters:
        evidence = ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS[parameter]
        assert evidence
        assert all(row.operator_confirmed for row in evidence)
        assert all(
            len(row.generated_sha256) == 64
            and row.generated_sha256 == row.generated_sha256.lower()
            and set(row.generated_sha256) <= set("0123456789abcdef")
            for row in evidence
        )


def test_sysex_calibration_mapping_is_reexported_from_data_layer() -> None:
    from rytm_randomizer.data import (
        ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
        ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
    )
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS as MODULE_FIELD_CALIBRATIONS,
    )

    assert set(ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS) >= {
        "Filter1 Frequency",
        "Filter1 Resonance",
        "Filter2 Frequency",
        "Filter2 Resonance",
    }
    assert ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS is MODULE_FIELD_CALIBRATIONS
    assert set(ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS) == {"Filter2 Resonance"}


@pytest.mark.parametrize("track", [0, 5, True, 1.0])
def test_sysex_calibration_rejects_tracks_outside_a4_synth_range(track: object) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Resonance")

    with pytest.raises(ValueError, match="track must be in 1..4"):
        calibration.primary_raw_offset_for_track(track)  # type: ignore[arg-type]


def test_sysex_calibration_rejects_unknown_parameters() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    with pytest.raises(KeyError, match="Unknown Analog Four SysEx calibration"):
        analog_four_sysex_calibration_for("Filter1 Width")


@pytest.mark.parametrize("value", [True, False, 1.0, 1, None])
def test_exact_fixed_point_parser_rejects_non_text_without_coercion(value: object) -> None:
    from rytm_randomizer.data.analog_four_kit_fields import parse_a4_fixed_8_8

    with pytest.raises(ValueError, match="unsupported screen value"):
        parse_a4_fixed_8_8(value)


def test_shared_fixed_point_codec_covers_full_native_range_and_public_exports() -> None:
    from rytm_randomizer.data import (
        A4_FIXED_8_8_ENCODING,
        A4_FIXED_8_8_RAW_MAX,
        A4_FIXED_8_8_SCALE,
        A4_FIXED_8_8_WIDTH,
    )
    from rytm_randomizer.data.analog_four_kit_fields import (
        format_a4_fixed_8_8,
        parse_a4_fixed_8_8,
    )

    assert (A4_FIXED_8_8_ENCODING, A4_FIXED_8_8_WIDTH, A4_FIXED_8_8_SCALE) == (
        "unsigned-big-endian-q8.8",
        2,
        256,
    )
    assert A4_FIXED_8_8_RAW_MAX == 0x7FFF
    assert format_a4_fixed_8_8(A4_FIXED_8_8_RAW_MAX) == "127.99609375"
    assert parse_a4_fixed_8_8("127.99609375") == A4_FIXED_8_8_RAW_MAX


def test_calibration_value_parser_obeys_its_explicit_promoted_range() -> None:
    from dataclasses import replace

    from rytm_randomizer.data.analog_four_sysex_calibration import analog_four_sysex_calibration_for

    calibration = replace(
        analog_four_sysex_calibration_for("Filter1 Frequency"),
        screen_min="1",
        native_raw_min=256,
        screen_max="64",
        native_raw_max=16384,
    )
    assert calibration.parse_native_screen_value("1") == 256
    assert calibration.parse_native_screen_value("64") == 16384
    with pytest.raises(ValueError, match="unsupported screen value"):
        calibration.parse_native_screen_value("64.00390625")
    with pytest.raises(ValueError, match="unsupported screen value"):
        calibration.parse_native_screen_value("0.99609375")
