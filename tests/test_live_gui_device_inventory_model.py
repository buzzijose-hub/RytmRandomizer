"""Tests for the passive live-GUI device inventory model."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.devices import all_devices
from rytm_randomizer.reports.live_gui_device_inventory_model import (
    BLOCKED_ACTIONS,
    SAFETY_LINES,
    build_live_gui_device_inventory_model,
    format_live_gui_device_inventory_model_report,
    live_gui_device_inventory_model_payload,
)


def test_build_model_exposes_rytm_and_analog_four_device_cards() -> None:
    model = build_live_gui_device_inventory_model()

    assert model.device_count == len(all_devices())
    # Cards are ordered by each device's own display_order. The exact roster
    # is pinned once in tests/test_device_family_conformance.py, so adding a
    # family does not edit this test.
    card_ids = list(model.cards_by_device_id)
    assert card_ids == sorted(card_ids, key=lambda did: all_devices()[did].display_order)
    assert card_ids[0] == "analog_rytm_mk2"

    rytm = model.cards_by_device_id["analog_rytm_mk2"]
    assert rytm.display_name == "Elektron Analog Rytm MKII"
    assert rytm.track_count == 12
    assert rytm.role_summary == "12-pad drum and sample performance surface"
    assert rytm.default_midi_channel_label == "1"
    assert rytm.port_state == "not_open"
    assert rytm.hardware_state == "locked"
    assert rytm.mock_state == "mock_safe"
    assert rytm.capability_badges == (
        "snapshot_decode",
        "mutation_plan",
        "mock_render",
        "guarded_send",
    )

    analog_four = model.cards_by_device_id["analog_four_mk2"]
    assert analog_four.display_name == "Elektron Analog Four MKII"
    assert analog_four.track_count == 4
    assert analog_four.role_summary == "4-track synth performance surface"
    assert analog_four.default_midi_channel_label == "1"
    assert analog_four.sysex_manufacturer_id_hex == "00 20 3c"

    digitakt = model.cards_by_device_id["digitakt_mk1"]
    assert digitakt.display_name == "Elektron Digitakt"
    assert digitakt.track_count == 8
    assert digitakt.role_summary == "8-track drum and sample performance surface"
    assert digitakt.hardware_state == "locked"

    digitakt_ii = model.cards_by_device_id["digitakt_ii"]
    assert digitakt_ii.display_name == "Elektron Digitakt II"
    assert digitakt_ii.track_count == 16
    assert digitakt_ii.role_summary == "16-track drum and sample performance surface"
    assert digitakt_ii.hardware_state == "locked"


def test_payload_is_gui_ready_and_keeps_hardware_controls_blocked() -> None:
    payload = live_gui_device_inventory_model_payload()

    assert payload["model_version"] == "live_gui_device_inventory_v1"
    assert payload["device_count"] == len(all_devices())
    assert payload["blocked_actions"] == BLOCKED_ACTIONS
    assert payload["safety"] == SAFETY_LINES

    cards = payload["cards"]
    assert isinstance(cards, tuple)
    assert cards[0]["device_id"] == "analog_rytm_mk2"
    assert cards[0]["hardware_state"] == "locked"
    assert cards[0]["port_state"] == "not_open"
    assert cards[1]["device_id"] == "analog_four_mk2"
    assert cards[1]["role_summary"] == "4-track synth performance surface"


def test_build_model_handles_future_registered_devices(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer.reports import live_gui_device_inventory_model as report_mod

    class _FutureDevice:
        device_id = "syntakt_mk2"
        display_name = "Elektron Syntakt MKII"
        default_midi_channel = 9
        track_count = 8
        sysex_manufacturer_id = bytes([0x00, 0x20, 0x3C])
        # A future family declares its own role and order; the reports layer
        # no longer guesses either from track_count.
        role_summary = "12-track drum and synth performance surface"
        display_order = 7

    monkeypatch.setattr(report_mod, "all_devices", lambda: {"syntakt_mk2": _FutureDevice()})

    model = report_mod.build_live_gui_device_inventory_model()
    card = model.cards_by_device_id["syntakt_mk2"]

    assert card.order == 7
    assert card.default_midi_channel_label == "10"
    assert card.role_summary == "12-track drum and synth performance surface"


def test_format_report_names_both_devices_and_passive_boundaries() -> None:
    lines = format_live_gui_device_inventory_model_report()

    assert lines[0] == "RytmRandomizer passive live GUI device inventory model"
    assert f"- Devices: {len(all_devices())}" in lines
    assert "Device analog_rytm_mk2 / Elektron Analog Rytm MKII:" in lines
    assert "Device analog_four_mk2 / Elektron Analog Four MKII:" in lines
    assert "  MIDI port: not_open" in lines
    assert "  Hardware: locked" in lines
    assert "- open_midi_port" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.live_gui_device_inventory_model" in lines
    assert "In-memory only: True" in lines
