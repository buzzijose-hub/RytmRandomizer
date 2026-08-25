import json
from pathlib import Path

import pytest

from rytm_randomizer.snapshot import Elektron7BitMaskOrder, pack_elektron_7bit

pytestmark = pytest.mark.fast


def _snapshot(*, offsets_promoted: bool = True):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=3,
        kit_name="A4MOCK",
        raw=b"\x00\x20\x3c\x07" + b"A4MOCK".ljust(16, b"\x00"),
        offsets_promoted=offsets_promoted,
    )


def _saved_kit_snapshot():
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_SNAPSHOT_LAYOUT_SAVED_KIT,
    )

    return AnalogFourKitSnapshot(
        slot=4,
        kit_name="REAL A4",
        raw=b"\x00\x20\x3c\x06",
        offsets_promoted=False,
        unpacked=b"\x52\x01\x01",
        snapshot_layout=A4_SNAPSHOT_LAYOUT_SAVED_KIT,
    )


def _framed_a4_payload(name: bytes = b"A4MOCK") -> bytes:
    padded_name = name[:16].ljust(16, b"\x00")
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02])
    return bytes([0xF0]) + payload + bytes([0xF7])


def _framed_a4_saved_kit_payload(name: bytes = b"REAL A4") -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_FAMILY_BYTE,
        A4_KIT_NAME_LENGTH,
        A4_KIT_NAME_OFFSET,
        A4_KIT_OBJECT_BYTE,
    )
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    prefix = ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE, 0x00, A4_KIT_OBJECT_BYTE, 0x01, 0x01, 0x00])
    unpacked = bytearray(A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH + 8)
    unpacked[A4_KIT_NAME_OFFSET : A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH] = name[
        :A4_KIT_NAME_LENGTH
    ].ljust(A4_KIT_NAME_LENGTH, b"\x00")
    payload = prefix + pack_elektron_7bit(
        bytes(unpacked),
        mask_order=Elektron7BitMaskOrder.MSB_FIRST,
    )
    return bytes([0xF0]) + payload + bytes([0xF7])


def _event_by_zone(preview, *, track: int, zone: str):
    return next(row for row in preview.event_rows if row.track == track and row.zone == zone)


def test_analog_four_style_mutation_mock_preview_builds_jose_core_cc_rows():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        build_analog_four_style_mutation_mock_preview,
    )

    preview = build_analog_four_style_mutation_mock_preview(
        _snapshot(offsets_promoted=True),
        "jose_core_techno",
        discovery_amount=45,
    )

    assert preview.kit_name == "A4MOCK"
    assert preview.slot == 3
    assert preview.style_key == "jose_core_techno"
    assert preview.discovery_amount == 45
    assert preview.discovery_band == "balanced"
    assert preview.mutation_depth == "groove"
    assert preview.preview_ready is True
    assert preview.readiness_reason == "ready"
    assert preview.ready_track_count == 4
    assert preview.blocked_track_count == 0
    assert preview.intent_row_count == 12
    assert preview.mock_message_count == 8
    assert preview.deferred_row_count == 4
    assert preview.planned_tracks == (1, 2, 3, 4)

    oscillator = _event_by_zone(preview, track=1, zone="oscillator")
    assert oscillator.parameter == "OSC1 Level"
    assert oscillator.channel == 0
    assert oscillator.control == 69
    assert oscillator.value == 75
    assert oscillator.target_bias == 75
    assert oscillator.target_direction == "higher"

    filter_row = _event_by_zone(preview, track=1, zone="filter")
    assert filter_row.parameter == "Filter 1 Frequency"
    assert filter_row.control == 18
    assert filter_row.value == 52
    assert filter_row.target_bias == 75
    assert filter_row.target_direction == "lower"


def test_analog_four_style_mutation_mock_preview_defers_nrpn_only_drive_rows():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        build_analog_four_style_mutation_mock_preview,
    )

    preview = build_analog_four_style_mutation_mock_preview(
        _snapshot(offsets_promoted=True),
        "jose_core_techno",
        discovery_amount=45,
    )

    assert all(row.zone == "drive" for row in preview.deferred_rows)
    assert {row.track for row in preview.deferred_rows} == {1, 2, 3, 4}
    assert all("NRPN-only" in row.reason for row in preview.deferred_rows)
    assert all(row.zone != "drive" for row in preview.event_rows)


def test_analog_four_style_mutation_mock_preview_blocks_candidate_offsets():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        build_analog_four_style_mutation_mock_preview,
    )

    preview = build_analog_four_style_mutation_mock_preview(
        _snapshot(offsets_promoted=False),
        "jose_core_techno",
        discovery_amount=45,
    )

    assert preview.preview_ready is False
    assert preview.readiness_reason == (
        "Analog Four offsets are candidate-only; promote offsets before mock CC preview"
    )
    assert preview.ready_track_count == 0
    assert preview.blocked_track_count == 4
    assert preview.event_rows == ()
    assert preview.mock_message_count == 0
    assert preview.deferred_row_count == 12
    assert {row.reason for row in preview.deferred_rows} == {
        "Analog Four offsets are candidate-only"
    }


