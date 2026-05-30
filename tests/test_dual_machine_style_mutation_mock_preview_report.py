"""Tests for passive dual-machine style mutation mock-preview report."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _rytm_snapshot():
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
        kit_name="RIGRYTM",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _blocked_rytm_snapshot():
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
        slot=7,
        kit_name="BLOCKEDRYTM",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _analog_four_snapshot(*, offsets_promoted: bool = True):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=2,
        kit_name="RIGA4",
        raw=b"\x00\x20\x3c\x07" + b"RIGA4".ljust(16, b"\x00"),
        offsets_promoted=offsets_promoted,
    )


def _framed_a4_payload(name: bytes = b"RIGA4") -> bytes:
    padded_name = name[:16].ljust(16, b"\x00")
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02])
    return bytes([0xF0]) + payload + bytes([0xF7])


def test_dual_machine_style_mutation_mock_preview_builds_ready_rig_plan():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
    )

    plan = build_dual_machine_style_mutation_mock_preview_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
        discovery_amount=45,
    )

    assert plan.style_key == "jose_core_techno"
    assert plan.discovery_amount == 45
    assert plan.discovery_band == "balanced"
    assert plan.mutation_depth == "groove"
    assert plan.rig_readiness == "ready"
    assert plan.rytm_preview_ready is True
    assert plan.analog_four_preview_ready is True
    assert plan.rytm_kit_name == "RIGRYTM"
    assert plan.rytm_ready_pad_count == 3
    assert plan.rytm_blocked_pad_count == 1
    assert plan.rytm_planned_pads == (1, 2, 3)
    assert plan.analog_four_kit_name == "RIGA4"
    assert plan.analog_four_ready_track_count == 4
    assert plan.analog_four_blocked_track_count == 0
    assert plan.analog_four_deferred_row_count == 4
    assert plan.analog_four_planned_tracks == (1, 2, 3, 4)
    assert plan.total_mock_message_count == (
        plan.rytm_mock_message_count + plan.analog_four_mock_message_count
    )
    assert plan.total_deferred_row_count == plan.analog_four_deferred_row_count


def test_dual_machine_style_mutation_mock_preview_marks_partial_when_a4_is_candidate_only():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
    )

    plan = build_dual_machine_style_mutation_mock_preview_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="jose_core_techno",
        discovery_amount=45,
    )

    assert plan.rig_readiness == "partial"
    assert plan.rytm_preview_ready is True
    assert plan.analog_four_preview_ready is False
    assert plan.total_mock_message_count == plan.rytm_mock_message_count
    assert plan.analog_four_mock_message_count == 0
    assert plan.analog_four_deferred_row_count == 12
    assert "candidate-only" in plan.analog_four_readiness_reason


def test_dual_machine_style_mutation_mock_preview_marks_blocked_when_no_mock_rows():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
        format_dual_machine_style_mutation_mock_preview_report,
    )

    plan = build_dual_machine_style_mutation_mock_preview_report(
        _blocked_rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="jose_core_techno",
        discovery_amount=45,
    )

    lines = format_dual_machine_style_mutation_mock_preview_report(
        plan,
        include_events=True,
    )

    assert plan.rig_readiness == "blocked"
    assert plan.rytm_preview_ready is False
    assert plan.analog_four_preview_ready is False
    assert plan.total_mock_message_count == 0
    assert "- No mock rows available because the rig preview is not ready." in lines


def test_dual_machine_style_mutation_mock_preview_formats_operator_report_with_events():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
        format_dual_machine_style_mutation_mock_preview_report,
    )

    plan = build_dual_machine_style_mutation_mock_preview_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
        discovery_amount=45,
    )

    lines = format_dual_machine_style_mutation_mock_preview_report(
        plan,
        include_events=True,
        event_limit=0,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive dual-machine style mutation mock preview"
    assert "Style target: jose_core_techno" in lines
    assert "Rig readiness: ready" in lines
    assert "Total mock messages: " in text
    assert "Rytm:" in lines
    assert "- Kit: RIGRYTM" in lines
    assert "- Preview ready: True" in lines
    assert "Analog Four:" in lines
    assert "- Kit: RIGA4" in lines
    assert "- Deferred rows: 4" in lines
    assert "Event preview:" in lines
    assert "- Showing all events" in lines
    assert "Rytm Pad 1 | profile 2 | grit | SRC Snap | ch 0 | CC21 -> 49" in text
    assert (
        "Analog Four Track 1 | bass_foundation | oscillator | OSC1 Level | ch 0 | CC69 -> 75"
        in text
    )
    assert "Deferred rows:" in lines
    assert "Analog Four Track 1 | bass_foundation | drive | NRPN-only A4 zone" in text
    assert "- mock-only dual-machine preview" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_dual_machine_style_mutation_mock_preview_can_hide_or_limit_events():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
        format_dual_machine_style_mutation_mock_preview_report,
    )

    plan = build_dual_machine_style_mutation_mock_preview_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
    )

    hidden_lines = format_dual_machine_style_mutation_mock_preview_report(
        plan,
        include_events=False,
    )
    limited_lines = format_dual_machine_style_mutation_mock_preview_report(
        plan,
        include_events=True,
        event_limit=1,
    )

    assert "Event preview:" not in hidden_lines
    assert "Deferred rows:" in hidden_lines
    assert "Event preview:" in limited_lines
    assert f"- Showing first 1 of {plan.total_event_row_count} events" in limited_lines
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_dual_machine_style_mutation_mock_preview_report(
            plan,
            include_events=True,
            event_limit=-1,
        )


def test_dual_machine_style_mutation_mock_preview_formats_empty_deferred_rows():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _deferred_preview_lines,
    )

    assert _deferred_preview_lines(()) == ["Deferred rows:", "- none"]


def test_dual_machine_style_mutation_mock_preview_serializes_json_contract():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
        to_dual_machine_style_mutation_mock_preview_json,
    )

    plan = build_dual_machine_style_mutation_mock_preview_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=True),
        style_key="jose_core_techno",
        discovery_amount=45,
    )

    payload = to_dual_machine_style_mutation_mock_preview_json(plan)

    assert payload["style_key"] == "jose_core_techno"
    assert payload["rig_readiness"] == "ready"
    assert payload["total_mock_message_count"] == plan.total_mock_message_count
    assert payload["total_deferred_row_count"] == 4
    assert payload["machines"]["rytm"]["kit_name"] == "RIGRYTM"
    assert payload["machines"]["rytm"]["events"][0]["parameter"] == "SRC Snap"
    assert payload["machines"]["analog_four"]["kit_name"] == "RIGA4"
    assert payload["machines"]["analog_four"]["events"][0]["parameter"] == "OSC1 Level"
    assert payload["machines"]["analog_four"]["deferred_rows"][0]["reason"].startswith("NRPN-only")
    assert payload["safety"][0] == "passive/read-only"


def test_dual_machine_style_mutation_mock_preview_rejects_unknown_style_key():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        build_dual_machine_style_mutation_mock_preview_report,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        build_dual_machine_style_mutation_mock_preview_report(
            _rytm_snapshot(),
            _analog_four_snapshot(),
            style_key="ghost_style",
        )


def test_dual_machine_style_mutation_mock_preview_cli_parser_accepts_options():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _parse_cli_args,
    )

    assert _parse_cli_args(["rytm.syx", "a4.syx", "jose_core_techno"]) == {
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "style_key": "jose_core_techno",
        "rytm_slot": 0,
        "analog_four_slot": 0,
        "discovery_amount": 45,
        "include_events": False,
        "event_limit": 24,
        "json_output": False,
    }
    assert _parse_cli_args(
        [
            "rytm.syx",
            "a4.syx",
            "birmingham_pressure",
            "--rytm-slot",
            "2",
            "--a4-slot",
            "1",
            "--discovery",
            "95",
            "--events",
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "style_key": "birmingham_pressure",
        "rytm_slot": 2,
        "analog_four_slot": 1,
        "discovery_amount": 95,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["rytm.syx", "a4.syx"], "usage"),
        (["rytm.syx", "a4.syx", "jose_core_techno", "--rytm-slot"], "usage"),
        (["rytm.syx", "a4.syx", "jose_core_techno", "--limit"], "usage"),
        (["rytm.syx", "a4.syx", "jose_core_techno", "--bank", "1"], "usage"),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--rytm-slot", "bad"],
            "--rytm-slot must be an integer",
        ),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--a4-slot", "-1"],
            "--a4-slot must be >= 0",
        ),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--limit", "-1"],
            "--limit must be >= 0",
        ),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--discovery", "bad"],
            "--discovery must be an integer",
        ),
        (
            ["rytm.syx", "a4.syx", "jose_core_techno", "--discovery", "101"],
            "discovery amount must be between 0 and 100",
        ),
    ],
)
def test_dual_machine_style_mutation_mock_preview_cli_parser_rejects_bad_args(
    argv,
    message,
):
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _parse_cli_args,
    )

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_dual_machine_style_mutation_mock_preview_cli_error_formatter_is_stable():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _format_cli_error,
    )

    assert _format_cli_error(ValueError("bad rig")) == "Error: bad rig"


def test_dual_machine_style_mutation_mock_preview_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _handle_cli_report,
    )

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"RIGRYTM") + bytes([0xF7])
    )
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(_framed_a4_payload(b"RIGA4"))

    rc = _handle_cli_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        style_key="jose_core_techno",
        rytm_slot=0,
        analog_four_slot=0,
        discovery_amount=45,
        include_events=True,
        event_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style mutation mock preview" in captured.out
    assert "- Kit: RIGRYTM" in captured.out
    assert "- Kit: RIGA4" in captured.out
    assert "Style target: jose_core_techno" in captured.out
    assert "Event preview:" in captured.out
    assert "- no MIDI sending" in captured.out
    assert captured.err == ""


def test_dual_machine_style_mutation_mock_preview_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _handle_cli_report,
    )

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"JSONRYTM") + bytes([0xF7])
    )
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(_framed_a4_payload(b"JSONA4"))

    rc = _handle_cli_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        style_key="jose_core_techno",
        rytm_slot=0,
        analog_four_slot=0,
        discovery_amount=95,
        include_events=False,
        event_limit=24,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["style_key"] == "jose_core_techno"
    assert payload["discovery_amount"] == 95
    assert payload["discovery_band"] == "wild_discovery"
    assert payload["machines"]["rytm"]["kit_name"] == "JSONRYTM"
    assert payload["machines"]["analog_four"]["kit_name"] == "JSONA4"
    assert "RytmRandomizer passive dual-machine" not in captured.out
    assert captured.err == ""


def test_dual_machine_style_mutation_mock_preview_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import (
        _handle_cli_report,
    )

    rc = _handle_cli_report(
        rytm_sysex_path=tmp_path / "missing-rytm.syx",
        analog_four_sysex_path=tmp_path / "missing-a4.syx",
        style_key="jose_core_techno",
        rytm_slot=0,
        analog_four_slot=0,
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
