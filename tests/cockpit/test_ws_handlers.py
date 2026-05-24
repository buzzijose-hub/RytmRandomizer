"""Unit tests for ``rytm_randomizer.cockpit.ws.handlers`` — every command path.

The handlers module exposes one async dispatcher (``handle_command``) plus
ten command-specific async functions. These tests drive the dispatcher
directly with a fake :class:`EventEmitter` (a recorder that captures every
emitted event) and a fully-wired :class:`CockpitSession` so the engine,
device, history, and profiles modules all participate.

Coverage discipline (Gate 1): every branch of every handler is exercised,
including error paths (no active profile, no current candidate, unknown
profile id, unknown command type, missing envelope keys, unknown
``target`` for export, undo with no parent, save with no current
snapshot, load with unknown id, generic handler exception).

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/ws/handlers.py``.
"""

from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.handlers import drain_pending_events, handle_command
from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_PROFILE_CHANGED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
)
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Recorder fixture — captures every event the dispatcher emits.
# ---------------------------------------------------------------------------


@dataclass
class _Recorder:
    """Test double satisfying the :class:`EventEmitter` Protocol."""

    events: list[dict] = field(default_factory=list)

    async def send_event(self, event: dict) -> None:
        self.events.append(event)


# ---------------------------------------------------------------------------
# Snapshot + profile fixtures.
# ---------------------------------------------------------------------------


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000A",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 30, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _profile(profile_id: str = "profile-test") -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name="test-profile",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="t1", value=0.6),),
        pad_mappings=(
            TraitPadWeight(trait="t1", pad_id=1, weight=0.5),
            TraitPadWeight(trait="t1", pad_id=2, weight=0.3),
        ),
        transition_curve="linear",
        source_summary="test fixture",
    )


def _make_session(tmp_path: Path, profile: ProfileModel | None = None) -> CockpitSession:
    """Build a fresh session backed by a writable profiles dir + mock device."""

    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    if profile is not None:
        registry.save(profile)
    return CockpitSession(profile_registry=registry, history_store=history, device=device)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro) -> Any:
    """Run an async coroutine to completion in tests."""

    return asyncio.run(coro)


def _envelope(cmd_type: str, request_id: str = "req-1", **body: Any) -> dict:
    return {"request_id": request_id, "command": {"type": cmd_type, **body}}


def _dispatch(envelope: dict, session: CockpitSession, recorder: _Recorder) -> dict:
    """Run the dispatcher AND drain queued events — mirrors the server's wire loop.

    The server endpoint sends the ack with ``send_json`` and then awaits
    :func:`drain_pending_events` so events arrive after the ack on the
    wire. In handler tests, we don't care about wire timing — we only
    care that the events the handler queued show up in the recorder
    afterwards. This helper bundles the two awaits into one call so
    every test asserts against the post-drain state of the recorder.
    """

    async def _go() -> dict:
        ack = await handle_command(envelope, session, recorder)
        await drain_pending_events(session, recorder)
        return ack

    return _run(_go())


# ---------------------------------------------------------------------------
# Dispatcher-level paths: missing keys, unknown command, generic exception.
# ---------------------------------------------------------------------------


