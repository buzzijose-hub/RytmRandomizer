import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _framed(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _framed_a4_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return _framed(payload)


def _bank_files(tmp_path: Path) -> tuple[Path, Path]:
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm-bank.syx"
    rytm_path.write_bytes(
        _framed(rytm_real_layout_kit_payload(name=b"RYTM ONE"))
        + _framed(rytm_real_layout_kit_payload(name=b"RYTM TWO"))
    )
    a4_path = tmp_path / "a4-bank.syx"
    a4_path.write_bytes(_framed_a4_payload(b"A4 ONE") + _framed_a4_payload(b"A4 TWO"))
    return rytm_path, a4_path


def test_dual_machine_style_kit_readiness_builds_recommended_pairings(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        build_dual_machine_style_kit_readiness_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_readiness_report(
        rytm_path,
        a4_path,
        "jose_core_techno",
    )

    assert report.style_key == "jose_core_techno"
    assert report.rytm_kit_count == 2
    assert report.analog_four_kit_count == 2
    assert report.pairing_count == 4
    assert report.ready_pair_count == 0
    assert report.partial_pair_count == 4
    assert report.blocked_pair_count == 0
    assert report.entries[0].rig_readiness == "partial"
    assert report.entries[0].rytm_kit_name == "RYTM ONE"
    assert report.entries[0].analog_four_kit_name == "A4 ONE"
    assert report.entries[0].rytm_preview_ready is True
    assert report.entries[0].analog_four_preview_ready is False
    assert report.entries[0].score > 0
    assert len(report.entries[0].rytm_payload_fingerprint) == 16
    assert len(report.entries[0].analog_four_payload_fingerprint) == 16


def test_dual_machine_style_kit_readiness_classifies_ready_and_blocked_pairs():
    from rytm_randomizer.reports.analog_four_style_kit_readiness import (
        AnalogFourStyleKitReadinessEntry,
    )
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        _entry_from_pair,
    )
    from rytm_randomizer.reports.rytm_style_kit_readiness import (
        RytmStyleKitReadinessEntry,
    )

    rytm_ready = RytmStyleKitReadinessEntry(
        slot=0,
        kit_name="RYTM READY",
        discovery_band="balanced",
        mutation_depth="groove",
        preview_ready=True,
        ready_pad_count=4,
        blocked_pad_count=8,
        render_event_count=8,
        mock_message_count=8,
        planned_pads=(1, 2),
        payload_fingerprint="1" * 16,
        readiness_reason="ready",
    )
    rytm_blocked = RytmStyleKitReadinessEntry(
        slot=1,
        kit_name="RYTM BLOCKED",
        discovery_band="balanced",
        mutation_depth="groove",
        preview_ready=False,
        ready_pad_count=0,
        blocked_pad_count=12,
        render_event_count=0,
        mock_message_count=0,
        planned_pads=(),
        payload_fingerprint="2" * 16,
        readiness_reason="blocked",
    )
    a4_ready = AnalogFourStyleKitReadinessEntry(
        slot=0,
        kit_name="A4 READY",
        snapshot_layout="saved_kit",
        discovery_band="balanced",
        mutation_depth="groove",
        preview_ready=True,
        ready_track_count=4,
        blocked_track_count=0,
        intent_row_count=8,
        mock_message_count=8,
        deferred_row_count=0,
        payload_fingerprint="3" * 16,
        readiness_reason="ready",
    )
    a4_blocked = AnalogFourStyleKitReadinessEntry(
        slot=1,
        kit_name="A4 BLOCKED",
        snapshot_layout="candidate",
        discovery_band="balanced",
        mutation_depth="groove",
        preview_ready=False,
        ready_track_count=0,
        blocked_track_count=4,
        intent_row_count=8,
        mock_message_count=0,
        deferred_row_count=8,
        payload_fingerprint="4" * 16,
        readiness_reason="blocked",
    )

    assert _entry_from_pair(rytm_ready, a4_ready).rig_readiness == "ready"
    assert _entry_from_pair(rytm_blocked, a4_blocked).rig_readiness == "blocked"


def test_dual_machine_style_kit_readiness_formats_limited_operator_report(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        build_dual_machine_style_kit_readiness_report,
        format_dual_machine_style_kit_readiness_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_readiness_report(
        rytm_path,
        a4_path,
        "jose_core_techno",
    )
    lines = format_dual_machine_style_kit_readiness_report(report, display_limit=2)
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive dual-machine style kit readiness"
    assert "Style target: jose_core_techno" in lines
    assert "Rytm kits: 2" in lines
    assert "Analog Four kits: 2" in lines
    assert "Pairings: 4" in lines
    assert "Ready pairings: 0" in lines
    assert "Partial pairings: 4" in lines
    assert "Shown pairings: 2" in lines
    assert "Truncated pairings: 2" in lines
    assert "- Rytm slot 0 RYTM ONE + A4 slot 0 A4 ONE | readiness partial" in text
    assert "A4 TWO" in text
    assert "- rig-level kit-bank readiness only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_dual_machine_style_kit_readiness_formats_empty_report(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        DualMachineStyleKitReadinessReport,
        format_dual_machine_style_kit_readiness_report,
    )

    report = DualMachineStyleKitReadinessReport(
        rytm_sysex_path=tmp_path / "rytm.syx",
        analog_four_sysex_path=tmp_path / "a4.syx",
        style_key="jose_core_techno",
        discovery_amount=45,
        rytm_kit_count=0,
        analog_four_kit_count=0,
        pairing_count=0,
        ready_pair_count=0,
        partial_pair_count=0,
        blocked_pair_count=0,
        entries=(),
    )
    lines = format_dual_machine_style_kit_readiness_report(report)

    assert "- none" in lines


def test_dual_machine_style_kit_readiness_rejects_negative_display_limit(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        build_dual_machine_style_kit_readiness_report,
        format_dual_machine_style_kit_readiness_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_readiness_report(
        rytm_path,
        a4_path,
        "jose_core_techno",
    )

    with pytest.raises(ValueError, match="display_limit must be >= 0"):
        format_dual_machine_style_kit_readiness_report(report, display_limit=-1)


def test_dual_machine_style_kit_readiness_json_is_deterministic(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        build_dual_machine_style_kit_readiness_report,
        to_dual_machine_style_kit_readiness_json,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_readiness_report(
        rytm_path,
        a4_path,
        "jose_core_techno",
        discovery_amount=45,
    )
    payload = to_dual_machine_style_kit_readiness_json(report, display_limit=1)

    assert payload["style_key"] == "jose_core_techno"
    assert payload["pairing_count"] == 4
    assert payload["shown_count"] == 1
    assert payload["truncated_count"] == 3
    assert payload["entries"][0]["rig_readiness"] == "partial"
    assert payload["entries"][0]["rytm"]["kit_name"] == "RYTM ONE"
    assert payload["entries"][0]["analog_four"]["kit_name"] == "A4 ONE"
    assert payload["safety"][0] == "passive/read-only"


def test_dual_machine_style_kit_readiness_cli_parser_accepts_options():
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import _parse_cli_args

    assert _parse_cli_args(["rytm.syx", "a4.syx", "jose_core_techno"]) == {
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "style_key": "jose_core_techno",
        "discovery_amount": 45,
        "display_limit": None,
        "json_output": False,
    }
    assert _parse_cli_args(
        [
            "rytm.syx",
            "a4.syx",
            "jose_core_techno",
            "--discovery",
            "95",
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "style_key": "jose_core_techno",
        "discovery_amount": 95,
        "display_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["rytm.syx", "a4.syx"], "usage"),
        (["rytm.syx", "a4.syx", "jose_core_techno", "--limit"], "usage"),
        (["rytm.syx", "a4.syx", "jose_core_techno", "--unknown", "1"], "usage"),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--limit", "bad"],
            "--limit must be an integer",
        ),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--limit", "-1"],
            "--limit must be >= 0",
        ),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--discovery", "bad"],
            "--discovery must be an integer",
        ),
    ],
)
def test_dual_machine_style_kit_readiness_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_dual_machine_style_kit_readiness_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import _handle_cli_report

    rytm_path, a4_path = _bank_files(tmp_path)
    rc = _handle_cli_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        style_key="jose_core_techno",
        discovery_amount=45,
        display_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style kit readiness" in captured.out
    assert "RYTM ONE" in captured.out
    assert "A4 ONE" in captured.out
    assert "RYTM TWO" not in captured.out
    assert captured.err == ""


def test_dual_machine_style_kit_readiness_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import _handle_cli_report

    rytm_path, a4_path = _bank_files(tmp_path)
    rc = _handle_cli_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        style_key="jose_core_techno",
        discovery_amount=45,
        display_limit=1,
        json_output=True,
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert rc == 0
    assert parsed["entries"][0]["rytm"]["kit_name"] == "RYTM ONE"
    assert parsed["entries"][0]["analog_four"]["kit_name"] == "A4 ONE"
    assert captured.err == ""


def test_dual_machine_style_kit_readiness_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import _handle_cli_report

    rc = _handle_cli_report(
        rytm_sysex_path=tmp_path / "missing-rytm.syx",
        analog_four_sysex_path=tmp_path / "missing-a4.syx",
        style_key="jose_core_techno",
        discovery_amount=45,
        display_limit=None,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err


def test_dual_machine_style_kit_readiness_cli_error_formatter():
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import (
        _format_cli_error,
    )

    assert _format_cli_error(ValueError("bad")) == "Error: bad"
