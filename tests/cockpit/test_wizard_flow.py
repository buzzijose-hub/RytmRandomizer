"""WS-F: handler-level Profile Wizard flow composition tests.

This module is the *composition* safety net for the Profile Wizard: it
exercises the full operator journey -- ``wizard_start`` →
``wizard_set_metadata`` → ``wizard_add_source`` → ``wizard_analyze`` →
``wizard_review`` → ``wizard_save`` -- through the dispatcher in
:func:`rytm_randomizer.cockpit.ws.handlers.handle_command` using the REAL
collaborators (real :func:`reference_analyzer.lookup_traits`, real
:func:`builder.build_profile`, real on-disk :class:`ProfileRegistry`).

Where :mod:`tests.cockpit.test_ws_wizard_handlers` exercises each handler
in isolation with a stubbed analyzer, this module's purpose is the
*opposite*: prove the WS-A state + WS-B analyzers + WS-C builder + WS-D
WS handlers + the existing ProfileRegistry actually wire together end-to-
end without an in-process live WebSocket. The complementary file
:mod:`tests.cockpit.test_integration_wizard_flow` then re-runs the same
happy path across the FastAPI ``TestClient`` boundary.

Why this layer exists at all
----------------------------

The handler-level tests stub the analyzer; the WS-level tests open a
real socket. The middle layer -- "all the real collaborators wired
through the real dispatcher" -- is where a bug like "WS-B's reference
analyzer returns 5 traits but WS-C's pad mapping has 4" first surfaces.
Catching it here is faster than catching it through the WebSocket.

The reference analyzer (``mode="reference"``) is the only kind that
touches no filesystem, so it is the default analyzer for every happy
path here -- no audio fixtures, no SysEx stubs, fully deterministic.
A single test covers the analyzer-error branch by monkey-patching
:func:`analyze_source` to raise.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.wizard.state import InspirationSource
from rytm_randomizer.cockpit.ws import wizard_handlers
from rytm_randomizer.cockpit.ws.handlers import drain_pending_events, handle_command
from rytm_randomizer.cockpit.ws.protocol import EVENT_PROFILE_CHANGED
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.wizard_protocol import (
    EVENT_ANALYSIS_PROGRESS,
    EVENT_PROFILE_CREATED,
    EVENT_WIZARD_STATE_CHANGED,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers — fresh session, recording emitter, dispatch one envelope.
# ---------------------------------------------------------------------------


@dataclass
class _Recorder:
    """In-memory :class:`EventEmitter` that records every event for assertions."""

    events: list[dict] = field(default_factory=list)

    async def send_event(self, event: dict) -> None:
        self.events.append(event)


def _reference_snapshot() -> Snapshot:
    """Build the 4-pad reference Rytm snapshot the wizard's pad mapping targets."""

    from datetime import datetime, timezone

    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000F",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc),
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
            PadState(pad_id=3, machine="SY Raw", params={"tun": 50, "dec": 70, "lev": 95}),
            PadState(pad_id=4, machine="FX Metal", params={"tun": 64, "dec": 90, "lev": 85}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _make_session(tmp_path: Path) -> CockpitSession:
    """Construct a fresh :class:`CockpitSession` with a tmp_path-backed registry."""

    device = MockDeviceAdapter(initial=_reference_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    return CockpitSession(profile_registry=registry, history_store=history, device=device)


def _envelope(cmd_type: str, request_id: str = "req-1", **body: Any) -> dict:
    """Wrap a command body in a :class:`CommandEnvelope`-shaped dict."""

    return {"request_id": request_id, "command": {"type": cmd_type, **body}}


def _dispatch(envelope: dict, session: CockpitSession, recorder: _Recorder) -> dict:
    """Drive the dispatcher synchronously, including the post-ack drain step.

    Mirrors what :func:`rytm_randomizer.cockpit.ws.server.create_app`'s
    websocket loop does on every command: ``handle_command`` first
    (returns the ack and queues events on the session), then
    ``drain_pending_events`` to push those events through the emitter.
    """

    async def _go() -> dict:
        ack = await handle_command(envelope, session)
        await drain_pending_events(session, recorder)
        return ack

    return asyncio.run(_go())


# ---------------------------------------------------------------------------
# Full happy-path composition — start → set_metadata → add_source → analyze
# → review → save. Uses the REAL reference analyzer + REAL builder + REAL
# on-disk ProfileRegistry; no stubs, no mocks.
# ---------------------------------------------------------------------------


def test_full_wizard_flow_persists_user_profile(tmp_path: Path) -> None:
    """The full operator journey produces a saved ``kind="user"`` profile on disk."""

    session = _make_session(tmp_path)

    # Step 1: wizard_start
    start_recorder = _Recorder()
    start_ack = _dispatch(_envelope("wizard_start"), session, start_recorder)
    assert start_ack["ok"] is True
    wizard_id = start_ack["wizard_id"]
    assert isinstance(wizard_id, str) and len(wizard_id) == 26
    assert session.active_wizard is not None
    assert session.active_wizard.wizard_id == wizard_id
    assert len(start_recorder.events) == 1
    state_event = start_recorder.events[0]
    assert state_event["type"] == EVENT_WIZARD_STATE_CHANGED
    assert state_event["state"]["step"] == "name"

    # Step 2: wizard_set_metadata
    metadata_recorder = _Recorder()
    metadata_ack = _dispatch(
        _envelope("wizard_set_metadata", name="my profile", description="techno"),
        session,
        metadata_recorder,
    )
    assert metadata_ack["ok"] is True
    assert session.active_wizard.state.name == "my profile"
    assert session.active_wizard.state.description == "techno"

    # Step 3: wizard_add_source (reference mode = no filesystem)
    add_recorder = _Recorder()
    add_ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        ),
        session,
        add_recorder,
    )
    assert add_ack["ok"] is True
    source_id = add_ack["source_id"]
    assert isinstance(source_id, str) and len(source_id) == 26
    assert len(session.active_wizard.state.sources) == 1
    assert session.active_wizard.state.jobs[0].status == "pending"

    # Step 4: wizard_analyze — the REAL reference analyzer turns "Surgeon"
    # into the curated 4-trait tuple from ``_REFERENCE_LOOKUP``.
    analyze_recorder = _Recorder()
    analyze_ack = _dispatch(_envelope("wizard_analyze"), session, analyze_recorder)
    assert analyze_ack["ok"] is True
    # Per source: analyzing + terminal-OK; final state_changed.
    event_types = [e["type"] for e in analyze_recorder.events]
    assert event_types == [
        EVENT_ANALYSIS_PROGRESS,  # analyzing
        EVENT_ANALYSIS_PROGRESS,  # ok
        EVENT_WIZARD_STATE_CHANGED,
    ]
    job = session.active_wizard.state.jobs[0]
    assert job.status == "ok"
    assert job.progress == 1.0
    # "Surgeon" yields the curated 4-trait tuple (0.85, 0.78, 0.55, 0.65).
    trait_by_name = {t.name: t.value for t in job.extracted_traits}
    assert trait_by_name == {
        "rolling_low_end": 0.85,
        "metallic_tension": 0.78,
        "hat_density": 0.55,
        "filter_motion": 0.65,
    }

    # Step 5: wizard_review — builder collapses traits + assigns pads.
    review_recorder = _Recorder()
    review_ack = _dispatch(_envelope("wizard_review"), session, review_recorder)
    assert review_ack["ok"] is True
    candidate = review_ack["candidate_profile"]
    assert candidate["name"] == "my profile"
    assert candidate["kind"] == "user"
    assert candidate["model_version"] == "1.0.0"
    assert candidate["transition_curve"] == "progressive"
    # Pad mapping: 4 entries, one per canonical trait → pads 1..4.
    pad_ids = sorted(pm["pad_id"] for pm in candidate["pad_mappings"])
    assert pad_ids == [1, 2, 3, 4]
    assert candidate["source_summary"] == "1 sources · 4 analyzed signals"
    assert session.active_wizard.state.candidate_profile is not None

    # Step 6: wizard_save — registry persists to {tmp_path}/user/<id>.json.
    save_recorder = _Recorder()
    save_ack = _dispatch(_envelope("wizard_save"), session, save_recorder)
    assert save_ack["ok"] is True
    profile_id = save_ack["profile_id"]
    # Both wizard-specific AND cockpit-existing events fire on save.
    save_event_types = [e["type"] for e in save_recorder.events]
    assert EVENT_PROFILE_CREATED in save_event_types
    assert EVENT_PROFILE_CHANGED in save_event_types
    # Active wizard cleared after a successful save.
    assert session.active_wizard is None

    # On-disk persistence: {tmp_path}/user/<profile_id>.json exists.
    saved_path = tmp_path / "user" / f"{profile_id}.json"
    assert saved_path.is_file()
    # Registry sees the new profile by id.
    saved = session.profile_registry.get(profile_id)
    assert saved is not None
    assert saved.name == "my profile"
    assert saved.kind == "user"
    # And ``list_profiles`` includes it.
    listed_ids = [p.profile_id for p in session.profile_registry.list_profiles()]
    assert profile_id in listed_ids


