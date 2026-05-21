"""Tests for passive Analog Four style snapshot routing."""

from __future__ import annotations

import json
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=3,
        kit_name="A4STYLE",
        raw=b"\x00\x20\x3c\x07" + b"A4STYLE".ljust(16, b"\x00"),
        offsets_promoted=offsets_promoted,
    )


def _framed_a4_payload(name: bytes = b"A4STYLE") -> bytes:
    padded_name = name[:16].ljust(16, b"\x00")
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02])
    return bytes([0xF0]) + payload + bytes([0xF7])


def test_analog_four_style_routes_block_candidate_only_offsets():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    plan = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=False),
        "birmingham_pressure",
    )

    assert plan.kit_name == "A4STYLE"
    assert plan.slot == 3
    assert plan.style_key == "birmingham_pressure"
    assert plan.style_focus == (
        "overdriven monotone stab",
        "dark filter pressure",
        "short metallic scrape",
    )
    assert plan.favored_zones[:3] == ("drive", "oscillator", "filter")
    assert plan.ready_track_count == 0
    assert plan.blocked_track_count == 4
    assert plan.partial_snapshot_mutation_ready is False
    assert tuple(plan.tracks_by_track) == (1, 2, 3, 4)
    assert all(not track.route_ready for track in plan.tracks_by_track.values())
    assert all(
        "offsets are candidate-only" in track.readiness_reason
        for track in plan.tracks_by_track.values()
    )


def test_analog_four_style_routes_promoted_offsets_to_four_ready_tracks():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    plan = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=True),
        "deep_dark_hypnosis",
    )

    assert plan.favored_zones[:3] == ("effects", "modulation", "filter")
    assert plan.ready_track_count == 4
    assert plan.blocked_track_count == 0
    assert plan.partial_snapshot_mutation_ready is True
    assert {track.role_key for track in plan.tracks_by_track.values()} == {
        "bass_foundation",
        "stab_pulse",
        "texture_motion",
        "space_accent",
    }
    assert all(track.route_ready for track in plan.tracks_by_track.values())
    assert all(track.readiness_reason == "" for track in plan.tracks_by_track.values())
    assert plan.tracks_by_track[4].score > plan.tracks_by_track[2].score


def test_analog_four_style_routes_apply_reference_discovery_slider():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    reference = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=True),
        "industrial_dark",
        discovery_amount=10,
    )
    wild = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=True),
        "industrial_dark",
        discovery_amount=95,
    )

    assert reference.discovery_amount == 10
    assert reference.discovery_band == "reference"
    assert reference.machine_switching_allowed is False
    assert reference.favored_zones == ("drive", "oscillator")
    assert all(track.discovery_band == "reference" for track in reference.tracks_by_track.values())

    assert wild.discovery_amount == 95
    assert wild.discovery_band == "wild_discovery"
    assert wild.machine_switching_allowed is True
    assert len(wild.favored_zones) > len(reference.favored_zones)
    assert all(track.discovery_band == "wild_discovery" for track in wild.tracks_by_track.values())


def test_analog_four_style_zone_bias_uses_neutral_score_for_unknown_zone():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS
    from rytm_randomizer.devices.strategies.analog_four_style_snapshot_routing import (
        analog_four_style_zone_bias,
    )

    assert analog_four_style_zone_bias(STYLE_TARGET_VECTORS["industrial_dark"], "drive") == 95
    assert analog_four_style_zone_bias(STYLE_TARGET_VECTORS["industrial_dark"], "ghost") == 50


def test_analog_four_style_routes_reject_bad_discovery_amount():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    with pytest.raises(ValueError, match="discovery amount must be between 0 and 100"):
        plan_analog_four_style_snapshot_routes(
            _snapshot(),
            "industrial_dark",
            discovery_amount=-1,
        )


def test_analog_four_style_routes_reject_unknown_style_key():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_analog_four_style_snapshot_routes(_snapshot(), "ghost_style")


def test_analog_four_style_routes_reject_wrong_snapshot_type():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    with pytest.raises(ValueError, match="AnalogFourKitSnapshot"):
        plan_analog_four_style_snapshot_routes("not a snapshot", "detroit_minimal")