def test_analog_four_style_mutation_mock_preview_explains_decoded_saved_kit_block():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        build_analog_four_style_mutation_mock_preview,
    )

    preview = build_analog_four_style_mutation_mock_preview(
        _saved_kit_snapshot(),
        "jose_core_techno",
        discovery_amount=45,
    )

    assert preview.preview_ready is False
    assert preview.snapshot_layout == "saved_kit"
    assert preview.readiness_reason == (
        "Analog Four saved-kit SysEx decoded; offsets remain candidate-only; "
        "promote offsets before mock CC preview"
    )
    assert preview.event_rows == ()
    assert preview.deferred_row_count == 12


def test_analog_four_style_mutation_mock_preview_rejects_bad_mock_metadata():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        _metadata_int,
        _metadata_str,
    )
    from rytm_randomizer.mock_midi import build_cc_message

    message = build_cc_message(
        0,
        18,
        52,
        metadata={"track": "one", "parameter": 3},
    )

    with pytest.raises(TypeError, match="metadata 'track' must be an int"):
        _metadata_int(message, "track")
    with pytest.raises(TypeError, match="metadata 'parameter' must be a str"):
        _metadata_str(message, "parameter")


def test_analog_four_style_mutation_mock_preview_rejects_unknown_style():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        build_analog_four_style_mutation_mock_preview,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        build_analog_four_style_mutation_mock_preview(_snapshot(), "ghost_style")


def test_analog_four_style_mutation_mock_preview_skips_blocked_tracks_and_center_targets():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        AnalogFourStyleMutationIntentPlan,
        AnalogFourStyleMutationIntentRow,
        AnalogFourStyleMutationTrackIntent,
    )
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        _plan_pairs,
        _render_mock_rows,
        _target_value,
    )

    row = AnalogFourStyleMutationIntentRow(
        zone="filter",
        mutation_depth="micro",
        target_bias=75,
        target_direction="center",
    )
    track = AnalogFourStyleMutationTrackIntent(
        track=1,
        role_key="blocked_bass",
        label="Blocked bass",
        route_ready=False,
        readiness_reason="not promoted",
        favored_zones=("filter",),
        mutation_depth="micro",
        intent_rows=(row,),
        intent_row_count=1,
    )
    plan = AnalogFourStyleMutationIntentPlan(
        kit_name="A4MOCK",
        slot=3,
        style_key="jose_core_techno",
        discovery_amount=45,
        discovery_band="balanced",
        mutation_depth="micro",
        ready_track_count=0,
        blocked_track_count=1,
        intent_row_count=1,
        tracks_by_track={1: track},
    )

    assert _target_value(row) == 64
    assert _plan_pairs(plan) == ()
    assert _render_mock_rows(snapshot=_snapshot(offsets_promoted=True), intent_plan=plan) == ()


def test_analog_four_style_mutation_mock_preview_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import (
        format_analog_four_style_mutation_mock_preview_report,
    )

    lines = format_analog_four_style_mutation_mock_preview_report(
        _snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
        discovery_amount=45,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Analog Four style mutation mock preview"
    assert "Kit: A4MOCK" in lines
    assert "Snapshot layout: candidate" in lines
    assert "Style target: jose_core_techno" in lines
    assert "Preview ready: True" in lines
    assert "- Mock messages: 8" in lines
    assert "- Deferred rows: 4" in lines
    assert "Event preview:" in lines
    assert "- Showing first 1 of 8 events" in lines
    assert "Track 1 | bass_foundation | oscillator | OSC1 Level | ch 0 | CC69 -> 75" in text
    assert "Deferred rows:" in lines
    assert "Track 1 | bass_foundation | drive | NRPN-only A4 zone; no CC mock row rendered" in text
    assert "- mock-only preview" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_analog_four_style_mutation_mock_preview_report_can_show_all_events_and_rejects_negative_limit():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import (
        format_analog_four_style_mutation_mock_preview_report,
    )

    lines = format_analog_four_style_mutation_mock_preview_report(
        _snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
        discovery_amount=45,
        include_events=True,
        event_limit=0,
    )

    assert "- Showing all events" in lines
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_analog_four_style_mutation_mock_preview_report(
            _snapshot(offsets_promoted=True),
            style_key="jose_core_techno",
            discovery_amount=45,
            include_events=True,
            event_limit=-1,
        )


def test_analog_four_style_mutation_mock_preview_report_can_hide_event_preview():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import (
        format_analog_four_style_mutation_mock_preview_report,
    )

    lines = format_analog_four_style_mutation_mock_preview_report(
        _snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
        discovery_amount=45,
        include_events=False,
    )

    assert "Event preview:" not in lines
    assert "Deferred rows:" in lines


def test_analog_four_style_mutation_mock_preview_report_formats_no_deferred_rows():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import (
        _deferred_preview_lines,
    )

    assert _deferred_preview_lines(()) == ["Deferred rows:", "- none"]


def test_analog_four_style_mutation_mock_preview_json_contract_is_deterministic():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        build_analog_four_style_mutation_mock_preview,
    )
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import (
        to_analog_four_style_mutation_mock_preview_json,
    )

    preview = build_analog_four_style_mutation_mock_preview(
        _snapshot(offsets_promoted=True),
        "jose_core_techno",
        discovery_amount=45,
    )
    payload = to_analog_four_style_mutation_mock_preview_json(preview)

    assert payload["kit_name"] == "A4MOCK"
    assert payload["snapshot_layout"] == "candidate"
    assert payload["style_key"] == "jose_core_techno"
    assert payload["preview_ready"] is True
    assert payload["mock_message_count"] == 8
    assert payload["events"][0] == {
        "track": 1,
        "role_key": "bass_foundation",
        "zone": "oscillator",
        "parameter": "OSC1 Level",
        "channel": 0,
        "control": 69,
        "value": 75,
        "target_bias": 75,
        "mutation_depth": "groove",
        "target_direction": "higher",
    }
    assert payload["deferred_rows"][0] == {
        "track": 1,
        "role_key": "bass_foundation",
        "zone": "drive",
        "target_bias": 91,
        "mutation_depth": "groove",
        "target_direction": "higher",
        "reason": "NRPN-only A4 zone; no CC mock row rendered",
    }
    assert payload["safety"][0] == "passive/read-only"


