"""Unit tests for ``rytm_randomizer.cockpit.ws.wizard_handlers`` — 8 commands.

Each wizard handler is exercised on both happy and error paths through
the public dispatcher in :mod:`handlers`. The dispatcher integration
test confirms the ``cmd_type.startswith("wizard_")`` branch routes to
:data:`WIZARD_HANDLERS` correctly.

The analyzer handler (``wizard_analyze``) uses :func:`asyncio.to_thread`
internally; the tests stub :func:`analyze_source` via ``monkeypatch`` on
the handler module so the analyzer's real file I/O is bypassed and the
test stays deterministic + fast.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/ws/wizard_handlers.py`` and the additive
dispatcher branch in ``rytm_randomizer/cockpit/ws/handlers.py``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot, StyleTrait
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.wizard.state import (
    AnalysisJob,
    InspirationSource,
    WizardState,
)
from rytm_randomizer.cockpit.ws import wizard_handlers
from rytm_randomizer.cockpit.ws.handlers import drain_pending_events, handle_command
from rytm_randomizer.cockpit.ws.protocol import EVENT_PROFILE_CHANGED
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.wizard_protocol import (
    EVENT_ANALYSIS_PROGRESS,
    EVENT_PROFILE_CREATED,
    EVENT_WIZARD_STATE_CHANGED,
)
from rytm_randomizer.cockpit.ws.wizard_session import WizardSession

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)
_WID = "01HXY5Q9PJM0000000000WIZARD"


# ---------------------------------------------------------------------------
# Recorder + session fixtures.
# ---------------------------------------------------------------------------


@dataclass
class _Recorder:
    events: list[dict] = field(default_factory=list)

    async def send_event(self, event: dict) -> None:
        self.events.append(event)


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000A",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 30, "dec": 80, "lev": 110}),),
        scene_slot="A01",
        bpm=124.0,
    )


def _make_session(tmp_path: Path) -> CockpitSession:
    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    return CockpitSession(profile_registry=registry, history_store=history, device=device)


def _attach_wizard(session: CockpitSession, *, with_source: bool = False) -> WizardSession:
    """Attach a fresh :class:`WizardSession` to ``session`` and return it."""

    state = WizardState.empty(_WID)
    if with_source:
        state = state.with_source(
            InspirationSource(
                source_id="src-1",
                kind="artist",
                mode="reference",
                location="Surgeon",
                display_name="Surgeon",
                added_at=_FIXED_TS,
            )
        )
    wizard = WizardSession(wizard_id=_WID, state=state)
    session.active_wizard = wizard
    return wizard


def _envelope(cmd_type: str, request_id: str = "req-1", **body: Any) -> dict:
    return {"request_id": request_id, "command": {"type": cmd_type, **body}}


def _dispatch(envelope: dict, session: CockpitSession, recorder: _Recorder) -> dict:
    async def _go() -> dict:
        ack = await handle_command(envelope, session, recorder)
        await drain_pending_events(session, recorder)
        return ack

    return asyncio.run(_go())


# ---------------------------------------------------------------------------
# Dispatcher integration — wizard_ commands route to wizard handlers.
# ---------------------------------------------------------------------------


def test_dispatcher_routes_wizard_prefix_to_wizard_handlers(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_start"), session, recorder)

    assert ack["ok"] is True
    assert "wizard_id" in ack
    assert session.active_wizard is not None
    assert recorder.events[0]["type"] == EVENT_WIZARD_STATE_CHANGED


def test_dispatcher_returns_error_for_unknown_wizard_command(tmp_path: Path) -> None:
    """An unknown ``wizard_*`` command name still routes through the wizard branch."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_not_a_real_command"), session, recorder)

    assert ack["ok"] is False
    assert "unknown command" in ack["error"]


# ---------------------------------------------------------------------------
# wizard_start — always succeeds; replaces any in-flight wizard.
# ---------------------------------------------------------------------------