def test_dispatcher_replies_with_error_when_envelope_lacks_command_key(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()
    envelope = {"request_id": "req-1"}  # no "command"

    ack = _dispatch(envelope, session, recorder)

    assert ack["ok"] is False
    assert "command" in ack["error"]
    assert ack["request_id"] == "req-1"


def test_dispatcher_replies_with_error_when_command_lacks_type(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()
    envelope = {"request_id": "req-2", "command": {}}  # no "type"

    ack = _dispatch(envelope, session, recorder)

    assert ack["ok"] is False
    assert "type" in ack["error"]


def test_dispatcher_replies_with_error_for_unknown_command_type(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("not_a_real_command"), session, recorder)

    assert ack["ok"] is False
    assert "unknown command" in ack["error"]
    assert "not_a_real_command" in ack["error"]


def test_dispatcher_replies_with_error_when_envelope_missing_request_id(tmp_path: Path) -> None:
    """Missing ``request_id`` is tolerated; the ack echoes an empty string."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch({"command": {"type": "regen"}}, session, recorder)

    assert ack["request_id"] == ""
    assert ack["ok"] is False  # regen with no profile fails


def test_dispatcher_catches_handler_exception_into_ok_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bug raising inside a handler must surface as ``ok=False, error=str(exc)``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    async def _boom(_cmd: dict, _sess: CockpitSession) -> handlers.HandlerResult:
        raise RuntimeError("deliberate test bug")

    monkeypatch.setitem(handlers._HANDLERS, "select_profile", _boom)
    ack = _dispatch(_envelope("select_profile", profile_id="p"), session, recorder)

    assert ack["ok"] is False
    assert "deliberate test bug" in ack["error"]


# ---------------------------------------------------------------------------
# select_profile — happy path + unknown profile.
# ---------------------------------------------------------------------------


def test_select_profile_happy_path_emits_profile_changed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    recorder = _Recorder()

    ack = _dispatch(_envelope("select_profile", profile_id=profile.profile_id), session, recorder)

    assert ack["ok"] is True
    assert session.active_profile == profile
    assert any(e["type"] == EVENT_PROFILE_CHANGED for e in recorder.events)


def test_select_profile_with_preview_on_emits_mutation_previewed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.preview_on = True
    recorder = _Recorder()

    _dispatch(_envelope("select_profile", profile_id=profile.profile_id), session, recorder)

    assert any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


def test_select_profile_with_preview_off_does_not_emit_mutation_previewed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.preview_on = False
    recorder = _Recorder()

    _dispatch(_envelope("select_profile", profile_id=profile.profile_id), session, recorder)

    assert not any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


def test_select_profile_unknown_id_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("select_profile", profile_id="nonexistent"), session, recorder)

    assert ack["ok"] is False
    assert "nonexistent" in ack["error"]
    assert session.active_profile is None


# ---------------------------------------------------------------------------
# set_depth — emits or omits mutation_previewed based on preview_on.
# ---------------------------------------------------------------------------


def test_set_depth_with_active_profile_returns_candidate(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    recorder = _Recorder()

    ack = _dispatch(_envelope("set_depth", depth=0.6), session, recorder)

    assert ack["ok"] is True
    assert session.depth == 0.6
    assert ack["candidate"] is not None
    assert ack["candidate"]["depth"] == 0.6


def test_set_depth_with_preview_on_emits_mutation_previewed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    session.preview_on = True
    recorder = _Recorder()

    _dispatch(_envelope("set_depth", depth=0.5), session, recorder)

    assert any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


def test_set_depth_with_preview_off_does_not_emit_mutation_previewed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    session.preview_on = False
    recorder = _Recorder()

    _dispatch(_envelope("set_depth", depth=0.5), session, recorder)

    assert not any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


def test_set_depth_without_active_profile_returns_null_candidate(tmp_path: Path) -> None:
    """Recompute returns ``None`` when no profile is selected."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("set_depth", depth=0.4), session, recorder)

    assert ack["ok"] is True
    assert ack["candidate"] is None
    assert session.current_candidate is None


# ---------------------------------------------------------------------------
# set_pad_lock — locked True / False.
# ---------------------------------------------------------------------------


def test_set_pad_lock_adds_pad_to_locks(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("set_pad_lock", pad_id=2, locked=True), session, recorder)

    assert ack["ok"] is True
    assert 2 in session.pad_locks


def test_set_pad_lock_removes_pad_from_locks(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.pad_locks.add(2)
    recorder = _Recorder()

    ack = _dispatch(_envelope("set_pad_lock", pad_id=2, locked=False), session, recorder)

    assert ack["ok"] is True
    assert 2 not in session.pad_locks


def test_set_pad_lock_remove_nonpresent_pad_is_noop(tmp_path: Path) -> None:
    """Removing a pad that wasn't locked is a no-op (no KeyError)."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("set_pad_lock", pad_id=3, locked=False), session, recorder)

    assert ack["ok"] is True
    assert 3 not in session.pad_locks


def test_set_pad_lock_does_not_emit_events(tmp_path: Path) -> None:
    """Pad-lock state lives on the client; no event is broadcast."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    _dispatch(_envelope("set_pad_lock", pad_id=1, locked=True), session, recorder)

    assert recorder.events == []


# ---------------------------------------------------------------------------
# toggle_preview — on/off branches.
# ---------------------------------------------------------------------------


def test_toggle_preview_on_with_profile_emits_candidate(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    recorder = _Recorder()

    ack = _dispatch(_envelope("toggle_preview", on=True), session, recorder)

    assert ack["ok"] is True
    assert session.preview_on is True
    assert ack["candidate"] is not None
    assert any(
        e["type"] == EVENT_MUTATION_PREVIEWED and e["candidate"] is not None
        for e in recorder.events
    )


def test_toggle_preview_off_emits_null_candidate(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    session.preview_on = True
    recorder = _Recorder()

    ack = _dispatch(_envelope("toggle_preview", on=False), session, recorder)

    assert ack["ok"] is True
    assert session.preview_on is False
    assert ack["candidate"] is None
    assert any(
        e["type"] == EVENT_MUTATION_PREVIEWED and e["candidate"] is None for e in recorder.events
    )


def test_toggle_preview_on_without_profile_emits_null_candidate(tmp_path: Path) -> None:
    """Toggling preview on with no profile still emits a (null) mutation_previewed."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("toggle_preview", on=True), session, recorder)

    assert ack["ok"] is True
    assert ack["candidate"] is None
    # null event was emitted (preview is on but there's nothing to preview)
    assert any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


# ---------------------------------------------------------------------------
# regen — happy + error.
# ---------------------------------------------------------------------------


def test_regen_with_active_profile_bumps_seed_and_returns_candidate(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    original_seed = session.seed
    recorder = _Recorder()

    ack = _dispatch(_envelope("regen"), session, recorder)

    assert ack["ok"] is True
    assert session.seed != original_seed
    assert ack["candidate"] is not None


def test_regen_with_preview_on_emits_mutation_previewed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    session.preview_on = True
    recorder = _Recorder()

    _dispatch(_envelope("regen"), session, recorder)

    assert any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


def test_regen_with_preview_off_does_not_emit_mutation_previewed(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    session.preview_on = False
    recorder = _Recorder()

    _dispatch(_envelope("regen"), session, recorder)

    assert not any(e["type"] == EVENT_MUTATION_PREVIEWED for e in recorder.events)


def test_regen_without_active_profile_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("regen"), session, recorder)

    assert ack["ok"] is False
    assert "no active profile" in ack["error"]


# ---------------------------------------------------------------------------
# prepare_send_plan — explicit preflight between preview and SEND.
# ---------------------------------------------------------------------------


def test_prepare_send_plan_without_candidate_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("prepare_send_plan"), session, recorder)

    assert ack["ok"] is False
    assert "no current candidate" in ack["error"]
    assert session.current_send_plan is None
    assert recorder.events == []


def test_prepare_send_plan_with_candidate_stores_and_emits_plan(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(_envelope("prepare_send_plan"), session, recorder)

    assert ack["ok"] is True
    assert ack["send_plan"]["ready"] is True
    assert session.current_send_plan is not None
    assert ack["send_plan"]["plan_id"] == session.current_send_plan.plan_id
    assert recorder.events == [
        {
            "type": EVENT_SEND_PLAN_CHANGED,
            "send_plan": session.current_send_plan.to_dict(),
        }
    ]


def test_prepare_send_plan_without_active_profile_returns_error(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    assert session.current_candidate is not None
    session.active_profile = None
    recorder = _Recorder()

    ack = _dispatch(_envelope("prepare_send_plan"), session, recorder)

    assert ack["ok"] is False
    assert "no active profile" in ack["error"]
    assert session.current_send_plan is None
    assert recorder.events == []


def test_set_pad_lock_clears_stale_send_plan(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    _dispatch(_envelope("prepare_send_plan"), session, _Recorder())
    assert session.current_send_plan is not None

    recorder = _Recorder()
    ack = _dispatch(_envelope("set_pad_lock", pad_id=1, locked=True), session, recorder)

    assert ack["ok"] is True
    assert session.current_send_plan is None
    assert recorder.events == [{"type": EVENT_SEND_PLAN_CHANGED, "send_plan": None}]


def test_send_with_candidate_but_no_ready_plan_returns_error(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(_envelope("send"), session, recorder)

    assert ack["ok"] is False
    assert "no ready send plan" in ack["error"]
    assert recorder.events == []


# ---------------------------------------------------------------------------
# send — happy + no-candidate error.
# ---------------------------------------------------------------------------


def test_send_with_ready_plan_applies_and_emits_five_events(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    # Prime current_candidate via a set_depth call.
    recorder_setup = _Recorder()
    _dispatch(_envelope("set_depth", depth=0.5), session, recorder_setup)
    _dispatch(_envelope("prepare_send_plan"), session, _Recorder())

    recorder = _Recorder()
    ack = _dispatch(_envelope("send"), session, recorder)

    assert ack["ok"] is True
    assert ack["new_snapshot_id"]
    assert ack["send_plan_id"]
    # Five events in order: snapshot, history, preview(null), send_plan(null), status.
    types_emitted = [e["type"] for e in recorder.events]
    assert types_emitted == [
        EVENT_SNAPSHOT_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_MUTATION_PREVIEWED,
        EVENT_SEND_PLAN_CHANGED,
        EVENT_SESSION_STATUS,
    ]
    # mutation_previewed must carry null (preview clears post-send)
    null_event = next(e for e in recorder.events if e["type"] == EVENT_MUTATION_PREVIEWED)
    assert null_event["candidate"] is None
    assert session.current_candidate is None
    assert session.current_send_plan is None
    assert session.unsaved_sends == 1


def test_send_respects_pad_locks(tmp_path: Path) -> None:
    """Send must skip locked pads — verify by inspecting the post-send snapshot."""

    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    session.pad_locks.add(1)
    # Prime a candidate
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    _dispatch(_envelope("prepare_send_plan"), session, _Recorder())
    pre_pad1_params = dict(session.device.capture_snapshot().pads[0].params)

    _dispatch(_envelope("send"), session, _Recorder())

    post_pad1_params = dict(session.device.capture_snapshot().pads[0].params)
    assert pre_pad1_params == post_pad1_params  # pad 1 locked → unchanged


def test_send_without_candidate_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("send"), session, recorder)

    assert ack["ok"] is False
    assert "no current candidate" in ack["error"]


# ---------------------------------------------------------------------------
# save — label / no label / no current.
# ---------------------------------------------------------------------------


def test_save_with_label_promotes_entry_and_resets_unsaved_sends(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    session.unsaved_sends = 3
    recorder = _Recorder()

    ack = _dispatch(_envelope("save", label="my-kit"), session, recorder)

    assert ack["ok"] is True
    current = session.history_store.current
    saved_entry = next(e for e in current.entries if e.snapshot.snapshot_id == current.current_id)
    assert saved_entry.kind == "saved"
    assert saved_entry.label == "my-kit"
    assert session.unsaved_sends == 0


def test_save_without_label_uses_none(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("save"), session, recorder)

    assert ack["ok"] is True
    current = session.history_store.current
    saved_entry = next(e for e in current.entries if e.snapshot.snapshot_id == current.current_id)
    assert saved_entry.label is None


def test_save_with_explicit_none_label_uses_none(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("save", label=None), session, recorder)

    assert ack["ok"] is True
    current = session.history_store.current
    saved_entry = next(e for e in current.entries if e.snapshot.snapshot_id == current.current_id)
    assert saved_entry.label is None


def test_save_emits_history_and_session_status(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    _dispatch(_envelope("save", label="x"), session, recorder)

    types_emitted = [e["type"] for e in recorder.events]
    assert EVENT_HISTORY_UPDATED in types_emitted
    assert EVENT_SESSION_STATUS in types_emitted


def test_save_with_empty_history_returns_error(tmp_path: Path) -> None:
    """A session whose history is empty (initial not called) cannot save."""

    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()  # no .initial()
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)
    recorder = _Recorder()

    ack = _dispatch(_envelope("save"), session, recorder)

    assert ack["ok"] is False
    assert "no current snapshot" in ack["error"]


# ---------------------------------------------------------------------------
# load_snapshot — known + unknown id.
# ---------------------------------------------------------------------------


def test_load_snapshot_existing_id_emits_snapshot_and_history(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    # Push two more snapshots so we have something to load back to.
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    _dispatch(_envelope("prepare_send_plan"), session, _Recorder())
    _dispatch(_envelope("send"), session, _Recorder())
    original_id = "01HXY5Q9PJM0000000000000A"

    recorder = _Recorder()
    ack = _dispatch(_envelope("load_snapshot", snapshot_id=original_id), session, recorder)

    assert ack["ok"] is True
    assert ack["snapshot_id"] == original_id
    types_emitted = [e["type"] for e in recorder.events]
    assert EVENT_SNAPSHOT_CHANGED in types_emitted
    assert EVENT_HISTORY_UPDATED in types_emitted


def test_load_snapshot_unknown_id_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("load_snapshot", snapshot_id="missing"), session, recorder)

    assert ack["ok"] is False
    assert "missing" in ack["error"]


# ---------------------------------------------------------------------------
# undo — can-undo / cannot-undo.
# ---------------------------------------------------------------------------


def test_undo_walks_pointer_when_parent_exists(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    # set_depth + send to advance the chain
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    _dispatch(_envelope("prepare_send_plan"), session, _Recorder())
    _dispatch(_envelope("send"), session, _Recorder())
    pre_undo_id = session.history_store.current.current_id

    recorder = _Recorder()
    ack = _dispatch(_envelope("undo"), session, recorder)

    assert ack["ok"] is True
    assert ack["snapshot_id"] != pre_undo_id
    types_emitted = [e["type"] for e in recorder.events]
    assert EVENT_SNAPSHOT_CHANGED in types_emitted
    assert EVENT_HISTORY_UPDATED in types_emitted


def test_undo_at_root_returns_error(tmp_path: Path) -> None:
    """The bootstrap snapshot has no parent — undo must refuse."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("undo"), session, recorder)

    assert ack["ok"] is False
    assert "nothing to undo" in ack["error"]


# ---------------------------------------------------------------------------
# export_profile_model — binary, json, unknown profile, bad target.
# ---------------------------------------------------------------------------


def test_export_profile_model_binary_returns_base64_blob(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("export_profile_model", profile_id=profile.profile_id, target="binary"),
        session,
        recorder,
    )

    assert ack["ok"] is True
    raw = base64.b64decode(ack["model_bytes_b64"])
    # The binary header starts with "RYMP" magic per cockpit/export spec.
    assert raw[:4] == b"RYMP"
    # Export emits no event — bytes ride on the ack
    assert recorder.events == []


def test_export_profile_model_json_returns_base64_utf8_json(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("export_profile_model", profile_id=profile.profile_id, target="json"),
        session,
        recorder,
    )

    assert ack["ok"] is True
    decoded = json.loads(base64.b64decode(ack["model_bytes_b64"]).decode("utf-8"))
    assert decoded["profile_id"] == profile.profile_id


def test_export_profile_model_unknown_profile_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("export_profile_model", profile_id="nonexistent", target="binary"),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "nonexistent" in ack["error"]


def test_export_profile_model_bad_target_returns_error(tmp_path: Path) -> None:
    profile = _profile()
    session = _make_session(tmp_path, profile)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("export_profile_model", profile_id=profile.profile_id, target="xml"),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "target" in ack["error"]


# ---------------------------------------------------------------------------
# emit_initial_events — covers helper function.
# ---------------------------------------------------------------------------


def test_emit_initial_events_sends_four_events_in_order(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    _run(handlers.emit_initial_events(recorder, session))

    types_emitted = [e["type"] for e in recorder.events]
    assert types_emitted == [
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_PROFILE_CHANGED,
        EVENT_HISTORY_UPDATED,
    ]


def test_emit_initial_events_carries_armed_false_for_mock(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    _run(handlers.emit_initial_events(recorder, session))

    status = next(e for e in recorder.events if e["type"] == EVENT_SESSION_STATUS)
    assert status["armed"] is False
    assert status["mode"] == "mock"
    assert status["midi_port"] is None
    assert status["unsaved_sends"] == 0


def test_emit_initial_events_with_armed_adapter_reports_live(tmp_path: Path) -> None:
    """Cover the ``is_armed`` true branch of the mode resolver."""

    class _ArmedFakeDevice:
        is_armed = True
        midi_port = "Rytm MK2 Port 1"

        def capture_snapshot(self) -> Snapshot:
            return _snapshot()

        def apply(self, candidate: Any, pad_locks: Any) -> Snapshot:  # pragma: no cover - unused
            return _snapshot()

        def commit_kit(
            self, snapshot: Snapshot, label: str | None
        ) -> None:  # pragma: no cover - unused
            return None

    device = _ArmedFakeDevice()
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)
    recorder = _Recorder()

    _run(handlers.emit_initial_events(recorder, session))

    status = next(e for e in recorder.events if e["type"] == EVENT_SESSION_STATUS)
    assert status["armed"] is True
    assert status["mode"] == "live"
    assert status["midi_port"] == "Rytm MK2 Port 1"


def test_emit_initial_events_with_active_profile_emits_profile_dict(tmp_path: Path) -> None:
    """Cover the ``profile is not None`` branch of ``_build_profile_changed``."""

    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    recorder = _Recorder()

    _run(handlers.emit_initial_events(recorder, session))

    profile_event = next(e for e in recorder.events if e["type"] == EVENT_PROFILE_CHANGED)
    assert profile_event["profile"]["profile_id"] == profile.profile_id


def test_emit_initial_events_with_current_candidate_via_helper(tmp_path: Path) -> None:
    """Cover ``_build_mutation_previewed`` with a non-None candidate via direct call."""

    profile = _profile()
    session = _make_session(tmp_path, profile)
    session.active_profile = profile
    # Force a candidate
    _dispatch(_envelope("set_depth", depth=0.5), session, _Recorder())
    assert session.current_candidate is not None

    # Directly exercise the helper to cover the non-null branch
    payload = handlers._build_mutation_previewed(session.current_candidate)
    assert payload["candidate"] is not None
    assert payload["candidate"]["candidate_id"] == session.current_candidate.candidate_id


def test_midi_port_helper_handles_string_port(tmp_path: Path) -> None:
    """The ``_midi_port`` helper must coerce a non-string port to str."""

    class _IntPortDevice:
        is_armed = True
        midi_port = 42  # weird-but-legal: emulator returns an int

        def capture_snapshot(self) -> Snapshot:
            return _snapshot()

        def apply(self, candidate: Any, pad_locks: Any) -> Snapshot:  # pragma: no cover - unused
            return _snapshot()

        def commit_kit(
            self, snapshot: Snapshot, label: str | None
        ) -> None:  # pragma: no cover - unused
            return None

    device = _IntPortDevice()
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)

    assert handlers._midi_port(session) == "42"
