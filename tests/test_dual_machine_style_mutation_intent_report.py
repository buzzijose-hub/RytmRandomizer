"""Tests for passive dual-machine style mutation-intent report."""

from __future__ import annotations

import json
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


def _analog_four_snapshot(*, offsets_promoted: bool = False):
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


def test_dual_machine_style_mutation_intent_builds_partial_rig_plan():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        build_dual_machine_style_mutation_intent_report,
    )

    plan = build_dual_machine_style_mutation_intent_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="birmingham_pressure",
        discovery_amount=75,
    )

    assert plan.style_key == "birmingham_pressure"
    assert plan.discovery_amount == 75
    assert plan.discovery_band == "discovery"
    assert plan.mutation_depth == "strong"
    assert plan.machine_switching_allowed is True
    assert plan.rig_readiness == "partial"
    assert plan.rytm_kit_name == "RIGRYTM"
    assert plan.rytm_ready_pad_count == 3
    assert plan.rytm_blocked_pad_count == 1
    assert plan.rytm_intent_row_count > 0
    assert plan.analog_four_kit_name == "RIGA4"
    assert plan.analog_four_ready_track_count == 0
    assert plan.analog_four_blocked_track_count == 4
    assert plan.analog_four_intent_row_count == 16
    assert plan.analog_four_candidate_only is True
    assert plan.total_intent_row_count == (
        plan.rytm_intent_row_count + plan.analog_four_intent_row_count
    )


def test_dual_machine_style_mutation_intent_formats_operator_report():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        build_dual_machine_style_mutation_intent_report,
        format_dual_machine_style_mutation_intent_report,
    )

    plan = build_dual_machine_style_mutation_intent_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="birmingham_pressure",
        discovery_amount=10,
    )

    lines = format_dual_machine_style_mutation_intent_report(plan)

    assert lines[0] == "RytmRandomizer passive dual-machine style mutation intent"
    assert "Style target: birmingham_pressure" in lines
    assert "Discovery amount: 10" in lines
    assert "Discovery band: reference" in lines
    assert "Mutation depth: micro" in lines
    assert "Rig readiness: partial" in lines
    assert "Rytm:" in lines
    assert "- Kit: RIGRYTM" in lines
    assert "- Ready pads: 3" in lines
    assert "- Intent rows: " in "\n".join(lines)
    assert "Analog Four:" in lines
    assert "- Kit: RIGA4" in lines
    assert "- Ready tracks: 0" in lines
    assert "- Candidate-only A4 offsets: True" in lines
    assert "- style mutation intent metadata only" in lines
    assert "- no MIDI rendering" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_dual_machine_style_mutation_intent_serializes_json_contract():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        build_dual_machine_style_mutation_intent_report,
        to_dual_machine_style_mutation_intent_json,
    )

    plan = build_dual_machine_style_mutation_intent_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="birmingham_pressure",
        discovery_amount=75,
    )

    payload = to_dual_machine_style_mutation_intent_json(plan)

    assert payload["style_key"] == "birmingham_pressure"
    assert payload["mutation_depth"] == "strong"
    assert payload["rig_readiness"] == "partial"
    assert payload["total_intent_row_count"] == plan.total_intent_row_count
    assert payload["machines"]["rytm"]["kit_name"] == "RIGRYTM"
    assert payload["machines"]["rytm"]["ready_pad_count"] == 3
    assert payload["machines"]["rytm"]["pads"][0]["intent_rows"][0]["zone"] == "grit"
    assert payload["machines"]["analog_four"]["kit_name"] == "RIGA4"
    assert payload["machines"]["analog_four"]["ready_track_count"] == 0
    assert payload["machines"]["analog_four"]["tracks"][0]["intent_rows"][0] == {
        "zone": "drive",
        "mutation_depth": "strong",
        "target_bias": 94,
        "target_direction": "higher",
    }
    assert payload["safety"][0] == "passive/read-only"


def test_dual_machine_style_mutation_intent_marks_ready_when_both_machines_ready():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        AnalogFourStyleMutationIntentPlan,
    )
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        RytmStyleMutationIntentPlan,
    )
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        build_dual_machine_style_mutation_intent_report,
    )

    rytm_plan = RytmStyleMutationIntentPlan(
        kit_name="RYTMREADY",
        slot=1,
        style_key="detroit_minimal",
        discovery_amount=75,
        discovery_band="discovery",
        mutation_depth="strong",
        ready_pad_count=1,
        blocked_pad_count=0,
        intent_row_count=0,
        pads_by_pad=MappingProxyType({}),
    )
    analog_four_plan = AnalogFourStyleMutationIntentPlan(
        kit_name="A4READY",
        slot=2,
        style_key="detroit_minimal",
        discovery_amount=75,
        discovery_band="discovery",
        mutation_depth="strong",
        ready_track_count=1,
        blocked_track_count=0,
        intent_row_count=0,
        tracks_by_track=MappingProxyType({}),
    )

    plan = build_dual_machine_style_mutation_intent_report(
        rytm_plan,
        analog_four_plan,
        style_key="detroit_minimal",
    )

    assert plan.rig_readiness == "ready"
    assert plan.total_intent_row_count == 0
    assert plan.analog_four_candidate_only is False


