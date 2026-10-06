"""Actual offline artifact failures retain state and expose only recovery guidance."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast, get_args

import pytest

from rytm_randomizer.cockpit.export import writer
from rytm_randomizer.cockpit.export.file_export_contracts import (
    LOCAL_FILE_EXPORT_ERROR_CODES,
    LocalFileExportErrorCode,
    attach_local_file_export_error_context,
)
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.library.store import LIBRARY_STORE_ID, SourceRefusal
from rytm_randomizer.cockpit.show_bank.export import (
    SHOW_PACK_MANIFEST_NAME,
    ShowPackService,
)
from rytm_randomizer.cockpit.show_bank.store import (
    SHOW_BANK_CORRUPTION_CATEGORY_VALUES,
    show_bank_corruption_category,
)
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.protocol import ERR_INTERNAL, ERR_VALIDATION
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.show_bank_handlers import local_artifact_failure_message
from rytm_randomizer.observability.errors import DataError, PersistedStateVersionError

from .test_native_offline_journey import _disk, _favorite, _generate, _journey, _session
from .test_observability import package_logs as package_logs

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("offline_hardware_denied", "package_logs"),
]
_MISSING_MESSAGE: Final[str] = (
    "Local artifact is missing. Restore the complete package or retained source, then retry."
)
_CORRUPT_MESSAGE: Final[str] = (
    "Local artifact failed integrity checks. Restore a verified copy or re-export it, then retry."
)
_SCHEMA_MESSAGE: Final[str] = (
    "Local artifact schema is incompatible or invalid. Use a compatible app or re-export a verified package."
)
_MISMATCH_MESSAGE: Final[str] = (
    "Local artifact does not match its source or manifest. Restore matching source files or re-export the package."
)
_WRITE_MESSAGE: Final[str] = (
    "Local files could not be saved. Check available space and folder access, then retry."
)
_SECRET: Final[str] = "private-source-id SECRET_TOKEN C:\\private\\secret-kit.syx\nsecret-value"


@dataclass(frozen=True)
class _Harness:
    session: CockpitSession
    service: ShowPackService
    bank_id: str
    entry_id: str
    candidate_id: str


def _command(session: CockpitSession, command_type: str, **body: object) -> dict[str, object]:
    return asyncio.run(
        handle_command(
            {"request_id": "diagnostic-request", "command": {"type": command_type, **body}},
            session,
        )
    )


@pytest.fixture
def artifact_harness(tmp_path: Path) -> _Harness:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    bank = _favorite(journey, candidate)
    session = _session(journey.workspace, bank.bank_id, journey.entry_id, tmp_path)
    service = ShowPackService(tmp_path / "packages", store=journey.workspace.store)
    session.show_pack_service = service
    session.library_store = LibraryStore(tmp_path / "library")
    ack = _command(
        session,
        "show_bank_select_candidate",
        bank_id=bank.bank_id,
        entry_id=journey.entry_id,
        candidate_id=candidate.candidate_id,
        expected_revision=bank.revision,
    )
    assert ack["ok"] is True
    session.clear_pending_events()
    return _Harness(session, service, bank.bank_id, journey.entry_id, candidate.candidate_id)


def _assert_command_refused(
    harness: _Harness,
    command_type: str,
    message: str,
    caplog: pytest.LogCaptureFixture,
    *,
    forbidden: tuple[str, ...] = (),
    **body: object,
) -> None:
    session = harness.session
    workspace = session.show_kit_forge
    assert workspace is not None
    before = (
        workspace.state_dict(),
        session.device.capture_snapshot(),
        session.history_store.current,
        session.current_candidate,
        session.active_profile,
        session.current_send_plan,
        session.depth,
        session.seed,
        session.preview_on,
        session.recalled_offline_favorite,
        session.stage_coordinator.state,
        session.rytm_parameters,
        session.a4_parameters,
        set(session.pad_locks),
        set(session.a4_track_locks),
        set(session.rytm_pad_targets),
        set(session.a4_track_targets),
    )
    files = _disk(workspace.store.root)
    package_files = _disk(harness.service.package_root)
    library_files = _disk(harness.service.package_root.parent / "library")
    caplog.clear()
    caplog.set_level(logging.DEBUG, logger="rytm_randomizer")
    ack = _command(session, command_type, **body)
    assert ack == {
        "request_id": "diagnostic-request",
        "ok": False,
        "code": ERR_VALIDATION,
        "message": message,
    }
    assert session.pending_events == []
    assert before == (
        workspace.state_dict(),
        session.device.capture_snapshot(),
        session.history_store.current,
        session.current_candidate,
        session.active_profile,
        session.current_send_plan,
        session.depth,
        session.seed,
        session.preview_on,
        session.recalled_offline_favorite,
        session.stage_coordinator.state,
        session.rytm_parameters,
        session.a4_parameters,
        set(session.pad_locks),
        set(session.a4_track_locks),
        set(session.rytm_pad_targets),
        set(session.a4_track_targets),
    )
    assert _disk(workspace.store.root) == files
    assert _disk(harness.service.package_root) == package_files
    assert _disk(harness.service.package_root.parent / "library") == library_files
    assert any(record.msg == "handler_exception" for record in caplog.records)
    visible = json.dumps(ack) + repr([record.__dict__ for record in caplog.records])
    journal = session.error_journal.to_dicts()
    visible += repr(journal)
    for private in (
        *forbidden,
        str(workspace.store.root),
        "SECRET_TOKEN",
        "secret-kit.syx",
        "secret-value",
        "private-source-id",
    ):
        assert private not in visible
        assert repr(private)[1:-1] not in visible


def _assert_import_refused(
    harness: _Harness, package_id: str, message: str, caplog: pytest.LogCaptureFixture
) -> None:
    _assert_command_refused(
        harness,
        "show_bank_import",
        message,
        caplog,
        forbidden=(package_id,),
        pack_name=package_id,
        destination_bank_id="new-import",
    )


def test_missing_package_category_reaches_actual_command_without_replacing_favorite(
    artifact_harness: _Harness, caplog: pytest.LogCaptureFixture
) -> None:
    with pytest.raises(DataError) as failure:
        artifact_harness.service.verify("private-missing-package")
    assert show_bank_corruption_category(failure.value) == "missing"
    _assert_import_refused(artifact_harness, "private-missing-package", _MISSING_MESSAGE, caplog)


@pytest.mark.parametrize(
    "damage,category,message",
    [
        ("missing-manifest", "missing", _MISSING_MESSAGE),
        ("missing-frame", "missing", _MISSING_MESSAGE),
        ("invalid-json", "malformed-json", _CORRUPT_MESSAGE),
        ("newer-schema", "schema", _SCHEMA_MESSAGE),
        ("frame-hash", "hash", _CORRUPT_MESSAGE),
        ("source-mismatch", "cross-reference", _MISMATCH_MESSAGE),
    ],
)
def test_real_package_damage_projects_recovery_and_never_publishes_an_import(
    artifact_harness: _Harness,
    damage: str,
    category: str,
    message: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    harness = artifact_harness
    workspace = harness.session.show_kit_forge
    assert workspace is not None
    result = harness.service.export(workspace.bank(harness.bank_id), package_id="private-package")
    manifest = result.package_dir / SHOW_PACK_MANIFEST_NAME
    if damage == "missing-manifest":
        manifest.unlink()
    elif damage == "missing-frame":
        next(result.package_dir.glob("*.syx")).unlink()
    elif damage == "invalid-json":
        manifest.write_bytes(b'{"secret-kit.syx":')
    elif damage == "newer-schema":
        raw = json.loads(manifest.read_bytes())
        raw["schema_version"] = "show-pack-v999"
        manifest.write_text(json.dumps(raw), encoding="utf-8")
    elif damage == "frame-hash":
        frame_path = next(result.package_dir.glob("*.syx"))
        frame_path.write_bytes(frame_path.read_bytes().replace(b"\xf0", b"\xf1", 1))
    else:
        raw = json.loads(manifest.read_bytes())
        raw["bank"]["entries"][0]["rytm_source"]["kit_name"] = "WRONG SOURCE"
        manifest.write_bytes(
            (
                json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode()
        )
    with pytest.raises(DataError) as failure:
        harness.service.verify(result.package_id)
    assert show_bank_corruption_category(failure.value) == category
    _assert_import_refused(harness, result.package_id, message, caplog)


@pytest.mark.parametrize("damage", ["missing", "hash"])
@pytest.mark.parametrize("command_type", ["show_bank_select_candidate", "show_bank_mark_favorite"])
def test_missing_or_corrupt_retained_frame_prevents_recall_before_state_changes(
    artifact_harness: _Harness,
    damage: str,
    command_type: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    harness = artifact_harness
    workspace = harness.session.show_kit_forge
    assert workspace is not None
    bank = workspace.bank(harness.bank_id)
    candidate = bank.entry(harness.entry_id).candidate_by_id(harness.candidate_id)
    retained = candidate.analog_four_candidate.sysex.retained
    assert retained is not None
    frame_path = workspace.store.root / retained.artifact_name
    if damage == "missing":
        frame_path.unlink()
    else:
        frame_path.write_bytes(frame_path.read_bytes().replace(b"\xf0", b"\xf1", 1))
    _assert_command_refused(
        harness,
        command_type,
        _MISSING_MESSAGE if damage == "missing" else _CORRUPT_MESSAGE,
        caplog,
        forbidden=(retained.artifact_name, harness.candidate_id),
        bank_id=harness.bank_id,
        entry_id=harness.entry_id,
        candidate_id=harness.candidate_id,
        expected_revision=bank.revision,
    )


def test_actual_revision_publication_failure_is_actionable_and_preserves_every_byte(
    artifact_harness: _Harness,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    harness = artifact_harness
    workspace = harness.session.show_kit_forge
    assert workspace is not None
    original_link = writer.os.link

    def refuse_publication(source: str, destination: Path, *args: object, **kwargs: object) -> None:
        if Path(destination).name.endswith(".show-bank.json"):
            raise PermissionError(_SECRET)
        original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(writer.os, "link", refuse_publication)
    _assert_command_refused(
        harness,
        "show_bank_update",
        _WRITE_MESSAGE,
        caplog,
        forbidden=(harness.bank_id,),
        bank_id=harness.bank_id,
        expected_revision=workspace.bank(harness.bank_id).revision,
        name="A rejected replacement",
        description="",
        notes=[],
    )


def test_actual_pack_publication_failure_reports_recovery_without_a_commit_marker(
    artifact_harness: _Harness,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    harness = artifact_harness
    workspace = harness.session.show_kit_forge
    assert workspace is not None
    original_link = writer.os.link

    def refuse_commit(source: str, destination: Path, *args: object, **kwargs: object) -> None:
        if Path(destination).name == SHOW_PACK_MANIFEST_NAME:
            raise PermissionError(_SECRET)
        original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(writer.os, "link", refuse_commit)
    _assert_command_refused(
        harness,
        "show_bank_export",
        _WRITE_MESSAGE,
        caplog,
        forbidden=("private-package",),
        bank_id=harness.bank_id,
        expected_revision=workspace.bank(harness.bank_id).revision,
        artifact_name="private-package",
    )
    assert tuple(harness.service.package_root.iterdir()) == ()


@pytest.mark.parametrize(
    "damage,message",
    [
        ("missing-frame", _MISSING_MESSAGE),
        ("frame-hash", _CORRUPT_MESSAGE),
        ("newer-schema", _SCHEMA_MESSAGE),
        ("source-mismatch", _MISMATCH_MESSAGE),
    ],
)
def test_actual_library_source_failure_is_projected_without_adopting_or_publishing(
    artifact_harness: _Harness,
    damage: str,
    message: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    harness = artifact_harness
    workspace = harness.session.show_kit_forge
    library = harness.session.library_store
    assert workspace is not None and library is not None
    records = {record.device_id: record for record in library.list_records()}
    rytm = records["analog_rytm_mk2"]
    a4 = records["analog_four_mk2"]
    assert rytm.source_frame is not None
    source_path = library.library_dir / rytm.source_frame.artifact_name
    record_path = library.library_dir / f"{rytm.record_id}.json"
    if damage == "missing-frame":
        source_path.unlink()
    elif damage == "frame-hash":
        source_path.write_bytes(source_path.read_bytes().replace(b"\xf0", b"\xf1", 1))
    else:
        raw = json.loads(record_path.read_bytes())
        raw["schema_version" if damage == "newer-schema" else "kit_name"] = (
            999 if damage == "newer-schema" else "WRONG SOURCE"
        )
        record_path.write_text(json.dumps(raw), encoding="utf-8")
    _assert_command_refused(
        harness,
        "show_bank_adopt_library_sources",
        message,
        caplog,
        forbidden=(rytm.record_id, rytm.source_frame.artifact_name),
        bank_id=harness.bank_id,
        expected_revision=workspace.bank(harness.bank_id).revision,
        rytm_record_id=rytm.record_id,
        a4_record_id=a4.record_id,
        rytm_slot=22,
        a4_slot=23,
    )


@pytest.mark.parametrize("command_type", ["show_bank_import", "show_bank_export"])
@pytest.mark.parametrize(
    "unsafe", ["../SECRET_TOKEN", "C:\\private\\secret-kit.syx", "secret\nkit"]
)
def test_unsafe_package_values_do_not_leak_through_logs_or_diagnostics(
    artifact_harness: _Harness,
    command_type: str,
    unsafe: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    harness = artifact_harness
    workspace = harness.session.show_kit_forge
    assert workspace is not None
    body: dict[str, object] = (
        {"pack_name": unsafe}
        if command_type == "show_bank_import"
        else {
            "artifact_name": unsafe,
            "bank_id": harness.bank_id,
            "expected_revision": workspace.bank(harness.bank_id).revision,
        }
    )
    _assert_command_refused(
        harness,
        command_type,
        "Local file request is invalid. Review the selected source and destination, then retry.",
        caplog,
        forbidden=("SECRET_TOKEN", "private", "secret-kit", "secret\\nkit"),
        **body,
    )


@pytest.mark.parametrize("category", SHOW_BANK_CORRUPTION_CATEGORY_VALUES)
def test_public_data_categories_ignore_arbitrary_messages_causes_and_context(category: str) -> None:
    error = DataError(_SECRET, context={"category": category, "artifact_name": _SECRET})
    error.__cause__ = OSError(_SECRET)
    message = local_artifact_failure_message(error)
    assert message is not None and _SECRET not in message
    assert len(message) < 200
    assert handlers._local_artifact_failure_message(error, "show_bank_import") == message


@pytest.mark.parametrize("code", sorted(LOCAL_FILE_EXPORT_ERROR_CODES))
def test_existing_file_export_context_is_reused_without_reporting_secret_filenames(
    code: str,
) -> None:
    error = OSError(_SECRET)
    attach_local_file_export_error_context(
        error,
        error_code=cast(LocalFileExportErrorCode, code),
        phase="output_write",
        artifact_name="secret-kit.syx",
    )
    message = local_artifact_failure_message(error)
    assert message is not None
    assert "secret" not in message


@pytest.mark.parametrize("reason", get_args(SourceRefusal))
def test_public_library_reasons_ignore_arbitrary_error_text_and_identifiers(reason: str) -> None:
    error = DataError(
        _SECRET, context={"store_id": LIBRARY_STORE_ID, "reason": reason, "record_id": _SECRET}
    )
    assert local_artifact_failure_message(error) is not None
    assert "SECRET_TOKEN" not in cast(str, local_artifact_failure_message(error))


@pytest.mark.parametrize(
    "error", [FileNotFoundError(_SECRET), PermissionError(_SECRET), FileExistsError(_SECRET)]
)
def test_known_filesystem_failure_types_use_existing_file_export_categories(error: OSError) -> None:
    assert local_artifact_failure_message(error) is not None
    assert "SECRET_TOKEN" not in cast(str, local_artifact_failure_message(error))


def test_newer_persisted_state_refusal_has_compatible_app_guidance() -> None:
    error = PersistedStateVersionError(_SECRET, context={"store_id": LIBRARY_STORE_ID})
    assert local_artifact_failure_message(error) == _SCHEMA_MESSAGE


def test_invalid_library_reason_and_unrelated_store_do_not_acquire_recoverable_status() -> None:
    for context in (
        {"store_id": LIBRARY_STORE_ID, "reason": []},
        {"store_id": LIBRARY_STORE_ID, "reason": _SECRET},
        {"store_id": "another-store", "reason": "missing"},
    ):
        assert local_artifact_failure_message(DataError(_SECRET, context=context)) is None


@pytest.mark.parametrize("category", [None, True, 3, [], {}, "SECRET_TOKEN", "missing\nsecret"])
def test_unknown_or_unsafe_data_categories_remain_internal_failures(category: object) -> None:
    error = DataError(_SECRET, context={"category": category, "reason": _SECRET})
    assert local_artifact_failure_message(error) is None
    assert handlers._local_artifact_failure_message(error, "show_bank_import") is None
    assert handlers._classify_handler_exception(error) == (
        ERR_INTERNAL,
        "internal error processing command",
    )


@pytest.mark.parametrize("error_type", [RuntimeError, TypeError, DataError])
def test_programming_errors_are_not_disguised_as_recoverable_artifact_failures(
    artifact_harness: _Harness,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    error_type: Callable[[str], BaseException],
) -> None:
    def broken(_command: dict[str, object], _session: CockpitSession) -> object:
        raise error_type(_SECRET)

    monkeypatch.setattr(handlers, "_resolve_handler", lambda _kind: broken)
    caplog.clear()
    caplog.set_level(logging.DEBUG, logger="rytm_randomizer")
    ack = _command(artifact_harness.session, "show_bank_import", pack_name="unused")
    assert ack["code"] == ERR_INTERNAL
    assert ack["message"] == "internal error processing command"
    visible = repr([record.__dict__ for record in caplog.records]) + repr(ack)
    assert "SECRET_TOKEN" not in repr(ack) and "secret-kit" not in repr(ack)
    assert "SECRET_TOKEN" not in visible and "secret-kit" not in visible
    assert "redacted-local-artifact" in visible


def test_expected_artifact_categories_do_not_change_unrelated_handler_classification() -> None:
    error = DataError(_SECRET, context={"category": "missing"})
    assert handlers._local_artifact_failure_message(error, "regen") is None
    assert handlers._classify_handler_exception(error)[0] == ERR_INTERNAL
    assert handlers.dispatcher_failure_ack(error, "request")["code"] == ERR_INTERNAL
