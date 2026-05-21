"""Tests for passive dual-machine style snapshot routing report."""

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
        kit_name="RYTMSTYLE",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _analog_four_snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=2,
        kit_name="A4STYLE",
        raw=b"\x00\x20\x3c\x07" + b"A4STYLE".ljust(16, b"\x00"),
        offsets_promoted=offsets_promoted,
    )


def _framed_a4_payload(name: bytes = b"A4STYLE") -> bytes:
    padded_name = name[:16].ljust(16, b"\x00")
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02])
    return bytes([0xF0]) + payload + bytes([0xF7])


def test_dual_machine_style_routing_builds_partial_rig_plan():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
    )

    plan = build_dual_machine_style_snapshot_routing_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="industrial_dark",
        discovery_amount=10,
    )

    assert plan.style_key == "industrial_dark"
    assert plan.discovery_amount == 10
    assert plan.discovery_band == "reference"
    assert plan.machine_switching_allowed is False
    assert plan.rytm_kit_name == "RYTMSTYLE"
    assert plan.rytm_ready_pad_count == 3
    assert plan.analog_four_kit_name == "A4STYLE"
    assert plan.analog_four_ready_track_count == 0
    assert plan.analog_four_candidate_only is True
    assert plan.rig_readiness == "partial"
    assert "grit" in plan.favored_zones


def test_dual_machine_style_routing_formats_operator_report():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
        format_dual_machine_style_snapshot_routing_report,
    )

    plan = build_dual_machine_style_snapshot_routing_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="birmingham_pressure",
    )

    lines = format_dual_machine_style_snapshot_routing_report(plan)

    assert lines[0] == "RytmRandomizer passive dual-machine style snapshot routing"
    assert "Style target: birmingham_pressure" in lines
    assert "Discovery amount: 45" in lines
    assert "Discovery band: balanced" in lines
    assert "Machine switching allowed: False" in lines
    assert "Rig readiness: partial" in lines
    assert "Rytm:" in lines
    assert "- Kit: RYTMSTYLE" in lines
    assert "- Ready pads: 3" in lines
    assert "Analog Four:" in lines
    assert "- Kit: A4STYLE" in lines
    assert "- Ready tracks: 0" in lines
    assert "- Candidate-only A4 offsets: True" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_dual_machine_style_routing_serializes_json_contract():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
        to_dual_machine_style_snapshot_routing_json,
    )

    plan = build_dual_machine_style_snapshot_routing_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=False),
        style_key="industrial_dark",
    )

    payload = to_dual_machine_style_snapshot_routing_json(plan)

    assert payload["style_key"] == "industrial_dark"
    assert payload["discovery_amount"] == 45
    assert payload["discovery_band"] == "balanced"
    assert payload["machine_switching_allowed"] is False
    assert payload["rig_readiness"] == "partial"
    assert payload["machines"] == {
        "analog_four": {
            "blocked_track_count": 4,
            "candidate_only_offsets": True,
            "kit_name": "A4STYLE",
            "partial_snapshot_mutation_ready": False,
            "ready_track_count": 0,
            "slot": 2,
        },
        "rytm": {
            "blocked_pad_count": 1,
            "kit_name": "RYTMSTYLE",
            "partial_snapshot_mutation_ready": True,
            "ready_pad_count": 3,
            "slot": 4,
        },
    }
    assert payload["safety"][0] == "passive/read-only"


def test_dual_machine_style_routing_marks_fully_ready_when_both_machines_ready():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
    )

    plan = build_dual_machine_style_snapshot_routing_report(
        _rytm_snapshot(),
        _analog_four_snapshot(offsets_promoted=True),
        style_key="deep_dark_hypnosis",
    )

    assert plan.analog_four_ready_track_count == 4
    assert plan.rig_readiness == "partial"