def test_analog_four_style_routes_are_deterministic_and_read_only():
    from rytm_randomizer.devices.strategies import (
        AnalogFourStyleSnapshotRoutingPlan,
        plan_analog_four_style_snapshot_routes,
    )

    snapshot = _snapshot(offsets_promoted=True)
    first = plan_analog_four_style_snapshot_routes(snapshot, "warehouse_peak")
    second = plan_analog_four_style_snapshot_routes(snapshot, "warehouse_peak")

    assert isinstance(first, AnalogFourStyleSnapshotRoutingPlan)
    assert first == second
    assert isinstance(first.tracks_by_track, MappingProxyType)
    with pytest.raises(TypeError):
        first.tracks_by_track[5] = first.tracks_by_track[1]


def test_analog_four_style_routing_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import (
        format_analog_four_style_snapshot_routing_report,
    )

    lines = format_analog_four_style_snapshot_routing_report(
        _snapshot(offsets_promoted=False),
        style_key="industrial_dark",
    )

    assert lines[0] == "RytmRandomizer passive Analog Four style snapshot routing"
    assert "Kit: A4STYLE" in lines
    assert "Style target: industrial_dark" in lines
    assert "Discovery amount: 75" in lines
    assert "Discovery band: discovery" in lines
    assert "Machine switching allowed: True" in lines
    assert "- Ready tracks: 0" in lines
    assert "Analog Four focus:" in lines
    assert "- metallic FM-like bite" in lines
    assert "Track 1 / bass_foundation / Bass / low pulse:" in lines
    assert "  Route ready: False" in lines
    assert "candidate-only" in "\n".join(lines)
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_analog_four_style_routing_report_serializes_json_contract():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import (
        to_analog_four_style_snapshot_routing_json,
    )

    plan = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=False),
        "industrial_dark",
    )

    payload = to_analog_four_style_snapshot_routing_json(plan)

    assert payload["style_key"] == "industrial_dark"
    assert payload["kit_name"] == "A4STYLE"
    assert payload["discovery_amount"] == 75
    assert payload["discovery_band"] == "discovery"
    assert payload["machine_switching_allowed"] is True
    assert payload["ready_track_count"] == 0
    assert payload["blocked_track_count"] == 4
    assert payload["tracks"][0]["track"] == 1
    assert payload["tracks"][0]["role_key"] == "bass_foundation"
    assert payload["tracks"][0]["route_ready"] is False
    assert "candidate-only" in payload["tracks"][0]["readiness_reason"]
    assert payload["safety"][0] == "passive/read-only"


def test_analog_four_style_routing_report_accepts_prebuilt_empty_plan():
    from rytm_randomizer.devices.strategies import (
        AnalogFourStyleSnapshotRoutingPlan,
        AnalogFourStyleTrackPlan,
    )
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import (
        format_analog_four_style_snapshot_routing_report,
    )

    track = AnalogFourStyleTrackPlan(
        track=1,
        role_key="bass_foundation",
        label="Bass / low pulse",
        route_ready=True,
        readiness_reason="",
        favored_zones=(),
        discovery_band="discovery",
        score=0,
    )
    plan = AnalogFourStyleSnapshotRoutingPlan(
        kit_name="EMPTY",
        slot=1,
        style_key="detroit_minimal",
        style_focus=(),
        discovery_amount=75,
        discovery_band="discovery",
        machine_switching_allowed=True,
        favored_zones=(),
        ready_track_count=1,
        blocked_track_count=0,
        partial_snapshot_mutation_ready=True,
        tracks_by_track=MappingProxyType({1: track}),
    )

    lines = format_analog_four_style_snapshot_routing_report(
        plan,
        style_key="ignored_for_prebuilt_plan",
    )

    assert "Kit: EMPTY" in lines
    assert "Favored zones: none" in lines
    assert "  Reason: ready for promoted-offset planning" in lines
    assert "  Favored zones: none" in lines


