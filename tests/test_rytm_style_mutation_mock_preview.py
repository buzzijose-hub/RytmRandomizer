import json
from pathlib import Path
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _style_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
                2: RytmSnapshotMachineFact(2, 3, 3, True, "promoted"),
                3: RytmSnapshotMachineFact(3, 32, 32, True, "promoted"),
                10: RytmSnapshotMachineFact(10, 10, 10, True, "promoted"),
            }
        ),
        promoted=True,
    )
    return RytmKitSnapshot(
        slot=4,
        kit_name="STYLEKIT",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _blocked_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                10: RytmSnapshotMachineFact(10, 10, 10, True, "promoted"),
            }
        ),
        promoted=True,
    )
    return RytmKitSnapshot(
        slot=6,
        kit_name="BLOCKED",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _framed_sysex(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _row_by_parameter(preview, *, pad: int, parameter: str):
    return next(row for row in preview.event_rows if row.pad == pad and row.parameter == parameter)


def test_style_mutation_mock_preview_builds_jose_core_mock_rows():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_mock_preview import (
        build_rytm_style_mutation_mock_preview,
    )

    preview = build_rytm_style_mutation_mock_preview(
        _style_snapshot(),
        "jose_core_techno",
        discovery_amount=45,
    )

    assert preview.kit_name == "STYLEKIT"
    assert preview.slot == 4
    assert preview.style_key == "jose_core_techno"
    assert preview.discovery_amount == 45
    assert preview.discovery_band == "balanced"
    assert preview.mutation_depth == "groove"
    assert preview.preview_ready is True
    assert preview.readiness_reason == "ready"
    assert preview.mock_message_count == preview.render_event_count
    assert preview.planned_pads == (1, 2, 3)

    snap = _row_by_parameter(preview, pad=1, parameter="SRC Snap")
    assert snap.zone == "grit"
    assert snap.profile_key == "2"
    assert snap.channel == 0
    assert snap.control == 21
    assert snap.value == 49
    assert snap.window_low == 41
    assert snap.window_high == 55
    assert snap.target_direction == "higher"


def test_style_mutation_mock_preview_excludes_blocked_selectable_only_pads():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_mock_preview import (
        build_rytm_style_mutation_mock_preview,
    )

    preview = build_rytm_style_mutation_mock_preview(
        _style_snapshot(),
        "jose_core_techno",
        discovery_amount=45,
    )

    assert preview.blocked_pad_count == 1
    assert 10 not in preview.planned_pads
    assert all(row.pad != 10 for row in preview.event_rows)


def test_style_mutation_mock_preview_handles_no_render_ready_rows():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_mock_preview import (
        build_rytm_style_mutation_mock_preview,
    )
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import (
        format_rytm_style_mutation_mock_preview_report,
    )

    preview = build_rytm_style_mutation_mock_preview(
        _blocked_snapshot(),
        "jose_core_techno",
        discovery_amount=45,
    )
    lines = format_rytm_style_mutation_mock_preview_report(
        preview,
        style_key="jose_core_techno",
        include_events=True,
    )

    assert preview.preview_ready is False
    assert preview.readiness_reason == "no style render events available"
    assert preview.planned_pads == ()
    assert preview.event_rows == ()
    assert "- Planned pads: none" in lines
    assert "- No mock rows available because the preview is not ready." in lines


def test_style_mutation_mock_preview_rejects_bad_mock_metadata():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_mock_preview import (
        _metadata_int,
        _metadata_str,
    )
    from rytm_randomizer.mock_midi import build_cc_message

    message = build_cc_message(
        0,
        1,
        2,
        metadata={"pad": "one", "parameter": 3},
    )

    with pytest.raises(TypeError, match="metadata 'pad' must be an int"):
        _metadata_int(message, "pad")
    with pytest.raises(TypeError, match="metadata 'parameter' must be a str"):
        _metadata_str(message, "parameter")


def test_style_mutation_mock_preview_rejects_unknown_style():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_mock_preview import (
        build_rytm_style_mutation_mock_preview,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        build_rytm_style_mutation_mock_preview(_style_snapshot(), "ghost_style")


def test_style_mutation_mock_preview_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import (
        format_rytm_style_mutation_mock_preview_report,
    )

    lines = format_rytm_style_mutation_mock_preview_report(
        _style_snapshot(),
        style_key="jose_core_techno",
        discovery_amount=45,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style mutation mock preview"
    assert "Kit: STYLEKIT" in lines
    assert "Style target: jose_core_techno" in lines
    assert "Preview ready: True" in lines
    assert "- Mock messages: " in text
    assert "Event preview:" in lines
    assert "- Showing first 1 of " in text
    assert "Pad 1 | profile 2 | grit | SRC Snap | ch 0 | CC21 -> 49" in text
    assert "window 41-55" in text
    assert "- mock-only preview" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_style_mutation_mock_preview_report_can_show_all_events_and_rejects_negative_limit():
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import (
        format_rytm_style_mutation_mock_preview_report,
    )

    lines = format_rytm_style_mutation_mock_preview_report(
        _style_snapshot(),
        style_key="jose_core_techno",
        discovery_amount=45,
        include_events=True,
        event_limit=0,
    )

    assert "- Showing all events" in lines
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_rytm_style_mutation_mock_preview_report(
            _style_snapshot(),
            style_key="jose_core_techno",
            discovery_amount=45,
            include_events=True,
            event_limit=-1,
        )


def test_style_mutation_mock_preview_json_contract_is_deterministic():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_mock_preview import (
        build_rytm_style_mutation_mock_preview,
    )
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import (
        to_rytm_style_mutation_mock_preview_json,
    )

    preview = build_rytm_style_mutation_mock_preview(
        _style_snapshot(),
        "jose_core_techno",
        discovery_amount=45,
    )
    payload = to_rytm_style_mutation_mock_preview_json(preview)

    assert payload["kit_name"] == "STYLEKIT"
    assert payload["style_key"] == "jose_core_techno"
    assert payload["preview_ready"] is True
    assert payload["mock_message_count"] == preview.mock_message_count
    assert payload["events"][0] == {
        "pad": 1,
        "profile_key": "2",
        "zone": "grit",
        "parameter": "SRC Snap",
        "channel": 0,
        "control": 21,
        "value": 49,
        "target_value": 49,
        "window_low": 41,
        "window_high": 55,
        "mutation_depth": "groove",
        "target_direction": "higher",
    }
    assert payload["safety"][0] == "passive/read-only"


def test_style_mutation_mock_preview_cli_parser_accepts_options():
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import _parse_cli_args

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
def test_style_mutation_mock_preview_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_style_mutation_mock_preview_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"MOCKJSON")
    path = tmp_path / "kit.syx"
    path.write_bytes(_framed_sysex(payload))

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
    assert result["kit_name"] == "MOCKJSON"
    assert result["style_key"] == "jose_core_techno"
    assert result["preview_ready"] is True
    assert captured.err == ""


def test_style_mutation_mock_preview_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"MOCKTEXT")
    path = tmp_path / "kit.syx"
    path.write_bytes(_framed_sysex(payload))

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
    assert "RytmRandomizer passive Rytm style mutation mock preview" in captured.out
    assert "Kit: MOCKTEXT" in captured.out
    assert "Preview ready: True" in captured.out
    assert "CC" in captured.out
    assert "- no MIDI sending" in captured.out
    assert "- no port opening" in captured.out
    assert captured.err == ""


def test_style_mutation_mock_preview_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import _handle_cli_report

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


def test_style_mutation_mock_preview_cli_error_formatter():
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import _format_cli_error

    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"