def test_dual_machine_style_mutation_intent_marks_blocked_when_no_routes_are_ready():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        AnalogFourStyleMutationIntentPlan,
    )
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        RytmStyleMutationIntentPlan,
    )
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        build_dual_machine_style_mutation_intent_report,
    )

    rytm_plan = RytmStyleMutationIntentPlan(
        kit_name="RYTMBLOCKED",
        slot=1,
        style_key="detroit_minimal",
        discovery_amount=75,
        discovery_band="discovery",
        mutation_depth="strong",
        ready_pad_count=0,
        blocked_pad_count=1,
        intent_row_count=0,
        pads_by_pad=MappingProxyType({}),
    )
    analog_four_plan = AnalogFourStyleMutationIntentPlan(
        kit_name="A4BLOCKED",
        slot=2,
        style_key="detroit_minimal",
        discovery_amount=75,
        discovery_band="discovery",
        mutation_depth="strong",
        ready_track_count=0,
        blocked_track_count=1,
        intent_row_count=0,
        tracks_by_track=MappingProxyType({}),
    )

    plan = build_dual_machine_style_mutation_intent_report(
        rytm_plan,
        analog_four_plan,
        style_key="detroit_minimal",
    )

    assert plan.rig_readiness == "blocked"


def test_dual_machine_style_mutation_intent_rejects_unknown_style_key():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        build_dual_machine_style_mutation_intent_report,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        build_dual_machine_style_mutation_intent_report(
            _rytm_snapshot(),
            _analog_four_snapshot(),
            style_key="ghost_style",
        )


def test_dual_machine_style_mutation_intent_cli_parser_accepts_slots_and_json():
    from pathlib import Path

    from rytm_randomizer.reports.dual_machine_style_mutation_intent import _parse_cli_args

    assert _parse_cli_args(["rytm.syx", "a4.syx", "industrial_dark"]) == {
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "style_key": "industrial_dark",
        "rytm_slot": 0,
        "analog_four_slot": 0,
        "discovery_amount": 45,
        "json_output": False,
    }
    assert _parse_cli_args(
        [
            "rytm.syx",
            "a4.syx",
            "mills_hypnotic",
            "--rytm-slot",
            "2",
            "--a4-slot",
            "1",
            "--discovery",
            "10",
            "--json",
        ]
    ) == {
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "style_key": "mills_hypnotic",
        "rytm_slot": 2,
        "analog_four_slot": 1,
        "discovery_amount": 10,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["rytm.syx", "a4.syx"], "usage"),
        (["rytm.syx", "a4.syx", "industrial_dark", "--rytm-slot"], "usage"),
        (["rytm.syx", "a4.syx", "industrial_dark", "--discovery"], "usage"),
        (["rytm.syx", "a4.syx", "industrial_dark", "--bank", "1"], "usage"),
        (
            ["rytm.syx", "a4.syx", "industrial_dark", "--rytm-slot", "bad"],
            "--rytm-slot must be an integer",
        ),
        (
            ["rytm.syx", "a4.syx", "industrial_dark", "--a4-slot", "-1"],
            "--a4-slot must be >= 0",
        ),
        (
            ["rytm.syx", "a4.syx", "industrial_dark", "--discovery", "bad"],
            "--discovery must be an integer",
        ),
        (
            ["rytm.syx", "a4.syx", "industrial_dark", "--discovery", "101"],
            "discovery amount must be between 0 and 100",
        ),
    ],
)
def test_dual_machine_style_mutation_intent_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_dual_machine_style_mutation_intent_cli_error_formatter_is_stable():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import _format_cli_error

    assert _format_cli_error(ValueError("bad rig")) == "Error: bad rig"


def test_dual_machine_style_mutation_intent_cli_handler_reports_plan(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
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
        style_key="birmingham_pressure",
        rytm_slot=0,
        analog_four_slot=0,
        discovery_amount=10,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style mutation intent" in captured.out
    assert "- Kit: RIGRYTM" in captured.out
    assert "- Kit: RIGA4" in captured.out
    assert "Style target: birmingham_pressure" in captured.out
    assert "Discovery band: reference" in captured.out
    assert "Total intent rows:" in captured.out
    assert captured.err == ""


def test_dual_machine_style_mutation_intent_cli_handler_reports_json(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
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
        style_key="birmingham_pressure",
        rytm_slot=0,
        analog_four_slot=0,
        discovery_amount=95,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["style_key"] == "birmingham_pressure"
    assert payload["discovery_amount"] == 95
    assert payload["discovery_band"] == "wild_discovery"
    assert payload["machines"]["rytm"]["kit_name"] == "JSONRYTM"
    assert payload["machines"]["analog_four"]["kit_name"] == "JSONA4"
    assert "RytmRandomizer passive dual-machine" not in captured.out
    assert captured.err == ""


def test_dual_machine_style_mutation_intent_cli_handler_reports_errors(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import (
        _handle_cli_report,
    )

    rc = _handle_cli_report(
        rytm_sysex_path=tmp_path / "missing-rytm.syx",
        analog_four_sysex_path=tmp_path / "missing-a4.syx",
        style_key="industrial_dark",
        rytm_slot=0,
        analog_four_slot=0,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err
