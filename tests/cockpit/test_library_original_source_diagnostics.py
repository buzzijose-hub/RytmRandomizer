"""Bounded original-source diagnostics without weakening Library browse policy."""

from __future__ import annotations

import asyncio
import json
import logging
import traceback
from collections.abc import Iterator
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.rehearsal_favorite import LocalRehearsalFavorite
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.engine import mutate
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.library import LibraryRecord, LibraryStore
from rytm_randomizer.cockpit.library import store as library_module
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.observability.errors import DataError, PersistedStateVersionError
from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

from .conftest import make_default_snapshot

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


@pytest.fixture
def source_logs(
    isolated_observability: None, caplog: pytest.LogCaptureFixture
) -> Iterator[pytest.LogCaptureFixture]:
    logger = logging.getLogger("rytm_randomizer")
    caplog.set_level(logging.DEBUG, logger=logger.name)
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


@pytest.fixture
def retained_source(
    tmp_path: Path, rytm_rio_return_frame: bytes
) -> tuple[LibraryStore, LibraryRecord, KitCaptureResult]:
    store = LibraryStore(tmp_path / "library")
    result = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_rio_return_frame)
    return store, store.retain_source(result), result


def _record_path(store: LibraryStore, record: LibraryRecord) -> Path:
    return store.library_dir / f"{record.record_id}.json"


def _disk_bytes(store: LibraryStore) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in store.library_dir.iterdir() if path.is_file()}


def _outcomes(logs: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [record for record in logs.records if record.getMessage() == "library_original_source"]


def _assert_redacted(logs: pytest.LogCaptureFixture, *secrets: str) -> None:
    for record in logs.records:
        diagnostic = repr(record.__dict__)
        assert record.exc_info is None
        for secret in secrets:
            assert secret not in diagnostic


def test_retain_read_and_reuse_have_distinct_success_decisions_and_spans(
    tmp_path: Path, rytm_rio_return_frame: bytes, source_logs: pytest.LogCaptureFixture
) -> None:
    store = LibraryStore(tmp_path / "library")
    reset_metrics()
    result = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_rio_return_frame)
    record = store.retain_source(result)
    tagged = store.tag(record.record_id, ("keep",))
    before = _disk_bytes(store)
    newer = replace(result, captured_at=result.captured_at + timedelta(days=1))
    assert store.retain_source(newer, origin="file_import") == tagged
    assert store.read_source_frame(record.record_id) == result.frame
    assert _disk_bytes(store) == before
    outcomes = _outcomes(source_logs)
    assert [(log.decision, log.outcome) for log in outcomes] == [
        ("retain_source", "retained"),
        ("retain_source", "reused"),
        ("read_source_frame", "verified"),
    ]
    for outcome in outcomes:
        assert outcome.input_only is True and outcome.sent_midi is False
        assert outcome.reason is None
        assert outcome.op_id.startswith(f"library.{outcome.decision}/")
        assert any(
            log.getMessage().startswith("operation_end") and log.op_id == outcome.op_id
            for log in source_logs.records
        )
    assert not get_metrics().errors_by_kind
    assert dict(get_metrics().local_artifact_decisions) == {
        "retain_source:retained": 1,
        "retain_source:reused": 1,
        "read_source_frame:verified": 1,
    }
    reset_metrics()
    assert not get_metrics().local_artifact_decisions
    _assert_redacted(source_logs, str(store.library_dir), record.record_id, record.kit_name)


