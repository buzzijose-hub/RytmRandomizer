"""Tests for passive live GUI command queue and action history modeling."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def _history():
    from rytm_randomizer.cockpit.data.history import History, HistoryEntry
    from rytm_randomizer.cockpit.data.snapshot import PadState, Snapshot

    captured_at = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    root = Snapshot(
        snapshot_id="snap-root",
        device="analog_rytm_mk2",
        captured_at=captured_at,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"TUN": 64}),),
        scene_slot="A01",
        bpm=124.0,
    )
    sent = Snapshot(
        snapshot_id="snap-send",
        device="analog_rytm_mk2",
        captured_at=captured_at,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"TUN": 66}),),
        scene_slot="A01",
        bpm=124.0,
    )
    regen = Snapshot(
        snapshot_id="snap-regen",
        device="analog_rytm_mk2",
        captured_at=captured_at,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"TUN": 67}),),
        scene_slot="A01",
        bpm=124.0,
    )
    return History(
        entries=(
            HistoryEntry(
                snapshot=root,
                kind="auto",
                parent_id=None,
                via=None,
                label=None,
            ),
            HistoryEntry(
                snapshot=sent,
                kind="auto",
                parent_id="snap-root",
                via="send",
                label=None,
            ),
            HistoryEntry(
                snapshot=regen,
                kind="saved",
                parent_id="snap-send",
                via="regen",
                label="Warehouse take",
            ),
        ),
        current_id="snap-regen",
    )


def test_command_queue_model_defaults_to_mock_safe_queued_cards() -> None:
    from rytm_randomizer.reports.live_gui_command_queue_model import (
        build_live_gui_command_queue_model,
        format_live_gui_command_queue_model,
        to_live_gui_command_queue_model_json,
    )

    report = build_live_gui_command_queue_model(session_label="Warehouse rehearsal")

    assert report.command_queue_version == "live-gui-command-queue-model-v1"
    assert len(report.command_queue_id) == 16
    assert report.session_label == "Warehouse rehearsal"
    assert report.queue_status == "queued"
    assert report.dry_run_active is True
    assert report.hardware_armed is False
    assert [command.key for command in report.queued_commands] == [
        "queued-command-snapshot-save",
        "queued-command-mutate-pad-11",
        "queued-command-mutate-pad-1",
        "queued-command-parameter-lock-check",
    ]
    assert all(command.status == "queued" for command in report.queued_commands)
    assert all(command.dry_run_only for command in report.queued_commands)
    assert report.queued_commands[1].label == "Mutate Pad 11 (SY Raw)"
    assert report.last_actions[0].label == "No last actions"
    assert report.undo_stack[0].label == "No undo stack"
    assert "no MIDI sending" in report.safety_lines
    assert "dispatch queued command from model" in report.blocked_actions
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-command-queue-model-report "
        "--session-label 'Warehouse rehearsal'",
    )

    lines = format_live_gui_command_queue_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI command queue model"
    assert "Command queue summary:" in lines
    assert "Queued commands:" in lines
    assert "Last actions:" in lines
    assert "Undo stack:" in lines
    assert "- queued-command-mutate-pad-11: queued - Mutate Pad 11 (SY Raw)" in text
    assert "- no command execution" in lines
    assert "- no port opening" in lines

    payload = to_live_gui_command_queue_model_json(report)
    model = payload["live_gui_command_queue_model"]
    assert model["command_queue_id"] == report.command_queue_id
    assert model["queued_commands"][1]["estimated_message_count"] == 8
    assert model["last_actions"][0]["status"] == "empty"
    assert model["undo_stack"][0]["status"] == "empty"
    assert payload["safety"][0] == "passive/read-only"


def test_command_queue_model_maps_cockpit_history_to_last_actions_and_undo_stack() -> None:
    from rytm_randomizer.reports.live_gui_command_queue_model import (
        build_live_gui_command_queue_model,
    )

    report = build_live_gui_command_queue_model(
        session_label="Warehouse history",
        history=_history(),
    )

    assert report.queue_status == "queued"
    assert [action.snapshot_id for action in report.last_actions] == [
        "snap-regen",
        "snap-send",
        "snap-root",
    ]
    assert report.last_actions[0].action_type == "regen"
    assert report.last_actions[0].label == "Warehouse take"
    assert report.last_actions[0].status == "current"
    assert report.last_actions[1].action_type == "send"
    assert report.last_actions[2].action_type == "root"
    assert [entry.snapshot_id for entry in report.undo_stack] == [
        "snap-regen",
        "snap-send",
        "snap-root",
    ]
    assert report.undo_stack[0].is_current is True
    assert report.undo_stack[0].is_undo_target is False
    assert report.undo_stack[1].is_undo_target is True
    assert report.undo_stack[2].is_load_target is True


def test_command_queue_model_blocks_when_dry_run_is_inactive() -> None:
    from rytm_randomizer.reports.live_gui_command_queue_model import (
        build_live_gui_command_queue_model,
    )

    report = build_live_gui_command_queue_model(
        dry_run_active=False,
        active_command_key="queued-command-mutate-pad-1",
    )

    assert report.queue_status == "blocked"
    assert report.active_command_key == "queued-command-mutate-pad-1"
    assert {command.status for command in report.queued_commands} == {"blocked"}
    assert all(command.enabled is False for command in report.queued_commands)
    assert report.queued_commands[0].operator_action == (
        "Run a dry-run preview before allowing this command card."
    )


def test_command_queue_model_validation_edges() -> None:
    from rytm_randomizer.reports.live_gui_command_queue_model import (
        build_live_gui_command_queue_model,
    )

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_command_queue_model(session_label=" ")

    with pytest.raises(ValueError, match="active_command_key"):
        build_live_gui_command_queue_model(active_command_key=" ")

    with pytest.raises(ValueError, match="active_command_key"):
        build_live_gui_command_queue_model(active_command_key="missing-command")

    with pytest.raises(ValueError, match="history_limit"):
        build_live_gui_command_queue_model(history_limit=0)


def test_command_queue_model_json_is_serializable_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_command_queue_model import (
        build_live_gui_command_queue_model,
        to_live_gui_command_queue_model_json,
    )

    report = build_live_gui_command_queue_model(history=_history())
    json.dumps(to_live_gui_command_queue_model_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)
    assert "no hardware mutation" in report.safety_lines