def test_analog_four_style_mutation_mock_preview_cli_parser_accepts_options():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _parse_cli_args

    assert _parse_cli_args(["kit.syx", "jose_core_techno"]) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "jose_core_techno",
        "slot": 0,
        "discovery_amount": 45,
        "include_events": False,
        "event_limit": 24,
        "json_output": False,
    }
    assert _parse_cli_args(
        [
            "kit.syx",
            "jose_core_techno",
            "--slot",
            "3",
            "--discovery",
            "95",
            "--events",
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "jose_core_techno",
        "slot": 3,
        "discovery_amount": 95,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["kit.syx"], "usage"),
        (["kit.syx", "jose_core_techno", "--slot"], "usage"),
        (["kit.syx", "jose_core_techno", "--limit"], "usage"),
        (["kit.syx", "jose_core_techno", "--unknown", "1"], "usage"),
        (["kit.syx", "jose_core_techno", "--slot", "nope"], "--slot must be an integer"),
        (["kit.syx", "jose_core_techno", "--slot", "-1"], "--slot must be >= 0"),
        (["kit.syx", "jose_core_techno", "--limit", "nope"], "--limit must be an integer"),
        (["kit.syx", "jose_core_techno", "--limit", "-1"], "--limit must be >= 0"),
        (
            ["kit.syx", "jose_core_techno", "--discovery", "nope"],
            "--discovery must be an integer",
        ),
        (
            ["kit.syx", "jose_core_techno", "--discovery", "101"],
            "discovery amount must be between 0 and 100",
        ),
    ],
)
def test_analog_four_style_mutation_mock_preview_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_analog_four_style_mutation_mock_preview_cli_handler_reports_candidate_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _handle_cli_report

    path = tmp_path / "a4.syx"
    path.write_bytes(_framed_a4_payload(b"A4JSON"))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="jose_core_techno",
        slot=0,
        discovery_amount=45,
        include_events=False,
        event_limit=24,
        json_output=True,
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert rc == 0
    assert result["kit_name"] == "A4JSON"
    assert result["style_key"] == "jose_core_techno"
    assert result["preview_ready"] is False
    assert result["mock_message_count"] == 0
    assert "candidate-only" in result["readiness_reason"]
    assert captured.err == ""


def test_analog_four_style_mutation_mock_preview_cli_handler_reports_candidate_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _handle_cli_report

    path = tmp_path / "a4.syx"
    path.write_bytes(_framed_a4_payload(b"A4TEXT"))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="jose_core_techno",
        slot=0,
        discovery_amount=45,
        include_events=True,
        event_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four style mutation mock preview" in captured.out
    assert "Kit: A4TEXT" in captured.out
    assert "Preview ready: False" in captured.out
    assert "candidate-only" in captured.out
    assert "- no MIDI sending" in captured.out
    assert "- no port opening" in captured.out
    assert captured.err == ""


def test_analog_four_style_mutation_mock_preview_cli_handler_reports_saved_kit_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _handle_cli_report

    path = tmp_path / "a4-saved-kit.syx"
    path.write_bytes(_framed_a4_saved_kit_payload(b"REAL A4"))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="jose_core_techno",
        slot=0,
        discovery_amount=45,
        include_events=True,
        event_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "Kit: REAL A4" in captured.out
    assert "Snapshot layout: saved_kit" in captured.out
    assert "saved-kit SysEx decoded" in captured.out
    assert "- no MIDI sending" in captured.out
    assert "- no port opening" in captured.out
    assert captured.err == ""


def test_analog_four_style_mutation_mock_preview_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        style_key="jose_core_techno",
        slot=0,
        discovery_amount=45,
        include_events=False,
        event_limit=24,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_analog_four_style_mutation_mock_preview_cli_error_formatter():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import _format_cli_error

    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"