@pytest.mark.parametrize(
    "corruption,reason",
    (
        ("frame_bytes", "frame_integrity"),
        ("frame_truncation", "frame_integrity"),
        ("missing_frame", "missing"),
        ("payload", "payload_identity"),
        ("fingerprint", "payload_identity"),
        ("family", "codec"),
        ("name", "metadata"),
        ("naive_timestamp", "timestamp"),
        ("invalid_timestamp", "timestamp"),
        ("record_truncation", "record_shape"),
        ("duplicate_key", "record_shape"),
        ("wrong_shape", "record_schema"),
        ("unknown_field", "record_shape"),
        ("rehash_only", "payload_identity"),
        ("rehash_payload", "codec"),
    ),
)
def test_strict_source_preserves_exact_reason_while_browse_warns_and_skips(
    retained_source, source_logs: pytest.LogCaptureFixture, corruption: str, reason: str
) -> None:
    store, record, result = retained_source
    path = _record_path(store, record)
    raw = json.loads(path.read_bytes())
    artifact = store.library_dir / record.source_frame.artifact_name
    if corruption == "frame_bytes":
        artifact.write_bytes(b"\xf0\x00\xf7")
    elif corruption == "frame_truncation":
        artifact.write_bytes(result.frame[:-1])
    elif corruption == "missing_frame":
        artifact.unlink()
    elif corruption in ("rehash_only", "rehash_payload"):
        changed = bytearray(result.frame)
        changed[-4] ^= 1  # Corrupt the codec checksum, then rehash the external claims.
        frame = bytes(changed)
        digest = sha256(frame).hexdigest()
        raw["source_frame"] = {
            "artifact_name": f"{digest}.syx",
            "sha256": digest,
            "byte_count": len(frame),
        }
        store.library_dir.joinpath(f"{digest}.syx").write_bytes(frame)
        if corruption == "rehash_payload":
            raw["payload_hex"] = frame[1:-1].hex()
            raw["fingerprint"] = library_module.payload_fingerprint(frame[1:-1])
            raw["record_id"] = raw["fingerprint"]
            path.unlink()
            path = store.library_dir / f'{raw["record_id"]}.json'
        path.write_text(json.dumps(raw), encoding="utf-8")
    elif corruption == "record_truncation":
        path.write_bytes(path.read_bytes()[:-3])
    elif corruption == "duplicate_key":
        path.write_bytes(b'{"schema_version":3,"schema_version":2}')
    elif corruption == "wrong_shape":
        path.write_bytes(b"[]")
    else:
        field, value = {
            "payload": ("payload_hex", "00"),
            "fingerprint": ("fingerprint", "f" * 16),
            "family": ("device_id", ANALOG_FOUR_DEVICE_ID),
            "name": ("kit_name", "PRIVATE_KIT_NAME"),
            "naive_timestamp": ("captured_at", "2026-10-06T00:00:00"),
            "invalid_timestamp": ("captured_at", "PRIVATE_TIMESTAMP"),
            "unknown_field": ("PRIVATE_FIELD", "PRIVATE_VALUE"),
        }[corruption]
        raw[field] = value
        path.write_text(json.dumps(raw), encoding="utf-8")
    record_id = str(raw["record_id"])
    before = _disk_bytes(store)
    source_logs.clear()
    reset_metrics()
    assert store.get(record_id) is None
    assert store.list_records() == ()
    assert store.search("") == ()
    with pytest.raises(ValueError) as refusal:
        store.get(record_id, strict_original_source=True)
    assert refusal.value.context["reason"] == reason
    with pytest.raises(ValueError) as refusal:
        store.read_source_frame(record_id)
    assert refusal.value.context["reason"] == reason
    assert get_metrics().errors_by_kind == {f"library_source_{reason}": 1}
    assert _disk_bytes(store) == before
    outcomes = _outcomes(source_logs)
    assert len(outcomes) == 1
    assert (outcomes[0].decision, outcomes[0].outcome, outcomes[0].reason) == (
        "read_source_frame",
        "refused",
        reason,
    )
    assert any(log.outcome == "skipped" for log in source_logs.records if hasattr(log, "outcome"))
    assert any(
        log.getMessage().startswith("operation_error library.read_source_frame")
        for log in source_logs.records
    )
    _assert_redacted(
        source_logs,
        str(store.library_dir),
        record_id,
        record.kit_name,
        "PRIVATE_KIT_NAME",
        "PRIVATE_TIMESTAMP",
        "PRIVATE_FIELD",
        "PRIVATE_VALUE",
    )


