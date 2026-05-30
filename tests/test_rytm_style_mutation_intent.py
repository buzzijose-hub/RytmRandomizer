import json
from pathlib import Path
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _framed_sysex(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


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


def _row_by_parameter(plan, *, pad: int, parameter: str):
    return next(row for row in plan.pads_by_pad[pad].intent_rows if row.parameter == parameter)


def test_style_mutation_intent_maps_ready_pads_to_zone_parameter_rows():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    plan = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )

    assert plan.kit_name == "STYLEKIT"
    assert plan.slot == 4
    assert plan.style_key == "birmingham_pressure"
    assert plan.discovery_amount == 75
    assert plan.discovery_band == "discovery"
    assert plan.mutation_depth == "strong"
    assert plan.ready_pad_count == 3
    assert plan.blocked_pad_count == 1
    assert plan.intent_row_count > 0

    pad_1 = plan.pads_by_pad[1]
    assert pad_1.route_ready is True
    assert pad_1.profile_key == "2"
    assert pad_1.favored_zones == ("grit", "body", "amp", "lfo")
    assert pad_1.intent_row_count > 0
    assert pad_1.intent_rows[0].zone == "grit"
    assert pad_1.intent_rows[0].parameter == "SRC Snap"
    assert pad_1.intent_rows[0].low == 8
    assert pad_1.intent_rows[0].high == 55

    pad_10 = plan.pads_by_pad[10]
    assert pad_10.route_ready is False
    assert pad_10.intent_rows == ()
    assert "selectable-only" in pad_10.readiness_reason


def test_style_mutation_intent_adds_grit_bias_and_higher_direction():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    plan = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )

    row = _row_by_parameter(plan, pad=1, parameter="SRC Snap")
    assert row.target_bias == 86
    assert row.target_direction == "higher"


def test_style_mutation_intent_pulls_dark_filter_frequency_lower():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    plan = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "deep_dark_hypnosis",
        discovery_amount=75,
    )

    row = _row_by_parameter(plan, pad=1, parameter="FLT Frequency")
    assert row.target_bias == 82
    assert row.target_direction == "lower"


def test_style_mutation_intent_marks_short_and_long_tail_decay_directions():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    short_tail = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )
    long_tail = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "deep_dark_hypnosis",
        discovery_amount=75,
    )

    assert _row_by_parameter(short_tail, pad=1, parameter="SRC Decay").target_direction == "shorter"
    assert _row_by_parameter(long_tail, pad=1, parameter="SRC Decay").target_direction == "longer"


def test_style_mutation_intent_marks_motion_heavy_lfo_direction():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    plan = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "mills_hypnotic",
        discovery_amount=75,
    )

    row = _row_by_parameter(plan, pad=3, parameter="LFO Speed")
    assert row.target_bias == 83
    assert row.target_direction == "higher"


def test_style_mutation_intent_direction_helpers_cover_neutral_edges():
    from dataclasses import replace

    import rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent as intent
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    neutral = STYLE_TARGET_VECTORS["detroit_minimal"]
    bright = replace(neutral, darkness=20)

    assert intent._zone_bias(neutral, "unknown-zone") == 50
    assert intent._parameter_direction("FLT Frequency", zone="filter", target=bright) == "higher"
    assert intent._parameter_direction("FLT Frequency", zone="filter", target=neutral) == "center"
    assert intent._parameter_direction("SRC Decay", zone="body", target=neutral) == "center"


def test_style_mutation_intent_scales_depth_from_discovery_band():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    reference = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=10,
    )
    wild = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=95,
    )

    assert reference.discovery_band == "reference"
    assert reference.mutation_depth == "micro"
    assert wild.discovery_band == "wild_discovery"
    assert wild.mutation_depth == "wild"
    assert wild.intent_row_count > reference.intent_row_count


def test_style_mutation_intent_blocks_candidate_only_snapshot_without_rows():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    plan = plan_rytm_style_mutation_intent(
        _candidate_only_snapshot(),
        "warehouse_peak",
    )

    assert plan.ready_pad_count == 0
    assert plan.blocked_pad_count == 1
    assert plan.intent_row_count == 0
    assert plan.pads_by_pad[6].intent_rows == ()
    assert "candidate-only" in plan.pads_by_pad[6].readiness_reason


def test_style_mutation_intent_treats_missing_profile_as_no_parameter_rows(
    monkeypatch: pytest.MonkeyPatch,
):
    import rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent as intent

    monkeypatch.setattr(intent, "PROFILES", {})

    plan = intent.plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
    )

    assert plan.ready_pad_count == 3
    assert plan.intent_row_count == 0
    assert plan.pads_by_pad[1].route_ready is True
    assert plan.pads_by_pad[1].intent_rows == ()