def test_wizard_start_creates_fresh_session_and_emits_state(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_start"), session, recorder)

    assert ack["ok"] is True
    assert isinstance(ack["wizard_id"], str) and len(ack["wizard_id"]) == 26
    assert session.active_wizard is not None
    assert session.active_wizard.wizard_id == ack["wizard_id"]
    assert session.active_wizard.state.step == "name"
    assert len(recorder.events) == 1
    assert recorder.events[0]["state"]["wizard_id"] == ack["wizard_id"]


def test_wizard_start_replaces_any_in_flight_wizard(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session)
    original_wid = session.active_wizard.wizard_id  # type: ignore[union-attr]
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_start"), session, recorder)

    assert ack["ok"] is True
    assert session.active_wizard is not None
    assert session.active_wizard.wizard_id != original_wid


# ---------------------------------------------------------------------------
# wizard_set_metadata — name / description / both / no-wizard.
# ---------------------------------------------------------------------------


def test_wizard_set_metadata_sets_name_only(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_set_metadata", name="buzzi"), session, recorder)

    assert ack["ok"] is True
    assert session.active_wizard.state.name == "buzzi"  # type: ignore[union-attr]
    assert session.active_wizard.state.description is None  # type: ignore[union-attr]


def test_wizard_set_metadata_sets_both(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_set_metadata", name="buzzi", description="industrial techno"),
        session,
        recorder,
    )

    assert ack["ok"] is True
    assert session.active_wizard.state.name == "buzzi"  # type: ignore[union-attr]
    assert (
        session.active_wizard.state.description == "industrial techno"  # type: ignore[union-attr]
    )
    assert ack["state"]["name"] == "buzzi"


def test_wizard_set_metadata_leaves_omitted_fields_unchanged(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    wizard = _attach_wizard(session)
    wizard.state = wizard.state.with_metadata(name="initial", description="initial-desc")
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_set_metadata", name="updated"),
        session,
        recorder,
    )

    assert ack["ok"] is True
    # name updated, description preserved
    assert session.active_wizard.state.name == "updated"  # type: ignore[union-attr]
    assert session.active_wizard.state.description == "initial-desc"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# C4 — three-state wire semantics for ``wizard_set_metadata``.
# Missing key → unchanged; explicit ``null`` → cleared; string → set.
# ---------------------------------------------------------------------------


def test_wizard_set_metadata_null_name_clears_field(tmp_path: Path) -> None:
    """JSON ``null`` clears the field (C4 fix).

    Previously the handler treated ``None`` as "leave unchanged", which
    inverted the documented :meth:`WizardState.with_metadata` contract.
    The fix routes explicit ``null`` to ``with_metadata(name="")`` so the
    field actually clears.
    """

    session = _make_session(tmp_path)
    wizard = _attach_wizard(session)
    wizard.state = wizard.state.with_metadata(name="initial", description="initial-desc")
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_set_metadata", name=None),
        session,
        recorder,
    )

    assert ack["ok"] is True
    assert session.active_wizard.state.name == ""  # type: ignore[union-attr]
    # description was not touched (key was absent in the envelope body)
    assert session.active_wizard.state.description == "initial-desc"  # type: ignore[union-attr]


def test_wizard_set_metadata_null_description_clears_field(tmp_path: Path) -> None:
    """JSON ``null`` clears description while leaving name alone (C4 fix)."""

    session = _make_session(tmp_path)
    wizard = _attach_wizard(session)
    wizard.state = wizard.state.with_metadata(name="initial", description="initial-desc")
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_set_metadata", description=None),
        session,
        recorder,
    )

    assert ack["ok"] is True
    assert session.active_wizard.state.name == "initial"  # type: ignore[union-attr]
    assert session.active_wizard.state.description == ""  # type: ignore[union-attr]


