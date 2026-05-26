"""Tests for passive live GUI snapshot-history and undo/redo modeling."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import History, HistoryEntry, PadState, Snapshot

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)

_FIXED_TS = datetime(2026, 5, 26, 8, 15, 0, tzinfo=timezone.utc)
SNAP_A = "snapshot-a"
SNAP_B = "snapshot-b"
SNAP_C = "snapshot-c"


def _gui_history_snapshot(
    snapshot_id: str,
    *,
    tun: int = 64,
    scene_slot: str | None = "A01",
    bpm: float | None = 128.0,
) -> Snapshot:
    return Snapshot(
        snapshot_id=snapshot_id,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": tun, "dec": 70}),
            PadState(pad_id=2, machine="SD Classic", params={"tun": 48, "lev": 100}),
        ),
        scene_slot=scene_slot,
        bpm=bpm,
    )


def _gui_history_chain() -> History:
    return History(
        entries=(
            HistoryEntry(
                snapshot=_gui_history_snapshot(SNAP_A),
                kind="auto",
                parent_id=None,
                via=None,
                label=None,
            ),
            HistoryEntry(
                snapshot=_gui_history_snapshot(SNAP_B, tun=67),
                kind="auto",
                parent_id=SNAP_A,
                via="send",
                label="After S3B",
            ),
            HistoryEntry(
                snapshot=_gui_history_snapshot(SNAP_C, tun=61),
                kind="saved",
                parent_id=SNAP_B,
                via="regen",
                label="The Bells inspired snapshot",
            ),
        ),
        current_id=SNAP_C,
    )


def test_snapshot_history_model_exposes_entries_controls_and_passive_payload() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_history_model import (
        build_live_gui_snapshot_history_model,
        format_live_gui_snapshot_history_model,
        to_live_gui_snapshot_history_model_json,
    )

    report = build_live_gui_snapshot_history_model(
        _gui_history_chain(),
        session_label="The Bells test",
    )

    assert report.snapshot_history_version == "live-gui-snapshot-history-model-v1"
    assert len(report.snapshot_history_id) == 16
    assert report.session_label == "The Bells test"
    assert report.current_id == SNAP_C
    assert report.current_index == 2
    assert report.entry_count == 3
    assert [entry.order for entry in report.entries] == [0, 1, 2]
    assert [entry.snapshot_id for entry in report.entries] == [SNAP_A, SNAP_B, SNAP_C]
    assert report.entries[0].label == "Initial snapshot"
    assert report.entries[0].can_load is True
    assert report.entries[0].can_undo_to is False
    assert report.entries[1].label == "After S3B"
    assert report.entries[1].via == "send"
    assert report.entries[1].can_load is True
    assert report.entries[2].label == "The Bells inspired snapshot"
    assert report.entries[2].is_current is True
    assert report.entries[2].is_saved is True
    assert report.entries[2].can_load is False
    assert report.entries[2].can_undo_to is True
    assert report.entries[2].summary == "analog_rytm_mk2: 2 pad(s), scene A01, 128 BPM"
    assert report.entries[2].test_id == "snapshot-history-entry-2"

    controls = {control.key: control for control in report.controls}
    assert controls["undo"].enabled is True
    assert controls["undo"].target_snapshot_id == SNAP_B
    assert controls["undo"].reason == "Undo to previous snapshot snapshot-b."
    assert controls["redo"].enabled is False
    assert controls["redo"].reason == "No redo stack is modeled by the cockpit history store yet."
    assert controls["load-current"].enabled is False
    assert controls["load-current"].target_snapshot_id == SNAP_C
    assert "send MIDI from snapshot history" in report.blocked_actions
    assert "open MIDI port from snapshot history" in report.blocked_actions
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-snapshot-history-model-report "
        "--session-label 'The Bells test'",
    )

    lines = format_live_gui_snapshot_history_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI snapshot-history model"
    assert "Snapshot history summary:" in lines
    assert "- current index: 2" in lines
    assert "- [2] snapshot-c saved current: The Bells inspired snapshot" in text
    assert "Controls:" in lines
    assert "- undo: enabled, target snapshot-b" in lines
    assert "- redo: disabled, target none" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_live_gui_snapshot_history_model_json(report)
    history_payload = payload["live_gui_snapshot_history_model"]
    assert history_payload["snapshot_history_version"] == "live-gui-snapshot-history-model-v1"
    assert history_payload["snapshot_history_id"] == report.snapshot_history_id
    assert history_payload["entries"][2]["snapshot_id"] == SNAP_C
    assert history_payload["controls"][0]["key"] == "undo"
    assert payload["safety"][0] == "passive/read-only"


def test_snapshot_history_model_handles_empty_history_and_root_current_state() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_history_model import (
        build_live_gui_snapshot_history_model,
        format_live_gui_snapshot_history_model,
    )

    empty = build_live_gui_snapshot_history_model(History(entries=(), current_id=""))
    assert empty.entry_count == 0
    assert empty.current_index == -1
    assert empty.current_id == ""
    assert empty.entries == ()
    assert all(control.enabled is False for control in empty.controls)
    assert "No snapshots in history." in "\n".join(format_live_gui_snapshot_history_model(empty))

    root_only = build_live_gui_snapshot_history_model(
        History(
            entries=(
                HistoryEntry(
                    snapshot=_gui_history_snapshot(SNAP_A),
                    kind="auto",
                    parent_id=None,
                    via=None,
                    label=None,
                ),
            ),
            current_id=SNAP_A,
        )
    )
    controls = {control.key: control for control in root_only.controls}
    assert root_only.current_index == 0
    assert controls["undo"].enabled is False
    assert controls["undo"].reason == "Current snapshot has no parent to undo to."
    assert controls["load-current"].target_snapshot_id == SNAP_A


def test_snapshot_history_model_summarizes_unlabeled_unknown_or_fractional_snapshots() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_history_model import (
        build_live_gui_snapshot_history_model,
    )

    history = History(
        entries=(
            HistoryEntry(
                snapshot=_gui_history_snapshot(SNAP_A, scene_slot=None, bpm=None),
                kind="auto",
                parent_id=None,
                via=None,
                label=None,
            ),
            HistoryEntry(
                snapshot=_gui_history_snapshot(SNAP_B, scene_slot="B12", bpm=132.5),
                kind="auto",
                parent_id=SNAP_A,
                via="load",
                label=None,
            ),
        ),
        current_id=SNAP_B,
    )

    report = build_live_gui_snapshot_history_model(history)

    assert report.entries[0].summary == "analog_rytm_mk2: 2 pad(s), scene none, unknown BPM"
    assert report.entries[1].label == "Auto snapshot 2"
    assert report.entries[1].summary == "analog_rytm_mk2: 2 pad(s), scene B12, 132.5 BPM"


def test_snapshot_history_model_validates_session_label() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_history_model import (
        build_live_gui_snapshot_history_model,
    )

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_snapshot_history_model(_gui_history_chain(), session_label=" ")


def test_snapshot_history_model_json_is_serializable_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_snapshot_history_model import (
        build_live_gui_snapshot_history_model,
        to_live_gui_snapshot_history_model_json,
    )

    report = build_live_gui_snapshot_history_model(_gui_history_chain())
    json.dumps(to_live_gui_snapshot_history_model_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)
    assert all("no " in action for action in report.safety_lines if action.startswith("no "))
