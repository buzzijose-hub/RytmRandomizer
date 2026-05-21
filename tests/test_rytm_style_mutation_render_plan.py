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


def _framed_sysex(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _event_by_parameter(plan, *, pad: int, parameter: str):
    return next(
        event for event in plan.pads_by_pad[pad].render_events if event.parameter == parameter
    )


def test_style_mutation_render_plan_builds_directional_value_envelopes():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        plan_rytm_style_mutation_render_plan,
    )

    plan = plan_rytm_style_mutation_render_plan(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )

    assert plan.kit_name == "STYLEKIT"
    assert plan.slot == 4
    assert plan.style_key == "birmingham_pressure"
    assert plan.discovery_band == "discovery"
    assert plan.mutation_depth == "strong"
    assert plan.render_ready is True
    assert plan.render_event_count > 0

    pad_1 = plan.pads_by_pad[1]
    assert pad_1.render_ready is True
    assert pad_1.profile_key == "2"
    assert pad_1.render_event_count > 0

    snap = _event_by_parameter(plan, pad=1, parameter="SRC Snap")
    assert snap.zone == "grit"
    assert snap.low == 8
    assert snap.high == 55
    assert snap.target_direction == "higher"
    assert snap.target_value == 48
    assert snap.window_low == 34
    assert snap.window_high == 55


def test_style_mutation_render_plan_preserves_blocked_pads_without_events():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        plan_rytm_style_mutation_render_plan,
    )

    plan = plan_rytm_style_mutation_render_plan(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )

    pad_10 = plan.pads_by_pad[10]
    assert pad_10.route_ready is False
    assert pad_10.render_ready is False
    assert pad_10.render_events == ()
    assert "selectable-only" in pad_10.readiness_reason


def test_style_mutation_render_plan_reference_window_is_narrower_than_wild():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        plan_rytm_style_mutation_render_plan,
    )

    reference = plan_rytm_style_mutation_render_plan(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=10,
    )
    wild = plan_rytm_style_mutation_render_plan(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=95,
    )

    reference_snap = _event_by_parameter(reference, pad=1, parameter="SRC Snap")
    wild_snap = _event_by_parameter(wild, pad=1, parameter="SRC Snap")

    assert reference.discovery_band == "reference"
    assert reference.mutation_depth == "micro"
    assert wild.discovery_band == "wild_discovery"
    assert wild.mutation_depth == "wild"
    assert reference_snap.window_high - reference_snap.window_low < (
        wild_snap.window_high - wild_snap.window_low
    )


def test_style_mutation_render_plan_moves_dark_filter_targets_lower():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        plan_rytm_style_mutation_render_plan,
    )

    plan = plan_rytm_style_mutation_render_plan(
        _style_snapshot(),
        "deep_dark_hypnosis",
        discovery_amount=75,
    )

    filter_frequency = _event_by_parameter(plan, pad=1, parameter="FLT Frequency")
    assert filter_frequency.target_direction == "lower"
    assert filter_frequency.target_value < (filter_frequency.low + filter_frequency.high) // 2
    assert filter_frequency.window_low == filter_frequency.low


def test_style_mutation_render_plan_rejects_unknown_style():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        plan_rytm_style_mutation_render_plan,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_rytm_style_mutation_render_plan(_style_snapshot(), "ghost_style")


def test_style_mutation_render_plan_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import (
        format_rytm_style_mutation_render_plan_report,
    )

    lines = format_rytm_style_mutation_render_plan_report(
        _style_snapshot(),
        style_key="birmingham_pressure",
        discovery_amount=75,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style mutation render plan"
    assert "Kit: STYLEKIT" in lines
    assert "Style target: birmingham_pressure" in lines
    assert "Render ready: True" in lines
    assert "Pad 1 / BD / Bass Drum:" in text
    assert "  Render events:" in text
    assert "    - grit | SRC Snap | target 48 | window 34-55 | safe 8-55" in text
    assert "- passive/read-only" in lines
    assert "- render-plan metadata only" in lines
    assert "- no MIDI rendering" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_style_mutation_render_plan_report_formats_empty_prebuilt_plan():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        RytmStyleMutationRenderPadPlan,
        RytmStyleMutationRenderPlan,
    )
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import (
        format_rytm_style_mutation_render_plan_report,
    )

    plan = RytmStyleMutationRenderPlan(
        kit_name="EMPTYRENDER",
        slot=8,
        style_key="detroit_minimal",
        discovery_amount=10,
        discovery_band="reference",
        mutation_depth="micro",
        render_ready=False,
        ready_pad_count=0,
        blocked_pad_count=1,
        render_event_count=0,
        pads_by_pad=MappingProxyType(
            {
                10: RytmStyleMutationRenderPadPlan(
                    pad=10,
                    track_code="OH",
                    label="Open Hihat",
                    current_machine_key="oh_classic",
                    profile_key=None,
                    route_ready=False,
                    render_ready=False,
                    readiness_reason="selectable-only",
                    favored_zones=(),
                    render_events=(),
                    render_event_count=0,
                )
            }
        ),
    )

    lines = format_rytm_style_mutation_render_plan_report(
        plan,
        style_key="ignored",
    )

    assert "Kit: EMPTYRENDER" in lines
    assert "Render ready: False" in lines
    assert "  Favored zones: none" in lines
    assert "  Render events: none" in lines