def test_analog_four_style_routing_cli_parser_accepts_slot():
    from pathlib import Path

    from rytm_randomizer.reports.analog_four_style_snapshot_routing import _parse_cli_args

    assert _parse_cli_args(["kit.syx", "industrial_dark"]) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "industrial_dark",
        "slot": 0,
        "discovery_amount": 75,
        "json_output": False,
    }
    assert _parse_cli_args(
        ["kit.syx", "mills_hypnotic", "--slot", "2", "--discovery", "95", "--json"]
    ) == {
        "sysex_path": Path("kit.syx"),
        "style_key": "mills_hypnotic",
        "slot": 2,
        "discovery_amount": 95,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["kit.syx"], "usage"),
        (["kit.syx", "industrial_dark", "--slot"], "usage"),
        (["kit.syx", "industrial_dark", "--discovery"], "usage"),
        (["kit.syx", "industrial_dark", "--bank", "1"], "usage"),
        (["kit.syx", "industrial_dark", "--slot", "bad"], "--slot must be an integer"),
        (["kit.syx", "industrial_dark", "--slot", "-1"], "--slot must be >= 0"),
        (["kit.syx", "industrial_dark", "--discovery", "bad"], "--discovery must be an integer"),
        (
            ["kit.syx", "industrial_dark", "--discovery", "-1"],
            "discovery amount must be between 0 and 100",
        ),
    ],
)
def test_analog_four_style_routing_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_analog_four_style_routing_cli_handler_reports_plan(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import _handle_cli_report

    path = tmp_path / "a4.syx"
    path.write_bytes(_framed_a4_payload(b"A4LIVE"))

    rc = _handle_cli_report(sysex_path=path, style_key="industrial_dark", slot=0)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four style snapshot routing" in captured.out
    assert "Kit: A4LIVE" in captured.out
    assert "Style target: industrial_dark" in captured.out
    assert "Discovery band: discovery" in captured.out
    assert captured.err == ""


def test_analog_four_style_routing_cli_handler_reports_json(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import _handle_cli_report

    path = tmp_path / "a4.syx"
    path.write_bytes(_framed_a4_payload(b"A4JSON"))

    rc = _handle_cli_report(
        sysex_path=path,
        style_key="industrial_dark",
        slot=0,
        discovery_amount=95,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["kit_name"] == "A4JSON"
    assert payload["style_key"] == "industrial_dark"
    assert payload["discovery_amount"] == 95
    assert payload["discovery_band"] == "wild_discovery"
    assert payload["tracks"][0]["track"] == 1
    assert "RytmRandomizer passive Analog Four" not in captured.out
    assert captured.err == ""


def test_analog_four_style_routing_decode_reports_unsupported_frames(tmp_path):
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import (
        decode_supported_analog_four_snapshots_from_path,
    )

    unsupported_path = tmp_path / "unsupported.syx"
    unsupported_path.write_bytes(bytes([0xF0, 0x01, 0x02, 0x03, 0xF7]))
    with pytest.raises(ValueError, match="frame 1"):
        decode_supported_analog_four_snapshots_from_path(unsupported_path)


def test_analog_four_style_routing_decode_reports_no_payloads(monkeypatch, tmp_path):
    from rytm_randomizer.reports import analog_four_style_snapshot_routing as report

    monkeypatch.setattr(report, "read_sysex_payloads_from_path", lambda _path: ())

    path = tmp_path / "empty.syx"
    with pytest.raises(ValueError, match="no SysEx payloads found"):
        report.decode_supported_analog_four_snapshots_from_path(path)


def test_analog_four_style_routing_slot_selection_reports_available_slots(tmp_path):
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import (
        select_supported_analog_four_snapshot,
    )

    sysex_path = tmp_path / "a4.syx"
    sysex_path.write_bytes(_framed_a4_payload())
    snapshots = (_snapshot(),)

    with pytest.raises(ValueError, match="only 1 supported Analog Four kit snapshot"):
        select_supported_analog_four_snapshot(sysex_path, 1, snapshots)

    with pytest.raises(ValueError, match="only 2 supported Analog Four kit snapshots"):
        select_supported_analog_four_snapshot(sysex_path, 2, (snapshots[0], snapshots[0]))


def test_analog_four_style_routing_cli_error_formatter_is_stable():
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import _format_cli_error

    assert _format_cli_error(ValueError("bad args")) == "Error: bad args"


def test_analog_four_style_routing_cli_handler_reports_errors(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        style_key="industrial_dark",
        slot=0,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err
