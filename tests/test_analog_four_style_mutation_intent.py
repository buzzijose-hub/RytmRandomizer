"""Tests for passive Analog Four style mutation intent."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=2,
        kit_name="A4INTENT",
        raw=b"\x00\x20\x3c\x07" + b"A4INTENT".ljust(16, b"\x00"),
        offsets_promoted=offsets_promoted,
    )


def _framed_a4_payload(name: bytes = b"A4INTENT") -> bytes:
    padded_name = name[:16].ljust(16, b"\x00")
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02])
    return bytes([0xF0]) + payload + bytes([0xF7])


def _row_by_zone(plan, *, track: int, zone: str):
    return next(row for row in plan.tracks_by_track[track].intent_rows if row.zone == zone)


def test_analog_four_style_mutation_intent_maps_tracks_to_zone_bias_rows():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )

    plan = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=False),
        "birmingham_pressure",
        discovery_amount=75,
    )

    assert plan.kit_name == "A4INTENT"
    assert plan.slot == 2
    assert plan.style_key == "birmingham_pressure"
    assert plan.discovery_amount == 75
    assert plan.discovery_band == "discovery"
    assert plan.mutation_depth == "strong"
    assert plan.ready_track_count == 0
    assert plan.blocked_track_count == 4
    assert plan.intent_row_count == 16
    assert tuple(plan.tracks_by_track) == (1, 2, 3, 4)

    track_1 = plan.tracks_by_track[1]
    assert track_1.route_ready is False
    assert "candidate-only" in track_1.readiness_reason
    assert track_1.favored_zones == ("drive", "oscillator", "filter", "envelope")
    assert track_1.intent_row_count == 4

    drive = _row_by_zone(plan, track=1, zone="drive")
    assert drive.mutation_depth == "strong"
    assert drive.target_bias == 94
    assert drive.target_direction == "higher"


def test_analog_four_style_mutation_intent_marks_dark_filter_lower():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )

    plan = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=True),
        "industrial_dark",
        discovery_amount=75,
    )

    row = _row_by_zone(plan, track=1, zone="filter")
    assert row.target_bias == 75
    assert row.target_direction == "lower"
    assert plan.ready_track_count == 4
    assert plan.blocked_track_count == 0


def test_analog_four_style_mutation_intent_marks_envelope_tail_direction():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )

    short_tail = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=True),
        "birmingham_pressure",
        discovery_amount=75,
    )
    long_tail = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=True),
        "deep_dark_hypnosis",
        discovery_amount=75,
    )

    assert _row_by_zone(short_tail, track=1, zone="envelope").target_direction == "shorter"
    assert _row_by_zone(long_tail, track=1, zone="effects").target_direction == "longer"


def test_analog_four_style_mutation_intent_marks_motion_modulation_higher():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )

    plan = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=True),
        "mills_hypnotic",
        discovery_amount=75,
    )

    row = _row_by_zone(plan, track=3, zone="modulation")
    assert row.target_bias == 83
    assert row.target_direction == "higher"


def test_analog_four_style_mutation_intent_direction_helpers_cover_neutral_edges():
    from dataclasses import replace

    import rytm_randomizer.devices.strategies.analog_four_style_mutation_intent as intent
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    neutral = STYLE_TARGET_VECTORS["detroit_minimal"]
    bright = replace(neutral, darkness=20)
    long_tail = replace(neutral, decay_tail=70, transient_density=45)
    round_tail = replace(neutral, decay_tail=50, attack_sharpness=50)
    centered_oscillator = replace(neutral, low_end_weight=65, metallicity=45, motion_amount=45)

    assert intent._zone_direction("filter", bright) == "higher"
    assert intent._zone_direction("filter", neutral) == "center"
    assert intent._zone_direction("envelope", long_tail) == "longer"
    assert intent._zone_direction("envelope", round_tail) == "center"
    assert intent._zone_direction("oscillator", centered_oscillator) == "center"
    assert intent._zone_direction("unknown-zone", neutral) == "center"


def test_analog_four_style_mutation_intent_scales_depth_from_discovery_band():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )

    reference = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=True),
        "industrial_dark",
        discovery_amount=10,
    )
    wild = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=True),
        "industrial_dark",
        discovery_amount=95,
    )

    assert reference.discovery_band == "reference"
    assert reference.mutation_depth == "micro"
    assert reference.intent_row_count == 8
    assert wild.discovery_band == "wild_discovery"
    assert wild.mutation_depth == "wild"
    assert wild.intent_row_count > reference.intent_row_count


def test_analog_four_style_mutation_intent_rejects_unknown_style():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_analog_four_style_mutation_intent(_snapshot(), "ghost_style")


def test_analog_four_style_mutation_intent_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.analog_four_style_mutation_intent import (
        format_analog_four_style_mutation_intent_report,
    )

    lines = format_analog_four_style_mutation_intent_report(
        _snapshot(offsets_promoted=False),
        style_key="birmingham_pressure",
        discovery_amount=75,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Analog Four style mutation intent"
    assert "Kit: A4INTENT" in lines
    assert "Slot: 2" in lines
    assert "Style target: birmingham_pressure" in lines
    assert "Mutation depth: strong" in lines
    assert "Track 1 / bass_foundation / Bass / low pulse:" in text
    assert "  Zone intents:" in text
    assert "    - drive | depth strong | bias 94 | direction higher" in text
    assert "candidate-only" in text
    assert "- no MIDI rendering" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_analog_four_style_mutation_intent_report_serializes_json_contract():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        plan_analog_four_style_mutation_intent,
    )
    from rytm_randomizer.reports.analog_four_style_mutation_intent import (
        to_analog_four_style_mutation_intent_json,
    )

    plan = plan_analog_four_style_mutation_intent(
        _snapshot(offsets_promoted=False),
        "birmingham_pressure",
        discovery_amount=75,
    )

    payload = to_analog_four_style_mutation_intent_json(plan)

    assert payload["kit_name"] == "A4INTENT"
    assert payload["style_key"] == "birmingham_pressure"
    assert payload["mutation_depth"] == "strong"
    assert payload["intent_row_count"] == 16
    assert payload["tracks"][0]["track"] == 1
    assert payload["tracks"][0]["intent_rows"][0] == {
        "zone": "drive",
        "mutation_depth": "strong",
        "target_bias": 94,
        "target_direction": "higher",
    }
    assert payload["safety"][0] == "passive/read-only"


def test_analog_four_style_mutation_intent_report_formats_empty_favored_zones():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_intent import (
        AnalogFourStyleMutationIntentPlan,
        AnalogFourStyleMutationTrackIntent,
    )
    from rytm_randomizer.reports.analog_four_style_mutation_intent import (
        format_analog_four_style_mutation_intent_report,
    )

    track = AnalogFourStyleMutationTrackIntent(
        track=1,
        role_key="bass_foundation",
        label="Bass / low pulse",
        route_ready=True,
        readiness_reason="",
        favored_zones=(),
        mutation_depth="micro",
        intent_rows=(),
        intent_row_count=0,
    )
    plan = AnalogFourStyleMutationIntentPlan(
        kit_name="EMPTYA4",
        slot=1,
        style_key="detroit_minimal",
        discovery_amount=10,
        discovery_band="reference",
        mutation_depth="micro",
        ready_track_count=1,
        blocked_track_count=0,
        intent_row_count=0,
        tracks_by_track=MappingProxyType({1: track}),
    )

    lines = format_analog_four_style_mutation_intent_report(
        plan,
        style_key="ignored",
    )

    assert "  Favored zones: none" in lines
    assert "  Zone intents: none" in lines


def test_analog_four_style_mutation_intent_cli_parser_accepts_slot_discovery_and_json():
    from rytm_randomizer.reports.analog_four_style_mutation_intent import _parse_cli_args

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
def test_analog_four_style_mutation_intent_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.analog_four_style_mutation_intent import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_analog_four_style_mutation_intent_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_intent import _handle_cli_report

    path = tmp_path / "a4.syx"
    path.write_bytes(_framed_a4_payload(b"A4JSON"))

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
    assert result["kit_name"] == "A4JSON"
    assert result["style_key"] == "birmingham_pressure"
    assert result["discovery_band"] == "discovery"
    assert captured.err == ""


def test_analog_four_style_mutation_intent_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_intent import _handle_cli_report

    path = tmp_path / "a4.syx"
    path.write_bytes(_framed_a4_payload(b"A4TEXT"))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="birmingham_pressure",
        slot=0,
        discovery_amount=75,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four style mutation intent" in captured.out
    assert "Kit: A4TEXT" in captured.out
    assert "bias 94" in captured.out
    assert "direction higher" in captured.out
    assert captured.err == ""


def test_analog_four_style_mutation_intent_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_mutation_intent import _handle_cli_report

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


def test_analog_four_style_mutation_intent_cli_error_formatter():
    from rytm_randomizer.reports.analog_four_style_mutation_intent import _format_cli_error

    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"