# ---------------------------------------------------------------------------
# wizard_cancel — clears state, idempotent across calls.
# ---------------------------------------------------------------------------


def test_wizard_cancel_clears_in_flight_wizard(tmp_path: Path) -> None:
    """``wizard_cancel`` after ``wizard_start`` resets ``active_wizard`` to ``None``."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    assert session.active_wizard is not None

    cancel_recorder = _Recorder()
    cancel_ack = _dispatch(_envelope("wizard_cancel"), session, cancel_recorder)

    assert cancel_ack["ok"] is True
    assert session.active_wizard is None
    # Cancel emits no events (the UI just closes the modal).
    assert cancel_recorder.events == []


def test_wizard_cancel_with_no_active_wizard_is_idempotent(tmp_path: Path) -> None:
    """Cancelling with no wizard in flight still returns ``ok=True``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    cancel_ack = _dispatch(_envelope("wizard_cancel"), session, recorder)

    assert cancel_ack["ok"] is True
    assert session.active_wizard is None


# ---------------------------------------------------------------------------
# Negative paths — every error branch the wizard handlers expose.
# ---------------------------------------------------------------------------


def test_wizard_set_metadata_before_start_returns_error(tmp_path: Path) -> None:
    """``wizard_set_metadata`` requires an active wizard session."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_set_metadata", name="x"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


def test_wizard_add_source_invalid_kind_returns_error(tmp_path: Path) -> None:
    """An unsupported ``kind`` value is rejected by the handler validator."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="bogus",
            mode="reference",
            location="x",
            display_name="x",
        ),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "kind" in ack["error"]