@pytest.mark.parametrize("target", ("record", "frame"))
@pytest.mark.parametrize(
    "failure", ("data_access", "os_access", "data_path", "data_size", "unexpected")
)
def test_reader_refusals_are_categorical_and_never_chain_private_paths(
    retained_source,
    source_logs: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    failure: str,
) -> None:
    store, record, _ = retained_source
    read = library_module.read_bounded_artifact
    secret = "PRIVATE_OPERATOR_DIRECTORY"

    def refused_read(path: Path, **kwargs) -> bytes:
        if (path.suffix == ".json") == (target == "record"):
            if failure == "os_access":
                raise PermissionError(13, secret, str(path))
            category = failure.removeprefix("data_")
            raise DataError(secret, context={"category": category, "artifact_name": path.name})
        return read(path, **kwargs)

    monkeypatch.setattr(library_module, "read_bounded_artifact", refused_read)
    source_logs.clear()
    reset_metrics()
    reason = (
        "validation"
        if failure == "unexpected"
        else failure.removeprefix("data_").removeprefix("os_")
    )
    with pytest.raises(ValueError) as refusal:
        store.read_source_frame(record.record_id)
    assert refusal.value.context["reason"] == reason
    rendered = "".join(traceback.format_exception(refusal.value))
    assert secret not in rendered and record.record_id not in rendered
    assert get_metrics().errors_by_kind == {f"library_source_{reason}": 1}
    assert store.get(record.record_id) is None
    _assert_redacted(source_logs, secret, str(store.library_dir), record.record_id)


@pytest.mark.parametrize(
    "change,reason",
    (
        ({"round_trip_verified": False}, "input_only"),
        ({"input_only": False}, "input_only"),
        ({"sent_midi": True}, "input_only"),
        ({"device_id": "PRIVATE_UNSUPPORTED_FAMILY"}, "codec"),
        ({"device_id": ANALOG_FOUR_DEVICE_ID}, "codec"),
        ({"kit_name": "PRIVATE_KIT_NAME"}, "metadata"),
        ({"frame_bytes": 1}, "metadata"),
        ({"fingerprint": "f" * 16}, "metadata"),
        ({"frame": b"\xf0\x00\xf7"}, "codec"),
    ),
)
def test_retention_refusals_count_once_and_do_not_publish(
    tmp_path: Path,
    rytm_rio_return_frame: bytes,
    source_logs: pytest.LogCaptureFixture,
    change: dict,
    reason: str,
) -> None:
    store = LibraryStore(tmp_path / "library")
    result = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_rio_return_frame)
    with pytest.raises(ValueError) as refusal:
        store.retain_source(replace(result, **change))
    assert refusal.value.context["reason"] == reason
    assert not store.library_dir.exists()
    assert get_metrics().errors_by_kind == {f"library_source_{reason}": 1}
    assert len(_outcomes(source_logs)) == 1
    _assert_redacted(
        source_logs, str(store.library_dir), "PRIVATE_UNSUPPORTED_FAMILY", "PRIVATE_KIT_NAME"
    )


def test_retention_invalid_origin_is_not_logged_as_an_unbounded_category(
    tmp_path: Path, rytm_rio_return_frame: bytes, source_logs: pytest.LogCaptureFixture
) -> None:
    result = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_rio_return_frame)
    with pytest.raises(ValueError) as refusal:
        LibraryStore(tmp_path / "library").retain_source(result, origin="PRIVATE_ORIGIN")
    assert refusal.value.context["reason"] == "provenance"
    assert get_metrics().errors_by_kind == {"library_source_provenance": 1}
    _assert_redacted(source_logs, "PRIVATE_ORIGIN")


def test_newer_schema_explicitly_refuses_browse_and_source_read_without_rewriting(
    retained_source, source_logs: pytest.LogCaptureFixture
) -> None:
    store, record, _ = retained_source
    path = _record_path(store, record)
    raw = json.loads(path.read_bytes())
    raw["schema_version"] = library_module.LIBRARY_STORE_SCHEMA_VERSION + 1
    path.write_text(json.dumps(raw), encoding="utf-8")
    before = _disk_bytes(store)
    source_logs.clear()
    reset_metrics()
    for read in (
        store.list_records,
        lambda: store.get(record.record_id),
        lambda: store.read_source_frame(record.record_id),
    ):
        with pytest.raises(PersistedStateVersionError):
            read()
    assert get_metrics().persisted_state_refusals_by_code == {
        "library_store:schema_newer_than_app": 3
    }
    assert get_metrics().errors_by_kind == {"library_source_schema_newer_than_app": 1}
    assert all(
        log.outcome == "refused"
        for log in source_logs.records
        if log.getMessage() == "library_record_refused"
    )
    assert _disk_bytes(store) == before
    _assert_redacted(source_logs, str(store.library_dir), record.record_id)


