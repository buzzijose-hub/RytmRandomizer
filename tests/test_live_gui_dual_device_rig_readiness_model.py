"""Tests for the passive live GUI dual-device rig readiness model."""

from __future__ import annotations

import json
import sys

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_dual_device_rig_readiness_summarizes_12_rytm_pads_and_4_a4_tracks() -> None:
    from rytm_randomizer.reports.live_gui_dual_device_rig_readiness_model import (
        build_live_gui_dual_device_rig_readiness_model,
        format_live_gui_dual_device_rig_readiness_model,
        to_live_gui_dual_device_rig_readiness_model_json,
    )

    report = build_live_gui_dual_device_rig_readiness_model(
        session_label="Warehouse live session",
    )

    assert report.model_version == "live-gui-dual-device-rig-readiness-v1"
    assert len(report.rig_id) == 16
    assert report.session_label == "Warehouse live session"
    assert report.rig_status == "mock-safe"
    assert report.total_device_count == 2
    assert report.total_track_count == 16
    assert report.active_track_count == 4
    assert report.planned_track_count == 12

    devices_by_id = {device.device_id: device for device in report.devices}
    assert devices_by_id["analog_rytm_mk2"].display_name == "Elektron Analog Rytm MKII"
    assert devices_by_id["analog_rytm_mk2"].track_count == 12
    assert devices_by_id["analog_rytm_mk2"].mapped_track_count == 12
    assert devices_by_id["analog_rytm_mk2"].status == "limited-active"
    assert devices_by_id["analog_four_mk2"].display_name == "Elektron Analog Four MKII"
    assert devices_by_id["analog_four_mk2"].track_count == 4
    assert devices_by_id["analog_four_mk2"].mapped_track_count == 4
    assert devices_by_id["analog_four_mk2"].status == "mock-staged"

    assert len(report.tracks) == 16
    tracks_by_test_id = {track.test_id: track for track in report.tracks}
    assert tracks_by_test_id["dual-rig-rytm-pad-01"].label == "Bass Drum"
    assert tracks_by_test_id["dual-rig-rytm-pad-12"].label == "Cow Bell"
    assert tracks_by_test_id["dual-rig-a4-track-01"].role == "Bass movement"
    assert tracks_by_test_id["dual-rig-a4-track-04"].role == "FX / texture"
    assert tracks_by_test_id["dual-rig-a4-track-04"].enabled is False

    assert report.required_actions == (
        "review-planned-rytm-pad-locks",
        "keep-analog-four-staged-until-routing-lands",
        "run-dry-run-before-hardware",
    )
    assert "no MIDI port opened" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert "no hardware mutation" in report.blocked_actions
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-dual-device-rig-readiness-report "
        "--session-label 'Warehouse live session'",
        "python -m rytm_randomizer.cli live-gui-hardware-rail-report "
        "--session 'Warehouse live session' --device 'Analog Rytm MKII' --dry-run on",
        "python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report",
    )

    payload = to_live_gui_dual_device_rig_readiness_model_json(report)
    rig = payload["live_gui_dual_device_rig_readiness"]
    assert rig["total_track_count"] == 16
    assert rig["tracks"][15]["test_id"] == "dual-rig-a4-track-04"
    assert payload["live_gui_12_pad_surface"]["pad_count"] == 12
    assert payload["live_gui_device_inventory"]["device_count"] == 2
    assert payload["live_gui_hardware_rail"]["rail_status"] == "mock-safe"
    assert payload["live_gui_snapshot_compatibility"]["pad_count"] == 12
    assert payload["safety"][0] == "passive/read-only"
    json.dumps(payload, sort_keys=True)

    lines = format_live_gui_dual_device_rig_readiness_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI dual-device rig readiness model"
    assert "- devices: 2" in lines
    assert "- total tracks: 16" in lines
    assert "Analog Four MKII: 4 tracks / mock-staged" in text
    assert "A4 track 4 / FX / texture" in text
    assert "- no MIDI sending" in lines


def test_dual_device_rig_readiness_validates_labels_and_stays_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_dual_device_rig_readiness_model import (
        build_live_gui_dual_device_rig_readiness_model,
        to_live_gui_dual_device_rig_readiness_model_json,
    )

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_dual_device_rig_readiness_model(session_label=" ")

    report = build_live_gui_dual_device_rig_readiness_model()
    json.dumps(to_live_gui_dual_device_rig_readiness_model_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)
    assert report.hardware_rail.port_status == "none"
    assert all("no " in line for line in report.safety if line.startswith("no "))
