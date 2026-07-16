"""Tests for promoted Analog Four SysEx calibration facts."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_filter1_frequency_calibration_records_promoted_track_stride() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")

    assert calibration.parameter == "Filter1 Frequency"
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
    assert {row.kit_name for row in calibration.evidence} == {"KIT 1"}
    assert all(row.source_file.endswith("_Kit.syx") for row in calibration.evidence)
    assert all(len(row.payload_fingerprint) == 16 for row in calibration.evidence)


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
        A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter2 Resonance")

    assert calibration.parameter == "Filter2 Resonance"
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


def test_sysex_calibration_mapping_is_reexported_from_data_layer() -> None:
    from rytm_randomizer.data import ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS
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


@pytest.mark.parametrize("track", [0, 5])
def test_sysex_calibration_rejects_tracks_outside_a4_synth_range(track: int) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Resonance")

    with pytest.raises(ValueError, match="track must be in 1..4"):
        calibration.primary_raw_offset_for_track(track)


def test_sysex_calibration_rejects_unknown_parameters() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    with pytest.raises(KeyError, match="Unknown Analog Four SysEx calibration"):
        analog_four_sysex_calibration_for("Filter1 Width")