@pytest.mark.parametrize("operation", ("get", "delete", "tag", "read_source_frame"))
@pytest.mark.parametrize(
    "record_id", ("../PRIVATE_PATH", "C:\\PRIVATE_PATH", "PRIVATE_ID" * 30, None)
)
def test_public_record_id_refusals_never_echo_operator_inputs(
    tmp_path: Path, source_logs: pytest.LogCaptureFixture, operation: str, record_id: object
) -> None:
    store = LibraryStore(tmp_path / "library")
    with pytest.raises(ValueError) as refusal:
        if operation == "tag":
            store.tag(record_id, ())
        else:
            getattr(store, operation)(record_id)
    assert repr(record_id) not in repr(refusal.value)
    assert "invalid library record_id" in str(refusal.value) or operation == "read_source_frame"
    assert not store.library_dir.exists()
    _assert_redacted(source_logs, "PRIVATE_PATH", "PRIVATE_ID")


def test_other_library_validation_messages_are_path_and_id_free(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library", captures_dir=tmp_path / "PRIVATE_CAPTURES")
    with pytest.raises(ValueError, match="does not exist") as refusal:
        store.import_captures()
    assert "PRIVATE_CAPTURES" not in repr(refusal.value)
    with pytest.raises(ValueError, match="unknown library record_id") as refusal:
        store.tag("PRIVATE_RECORD", ())
    assert "PRIVATE_RECORD" not in repr(refusal.value)
    with pytest.raises(ValueError, match="non-list tags") as refusal:
        LibraryRecord.from_dict({"record_id": "PRIVATE_RECORD", "tags": "invalid"})
    assert "PRIVATE_RECORD" not in repr(refusal.value)


@pytest.mark.parametrize("record_id", ("../PRIVATE_WS_PATH", "PRIVATE_WS_ID" * 30))
def test_dispatcher_exception_repr_does_not_expose_rejected_library_identity(
    tmp_path: Path, source_logs: pytest.LogCaptureFixture, record_id: str
) -> None:
    source = make_default_snapshot()
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=source),
        library_store=LibraryStore(tmp_path / "library"),
    )
    ack = asyncio.run(
        handle_command(
            {
                "request_id": "library-refusal",
                "command": {"type": "recall_rehearsal_favorite", "record_id": record_id},
            },
            session,
        )
    )
    assert ack["ok"] is False and ack["code"] == "validation_error"
    assert "PRIVATE_WS" not in repr(ack)
    failures = [log for log in source_logs.records if log.getMessage() == "handler_exception"]
    assert len(failures) == 1
    assert "redacted-local-artifact" in failures[0].exception_repr
    assert failures[0].exception_type == "_LibrarySourceError"
    assert len(failures[0].exception_repr) < 128
    _assert_redacted(source_logs, "PRIVATE_WS", str(tmp_path))
    assert session.armed_apply is None and session.hardware_intent is False


def test_retain_corrupt_existing_source_keeps_original_bytes_and_specific_reason(
    retained_source, source_logs: pytest.LogCaptureFixture
) -> None:
    store, record, result = retained_source
    artifact = store.library_dir / record.source_frame.artifact_name
    artifact.write_bytes(b"\xf0\x00\xf7")
    before = _disk_bytes(store)
    source_logs.clear()
    reset_metrics()
    with pytest.raises(ValueError) as refusal:
        store.retain_source(result)
    assert refusal.value.context["reason"] == "frame_integrity"
    assert get_metrics().errors_by_kind == {"library_source_frame_integrity": 1}
    assert _disk_bytes(store) == before
    assert len(_outcomes(source_logs)) == 1


