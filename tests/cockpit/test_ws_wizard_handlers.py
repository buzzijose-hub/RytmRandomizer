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
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot, StyleTrait
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.wizard.path_policy import WizardPathPolicy
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
    """When the analyzer raises, the job transitions to ``failed`` with a categorical reason.

    H4: the failure reason is one of
    :data:`wizard_handlers.ANALYZER_FAILURE_REASONS` -- the analyzer
    exception message (which often embeds the source path) is NEVER
    forwarded over the wire. Here ``FileNotFoundError`` maps to
    ``"path_not_found"`` and the offending path stays out of the ack.
    """

    session = _make_session(tmp_path)
    _attach_wizard(session, with_source=True)
    recorder = _Recorder()

    secret_marker = "no-such-file-marker"

    def _boom(source: InspirationSource) -> tuple[StyleTrait, ...]:
        raise FileNotFoundError(f"no such file: {secret_marker}")

    monkeypatch.setattr(wizard_handlers, "analyze_source", _boom)

    ack = _dispatch(_envelope("wizard_analyze"), session, recorder)

    assert ack["ok"] is True  # the command succeeded; the job failed
    wizard = session.active_wizard
    assert wizard is not None
    job = wizard.state.jobs[0]
    assert job.status == "failed"
    assert job.error == wizard_handlers.REASON_PATH_NOT_FOUND
    # The original path / message must NOT leak through.
    assert job.error is not None and secret_marker not in job.error
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


# ---------------------------------------------------------------------------
# M11 — wizard_start emits telemetry when it replaces an in-flight wizard.
# ---------------------------------------------------------------------------


@pytest.fixture
def wizard_handler_caplog(
    caplog: pytest.LogCaptureFixture,
) -> pytest.LogCaptureFixture:
    """Capture wizard-handler warnings even with package logger propagation off.

    The package logger sets ``propagate = False`` at import time (see
    ``rytm_randomizer.observability.__init__``), so caplog's default
    root-level handler never sees records emitted by
    ``rytm_randomizer.cockpit.ws.wizard_handlers``. Attaching
    ``caplog.handler`` directly to the module logger restores visibility
    inside the test scope and the teardown removes it cleanly. Mirrors the
    fixture in ``test_wizard_analyzer_error_sanitization.py``.
    """

    logger = logging.getLogger("rytm_randomizer.cockpit.ws.wizard_handlers")
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


def test_wizard_start_replacement_logs_warning_with_previous_id(
    tmp_path: Path, wizard_handler_caplog: pytest.LogCaptureFixture
) -> None:
    """Replacing an in-flight wizard fires a ``wizard_replaced`` WARNING with structure."""

    session = _make_session(tmp_path)
    previous = _attach_wizard(session, with_source=True)
    # Backdate ``started_at`` so the age-seconds field has a meaningful value.
    previous.started_at = datetime.now(timezone.utc) - timedelta(seconds=42)
    recorder = _Recorder()

    with wizard_handler_caplog.at_level(logging.WARNING):
        ack = _dispatch(_envelope("wizard_start"), session, recorder)

    assert ack["ok"] is True
    assert ack["previous_wizard_id"] == previous.wizard_id
    records = [rec for rec in wizard_handler_caplog.records if rec.message == "wizard_replaced"]
    assert records, "wizard_replaced WARNING was not emitted"
    record = records[-1]
    assert record.levelno == logging.WARNING
    assert record.previous_wizard_id == previous.wizard_id
    assert record.new_wizard_id == ack["wizard_id"]
    assert record.previous_step == previous.state.step
    assert record.previous_source_count == len(previous.state.sources)
    age = record.previous_state_age_seconds
    assert age >= 40.0  # backdated by 42s; allow for clock drift


def test_wizard_start_without_replacement_omits_previous_wizard_id(
    tmp_path: Path, wizard_handler_caplog: pytest.LogCaptureFixture
) -> None:
    """A clean start (no in-flight wizard) must NOT include ``previous_wizard_id``."""

    session = _make_session(tmp_path)
    recorder = _Recorder()

    with wizard_handler_caplog.at_level(logging.WARNING):
        ack = _dispatch(_envelope("wizard_start"), session, recorder)

    assert ack["ok"] is True
    assert "previous_wizard_id" not in ack
    assert [rec for rec in wizard_handler_caplog.records if rec.message == "wizard_replaced"] == []


# ---------------------------------------------------------------------------
# C2 — wizard_add_source enforces the path policy on file/folder modes.
# ---------------------------------------------------------------------------


def test_wizard_add_source_rejects_out_of_root_file_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file path outside the policy roots is refused categorically."""

    session = _make_session(tmp_path)
    _attach_wizard(session)
    # Pin the policy to ``tmp_path / blessed`` so out-of-root means OUTSIDE that subdir.
    blessed = tmp_path / "blessed"
    blessed.mkdir()
    monkeypatch.setattr(
        wizard_handlers, "_PATH_POLICY", WizardPathPolicy(roots=(blessed.resolve(),))
    )
    outside = tmp_path / "outside.syx"
    outside.write_bytes(b"\x00")

    recorder = _Recorder()
    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="kit",
            mode="file",
            location=str(outside),
            display_name="rejected kit",
        ),
        session,
        recorder,
    )

    assert ack["ok"] is False
    assert ack["code"] == "wizard_source_path_rejected"
    # The rejected path itself must NOT echo back over the wire.
    assert str(outside) not in ack["error"]
    assert "outside.syx" not in ack["error"]
    # The wizard state was not mutated.
    assert session.active_wizard.state.sources == ()  # type: ignore[union-attr]


def test_wizard_add_source_accepts_in_root_file_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file inside an allow-listed root passes the policy and lands as a source."""

    session = _make_session(tmp_path)
    _attach_wizard(session)
    blessed = tmp_path / "blessed"
    blessed.mkdir()
    monkeypatch.setattr(
        wizard_handlers, "_PATH_POLICY", WizardPathPolicy(roots=(blessed.resolve(),))
    )
    target = blessed / "kit.syx"
    target.write_bytes(b"\x00")

    recorder = _Recorder()
    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind="kit",
            mode="file",
            location=str(target),
            display_name="real kit",
        ),
        session,
        recorder,
    )

    assert ack["ok"] is True
    sources = session.active_wizard.state.sources  # type: ignore[union-attr]
    assert len(sources) == 1
    assert sources[0].location == str(target)


def test_wizard_add_source_skips_policy_for_reference_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reference-mode locations are free-text and skip the filesystem allow-list."""

    session = _make_session(tmp_path)
    _attach_wizard(session)
    blessed = tmp_path / "blessed"
    blessed.mkdir()
    monkeypatch.setattr(
        wizard_handlers, "_PATH_POLICY", WizardPathPolicy(roots=(blessed.resolve(),))
    )

    recorder = _Recorder()
    # An artist name is not a filesystem path; it must not be policy-checked.
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
    sources = session.active_wizard.state.sources  # type: ignore[union-attr]
    assert sources[0].location == "Surgeon"
