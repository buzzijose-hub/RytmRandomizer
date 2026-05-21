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


def test_dual_machine_style_kit_selection_defaults_to_dual_when_both_paths(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert report.scope == "dual"
    assert report.style_key == "jose_core_techno"
    assert report.candidate_count == 4
    assert report.ready_selection_count == 0
    assert report.partial_selection_count == 4
    assert report.blocked_selection_count == 0
    assert report.entries[0].selection_readiness == "partial"
    assert report.entries[0].rytm_choice is not None
    assert report.entries[0].rytm_choice.slot == 0
    assert report.entries[0].rytm_choice.kit_name == "RYTM ONE"
    assert report.entries[0].rytm_choice.preview_ready is True
    assert report.entries[0].analog_four_choice is not None
    assert report.entries[0].analog_four_choice.slot == 0
    assert report.entries[0].analog_four_choice.kit_name == "A4 ONE"
    assert report.entries[0].analog_four_choice.preview_ready is False
    assert "Use the Rytm snapshot now" in report.entries[0].operator_action


def test_dual_machine_style_kit_selection_supports_rytm_only_scope(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
    )

    rytm_path, _ = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )

    assert report.scope == "rytm-only"
    assert report.rytm_sysex_path == rytm_path
    assert report.analog_four_sysex_path is None
    assert report.candidate_count == 2
    assert report.ready_selection_count == 2
    assert report.partial_selection_count == 0
    assert report.blocked_selection_count == 0
    assert report.entries[0].selection_readiness == "ready"
    assert report.entries[0].rytm_choice is not None
    assert report.entries[0].rytm_choice.kit_name == "RYTM ONE"
    assert report.entries[0].analog_four_choice is None
    assert "leave Analog Four unchanged" in report.entries[0].operator_action


def test_dual_machine_style_kit_selection_supports_a4_only_alias(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
    )

    _, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
    )

    assert report.scope == "analog-four-only"
    assert report.rytm_sysex_path is None
    assert report.analog_four_sysex_path == a4_path
    assert report.candidate_count == 2
    assert report.ready_selection_count == 0
    assert report.partial_selection_count == 0
    assert report.blocked_selection_count == 2
    assert report.entries[0].selection_readiness == "blocked"
    assert report.entries[0].rytm_choice is None
    assert report.entries[0].analog_four_choice is not None
    assert report.entries[0].analog_four_choice.kit_name == "A4 ONE"
    assert "leave Rytm unchanged" in report.entries[0].operator_action


def test_dual_machine_style_kit_selection_auto_detects_a4_only_scope(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
    )

    _, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        analog_four_sysex_path=a4_path,
    )

    assert report.scope == "analog-four-only"
    assert report.candidate_count == 2


def test_dual_machine_style_kit_selection_covers_ready_and_blocked_actions():
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        StyleKitSelectionMachineChoice,
        _dual_operator_action,
        _entry_from_analog_four_choice,
        _entry_from_rytm_choice,
    )

    rytm_ready = StyleKitSelectionMachineChoice(
        device="rytm",
        slot=1,
        kit_name="RYTM READY",
        preview_ready=True,
        ready_unit_count=12,
        blocked_unit_count=0,
        mock_message_count=48,
        deferred_row_count=0,
        payload_fingerprint="1" * 16,
        readiness_reason="ready",
    )
    rytm_blocked = StyleKitSelectionMachineChoice(
        device="rytm",
        slot=2,
        kit_name="RYTM BLOCKED",
        preview_ready=False,
        ready_unit_count=0,
        blocked_unit_count=12,
        mock_message_count=0,
        deferred_row_count=0,
        payload_fingerprint="2" * 16,
        readiness_reason="blocked",
    )
    a4_ready = StyleKitSelectionMachineChoice(
        device="analog-four",
        slot=3,
        kit_name="A4 READY",
        preview_ready=True,
        ready_unit_count=4,
        blocked_unit_count=0,
        mock_message_count=16,
        deferred_row_count=0,
        payload_fingerprint="3" * 16,
        readiness_reason="ready",
    )
    a4_blocked = StyleKitSelectionMachineChoice(
        device="analog-four",
        slot=4,
        kit_name="A4 BLOCKED",
        preview_ready=False,
        ready_unit_count=0,
        blocked_unit_count=4,
        mock_message_count=0,
        deferred_row_count=8,
        payload_fingerprint="4" * 16,
        readiness_reason="blocked",
    )

    assert _dual_operator_action(rytm_ready, a4_ready) == (
        "Select both snapshots; both machines are preview-ready."
    )
    assert "Use the Analog Four snapshot now" in _dual_operator_action(
        rytm_blocked,
        a4_ready,
    )
    assert _dual_operator_action(rytm_blocked, a4_blocked) == (
        "Do not automate this pair yet; both machine snapshots are blocked."
    )
    assert (
        "Do not automate this Rytm snapshot yet"
        in _entry_from_rytm_choice(rytm_blocked).operator_action
    )
    assert "mutate A4 only" in _entry_from_analog_four_choice(a4_ready).operator_action


