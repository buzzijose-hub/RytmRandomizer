import json
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


def _candidate_only_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                6: RytmSnapshotMachineFact(
                    6,
                    8,
                    None,
                    False,
                    "candidate-only tom-pad machine fact",
                ),
            }
        ),
        promoted=False,
    )
    return RytmKitSnapshot(
        slot=5,
        kit_name="CANDIDATE",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def test_style_snapshot_routing_requires_known_style_key():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_rytm_style_snapshot_routes(_style_snapshot(), "ghost_style")


def test_style_snapshot_routing_reports_ready_and_blocked_pads():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")

    assert plan.kit_name == "STYLEKIT"
    assert plan.slot == 4
    assert plan.style_key == "birmingham_pressure"
    assert plan.ready_pad_count == 3
    assert plan.blocked_pad_count == 1
    assert plan.partial_snapshot_mutation_ready is True
    assert plan.pads_by_pad[1].route_ready is True
    assert plan.pads_by_pad[1].profile_key == "2"
    assert plan.pads_by_pad[10].track_code == "OH"
    assert plan.pads_by_pad[10].current_machine_key == "oh_classic"
    assert plan.pads_by_pad[10].route_ready is False
    assert "selectable-only" in plan.pads_by_pad[10].readiness_reason


def test_style_snapshot_routing_uses_style_vector_for_favored_zones():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    birmingham = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")
    deep = plan_rytm_style_snapshot_routes(_style_snapshot(), "deep_dark_hypnosis")

    assert birmingham.favored_zones[:3] == ("grit", "body", "amp")
    assert "filter" in deep.favored_zones
    assert "lfo" in deep.favored_zones


def test_style_snapshot_routing_ranks_legal_machine_candidates_per_pad():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "mills_hypnotic")

    assert plan.pads_by_pad[1].compatible_machine_candidates[0].machine_key == "bd_fm"
    pad_10_candidates = {
        candidate.machine_key for candidate in plan.pads_by_pad[10].compatible_machine_candidates
    }
    assert "oh_classic" in pad_10_candidates
    assert "oh_metallic" in pad_10_candidates
    assert "xt_classic" not in pad_10_candidates
    assert plan.pads_by_pad[10].mutable_machine_candidates == ()


def test_style_snapshot_routing_blocks_candidate_only_machine_facts():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_candidate_only_snapshot(), "warehouse_peak")

    assert plan.ready_pad_count == 0
    assert plan.blocked_pad_count == 1
    assert plan.partial_snapshot_mutation_ready is False
    assert plan.pads_by_pad[6].track_code == "LT"
    assert plan.pads_by_pad[6].route_ready is False
    assert "candidate-only" in plan.pads_by_pad[6].readiness_reason