def test_wizard_set_metadata_missing_keys_leave_state_unchanged(tmp_path: Path) -> None:
    """No ``name`` / ``description`` keys → both fields preserved (C4 fix).

    Distinct from the prior test: this asserts the "missing" branch
    behaves differently from the "explicit ``null``" branch — exactly
    the inversion C4 catches.
    """

    session = _make_session(tmp_path)
    wizard = _attach_wizard(session)
    wizard.state = wizard.state.with_metadata(name="initial", description="initial-desc")
    recorder = _Recorder()

    # Envelope intentionally carries neither ``name`` nor ``description``.
    ack = _dispatch(_envelope("wizard_set_metadata"), session, recorder)

    assert ack["ok"] is True
    assert session.active_wizard.state.name == "initial"  # type: ignore[union-attr]
    assert session.active_wizard.state.description == "initial-desc"  # type: ignore[union-attr]


def test_wizard_set_metadata_without_active_wizard_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_set_metadata", name="x"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


# ---------------------------------------------------------------------------
# wizard_add_source — happy + invalid kind + invalid mode + no-wizard.
# ---------------------------------------------------------------------------


def test_wizard_add_source_appends_reference_source(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        ),
        session,
        recorder,
    )

    assert ack["ok"] is True
    assert isinstance(ack["source_id"], str) and len(ack["source_id"]) == 26
    wizard = session.active_wizard
    assert wizard is not None
    assert len(wizard.state.sources) == 1
    assert wizard.state.sources[0].kind == "artist"
    assert len(wizard.state.jobs) == 1
    assert wizard.state.jobs[0].status == "pending"


def test_wizard_add_source_invalid_kind_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session)
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
    session = _make_session(tmp_path)
    _attach_wizard(session)
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


def test_wizard_add_source_without_active_wizard_returns_error(tmp_path: Path) -> None:
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


# ---------------------------------------------------------------------------
# wizard_remove_source — happy + missing-id + no-wizard.
# ---------------------------------------------------------------------------


def test_wizard_remove_source_drops_source_and_job(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_remove_source", source_id="src-1"),
        session,
        recorder,
    )

    assert ack["ok"] is True
    wizard = session.active_wizard
    assert wizard is not None
    assert wizard.state.sources == ()
    assert wizard.state.jobs == ()


def test_wizard_remove_source_unknown_id_returns_error(tmp_path: Path) -> None:
    """``state.without_source`` raises ``ValueError`` which the dispatcher catches."""

    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_remove_source", source_id="missing"),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "missing" in ack["error"]


def test_wizard_remove_source_empty_id_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_remove_source"), session, recorder)

    assert ack["ok"] is False
    assert "source_id is required" in ack["error"]


def test_wizard_remove_source_without_active_wizard_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(
        _envelope("wizard_remove_source", source_id="any"),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


# ---------------------------------------------------------------------------
# wizard_analyze — happy + failed + no-wizard + no-sources.
# ---------------------------------------------------------------------------


def test_wizard_analyze_happy_path_marks_job_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The analyzer is stubbed to return a deterministic trait tuple."""

    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    def _stub_analyze(source: InspirationSource) -> tuple[StyleTrait, ...]:
        return (StyleTrait(name="rolling_low_end", value=0.7),)

    monkeypatch.setattr(wizard_handlers, "analyze_source", _stub_analyze)

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is True
    wizard = session.active_wizard
    assert wizard is not None
    job = wizard.state.jobs[0]
    assert job.status == "ok"
    assert job.progress == 1.0
    assert job.extracted_traits[0].value == 0.7
    # Per-source: analyzing event + terminal event; plus final state_changed.
    event_types = [e["type"] for e in recorder.events]
    assert event_types == [
        EVENT_ANALYSIS_PROGRESS,  # analyzing
        EVENT_ANALYSIS_PROGRESS,  # ok
        EVENT_WIZARD_STATE_CHANGED,
    ]


def test_wizard_analyze_failed_source_marks_job_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the analyzer raises, the job transitions to ``failed`` with the message."""

    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    def _boom(source: InspirationSource) -> tuple[StyleTrait, ...]:
        raise FileNotFoundError("no such file: /tmp/x")

    monkeypatch.setattr(wizard_handlers, "analyze_source", _boom)

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is True  # the command succeeded; the job failed
    wizard = session.active_wizard
    assert wizard is not None
    job = wizard.state.jobs[0]
    assert job.status == "failed"
    assert job.error is not None and "no such file" in job.error
    assert job.extracted_traits == ()


def test_wizard_analyze_without_sources_emits_only_state_changed(tmp_path: Path) -> None:
    """No sources → no per-source progress events, just the final state event."""

    session = _make_session(tmp_path)
    _attach_wizard(session)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is True
    assert len(recorder.events) == 1
    assert recorder.events[0]["type"] == EVENT_WIZARD_STATE_CHANGED


def test_wizard_analyze_without_active_wizard_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


# ---------------------------------------------------------------------------
# wizard_review — happy + no-name + no-wizard.
# ---------------------------------------------------------------------------


def test_wizard_review_builds_candidate_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _make_session(tmp_path)
    wizard = _attach_wizard(session, with_source=True)
    wizard.state = wizard.state.with_metadata(name="buzzi", description="test")
    wizard.state = wizard.state.with_job_update(
        AnalysisJob(
            source_id="src-1",
            status="ok",
            progress=1.0,
            error=None,
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.6),),
        )
    )
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is True
    assert ack["candidate_profile"]["name"] == "buzzi"
    assert ack["candidate_profile"]["kind"] == "user"
    assert session.active_wizard is not None
    assert session.active_wizard.state.candidate_profile is not None