def test_legacy_reconstruction_is_logged_but_never_upgrades_provenance(
    retained_source, source_logs: pytest.LogCaptureFixture
) -> None:
    store, record, result = retained_source
    path = _record_path(store, record)
    raw = record.to_dict()
    raw.pop("source_frame")
    raw.pop("source_origin")
    raw["schema_version"] = 2
    path.write_text(json.dumps(raw), encoding="utf-8")
    before = _disk_bytes(store)
    source_logs.clear()
    reset_metrics()
    with pytest.raises(ValueError, match="explicit reconstruction"):
        store.read_source_frame(record.record_id)
    assert (
        store.read_source_frame(record.record_id, allow_legacy_reconstruction=True) == result.frame
    )
    assert store.get(record.record_id).source_origin is None
    assert [(log.outcome, log.reason) for log in _outcomes(source_logs)] == [
        ("refused", "legacy_reconstruction_required"),
        ("reconstructed", None),
    ]
    assert _disk_bytes(store) == before


def test_missing_original_read_is_observable_but_strict_get_still_returns_none(
    tmp_path: Path, source_logs: pytest.LogCaptureFixture
) -> None:
    store = LibraryStore(tmp_path / "library")
    assert store.get("PRIVATE_ABSENT", strict_original_source=True) is None
    with pytest.raises(ValueError) as refusal:
        store.read_source_frame("PRIVATE_ABSENT")
    assert refusal.value.context["reason"] == "no_original_source"
    assert get_metrics().errors_by_kind == {"library_source_no_original_source": 1}
    _assert_redacted(source_logs, "PRIVATE_ABSENT")


def test_retention_sanitizes_publication_access_errors_and_generic_validation(
    tmp_path: Path,
    rytm_rio_return_frame: bytes,
    source_logs: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_rio_return_frame)
    store = LibraryStore(tmp_path / "library")
    for exception, reason in (
        (PermissionError("PRIVATE_PATH"), "access"),
        (ValueError("PRIVATE_PATH"), "validation"),
    ):

        def refuse_write(*args, failure=exception, **kwargs):
            raise failure

        monkeypatch.setattr(store, "_write_record", refuse_write)
        with pytest.raises(ValueError) as refusal:
            store.retain_source(result)
        assert refusal.value.context["reason"] == reason
        assert "PRIVATE_PATH" not in "".join(traceback.format_exception(refusal.value))
    assert get_metrics().errors_by_kind == {
        "library_source_access": 1,
        "library_source_validation": 1,
    }
    _assert_redacted(source_logs, "PRIVATE_PATH")


@pytest.mark.parametrize(
    "changes,message",
    (
        ({"source_frame": "PRIVATE_FRAME"}, "must be an object"),
        ({"source_origin": "PRIVATE_ORIGIN"}, "unsupported library source provenance"),
        ({"source_origin": None}, "does not match record kind"),
        ({"source_frame": None}, "does not match record kind"),
    ),
)
def test_record_provenance_validation_refuses_inconsistent_artifact_claims(
    retained_source, changes: dict, message: str
) -> None:
    _, record, _ = retained_source
    raw = {**record.to_dict(), **changes}
    with pytest.raises(ValueError, match=message) as refusal:
        LibraryRecord.from_dict(raw)
    assert "PRIVATE_" not in repr(refusal.value)


def test_semantic_favorite_never_becomes_an_original_frame(retained_source) -> None:
    store, record, _ = retained_source
    source = make_default_snapshot()
    profile = ProfileRegistry(store.library_dir.parent / "profiles").builtin_scenes[0]
    favorite = LocalRehearsalFavorite(source, profile, mutate(source, profile, 0, 1))
    retained = store.retain_rehearsal(favorite, "semantic only")
    with pytest.raises(ValueError) as refusal:
        store.read_source_frame(retained.record_id, allow_legacy_reconstruction=True)
    assert refusal.value.context["reason"] == "no_original_source"
    raw = retained.to_dict()
    raw["source_frame"] = record.source_frame.to_dict()
    raw["source_origin"] = "input_capture"
    with pytest.raises(ValueError, match="does not match record kind"):
        LibraryRecord.from_dict(raw)


