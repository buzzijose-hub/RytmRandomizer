import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _framed(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _rytm_bank_file(tmp_path: Path) -> Path:
    from conftest import rytm_real_layout_kit_payload

    path = tmp_path / "rytm-bank.syx"
    path.write_bytes(
        _framed(rytm_real_layout_kit_payload(name=b"RYTM ONE"))
        + _framed(rytm_real_layout_kit_payload(name=b"RYTM TWO"))
    )
    return path


def test_rytm_snapshot_payload_fingerprint_is_stable():
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder import (
        AnalogRytmSnapshotDecoder,
        rytm_snapshot_payload_fingerprint,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        rytm_real_layout_kit_payload(name=b"FINGERPRINT"),
        slot=3,
    )

    first = rytm_snapshot_payload_fingerprint(snapshot)
    second = rytm_snapshot_payload_fingerprint(snapshot)

    assert first == second
    assert len(first) == 16
    assert int(first, 16) >= 0


def test_rytm_style_kit_readiness_builds_bank_sweep(tmp_path: Path):
    from rytm_randomizer.reports.rytm_style_kit_readiness import (
        build_rytm_style_kit_readiness_report,
    )

    report = build_rytm_style_kit_readiness_report(
        _rytm_bank_file(tmp_path),
        "jose_core_techno",
    )

    assert report.style_key == "jose_core_techno"
    assert report.kit_count == 2
    assert report.preview_ready_count == 2
    assert report.blocked_kit_count == 0
    assert [entry.slot for entry in report.entries] == [0, 1]
    assert [entry.kit_name for entry in report.entries] == ["RYTM ONE", "RYTM TWO"]
    assert report.entries[0].preview_ready is True
    assert report.entries[0].ready_pad_count > 0
    assert report.entries[0].mock_message_count > 0
    assert len(report.entries[0].payload_fingerprint) == 16
    assert report.entries[0].readiness_reason == "ready"


def test_rytm_style_kit_readiness_formats_limited_operator_report(tmp_path: Path):
    from rytm_randomizer.reports.rytm_style_kit_readiness import (
        build_rytm_style_kit_readiness_report,
        format_rytm_style_kit_readiness_report,
    )

    report = build_rytm_style_kit_readiness_report(
        _rytm_bank_file(tmp_path),
        "jose_core_techno",
    )
    lines = format_rytm_style_kit_readiness_report(report, display_limit=1)
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style kit readiness"
    assert "Style target: jose_core_techno" in lines
    assert "Supported kits: 2" in lines
    assert "Preview-ready kits: 2" in lines
    assert "Blocked kits: 0" in lines
    assert "Shown kits: 1" in lines
    assert "Truncated kits: 1" in lines
    assert "- Slot 0 | RYTM ONE | preview_ready True" in text
    assert "fingerprint " in text
    assert "RYTM TWO" not in text
    assert "- style/mock preview only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_rytm_style_kit_readiness_formats_empty_and_unplanned_entries(tmp_path: Path):
    from rytm_randomizer.reports.rytm_style_kit_readiness import (
        RytmStyleKitReadinessEntry,
        RytmStyleKitReadinessReport,
        format_rytm_style_kit_readiness_report,
    )

    empty_report = RytmStyleKitReadinessReport(
        sysex_path=tmp_path / "empty.syx",
        style_key="jose_core_techno",
        discovery_amount=45,
        kit_count=0,
        preview_ready_count=0,
        blocked_kit_count=0,
        entries=(),
    )
    empty_lines = format_rytm_style_kit_readiness_report(empty_report)

    blocked_report = RytmStyleKitReadinessReport(
        sysex_path=tmp_path / "blocked.syx",
        style_key="jose_core_techno",
        discovery_amount=45,
        kit_count=1,
        preview_ready_count=0,
        blocked_kit_count=1,
        entries=(
            RytmStyleKitReadinessEntry(
                slot=0,
                kit_name="BLOCKED",
                discovery_band="balanced",
                mutation_depth="groove",
                preview_ready=False,
                ready_pad_count=0,
                blocked_pad_count=12,
                render_event_count=0,
                mock_message_count=0,
                planned_pads=(),
                payload_fingerprint="0" * 16,
                readiness_reason="blocked",
            ),
        ),
    )
    blocked_lines = format_rytm_style_kit_readiness_report(blocked_report)

    assert "- none" in empty_lines
    assert "planned pads none" in "\n".join(blocked_lines)


def test_rytm_style_kit_readiness_rejects_negative_display_limit(tmp_path: Path):
    from rytm_randomizer.reports.rytm_style_kit_readiness import (
        build_rytm_style_kit_readiness_report,
        format_rytm_style_kit_readiness_report,
    )

    report = build_rytm_style_kit_readiness_report(
        _rytm_bank_file(tmp_path),
        "jose_core_techno",
    )

    with pytest.raises(ValueError, match="display_limit must be >= 0"):
        format_rytm_style_kit_readiness_report(report, display_limit=-1)


def test_rytm_style_kit_readiness_json_is_deterministic(tmp_path: Path):
    from rytm_randomizer.reports.rytm_style_kit_readiness import (
        build_rytm_style_kit_readiness_report,
        to_rytm_style_kit_readiness_json,
    )

    report = build_rytm_style_kit_readiness_report(
        _rytm_bank_file(tmp_path),
        "jose_core_techno",
        discovery_amount=45,
    )

    payload = to_rytm_style_kit_readiness_json(report, display_limit=1)

    assert payload["style_key"] == "jose_core_techno"
    assert payload["kit_count"] == 2
    assert payload["shown_count"] == 1
    assert payload["truncated_count"] == 1
    assert payload["entries"][0]["kit_name"] == "RYTM ONE"
    assert payload["entries"][0]["preview_ready"] is True
    assert payload["entries"][0]["mock_message_count"] == report.entries[0].mock_message_count
    assert payload["safety"][0] == "passive/read-only"


def test_rytm_style_kit_readiness_cli_parser_accepts_options():
    from rytm_randomizer.data.style_discovery import DEFAULT_STYLE_DISCOVERY_AMOUNT
    from rytm_randomizer.reports.rytm_style_kit_readiness import _parse_cli_args

    assert _parse_cli_args(["rytm.syx", "jose_core_techno"]) == {
        "sysex_path": Path("rytm.syx"),
        "style_key": "jose_core_techno",
        "discovery_amount": DEFAULT_STYLE_DISCOVERY_AMOUNT,
        "display_limit": None,
        "json_output": False,
    }
    assert _parse_cli_args(
        ["rytm.syx", "jose_core_techno", "--discovery", "95", "--limit", "0", "--json"]
    ) == {
        "sysex_path": Path("rytm.syx"),
        "style_key": "jose_core_techno",
        "discovery_amount": 95,
        "display_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["rytm.syx"], "usage"),
        (["rytm.syx", "jose_core_techno", "--limit"], "usage"),
        (["rytm.syx", "jose_core_techno", "--unknown", "1"], "usage"),
        (["rytm.syx", "jose_core_techno", "--limit", "bad"], "--limit must be an integer"),
        (["rytm.syx", "jose_core_techno", "--limit", "-1"], "--limit must be >= 0"),
        (
            ["rytm.syx", "jose_core_techno", "--discovery", "bad"],
            "--discovery must be an integer",
        ),
    ],
)
def test_rytm_style_kit_readiness_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.rytm_style_kit_readiness import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_rytm_style_kit_readiness_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.rytm_style_kit_readiness import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=_rytm_bank_file(tmp_path),
        style_key="jose_core_techno",
        discovery_amount=45,
        display_limit=1,
        json_output=True,
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert rc == 0
    assert parsed["entries"][0]["kit_name"] == "RYTM ONE"
    assert parsed["shown_count"] == 1
    assert captured.err == ""


def test_rytm_style_kit_readiness_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.rytm_style_kit_readiness import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        style_key="jose_core_techno",
        discovery_amount=45,
        display_limit=None,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err


def test_rytm_style_kit_readiness_cli_error_formatter():
    from rytm_randomizer.reports.rytm_style_kit_readiness import _format_cli_error

    assert _format_cli_error(ValueError("bad")) == "Error: bad"