def test_style_snapshot_routing_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    lines = format_rytm_style_snapshot_routing_report(
        _style_snapshot(),
        style_key="birmingham_pressure",
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style snapshot routing"
    assert "Kit: STYLEKIT" in lines
    assert "Slot: 4" in lines
    assert "Style target: birmingham_pressure" in lines
    assert "- Ready pads: 3" in lines
    assert "- Blocked pads: 1" in lines
    assert "Favored zones: grit, body, amp" in text
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "  Current machine: oh_classic / CC15 10" in text
    assert "  Route ready: False" in text
    assert "  Mutable candidates: none" in text
    assert "  Compatible candidates:" in text
    assert "oh_metallic" in text
    assert "xt_classic" not in text
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_style_snapshot_routing" in lines
    assert "In-memory only: True" in lines


def test_style_snapshot_routing_report_serializes_json_contract():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        to_rytm_style_snapshot_routing_json,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")

    payload = to_rytm_style_snapshot_routing_json(plan)

    assert payload["style_key"] == "birmingham_pressure"
    assert payload["kit_name"] == "STYLEKIT"
    assert payload["ready_pad_count"] == 3
    assert payload["blocked_pad_count"] == 1
    assert payload["pads"][0]["pad"] == 1
    assert payload["pads"][0]["route_ready"] is True
    assert payload["pads"][0]["mutable_machine_candidates"][0]["machine_key"] == "bd_fm"
    assert payload["pads"][3]["pad"] == 10
    assert payload["pads"][3]["mutable_machine_candidates"] == []
    assert payload["safety"][0] == "passive/read-only"


def test_style_snapshot_routing_report_rejects_unknown_style_safely():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        format_rytm_style_snapshot_routing_report(_style_snapshot(), style_key="ghost_style")


def test_style_snapshot_routing_report_formats_explicit_empty_plan():
    from rytm_randomizer.devices.strategies import (
        RytmStyleSnapshotPadPlan,
        RytmStyleSnapshotRoutingPlan,
    )
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    plan = RytmStyleSnapshotRoutingPlan(
        kit_name="EMPTY",
        slot=9,
        style_key="detroit_minimal",
        favored_zones=(),
        ready_pad_count=0,
        blocked_pad_count=1,
        partial_snapshot_mutation_ready=False,
        pads_by_pad=MappingProxyType(
            {
                12: RytmStyleSnapshotPadPlan(
                    pad=12,
                    track_code="CB",
                    label="Cow Bell",
                    current_machine_value=None,
                    current_machine_key=None,
                    profile_key=None,
                    route_ready=False,
                    readiness_reason="missing machine fact",
                    favored_zones=(),
                    compatible_machine_candidates=(),
                    mutable_machine_candidates=(),
                )
            }
        ),
    )

    lines = format_rytm_style_snapshot_routing_report(plan, style_key="ignored")

    assert "Kit: EMPTY" in lines
    assert "Favored zones: none" in lines
    assert "  Current machine: unknown" in lines
    assert "  Profile key: none" in lines
    assert "  Mutable candidates: none" in lines
    assert "  Compatible candidates: none" in lines


def test_style_snapshot_routing_cli_parser_accepts_slot():
    from pathlib import Path

    from rytm_randomizer.reports.rytm_style_snapshot_routing import _parse_cli_args

    assert _parse_cli_args(["kit.syx", "birmingham_pressure"]) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "birmingham_pressure",
        "slot": 0,
        "json_output": False,
    }
    assert _parse_cli_args(["kit.syx", "warehouse_peak", "--slot", "3", "--json"]) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "warehouse_peak",
        "slot": 3,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["kit.syx"], "usage"),
        (["kit.syx", "birmingham_pressure", "--slot"], "usage"),
        (["kit.syx", "birmingham_pressure", "--bank", "1"], "usage"),
        (["kit.syx", "birmingham_pressure", "--slot", "not-int"], "--slot must be an integer"),
        (["kit.syx", "birmingham_pressure", "--slot", "-1"], "--slot must be >= 0"),
    ],
)
def test_style_snapshot_routing_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.rytm_style_snapshot_routing import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_style_snapshot_routing_cli_error_formatter_is_operator_facing():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import _format_cli_error

    assert _format_cli_error(ValueError("bad style")) == "Error: bad style"


def test_style_snapshot_routing_cli_handler_reports_plan(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.rytm_style_snapshot_routing import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"STYLE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    rc = _handle_cli_report(sysex_path=path, style_key="birmingham_pressure", slot=0)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm style snapshot routing" in captured.out
    assert "Kit: STYLE" in captured.out
    assert "Style target: birmingham_pressure" in captured.out
    assert captured.err == ""


def test_style_snapshot_routing_cli_handler_reports_json(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.rytm_style_snapshot_routing import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"JSONSTYLE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="birmingham_pressure",
        slot=0,
        json_output=True,
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert rc == 0
    assert result["kit_name"] == "JSONSTYLE"
    assert result["style_key"] == "birmingham_pressure"
    assert result["pads"][0]["pad"] == 1
    assert "RytmRandomizer passive Rytm" not in captured.out
    assert captured.err == ""


def test_style_snapshot_routing_cli_handler_reports_errors(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.rytm_style_snapshot_routing import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        style_key="birmingham_pressure",
        slot=0,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err