def test_dual_machine_style_kit_selection_formats_operator_report(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
        format_dual_machine_style_kit_selection_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    lines = format_dual_machine_style_kit_selection_report(report, display_limit=1)
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive dual-machine style kit selection"
    assert "Scope: dual" in lines
    assert "Style target: jose_core_techno" in lines
    assert "Candidates: 4" in lines
    assert "Partial selections: 4" in lines
    assert "Shown selections: 1" in lines
    assert "Truncated selections: 3" in lines
    assert "- Scope dual | readiness partial" in text
    assert "Rytm slot 0 RYTM ONE" in text
    assert "A4 slot 0 A4 ONE" in text
    assert "fingerprints " in text
    assert "- operator selection only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_dual_machine_style_kit_selection_formats_empty_and_unusual_reports(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        DualMachineStyleKitSelectionEntry,
        DualMachineStyleKitSelectionReport,
        format_dual_machine_style_kit_selection_report,
    )

    empty_report = DualMachineStyleKitSelectionReport(
        style_key="jose_core_techno",
        discovery_amount=45,
        scope="dual",
        rytm_sysex_path=tmp_path / "rytm.syx",
        analog_four_sysex_path=tmp_path / "a4.syx",
        candidate_count=0,
        ready_selection_count=0,
        partial_selection_count=0,
        blocked_selection_count=0,
        entries=(),
    )
    unusual_report = DualMachineStyleKitSelectionReport(
        style_key="jose_core_techno",
        discovery_amount=45,
        scope="dual",
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        candidate_count=1,
        ready_selection_count=0,
        partial_selection_count=0,
        blocked_selection_count=1,
        entries=(
            DualMachineStyleKitSelectionEntry(
                scope="dual",
                selection_readiness="blocked",
                score=0,
                operator_action="manual inspection",
                rytm_choice=None,
                analog_four_choice=None,
            ),
        ),
    )

    empty_lines = format_dual_machine_style_kit_selection_report(empty_report)
    unusual_text = "\n".join(format_dual_machine_style_kit_selection_report(unusual_report))

    assert "- none" in empty_lines
    assert "Rytm unchanged" in unusual_text
    assert "A4 unchanged" in unusual_text
    assert "fingerprints none" in unusual_text


def test_dual_machine_style_kit_selection_rejects_negative_display_limit(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
        format_dual_machine_style_kit_selection_report,
    )

    rytm_path, _ = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
    )

    with pytest.raises(ValueError, match="display_limit must be >= 0"):
        format_dual_machine_style_kit_selection_report(report, display_limit=-1)


