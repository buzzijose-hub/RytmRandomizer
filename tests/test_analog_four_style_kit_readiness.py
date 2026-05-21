import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _framed_a4_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return bytes([0xF0]) + payload + bytes([0xF7])


def _readiness_file(tmp_path: Path) -> Path:
    path = tmp_path / "a4-readiness.syx"
    path.write_bytes(_framed_a4_payload(b"A4 ONE") + _framed_a4_payload(b"A4 TWO"))
    return path


def test_analog_four_style_kit_readiness_builds_slot_sweep(tmp_path: Path):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import (
        build_analog_four_style_kit_readiness_report,
    )

    report = build_analog_four_style_kit_readiness_report(
        _readiness_file(tmp_path),
        "jose_core_techno",
    )

    assert report.style_key == "jose_core_techno"
    assert report.kit_count == 2
    assert report.preview_ready_count == 0
    assert report.blocked_kit_count == 2
    assert [entry.slot for entry in report.entries] == [0, 1]
    assert [entry.kit_name for entry in report.entries] == ["A4 ONE", "A4 TWO"]
    assert report.entries[0].preview_ready is False
    assert report.entries[0].blocked_track_count == 4
    assert report.entries[0].deferred_row_count > 0
    assert report.entries[0].readiness_reason == (
        "Analog Four offsets are candidate-only; promote offsets before mock CC preview"
    )


def test_analog_four_style_kit_readiness_text_is_operator_facing_and_limited(
    tmp_path: Path,
):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import (
        build_analog_four_style_kit_readiness_report,
        format_analog_four_style_kit_readiness_report,
    )

    report = build_analog_four_style_kit_readiness_report(
        _readiness_file(tmp_path),
        "jose_core_techno",
    )
    lines = format_analog_four_style_kit_readiness_report(report, display_limit=1)
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Analog Four style kit readiness"
    assert "Style target: jose_core_techno" in lines
    assert "Supported kits: 2" in lines
    assert "Preview-ready kits: 0" in lines
    assert "Blocked kits: 2" in lines
    assert "Shown kits: 1" in lines
    assert "Truncated kits: 1" in lines
    assert "- Slot 0 | A4 ONE | layout candidate | preview_ready False" in text
    assert "A4 TWO" not in text
    assert "- style/mock preview only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_analog_four_style_kit_readiness_rejects_negative_limit(tmp_path: Path):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import (
        build_analog_four_style_kit_readiness_report,
        format_analog_four_style_kit_readiness_report,
    )

    report = build_analog_four_style_kit_readiness_report(
        _readiness_file(tmp_path),
        "jose_core_techno",
    )

    with pytest.raises(ValueError, match="display_limit must be >= 0"):
        format_analog_four_style_kit_readiness_report(report, display_limit=-1)


def test_analog_four_style_kit_readiness_formats_empty_report_and_unlimited_json():
    from rytm_randomizer.reports.analog_four_style_kit_readiness import (
        AnalogFourStyleKitReadinessReport,
        format_analog_four_style_kit_readiness_report,
        to_analog_four_style_kit_readiness_json,
    )

    report = AnalogFourStyleKitReadinessReport(
        sysex_path=Path("empty-a4.syx"),
        style_key="jose_core_techno",
        discovery_amount=45,
        kit_count=0,
        preview_ready_count=0,
        blocked_kit_count=0,
        entries=(),
    )

    lines = format_analog_four_style_kit_readiness_report(report)
    payload = to_analog_four_style_kit_readiness_json(report, display_limit=0)

    assert "Shown kits: 0" in lines
    assert "Truncated kits: 0" in lines
    assert "- none" in lines
    assert payload["shown_count"] == 0
    assert payload["truncated_count"] == 0
    assert payload["entries"] == []


def test_analog_four_style_kit_readiness_json_is_deterministic(tmp_path: Path):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import (
        build_analog_four_style_kit_readiness_report,
        to_analog_four_style_kit_readiness_json,
    )

    report = build_analog_four_style_kit_readiness_report(
        _readiness_file(tmp_path),
        "jose_core_techno",
    )
    payload = to_analog_four_style_kit_readiness_json(report, display_limit=1)

    assert payload["style_key"] == "jose_core_techno"
    assert payload["kit_count"] == 2
    assert payload["shown_count"] == 1
    assert payload["truncated_count"] == 1
    assert payload["entries"] == [
        {
            "slot": 0,
            "kit_name": "A4 ONE",
            "snapshot_layout": "candidate",
            "discovery_band": report.entries[0].discovery_band,
            "mutation_depth": report.entries[0].mutation_depth,
            "preview_ready": False,
            "ready_track_count": 0,
            "blocked_track_count": 4,
            "intent_row_count": report.entries[0].intent_row_count,
            "mock_message_count": 0,
            "deferred_row_count": report.entries[0].deferred_row_count,
            "readiness_reason": report.entries[0].readiness_reason,
        }
    ]
    assert payload["safety"][0] == "passive/read-only"


def test_analog_four_style_kit_readiness_cli_parser_accepts_options():
    from rytm_randomizer.data.style_discovery import DEFAULT_STYLE_DISCOVERY_AMOUNT
    from rytm_randomizer.reports.analog_four_style_kit_readiness import _parse_cli_args

    assert _parse_cli_args(["a4.syx", "jose_core_techno"]) == {
        "sysex_path": Path("a4.syx"),
        "style_key": "jose_core_techno",
        "discovery_amount": DEFAULT_STYLE_DISCOVERY_AMOUNT,
        "display_limit": None,
        "json_output": False,
    }
    assert _parse_cli_args(
        ["a4.syx", "jose_core_techno", "--discovery", "75", "--limit", "0", "--json"]
    ) == {
        "sysex_path": Path("a4.syx"),
        "style_key": "jose_core_techno",
        "discovery_amount": 75,
        "display_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["a4.syx"], "usage"),
        (["a4.syx", "jose_core_techno", "--limit"], "usage"),
        (["a4.syx", "jose_core_techno", "--unknown", "1"], "usage"),
        (["a4.syx", "jose_core_techno", "--limit", "nope"], "--limit must be an integer"),
        (["a4.syx", "jose_core_techno", "--limit", "-1"], "--limit must be >= 0"),
        (
            ["a4.syx", "jose_core_techno", "--discovery", "nope"],
            "--discovery must be an integer",
        ),
    ],
)
def test_analog_four_style_kit_readiness_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_analog_four_style_kit_readiness_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=_readiness_file(tmp_path),
        style_key="jose_core_techno",
        discovery_amount=50,
        display_limit=1,
        json_output=True,
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert rc == 0
    assert parsed["entries"][0]["kit_name"] == "A4 ONE"
    assert parsed["shown_count"] == 1
    assert parsed["truncated_count"] == 1
    assert captured.err == ""


def test_analog_four_style_kit_readiness_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=_readiness_file(tmp_path),
        style_key="jose_core_techno",
        discovery_amount=50,
        display_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four style kit readiness" in captured.out
    assert "A4 ONE" in captured.out
    assert "A4 TWO" not in captured.out
    assert captured.err == ""


def test_analog_four_style_kit_readiness_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_kit_readiness import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        style_key="jose_core_techno",
        discovery_amount=50,
        display_limit=None,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_analog_four_style_kit_readiness_cli_error_formatter_is_plain_error():
    from rytm_randomizer.reports.analog_four_style_kit_readiness import _format_cli_error

    assert _format_cli_error(ValueError("bad readiness")) == "Error: bad readiness"