def test_wizard_add_source_invalid_mode_returns_error(tmp_path: Path) -> None:
    """An unsupported ``mode`` value is rejected by the handler validator."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="kit",
            mode="bogus",
            location="x",
            display_name="x",
        ),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "mode" in ack["error"]


def test_wizard_remove_source_unknown_id_returns_error(tmp_path: Path) -> None:
    """Removing a source that is not in the state returns ``ok=False``."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    # Add a real source first so ``without_source`` can raise on the bad id.
    _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        ),
        session,
        _Recorder(),
    )
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_remove_source", source_id="does-not-exist"),
        session,
        recorder,
    )

    assert ack["ok"] is False
    # PR 14: the shared dispatcher categorises ``ValueError`` as
    # ``validation_error`` and the canonical wire ``message`` no longer
    # echoes the underlying exception text (so the unknown id from the
    # raised ``ValueError`` is intentionally absent from the wire).
    assert ack["code"] == "validation_error"
    assert "error" not in ack


def test_wizard_analyze_with_no_sources_succeeds_with_no_per_source_events(
    tmp_path: Path,
) -> None:
    """No sources → ``ok=True``, only the final ``wizard_state_changed`` event fires."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is True
    assert len(recorder.events) == 1
    assert recorder.events[0]["type"] == EVENT_WIZARD_STATE_CHANGED


def test_wizard_review_before_any_ok_job_returns_error(tmp_path: Path) -> None:
    """``wizard_review`` with no OK jobs raises ``EmptyAnalysisError`` → ack error."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    _dispatch(
        _envelope("wizard_set_metadata", name="x"),
        session,
        _Recorder(),
    )
    # No source added → no jobs → builder raises EmptyAnalysisError.
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is False
    # PR 14: ``EmptyAnalysisError`` subclasses ``ValueError`` and the
    # shared dispatcher categorises it as ``validation_error``. The
    # exception text (which would have echoed ``build_profile``) is
    # intentionally NOT on the wire -- only the categorical code is.
    assert ack["code"] == "validation_error"
    assert "error" not in ack