def test_wizard_review_without_name_returns_error(tmp_path: Path) -> None:
    """``WizardState.name`` is ``None`` by default; review must refuse."""

    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is False
    assert "name" in ack["error"]


def test_wizard_review_with_empty_string_name_returns_error(tmp_path: Path) -> None:
    """An empty string is treated as "no name" — refuse to advance."""

    session = _make_session(tmp_path)
    wizard = _attach_wizard(session, with_source=True)
    wizard.state = wizard.state.with_metadata(name="")
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is False
    assert "name" in ack["error"]


def test_wizard_review_without_active_wizard_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_review"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


# ---------------------------------------------------------------------------
# wizard_save — happy + no-candidate + no-wizard.
# ---------------------------------------------------------------------------


def test_wizard_save_persists_profile_and_emits_both_events(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    wizard = _attach_wizard(session, with_source=True)
    wizard.state = wizard.state.with_metadata(name="buzzi")
    wizard.state = wizard.state.with_job_update(
        AnalysisJob(
            source_id="src-1",
            status="ok",
            progress=1.0,
            error=None,
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.6),),
        )
    )
    # Pre-build the candidate via wizard_review (so wizard_save has something to save).
    _dispatch(_envelope("wizard_review"), session, _Recorder())
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_save"), session, recorder)

    assert ack["ok"] is True
    profile_id = ack["profile_id"]
    # The profile is now in the registry.
    saved = session.profile_registry.get(profile_id)
    assert saved is not None
    assert saved.name == "buzzi"
    assert saved.kind == "user"
    # Both wizard-specific and cockpit-existing events fire.
    event_types = [e["type"] for e in recorder.events]
    assert EVENT_PROFILE_CREATED in event_types
    assert EVENT_PROFILE_CHANGED in event_types
    # active_wizard is cleared after a successful save.
    assert session.active_wizard is None


def test_wizard_save_without_candidate_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_save"), session, recorder)

    assert ack["ok"] is False
    assert "no candidate" in ack["error"]
    assert session.active_wizard is not None  # cleared only on success


def test_wizard_save_without_active_wizard_returns_error(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_save"), session, recorder)

    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


# ---------------------------------------------------------------------------
# wizard_cancel — clears the session; idempotent.
# ---------------------------------------------------------------------------


def test_wizard_cancel_clears_active_wizard(tmp_path: Path) -> None:
    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_cancel"), session, recorder)

    assert ack["ok"] is True
    assert session.active_wizard is None
    assert recorder.events == []  # cancel emits no events


def test_wizard_cancel_is_idempotent_when_no_wizard_active(tmp_path: Path) -> None:
    """Cancelling with nothing in flight still returns ``ok=True``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    ack = _dispatch(_envelope("wizard_cancel"), session, recorder)

    assert ack["ok"] is True
    assert session.active_wizard is None