def test_style_mutation_intent_rejects_unknown_style():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_rytm_style_mutation_intent(_style_snapshot(), "ghost_style")


def test_style_mutation_intent_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.rytm_style_mutation_intent import (
        format_rytm_style_mutation_intent_report,
    )

    lines = format_rytm_style_mutation_intent_report(
        _style_snapshot(),
        style_key="birmingham_pressure",
        discovery_amount=10,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style mutation intent"
    assert "Kit: STYLEKIT" in lines
    assert "Slot: 4" in lines
    assert "Style target: birmingham_pressure" in lines
    assert "Discovery amount: 10" in lines
    assert "Discovery band: reference" in lines
    assert "Mutation depth: micro" in lines
    assert "Pad 1 / BD / Bass Drum:" in text
    assert "  Intent rows:" in text
    assert "    - grit | SRC Snap | safe 8-55 | depth micro" in text
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "  Intent rows: none" in text
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_style_mutation_intent" in lines
    assert "In-memory only: True" in lines


def test_style_mutation_intent_report_formats_empty_favored_zones():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        RytmStyleMutationIntentPlan,
        RytmStyleMutationPadIntent,
    )
    from rytm_randomizer.reports.rytm_style_mutation_intent import (
        format_rytm_style_mutation_intent_report,
    )

    plan = RytmStyleMutationIntentPlan(
        kit_name="EMPTYZONE",
        slot=9,
        style_key="warehouse_peak",
        discovery_amount=75,
        discovery_band="discovery",
        mutation_depth="strong",
        ready_pad_count=0,
        blocked_pad_count=1,
        intent_row_count=0,
        pads_by_pad=MappingProxyType(
            {
                6: RytmStyleMutationPadIntent(
                    pad=6,
                    track_code="LT",
                    label="Low Tom",
                    current_machine_key="unknown",
                    profile_key=None,
                    route_ready=False,
                    readiness_reason="blocked",
                    favored_zones=(),
                    intent_rows=(),
                    intent_row_count=0,
                )
            }
        ),
    )
    lines = format_rytm_style_mutation_intent_report(
        plan,
        style_key="warehouse_peak",
    )

    assert "  Favored zones: none" in lines
    assert "  Intent rows: none" in lines


def test_style_mutation_intent_report_serializes_json_contract():
    from rytm_randomizer.devices.strategies.analog_rytm_style_mutation_intent import (
        plan_rytm_style_mutation_intent,
    )
    from rytm_randomizer.reports.rytm_style_mutation_intent import (
        to_rytm_style_mutation_intent_json,
    )

    plan = plan_rytm_style_mutation_intent(
        _style_snapshot(),
        "birmingham_pressure",
        discovery_amount=75,
    )

    payload = to_rytm_style_mutation_intent_json(plan)

    assert payload["kit_name"] == "STYLEKIT"
    assert payload["style_key"] == "birmingham_pressure"
    assert payload["discovery_band"] == "discovery"
    assert payload["mutation_depth"] == "strong"
    assert payload["intent_row_count"] == plan.intent_row_count
    assert payload["pads"][0]["pad"] == 1
    assert payload["pads"][0]["intent_rows"][0] == {
        "zone": "grit",
        "parameter": "SRC Snap",
        "low": 8,
        "high": 55,
        "mutation_depth": "strong",
        "target_bias": 86,
        "target_direction": "higher",
    }
    assert payload["pads"][3]["pad"] == 10
    assert payload["pads"][3]["intent_rows"] == []
    assert payload["safety"][0] == "passive/read-only"


def test_style_mutation_intent_cli_parser_accepts_slot_discovery_and_json():
    from rytm_randomizer.reports.rytm_style_mutation_intent import _parse_cli_args

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
def test_style_mutation_intent_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.rytm_style_mutation_intent import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_style_mutation_intent_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.rytm_style_mutation_intent import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"INTENT")
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
    assert result["kit_name"] == "INTENT"
    assert result["style_key"] == "birmingham_pressure"
    assert result["discovery_band"] == "discovery"
    assert captured.err == ""


def test_style_mutation_intent_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.rytm_style_mutation_intent import _handle_cli_report

    payload = rytm_real_layout_kit_payload(name=b"INTEXT")
    path = tmp_path / "kit.syx"
    path.write_bytes(_framed_sysex(payload))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="birmingham_pressure",
        slot=0,
        discovery_amount=10,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm style mutation intent" in captured.out
    assert "Kit: INTEXT" in captured.out
    assert "Discovery band: reference" in captured.out
    assert "bias 86" in captured.out
    assert "direction higher" in captured.out
    assert captured.err == ""


def test_style_mutation_intent_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.rytm_style_mutation_intent import _handle_cli_report

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


def test_style_mutation_intent_cli_error_formatter():
    from rytm_randomizer.reports.rytm_style_mutation_intent import _format_cli_error

    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"
