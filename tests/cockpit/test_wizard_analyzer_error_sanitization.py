"""Tests for the H4 analyzer error sanitization in ``wizard_handlers``.

The wizard analyzer surface used to forward ``str(exc)`` from any
analyzer failure straight into the ``AnalysisJob.error`` field, which is
broadcast as ``analysis_progress`` to every connected client. Analyzer
exceptions routinely embed the source path -- so a hostile WS peer could
probe the filesystem ("does ``/etc/passwd`` exist?") via the error
field. PR 2 / H4 of the code-review plan replaced the leak with:

1. A fixed set of categorical reasons (``"path_not_found"``,
   ``"unsupported_format"``, ``"read_failed"``, ``"analysis_failed"``)
   that the wire-level ``error`` field can carry.
2. A server-side WARNING log line with the full exception detail
   (including the path) for operator triage.

Every test below pins one mapping or one log-line guarantee.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot, StyleTrait
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.wizard.errors import WizardSourcePathError
from rytm_randomizer.cockpit.wizard.path_policy import WizardSourcePathRejected
from rytm_randomizer.cockpit.wizard.state import (
    InspirationSource,
    WizardState,
)
from rytm_randomizer.cockpit.ws import wizard_handlers
from rytm_randomizer.cockpit.ws.handlers import drain_pending_events, handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.wizard_session import WizardSession

pytestmark = pytest.mark.fast

_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)
_WID = "01HXY5Q9PJM0000000000WIZARD"
_SECRET_PATH = "/etc/super-secret/private-file.syx"


# ---------------------------------------------------------------------------
# Recorder + session fixtures (mirroring test_ws_wizard_handlers.py).
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
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 30}),),
        scene_slot="A01",
        bpm=124.0,
    )


def _make_session(tmp_path: Path) -> CockpitSession:
    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    return CockpitSession(profile_registry=registry, history_store=history, device=device)


def _attach_wizard_with_source(session: CockpitSession) -> WizardSession:
    """Attach a wizard with one ``artist``/``reference`` source ready for analysis."""

    state = WizardState.empty(_WID).with_source(
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


def _run_analyze_with_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exc: BaseException,
) -> tuple[_Recorder, CockpitSession]:
    """Run ``wizard_analyze`` with the analyzer stubbed to raise ``exc``."""

    session = _make_session(tmp_path)
    _attach_wizard_with_source(session)
    recorder = _Recorder()

    def _boom(_source: InspirationSource) -> tuple[StyleTrait, ...]:
        raise exc

    monkeypatch.setattr(wizard_handlers, "analyze_source", _boom)
    _dispatch(_envelope("wizard_analyze"), session, recorder)
    return recorder, session


# ---------------------------------------------------------------------------
# Exception-type -> categorical-reason mapping
# ---------------------------------------------------------------------------


def test_file_not_found_maps_to_path_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _recorder, session = _run_analyze_with_exception(
        tmp_path, monkeypatch, FileNotFoundError(f"missing: {_SECRET_PATH}")
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert job.status == "failed"
    assert job.error == wizard_handlers.REASON_PATH_NOT_FOUND


def test_wizard_source_path_error_maps_to_path_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The analyzer's own taxonomy error (analyze.py / sysex_analyzer.py) maps cleanly."""

    _recorder, session = _run_analyze_with_exception(
        tmp_path, monkeypatch, WizardSourcePathError(f"kit path does not exist: {_SECRET_PATH}")
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert job.error == wizard_handlers.REASON_PATH_NOT_FOUND


def test_wizard_source_path_rejected_maps_to_path_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A policy-rejected path raised from inside the analyzer also reads as path_not_found."""

    _recorder, session = _run_analyze_with_exception(
        tmp_path, monkeypatch, WizardSourcePathRejected("path outside the allowed roots")
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert job.error == wizard_handlers.REASON_PATH_NOT_FOUND


def test_value_error_maps_to_unsupported_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _recorder, session = _run_analyze_with_exception(
        tmp_path,
        monkeypatch,
        ValueError(f"unsupported (kind, mode) combination at {_SECRET_PATH}"),
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert job.error == wizard_handlers.REASON_UNSUPPORTED_FORMAT


def test_os_error_maps_to_read_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _recorder, session = _run_analyze_with_exception(
        tmp_path, monkeypatch, PermissionError(f"cannot read {_SECRET_PATH}")
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    # PermissionError is an OSError but NOT a FileNotFoundError.
    assert job.error == wizard_handlers.REASON_READ_FAILED


def test_runtime_error_maps_to_analysis_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _recorder, session = _run_analyze_with_exception(
        tmp_path, monkeypatch, RuntimeError(f"librosa crashed on {_SECRET_PATH}")
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert job.error == wizard_handlers.REASON_ANALYSIS_FAILED


# ---------------------------------------------------------------------------
# Information disclosure guarantee: paths never reach the wire-shaped fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        FileNotFoundError(f"missing: {_SECRET_PATH}"),
        WizardSourcePathError(f"kit path does not exist: {_SECRET_PATH}"),
        ValueError(f"unsupported at {_SECRET_PATH}"),
        PermissionError(f"cannot read {_SECRET_PATH}"),
        RuntimeError(f"librosa crashed on {_SECRET_PATH}"),
    ],
)
def test_path_never_appears_in_analysis_job_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exc: BaseException
) -> None:
    """No matter the analyzer exception, the source path stays out of every job field."""

    recorder, session = _run_analyze_with_exception(tmp_path, monkeypatch, exc)
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert _SECRET_PATH not in (job.error or "")
    for trait in job.extracted_traits:
        assert _SECRET_PATH not in trait.name

    # Walk every analysis_progress event payload too.
    for event in recorder.events:
        if event.get("type") != "analysis_progress":
            continue
        job_dict = event["job"]
        assert _SECRET_PATH not in (job_dict.get("error") or "")


def test_reason_is_one_of_the_fixed_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every emitted reason must be a member of :data:`ANALYZER_FAILURE_REASONS`."""

    _recorder, session = _run_analyze_with_exception(
        tmp_path, monkeypatch, FileNotFoundError("missing")
    )
    job = session.active_wizard.state.jobs[0]  # type: ignore[union-attr]
    assert job.error in wizard_handlers.ANALYZER_FAILURE_REASONS


# ---------------------------------------------------------------------------
# Server-side logging: full detail IS captured
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
    inside the test scope and the teardown removes it cleanly.
    """

    logger = logging.getLogger("rytm_randomizer.cockpit.ws.wizard_handlers")
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


def test_full_exception_detail_is_logged_server_side(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wizard_handler_caplog: pytest.LogCaptureFixture,
) -> None:
    """The server logs the raw exception message (including the path) at WARNING."""

    with wizard_handler_caplog.at_level(logging.WARNING):
        _run_analyze_with_exception(
            tmp_path,
            monkeypatch,
            FileNotFoundError(f"audio path does not exist: {_SECRET_PATH}"),
        )

    # Find the analyzer-failure record we just emitted.
    failure_records = [
        rec for rec in wizard_handler_caplog.records if rec.message == "wizard_analyzer_failure"
    ]
    assert failure_records, "wizard_analyzer_failure log line was not emitted"
    record = failure_records[-1]

    # The categorical reason AND the raw detail are both present
    # server-side -- the operator running the cockpit can triage with the
    # full path while the WS caller saw only "path_not_found".
    assert record.levelno == logging.WARNING
    assert record.reason == wizard_handlers.REASON_PATH_NOT_FOUND
    assert record.exception_type == "FileNotFoundError"
    assert _SECRET_PATH in record.exception_message
    assert record.source_id == "src-1"
    assert record.wizard_id == _WID