def test_dual_machine_style_routing_formats_ready_plan_with_empty_zones():
    from rytm_randomizer.devices.strategies import (
        AnalogFourStyleSnapshotRoutingPlan,
        RytmStyleSnapshotRoutingPlan,
    )
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
        format_dual_machine_style_snapshot_routing_report,
    )

    rytm_plan = RytmStyleSnapshotRoutingPlan(
        kit_name="RYTMREADY",
        slot=1,
        style_key="detroit_minimal",
        discovery_amount=75,
        discovery_band="discovery",
        machine_switching_allowed=True,
        favored_zones=(),
        ready_pad_count=1,
        blocked_pad_count=0,
        partial_snapshot_mutation_ready=True,
        pads_by_pad=MappingProxyType({}),
    )
    analog_four_plan = AnalogFourStyleSnapshotRoutingPlan(
        kit_name="A4READY",
        slot=2,
        style_key="detroit_minimal",
        style_focus=(),
        discovery_amount=75,
        discovery_band="discovery",
        machine_switching_allowed=True,
        favored_zones=(),
        ready_track_count=1,
        blocked_track_count=0,
        partial_snapshot_mutation_ready=True,
        tracks_by_track=MappingProxyType({}),
    )

    plan = build_dual_machine_style_snapshot_routing_report(
        rytm_plan,
        analog_four_plan,
        style_key="detroit_minimal",
    )
    lines = format_dual_machine_style_snapshot_routing_report(plan)

    assert plan.rig_readiness == "ready"
    assert "Favored zones: none" in lines
    assert "- Candidate-only A4 offsets: False" in lines


def test_dual_machine_style_routing_marks_blocked_when_no_routes_are_ready():
    from rytm_randomizer.devices.strategies import (
        AnalogFourStyleSnapshotRoutingPlan,
        RytmStyleSnapshotRoutingPlan,
    )
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
    )

    rytm_plan = RytmStyleSnapshotRoutingPlan(
        kit_name="RYTMBLOCKED",
        slot=1,
        style_key="detroit_minimal",
        discovery_amount=75,
        discovery_band="discovery",
        machine_switching_allowed=True,
        favored_zones=("filter",),
        ready_pad_count=0,
        blocked_pad_count=1,
        partial_snapshot_mutation_ready=False,
        pads_by_pad=MappingProxyType({}),
    )
    analog_four_plan = AnalogFourStyleSnapshotRoutingPlan(
        kit_name="A4BLOCKED",
        slot=2,
        style_key="detroit_minimal",
        style_focus=(),
        discovery_amount=75,
        discovery_band="discovery",
        machine_switching_allowed=True,
        favored_zones=("effects",),
        ready_track_count=0,
        blocked_track_count=1,
        partial_snapshot_mutation_ready=False,
        tracks_by_track=MappingProxyType({}),
    )

    plan = build_dual_machine_style_snapshot_routing_report(
        rytm_plan,
        analog_four_plan,
        style_key="detroit_minimal",
    )

    assert plan.rig_readiness == "blocked"
    assert plan.favored_zones == ("filter", "effects")


def test_dual_machine_style_routing_rejects_unknown_style_key():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
        build_dual_machine_style_snapshot_routing_report,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        build_dual_machine_style_snapshot_routing_report(
            _rytm_snapshot(),
            _analog_four_snapshot(),
            style_key="ghost_style",
        )


def test_dual_machine_style_routing_cli_parser_accepts_slots():
    from pathlib import Path

    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import _parse_cli_args

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
def test_dual_machine_style_routing_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_dual_machine_style_routing_cli_error_formatter_is_stable():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import _format_cli_error

    assert _format_cli_error(ValueError("bad rig")) == "Error: bad rig"


def test_dual_machine_style_routing_cli_handler_reports_plan(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
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
        style_key="industrial_dark",
        rytm_slot=0,
        analog_four_slot=0,
        discovery_amount=10,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style snapshot routing" in captured.out
    assert "- Kit: RIGRYTM" in captured.out
    assert "- Kit: RIGA4" in captured.out
    assert "Style target: industrial_dark" in captured.out
    assert "Discovery band: reference" in captured.out
    assert captured.err == ""


def test_dual_machine_style_routing_cli_handler_reports_json(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
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
        style_key="industrial_dark",
        rytm_slot=0,
        analog_four_slot=0,
        discovery_amount=95,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["style_key"] == "industrial_dark"
    assert payload["discovery_amount"] == 95
    assert payload["discovery_band"] == "wild_discovery"
    assert payload["machines"]["rytm"]["kit_name"] == "JSONRYTM"
    assert payload["machines"]["analog_four"]["kit_name"] == "JSONA4"
    assert "RytmRandomizer passive dual-machine" not in captured.out
    assert captured.err == ""


def test_dual_machine_style_routing_cli_handler_reports_errors(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import (
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