def test_dual_machine_style_kit_selection_json_is_deterministic(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import (
        build_dual_machine_style_kit_selection_report,
        to_dual_machine_style_kit_selection_json,
    )

    rytm_path, _ = _bank_files(tmp_path)
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        discovery_amount=65,
    )
    payload = to_dual_machine_style_kit_selection_json(report, display_limit=1)

    assert payload["scope"] == "rytm-only"
    assert payload["style_key"] == "jose_core_techno"
    assert payload["discovery_amount"] == 65
    assert payload["candidate_count"] == 2
    assert payload["shown_count"] == 1
    assert payload["truncated_count"] == 1
    assert payload["entries"][0]["selection_readiness"] == "ready"
    assert payload["entries"][0]["rytm"]["kit_name"] == "RYTM ONE"
    assert payload["entries"][0]["analog_four"] is None
    assert payload["safety"][0] == "passive/read-only"


def test_dual_machine_style_kit_selection_cli_parser_accepts_scopes():
    from rytm_randomizer.data.style_discovery import DEFAULT_STYLE_DISCOVERY_AMOUNT
    from rytm_randomizer.reports.dual_machine_style_kit_selection import _parse_cli_args

    assert _parse_cli_args(
        ["jose_core_techno", "--rytm", "rytm.syx", "--analog-four", "a4.syx"]
    ) == {
        "style_key": "jose_core_techno",
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "discovery_amount": DEFAULT_STYLE_DISCOVERY_AMOUNT,
        "display_limit": None,
        "json_output": False,
    }
    assert _parse_cli_args(
        [
            "jose_core_techno",
            "--rytm",
            "rytm.syx",
            "--scope",
            "rytm-only",
            "--discovery",
            "75",
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "style_key": "jose_core_techno",
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": None,
        "scope": "rytm-only",
        "discovery_amount": 75,
        "display_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["jose_core_techno"], "requires at least one"),
        (["jose_core_techno", "--scope", "weird"], "unsupported scope"),
        (["jose_core_techno", "--scope", "dual", "--rytm", "rytm.syx"], "requires --analog-four"),
        (
            ["jose_core_techno", "--scope", "rytm-only", "--analog-four", "a4.syx"],
            "requires --rytm",
        ),
        (
            ["jose_core_techno", "--scope", "a4-only", "--rytm", "rytm.syx"],
            "requires --analog-four",
        ),
        (["--style", "--rytm", "rytm.syx"], "usage"),
        (["jose_core_techno", "--rytm"], "usage"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--bogus", "x"], "usage"),
        (
            ["jose_core_techno", "--rytm", "rytm.syx", "--discovery", "bad"],
            "must be an integer",
        ),
        (["jose_core_techno", "--rytm", "rytm.syx", "--limit", "bad"], "must be an integer"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--limit", "-1"], "must be >= 0"),
    ],
)
def test_dual_machine_style_kit_selection_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_dual_machine_style_kit_selection_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import _handle_cli_report

    rytm_path, _ = _bank_files(tmp_path)
    rc = _handle_cli_report(
        style_key="jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        discovery_amount=45,
        display_limit=1,
        json_output=True,
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert rc == 0
    assert parsed["scope"] == "rytm-only"
    assert parsed["entries"][0]["rytm"]["kit_name"] == "RYTM ONE"
    assert parsed["entries"][0]["analog_four"] is None
    assert captured.err == ""


def test_dual_machine_style_kit_selection_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import _handle_cli_report

    rytm_path, a4_path = _bank_files(tmp_path)
    rc = _handle_cli_report(
        style_key="jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope="dual",
        discovery_amount=45,
        display_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style kit selection" in captured.out
    assert "Rytm slot 0 RYTM ONE" in captured.out
    assert "A4 slot 0 A4 ONE" in captured.out
    assert captured.err == ""


def test_dual_machine_style_kit_selection_cli_handler_reports_errors(capsys):
    from rytm_randomizer.reports.dual_machine_style_kit_selection import _handle_cli_report

    rc = _handle_cli_report(
        style_key="jose_core_techno",
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope="dual",
        discovery_amount=45,
        display_limit=None,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert "requires --rytm" in captured.err


def test_dual_machine_style_kit_selection_cli_error_formatter():
    from rytm_randomizer.reports.dual_machine_style_kit_selection import _format_cli_error

    assert _format_cli_error(ValueError("bad selection")) == "Error: bad selection"