@pytest.mark.parametrize("mode", ("symlink", "scan_access", "file_count", "aggregate_size"))
def test_source_directory_refusals_are_bounded_and_path_free(
    retained_source,
    source_logs: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    store, record, _ = retained_source
    reason = "size"
    if mode == "symlink":
        reason = "path"
        is_symlink = Path.is_symlink
        monkeypatch.setattr(
            Path, "is_symlink", lambda path: path == store.library_dir or is_symlink(path)
        )
    elif mode == "scan_access":
        reason = "access"
        iterdir = Path.iterdir

        def refuse_scan(path: Path):
            if path == store.library_dir:
                raise PermissionError("PRIVATE_SCAN_PATH")
            return iterdir(path)

        monkeypatch.setattr(Path, "iterdir", refuse_scan)
    else:
        bound = "LIBRARY_MAX_FILES" if mode == "file_count" else "LIBRARY_MAX_TOTAL_BYTES"
        monkeypatch.setattr(library_module, bound, 1)
    source_logs.clear()
    reset_metrics()
    with pytest.raises(ValueError) as refusal:
        store.read_source_frame(record.record_id)
    assert refusal.value.context["reason"] == reason
    assert get_metrics().errors_by_kind == {f"library_source_{reason}": 1}
    _assert_redacted(source_logs, str(store.library_dir), record.record_id, "PRIVATE_SCAN_PATH")


@pytest.mark.parametrize(
    "field,value", (("device_id", ANALOG_FOUR_DEVICE_ID), ("payload_hex", "00"))
)
def test_legacy_identity_collision_is_not_overwritten_by_retention(
    retained_source, field: str, value: str
) -> None:
    store, record, result = retained_source
    path = _record_path(store, record)
    raw = record.to_dict()
    raw["source_frame"] = raw["source_origin"] = None
    raw[field] = value
    path.write_text(json.dumps(raw), encoding="utf-8")
    before = _disk_bytes(store)
    with pytest.raises(ValueError) as refusal:
        store.retain_source(result)
    assert refusal.value.context["reason"] == "identity_collision"
    assert _disk_bytes(store) == before


def test_reuse_refuses_when_reader_returns_a_different_frame_after_record_validation(
    retained_source, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, _, result = retained_source
    read = library_module._read_record_source_frame
    count = 0

    def racing_read(directory: Path, record: LibraryRecord) -> bytes:
        nonlocal count
        count += 1
        return read(directory, record) if count == 1 else b"different frame"

    monkeypatch.setattr(library_module, "_read_record_source_frame", racing_read)
    before = _disk_bytes(store)
    with pytest.raises(ValueError) as refusal:
        store.retain_source(result)
    assert refusal.value.context["reason"] == "identity_collision"
    assert _disk_bytes(store) == before


@pytest.mark.parametrize(
    "field,value,reason",
    (("payload_hex", "PRIVATE_HEX", "payload_identity"), ("kit_name", "PRIVATE_KIT", "metadata")),
)
def test_legacy_reconstruction_validation_remains_exact_and_redacted(
    retained_source, source_logs: pytest.LogCaptureFixture, field: str, value: str, reason: str
) -> None:
    store, record, _ = retained_source
    raw = record.to_dict()
    raw["source_frame"] = raw["source_origin"] = None
    raw[field] = value
    path = _record_path(store, record)
    path.write_text(json.dumps(raw), encoding="utf-8")
    before = _disk_bytes(store)
    source_logs.clear()
    reset_metrics()
    with pytest.raises(ValueError) as refusal:
        store.read_source_frame(record.record_id, allow_legacy_reconstruction=True)
    assert refusal.value.context["reason"] == reason
    assert get_metrics().errors_by_kind == {f"library_source_{reason}": 1}
    assert _disk_bytes(store) == before
    _assert_redacted(source_logs, value, record.record_id)


@pytest.mark.parametrize("framed", (False, True))
def test_generic_import_fallback_does_not_claim_exact_original_provenance(
    tmp_path: Path, rytm_rio_return_frame: bytes, monkeypatch: pytest.MonkeyPatch, framed: bool
) -> None:
    captures = tmp_path / "captures"
    captures.mkdir()
    frame = rytm_rio_return_frame
    (captures / "legacy.syx").write_bytes(frame if framed else frame[1:-1])
    if framed:

        def refuse_exact(*args):
            raise ValueError("historical decode is not exact codec proof")

        monkeypatch.setattr(library_module, "decode_kit_capture_frame", refuse_exact)
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    imported = store.import_captures()
    assert len(imported.imported) == 1 and not imported.failed_files
    record = imported.imported[0]
    assert record.source_frame is None and record.source_origin is None
    assert not tuple(store.library_dir.glob("*.syx"))
    with pytest.raises(ValueError, match="explicit reconstruction"):
        store.read_source_frame(record.record_id)


@pytest.mark.parametrize(
    "bound,limit,existing",
    (
        ("LIBRARY_MAX_RECORD_BYTES", 1, False),
        ("LIBRARY_MAX_FILES", 1, False),
        ("LIBRARY_MAX_FILES", 2, True),
        ("LIBRARY_MAX_TOTAL_BYTES", 100, False),
    ),
)
def test_retention_publication_bounds_include_all_new_artifacts_before_writing(
    tmp_path: Path,
    rytm_rio_return_frame: bytes,
    source_logs: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    bound: str,
    limit: int,
    existing: bool,
) -> None:
    store = LibraryStore(tmp_path / "library")
    if existing:
        store.library_dir.mkdir()
        (store.library_dir / "unrelated.txt").write_bytes(b"keep")
    monkeypatch.setattr(library_module, bound, limit)
    result = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_rio_return_frame)
    with pytest.raises(ValueError) as refusal:
        store.retain_source(result)
    assert refusal.value.context["reason"] == "size"
    assert get_metrics().errors_by_kind == {"library_source_size": 1}
    assert not tuple(store.library_dir.glob("*.json"))
    assert not tuple(store.library_dir.glob("*.syx"))


def test_record_publication_refuses_absent_frame_and_content_address_collision(
    retained_source,
) -> None:
    store, record, _ = retained_source
    before = _disk_bytes(store)
    with pytest.raises(ValueError) as refusal:
        store._write_record(record, overwrite=True, frame=b"different bytes")
    assert refusal.value.context["reason"] == "identity_collision"
    assert _disk_bytes(store) == before
    artifact = store.library_dir / record.source_frame.artifact_name
    artifact.unlink()
    before = _disk_bytes(store)
    with pytest.raises(ValueError) as refusal:
        store.tag(record.record_id, ("new",))
    assert "unknown library record_id" in str(refusal.value)
    with pytest.raises(ValueError) as refusal:
        store._write_record(record, overwrite=True)
    assert refusal.value.context["reason"] == "missing"
    assert _disk_bytes(store) == before


def test_source_helpers_refuse_absent_identity_and_unsafe_direct_dto_before_reading(
    retained_source, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, record, result = retained_source
    missing = replace(record, source_frame=None, source_origin=None)
    for validate in (
        lambda: library_module._validate_record_source_frame(missing, result.frame),
        lambda: library_module._read_record_source_frame(store.library_dir, missing),
    ):
        with pytest.raises(ValueError) as refusal:
            validate()
        assert refusal.value.context["reason"] == "no_original_source"
    # Simulate an invalid DTO supplied directly, beyond the disk parser's checks.
    artifact = replace(record.source_frame)
    object.__setattr__(artifact, "artifact_name", "../PRIVATE_PATH.syx")
    invalid = replace(record, source_frame=artifact)
    with pytest.raises(ValueError) as refusal:
        library_module._validate_record_source_frame(invalid, result.frame)
    assert refusal.value.context["reason"] == "path"

    def must_not_read(*args, **kwargs):
        pytest.fail("unsafe artifact name reached the filesystem reader")

    monkeypatch.setattr(library_module, "read_bounded_artifact", must_not_read)
    with pytest.raises(ValueError) as refusal:
        library_module._read_record_source_frame(store.library_dir, invalid)
    assert refusal.value.context["reason"] == "path"
    assert "PRIVATE_PATH" not in repr(refusal.value)