def test_wizard_save_before_review_returns_error(tmp_path: Path) -> None:
    """``wizard_save`` with no candidate_profile yet rejects with a clear message."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_save"), session, recorder)

    assert ack["ok"] is False
    assert "no candidate" in ack["error"]
    # active_wizard is preserved on error — only cleared on successful save.
    assert session.active_wizard is not None


def test_wizard_analyzer_failure_marks_job_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When :func:`analyze_source` raises, the job ends up ``status="failed"``.

    H4: the per-source ``error`` field is a CATEGORICAL reason -- the raw
    exception message (which routinely embeds the source path) is logged
    server-side but never echoed onto the wire. ``RuntimeError`` maps to
    :data:`wizard_handlers.REASON_ANALYSIS_FAILED`.
    """

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        ),
        session,
        _Recorder(),
    )

    def _explode(_source: InspirationSource) -> tuple:
        raise RuntimeError("analyzer crashed: simulated failure")

    monkeypatch.setattr(wizard_handlers, "analyze_source", _explode)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    # The command succeeds (per-source failures are surfaced via the job
    # status, NOT via an ack-level error).
    assert ack["ok"] is True
    job = session.active_wizard.state.jobs[0]
    assert job.status == "failed"
    assert job.error == wizard_handlers.REASON_ANALYSIS_FAILED
    # The raw exception message must NOT leak through.
    assert "analyzer crashed" not in job.error
    assert "simulated failure" not in job.error
    assert job.extracted_traits == ()


# ---------------------------------------------------------------------------
# Per-command "no active wizard" error guards — every wizard command
# other than ``wizard_start`` / ``wizard_cancel`` short-circuits when
# ``session.active_wizard is None``. These tests pin each guard so a
# refactor that removes one would surface here, not in production.
# ---------------------------------------------------------------------------


def test_wizard_add_source_without_active_wizard_returns_error(tmp_path: Path) -> None:
    """``wizard_add_source`` rejects when no wizard is in flight."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="x",
            display_name="x",
        ),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


def test_wizard_remove_source_without_active_wizard_returns_error(tmp_path: Path) -> None:
    """``wizard_remove_source`` rejects when no wizard is in flight."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_remove_source", source_id="any"),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


def test_wizard_remove_source_empty_source_id_returns_error(tmp_path: Path) -> None:
    """An empty ``source_id`` triggers the explicit guard before state mutation."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        ),
        session,
        _Recorder(),
    )
    recorder = _Recorder()

    # Omit ``source_id`` entirely; the handler reads it via ``cmd.get(...)``
    # and the default is the empty string -- the explicit guard returns
    # the "source_id is required" error before delegating to the state.
    ack = _dispatch(_envelope("wizard_remove_source"), session, recorder)

    assert ack["ok"] is False
    assert "source_id is required" in ack["error"]


def test_wizard_remove_source_happy_path_drops_source_and_job(tmp_path: Path) -> None:
    """The successful remove branch deletes both the source and its job."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    add_ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        ),
        session,
        _Recorder(),
    )
    source_id = add_ack["source_id"]
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_remove_source", source_id=source_id),
        session,
        recorder,
    )

    assert ack["ok"] is True
    assert session.active_wizard.state.sources == ()
    assert session.active_wizard.state.jobs == ()
    # The handler emits one ``wizard_state_changed`` event reflecting the drop.
    assert len(recorder.events) == 1
    assert recorder.events[0]["type"] == EVENT_WIZARD_STATE_CHANGED


def test_wizard_analyze_without_active_wizard_returns_error(tmp_path: Path) -> None:
    """``wizard_analyze`` rejects when no wizard is in flight."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


def test_wizard_review_without_active_wizard_returns_error(tmp_path: Path) -> None:
    """``wizard_review`` rejects when no wizard is in flight."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


def test_wizard_review_with_empty_name_returns_error(tmp_path: Path) -> None:
    """An empty-string name is treated as "no name" and refused by review."""

    session = _make_session(tmp_path)
    _dispatch(_envelope("wizard_start"), session, _Recorder())
    _dispatch(
        _envelope("wizard_set_metadata", name=""),
        session,
        _Recorder(),
    )
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is False
    assert "name" in ack["error"]


def test_wizard_save_without_active_wizard_returns_error(tmp_path: Path) -> None:
    """``wizard_save`` rejects when no wizard is in flight."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_save"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]