def test_style_mutation_render_plan_json_contract_is_deterministic():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_render_plan import (
        plan_rytm_style_mutation_render_plan,
    )
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import (
        to_rytm_style_mutation_render_plan_json,
    )

    plan = plan_rytm_style_mutation_render_plan(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )
    payload = to_rytm_style_mutation_render_plan_json(plan)

    assert payload["kit_name"] == "STYLEKIT"
    assert payload["style_key"] == "birmingham_pressure"
    assert payload["render_ready"] is True
    assert payload["render_event_count"] == plan.render_event_count
    assert payload["pads"][0]["pad"] == 1
    assert payload["pads"][0]["render_events"][0] == {
        "zone": "grit",
        "parameter": "SRC Snap",
        "low": 8,
        "high": 55,
        "mutation_depth": "strong",
        "target_bias": 86,
        "target_direction": "higher",
        "target_value": 48,
        "window_low": 34,
        "window_high": 55,
    }
    assert payload["safety"][0] == "passive/read-only"


def test_style_mutation_render_plan_cli_parser_accepts_slot_discovery_and_json():
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import _parse_cli_args

    assert _parse_cli_args(["kit.syx", "birmingham_pressure"]) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "birmingham_pressure",
        "slot": 0,
        "discovery_amount": 45,
        "json_output": False,
    }
    assert _parse_cli_args(
        ["kit.syx", "warehouse_peak", "--slot", "3", "--discovery", "95", "--json"]
    ) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "warehouse_peak",
        "slot": 3,
        "discovery_amount": 95,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["kit.syx"], "usage"),
        (["kit.syx", "birmingham_pressure", "--slot"], "usage"),
        (["kit.syx", "birmingham_pressure", "--discovery"], "usage"),
        (["kit.syx", "birmingham_pressure", "--unknown", "1"], "usage"),
        (["kit.syx", "birmingham_pressure", "--slot", "nope"], "--slot must be an integer"),
        (["kit.syx", "birmingham_pressure", "--slot", "-1"], "--slot must be >= 0"),
        (
            ["kit.syx", "birmingham_pressure", "--discovery", "nope"],
            "--discovery must be an integer",
        ),
        (
            ["kit.syx", "birmingham_pressure", "--discovery", "101"],
            "discovery amount must be between 0 and 100",
        ),
    ],
)
def test_style_mutation_render_plan_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_style_mutation_render_plan_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.rytm_style_mutation_render_plan import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"RENDER")
    path = tmp_path / "kit.syx"
    path.write_bytes(_framed_sysex(payload))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="birmingham_pressure",
        slot=0,
        discovery_amount=75,
        json_output=True,
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert rc == 0
    assert result["kit_name"] == "RENDER"
    assert result["style_key"] == "birmingham_pressure"
    assert result["render_ready"] is True
    assert captured.err == ""


def test_style_mutation_render_plan_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.rytm_style_mutation_render_plan import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"RENTEXT")
    path = tmp_path / "kit.syx"
    path.write_bytes(_framed_sysex(payload))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="birmingham_pressure",
        slot=0,
        discovery_amount=75,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm style mutation render plan" in captured.out
    assert "Kit: RENTEXT" in captured.out
    assert "Render ready: True" in captured.out
    assert "window" in captured.out
    assert captured.err == ""


def test_style_mutation_render_plan_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        style_key="birmingham_pressure",
        slot=0,
        discovery_amount=75,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_style_mutation_render_plan_cli_error_formatter():
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import _format_cli_error

    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"
