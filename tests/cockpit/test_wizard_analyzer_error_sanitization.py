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
        # PR 4 (CODE_REVIEW.md H1) dropped the emitter from
        # handle_command's signature — the emitter is only used by
        # drain_pending_events below.
        ack = await handle_command(envelope, session)
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


# ---------------------------------------------------------------------------
# PR 9 (H4 follow-up): wizard_add_source error-path sanitization
# ---------------------------------------------------------------------------
#
# The analyzer surface was sanitized in PR 2. PR 9 completes the sweep by
# draining the two remaining wire-side ``str(exc)`` sites in
# ``_handle_wizard_add_source``: the policy-rejected path branch and the
# field-validation branch. Both now emit a fixed categorical envelope on
# the wire and stash the raw exception detail in a server-side log line.

_INVALID_KIND_SECRET = "kind-with-embedded-secret-=='/etc/passwd'"


def _make_session_with_active_wizard(tmp_path: Path) -> CockpitSession:
    """Session + active wizard ready to receive ``wizard_add_source``."""

    session = _make_session(tmp_path)
    state = WizardState.empty(_WID)
    session.active_wizard = WizardSession(wizard_id=_WID, state=state)
    return session


def test_invalid_kind_returns_sanitized_envelope_not_str_exc(tmp_path: Path) -> None:
    """``wizard_add_source`` with an invalid ``kind`` → fixed code + fixed error string."""

    session = _make_session_with_active_wizard(tmp_path)
    recorder = _Recorder()
    ack = _dispatch(
        _envelope(
            "wizard_add_source",
            kind=_INVALID_KIND_SECRET,
            mode="reference",
            location="x",
            display_name="x",
        ),
        session,
        recorder,
    )
    assert ack["ok"] is False
    assert ack["code"] == wizard_handlers.CODE_WIZARD_HANDLER_ERROR
    assert ack["error"] == wizard_handlers.ERROR_WIZARD_INVALID_SOURCE
    # The operator's input must NOT echo back; the raw ValueError
    # message embeds it via ``_safe_repr`` but the wire ack does not.
    assert _INVALID_KIND_SECRET not in ack["error"]


def test_invalid_field_logs_raw_exception_server_side(
    tmp_path: Path,
    wizard_handler_caplog: pytest.LogCaptureFixture,
) -> None:
    """The raw ValueError message lives in the server-side ``wizard_add_source_invalid`` log.

    The handler attaches the exception via ``exc_info=exc`` rather than
    calling ``str(exc)`` explicitly — that keeps the architecture
    ratchet floor (which counts ``str(<bound-exc>)`` literally) low
    while preserving the full forensic detail on the log record.
    """

    session = _make_session_with_active_wizard(tmp_path)
    recorder = _Recorder()
    with wizard_handler_caplog.at_level(logging.WARNING):
        _dispatch(
            _envelope(
                "wizard_add_source",
                kind=_INVALID_KIND_SECRET,
                mode="reference",
                location="x",
                display_name="x",
            ),
            session,
            recorder,
        )

    invalid_records = [
        rec for rec in wizard_handler_caplog.records if rec.message == "wizard_add_source_invalid"
    ]
    assert invalid_records, "wizard_add_source_invalid log line was not emitted"
    record = invalid_records[-1]
    assert record.levelno == logging.WARNING
    assert record.exception_type == "ValueError"
    assert record.kind == _INVALID_KIND_SECRET
    assert record.wizard_id == _WID
    # ``exc_info`` carries the full ValueError instance — the operator
    # running the cockpit can read the original message (which embeds the
    # rejected input via ``_safe_repr``) from there.
    assert record.exc_info is not None
    _exc_type, exc_value, _tb = record.exc_info
    assert isinstance(exc_value, ValueError)
    assert _INVALID_KIND_SECRET in str(exc_value)


def test_path_rejected_returns_sanitized_envelope_not_str_exc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A path that fails the allow-list returns the fixed sanitized envelope.

    The underlying :class:`WizardSourcePathRejected` messages are already
    categorical, but the wire ack must not call ``str(exc)`` — the
    architecture ratchet forbids that pattern at the wire boundary
    regardless of message content.
    """

    from rytm_randomizer.cockpit.wizard.path_policy import WizardPathPolicy

    session = _make_session_with_active_wizard(tmp_path)
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
    assert ack["code"] == wizard_handlers.CODE_WIZARD_SOURCE_PATH_REJECTED
    assert ack["error"] == wizard_handlers.ERROR_WIZARD_SOURCE_PATH_REJECTED
    assert str(outside) not in ack["error"]


def test_path_rejected_logs_categorical_reason_server_side(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wizard_handler_caplog: pytest.LogCaptureFixture,
) -> None:
    """The categorical rejection reason + offending path are captured in the WARNING log."""

    from rytm_randomizer.cockpit.wizard.path_policy import WizardPathPolicy

    session = _make_session_with_active_wizard(tmp_path)
    blessed = tmp_path / "blessed"
    blessed.mkdir()
    monkeypatch.setattr(
        wizard_handlers, "_PATH_POLICY", WizardPathPolicy(roots=(blessed.resolve(),))
    )
    outside = tmp_path / "outside.syx"
    outside.write_bytes(b"\x00")

    recorder = _Recorder()
    with wizard_handler_caplog.at_level(logging.WARNING):
        _dispatch(
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

    rejected_records = [
        rec for rec in wizard_handler_caplog.records if rec.message == "wizard_source_path_rejected"
    ]
    assert rejected_records, "wizard_source_path_rejected log line was not emitted"
    record = rejected_records[-1]
    assert record.levelno == logging.WARNING
    # Categorical reason from WizardSourcePathRejected ("path is outside the allowed roots").
    assert "outside" in record.reason or "allowed" in record.reason
    assert record.location == str(outside)
    assert record.wizard_id == _WID
