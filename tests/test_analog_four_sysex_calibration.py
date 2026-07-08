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


def test_sysex_calibration_mapping_is_reexported_from_data_layer() -> None:
    from rytm_randomizer.data import ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS as MODULE_FIELD_CALIBRATIONS,
    )

    assert "Filter1 Frequency" in ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS
    assert ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS is MODULE_FIELD_CALIBRATIONS


@pytest.mark.parametrize("track", [0, 5])
def test_sysex_calibration_rejects_tracks_outside_a4_synth_range(track: int) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    calibration = analog_four_sysex_calibration_for("Filter1 Frequency")

    with pytest.raises(ValueError, match="track must be in 1..4"):
        calibration.primary_raw_offset_for_track(track)


def test_sysex_calibration_rejects_unknown_parameters() -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )

    with pytest.raises(KeyError, match="Unknown Analog Four SysEx calibration"):
        analog_four_sysex_calibration_for("Filter1 Resonance")
