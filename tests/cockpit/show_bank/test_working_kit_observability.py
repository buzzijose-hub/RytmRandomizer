"""Working-source policy refusals retain closed diagnostics and committed evidence."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    KitCaptureResult,
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.show_bank import RetainedSysexArtifact, ShowKitCapture
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.export import ShowPackImportResult, ShowPackService
from rytm_randomizer.cockpit.show_bank.store import validate_show_bank_capture_frame
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.protocol import ERR_INTERNAL, ERR_VALIDATION
from rytm_randomizer.cockpit.ws.result import HandlerResult
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.show_bank_handlers import local_artifact_failure_message
from rytm_randomizer.data.analog_four_saved_kit_layout import AnalogFourKitSourceKind
from rytm_randomizer.devices.strategies.analog_four_saved_kit_candidate import (
    validate_analog_four_candidate_source,
)
from rytm_randomizer.observability.errors import (
    BoundaryError,
    DataError,
    WorkingKitSourceRefusalError,
)
from rytm_randomizer.observability.metrics import get_metrics

from .conftest import ShowBankHarness, build_show_bank_harness

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def _files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def _working_capture(indexed: KitCaptureResult) -> KitCaptureResult:
    frame = bytearray(indexed.frame)
    frame[6] = 0x58
    working = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, bytes(frame))
    assert working.fingerprint == indexed.fingerprint
    return replace(working, captured_at=indexed.captured_at, snapshot_layout="saved_kit")


def _claim_frame(capture: ShowKitCapture, frame: bytes) -> ShowKitCapture:
    digest = sha256(frame).hexdigest()
    return replace(
        capture,
        sysex=replace(
            capture.sysex,
            frame_sha256=digest,
            frame_bytes=len(frame),
            retained=RetainedSysexArtifact(f"{digest}.syx", digest, len(frame)),
        ),
    )


@pytest.fixture
def refusal_session(tmp_path: Path) -> tuple[ShowBankHarness, CockpitSession]:
    harness = build_show_bank_harness(tmp_path)
    workspace = harness.workspace
    (candidate,) = workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        profile=harness.profile,
        depth_preset="small",
        depth=0.0,
        seed=91,
        candidate_count=1,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(),
        analog_four_locks=(1, 2, 3, 4),
    )
    assert candidate.analog_four_candidate.values == ()
    workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    for device in harness.captures:
        workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device,
            hardware_slot=64,
        )
    snapshot = cockpit_snapshot_from_rytm_capture(harness.rytm)
    history = HistoryStore()
    history.initial(snapshot)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial=snapshot),
        kit_captures=harness.captures,
        show_kit_forge=workspace,
    )
    return harness, session


def _fresh_captures(harness: ShowBankHarness) -> dict[str, KitCaptureResult]:
    harness.clock.current += timedelta(minutes=2)
    return {
        device: replace(capture, captured_at=harness.clock.current - timedelta(minutes=1))
        for device, capture in harness.captures.items()
    }


def _request(session: CockpitSession, command: dict[str, object]) -> dict[str, object]:
    return asyncio.run(
        handlers.handle_command({"request_id": "working-source", "command": command}, session)
    )


@pytest.mark.parametrize(
    "action",
    ["show_bank_adopt_sources", "show_bank_verify_recapture", "show_bank_run_preflight"],
)
def test_ws_working_source_refusal_preserves_bank_and_reports_one_safe_fingerprint(
    refusal_session: tuple[ShowBankHarness, CockpitSession],
    ws_handler_caplog: pytest.LogCaptureFixture,
    action: str,
) -> None:
    harness, session = refusal_session
    workspace = harness.workspace
    captures = _fresh_captures(harness)
    if action == "show_bank_run_preflight":
        workspace.verify_recaptures(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            captures=captures,
        )
        captures = _fresh_captures(harness)
    session.kit_captures = {
        **captures,
        ANALOG_FOUR_DEVICE_ID: _working_capture(captures[ANALOG_FOUR_DEVICE_ID]),
    }
    bank = workspace.bank(harness.bank_id)
    before = _files(harness.store.root)
    history = session.history_store.current
    snapshot = session.device.capture_snapshot()
    metrics = get_metrics()
    errors_before = metrics.errors_by_kind.copy()
    sent_before = metrics.cc_sent_by_channel.copy()
    ws_handler_caplog.clear()
    command: dict[str, object] = {
        "type": action,
        "bank_id": harness.bank_id,
        "entry_id": harness.entry_id,
        "expected_revision": bank.revision,
        "rytm_fingerprint": harness.rytm.fingerprint,
        "a4_fingerprint": harness.analog_four.fingerprint,
        "rytm_slot": 20,
        "a4_slot": 21,
    }
    ack = _request(session, command)
    assert ack == {
        "request_id": "working-source",
        "ok": False,
        "code": ERR_VALIDATION,
        "message": WorkingKitSourceRefusalError.recovery_message,
    }
    fingerprint = WorkingKitSourceRefusalError.fingerprint
    errors_before[fingerprint] += 1
    assert metrics.errors_by_kind == errors_before
    assert metrics.cc_sent_by_channel == sent_before
    (journal,) = session.error_journal.entries
    assert journal.fingerprint == fingerprint
    assert journal.message == ack["message"]
    assert dict(journal.context) == {"cmd_type": action, "code": ERR_VALIDATION}
    records = [item for item in ws_handler_caplog.records if item.msg == "handler_exception"]
    assert len(records) == 1
    assert records[0].fingerprint == fingerprint
    assert records[0].exception_type == "WorkingKitSourceRefusalError"
    visible = json.dumps(ack) + json.dumps(session.error_journal.to_dicts())
    visible += repr(records[0].__dict__)
    for private in (
        str(harness.store.root),
        bank.name,
        bank.entries[0].analog_four_source.kit_name,
    ):
        assert private not in visible
    assert workspace.bank(harness.bank_id) == bank
    assert harness.store.load(harness.bank_id) == bank
    assert _files(harness.store.root) == before
    assert session.history_store.current == history
    assert session.device.capture_snapshot() == snapshot
    assert session.pending_events == []
    assert session.armed_apply is session.current_send_plan is None
    assert session.hardware_intent is False and session.unsaved_sends == 0


def test_store_validation_preserves_working_policy_type_and_malformed_framing_category(
    refusal_session: tuple[ShowBankHarness, CockpitSession],
) -> None:
    harness, _session = refusal_session
    bank = harness.workspace.bank(harness.bank_id)
    original = bank.entry(harness.entry_id).analog_four_source
    before = _files(harness.store.root)
    frame = _working_capture(harness.analog_four).frame
    with pytest.raises(WorkingKitSourceRefusalError) as failure:
        validate_show_bank_capture_frame(_claim_frame(original, frame), frame)
    assert failure.value.__cause__ is None
    assert dict(failure.value.context) == {"reason": "working_kit_read_only"}
    malformed = bytearray(harness.analog_four.frame)
    malformed[1] = 1
    frame = bytes(malformed)
    with pytest.raises(DataError) as failure:
        validate_show_bank_capture_frame(_claim_frame(original, frame), frame)
    assert failure.value.context["category"] == "framing"
    assert failure.value.__cause__ is not None
    assert harness.workspace.bank(harness.bank_id) == bank
    assert _files(harness.store.root) == before


def test_store_import_refuses_forged_working_source_without_changing_existing_favorite(
    tmp_path: Path,
    refusal_session: tuple[ShowBankHarness, CockpitSession],
) -> None:
    harness, session = refusal_session
    incoming = build_show_bank_harness(tmp_path / "incoming")
    bank = incoming.workspace.bank(incoming.bank_id)
    entry = bank.entry(incoming.entry_id)
    working = _working_capture(incoming.analog_four).frame
    forged = replace(
        bank,
        entries=(
            replace(entry, analog_four_source=_claim_frame(entry.analog_four_source, working)),
        ),
    )
    result = ShowPackImportResult(
        package_id="working-import",
        bank=forged,
        frames_by_artifact_id={
            entry.rytm_source.sysex.artifact_id: incoming.rytm.frame,
            entry.analog_four_source.sysex.artifact_id: working,
        },
    )
    before = _files(harness.store.root)
    committed = harness.workspace.bank(harness.bank_id)
    service = ShowPackService(tmp_path / "packs", store=harness.store)
    with pytest.raises(WorkingKitSourceRefusalError):
        service.store_verified_import(result, destination_bank_id="working-import")
    assert _files(harness.store.root) == before
    assert harness.store.load(harness.bank_id) == committed
    assert harness.workspace.bank(harness.bank_id) == committed
    assert harness.store.latest_revision("working-import") is None
    assert session.armed_apply is session.current_send_plan is None
    assert session.hardware_intent is False and session.unsaved_sends == 0


@pytest.mark.parametrize("reason", [True, False, "unknown", "working_kit_read_only"])
def test_unrelated_error_context_cannot_spoof_working_reason_or_increment_its_counter(
    refusal_session: tuple[ShowBankHarness, CockpitSession],
    monkeypatch: pytest.MonkeyPatch,
    reason: object,
) -> None:
    _harness, session = refusal_session
    error = BoundaryError(
        "PRIVATE arbitrary detail",
        context={"reason": reason, "fingerprint": WorkingKitSourceRefusalError.fingerprint},
    )
    assert local_artifact_failure_message(error) is None

    async def reject(_cmd: dict[str, object], _session: CockpitSession) -> HandlerResult:
        raise error

    monkeypatch.setattr(handlers, "_resolve_handler", lambda _command: reject)
    before = get_metrics().errors_by_kind.copy()
    ack = _request(session, {"type": "show_bank_list"})
    assert ack["ok"] is False and ack["code"] == ERR_INTERNAL
    assert ack["message"] == "internal error processing command"
    assert get_metrics().errors_by_kind == before
    assert session.error_journal.entries[0].fingerprint == BoundaryError.fingerprint
    assert "PRIVATE" not in json.dumps(ack) + json.dumps(session.error_journal.to_dicts())


def test_working_source_error_is_closed_and_passive_reader_remains_allowed(
    refusal_session: tuple[ShowBankHarness, CockpitSession],
) -> None:
    harness, _session = refusal_session
    error = WorkingKitSourceRefusalError()
    assert isinstance(error, BoundaryError) and isinstance(error, ValueError)
    assert error.fingerprint == "boundary.kit.working_source_refused"
    assert error.message == WorkingKitSourceRefusalError.recovery_message
    assert error.reason == "working_kit_read_only"
    assert local_artifact_failure_message(error) == error.message
    for kwargs in (
        {"reason": True},
        {"reason": "unknown"},
        {"message": "PRIVATE"},
        {"context": {}},
    ):
        with pytest.raises(TypeError):
            WorkingKitSourceRefusalError(**kwargs)
    frame = _working_capture(harness.analog_four).frame
    with pytest.raises(WorkingKitSourceRefusalError):
        validate_analog_four_candidate_source(frame)
    assert (
        validate_analog_four_candidate_source(frame, allow_working=True).source_kind
        is AnalogFourKitSourceKind.WORKING_RAM
    )
