"""Tests for the passive live-GUI 12-pad Rytm surface model."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.reports.live_gui_12_pad_surface_model import (
    BLOCKED_ACTIONS,
    SAFETY_LINES,
    build_live_gui_12_pad_surface_model,
    format_live_gui_12_pad_surface_model_report,
    live_gui_12_pad_surface_model_payload,
)


def test_build_model_exposes_all_12_pads_with_active_and_planned_lanes() -> None:
    model = build_live_gui_12_pad_surface_model()

    assert model.pad_count == 12
    assert model.active_pad_count == 4
    assert model.planned_pad_count == 8
    assert tuple(model.cards_by_pad) == tuple(range(1, 13))

    pad_1 = model.cards_by_pad[1]
    assert pad_1.track_code == "BD"
    assert pad_1.label == "Bass Drum"
    assert pad_1.surface_state == "active_v134"
    assert pad_1.ui_enabled is True
    assert pad_1.ui_locked is False
    assert pad_1.default_role == "kick"
    assert pad_1.default_machine_label == "BD Hard"
    assert pad_1.legal_machine_count == 17
    assert pad_1.snapshot_mutable_machine_count == 11
    assert pad_1.primary_machine_labels == (
        "BD Hard",
        "BD Classic",
        "BD FM",
        "BD Plastic",
    )

    pad_12 = model.cards_by_pad[12]
    assert pad_12.track_code == "CB"
    assert pad_12.label == "Cow Bell"
    assert pad_12.surface_state == "planned_expansion"
    assert pad_12.ui_enabled is False
    assert pad_12.ui_locked is True
    assert pad_12.default_role == "cowbell"
    assert pad_12.lock_reason == "awaiting V1.34-compatible mutation routing for pads 5-12"
    assert pad_12.primary_machine_labels == (
        "CB Classic",
        "CB Metallic",
        "CY Classic",
        "CY Metallic",
    )


def test_payload_is_serializable_and_gui_ready_without_hardware_scope() -> None:
    payload = live_gui_12_pad_surface_model_payload()

    assert payload["model_version"] == "live_gui_12_pad_surface_v1"
    assert payload["pad_count"] == 12
    assert payload["active_pad_count"] == 4
    assert payload["planned_pad_count"] == 8
    assert payload["blocked_actions"] == BLOCKED_ACTIONS
    assert payload["safety"] == SAFETY_LINES

    cards = payload["cards"]
    assert isinstance(cards, tuple)
    assert len(cards) == 12
    assert cards[9]["pad"] == 10
    assert cards[9]["track_code"] == "OH"
    assert cards[9]["surface_state"] == "planned_expansion"
    assert cards[9]["default_role"] == "hihat"
    assert cards[9]["primary_machine_labels"] == (
        "OH Classic",
        "OH Metallic",
        "HH Basic",
        "HH Lab",
    )


def test_format_report_names_safety_and_all_12_pad_cards() -> None:
    lines = format_live_gui_12_pad_surface_model_report()

    assert lines[0] == "RytmRandomizer passive live GUI 12-pad surface model"
    assert "- Pads: 12" in lines
    assert "- Active V1.34 pads: 4" in lines
    assert "- Planned/locked pads: 8" in lines
    assert "Pad 10 / OH / Open Hihat:" in lines
    assert "Pad 12 / CB / Cow Bell:" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.live_gui_12_pad_surface_model" in lines
    assert "In-memory only: True" in lines
