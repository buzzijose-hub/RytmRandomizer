"""Public command regressions for retained, inert RIO145 Library sources."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import Final, cast

import pytest
from cockpit.show_bank.test_offline_retention import (  # noqa: F401 - reuse the autouse offline backend guard
    refuse_hardware_imports,
)
from cockpit.test_show_bank_ws_boundary import _Boundary, _boundary, _command
from cockpit.test_ws_armed_send import _FakeProvider, _stage_send

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.library import LibraryRecord, LibraryStore
from rytm_randomizer.cockpit.library.store import SourceOrigin
from rytm_randomizer.cockpit.show_bank.readiness import is_catalog_only_show_bank
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace

pytestmark = pytest.mark.fast

_FIXTURES: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "rio145"


@dataclass(frozen=True)
class _OfflineBoundary:
    boundary: _Boundary
    library: LibraryStore
    records: dict[str, LibraryRecord]
    frames: dict[str, bytes]
    bank_id: str


def _offline_boundary(tmp_path: Path, *, origin: SourceOrigin = "file_import") -> _OfflineBoundary:
    boundary = _boundary(tmp_path)
    frames = {
        ANALOG_RYTM_DEVICE_ID: (_FIXTURES / "RYTM_RIO145_AR_CORE_RETURN_Kit.syx").read_bytes(),
        ANALOG_FOUR_DEVICE_ID: (_FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes(),
    }
    library = LibraryStore(tmp_path / "library")
    retained_at = boundary.clock() - timedelta(days=30)
    records = {
        device_id: library.retain_source(
            replace(decode_kit_capture_frame(device_id, frame), captured_at=retained_at),
            origin=origin,
        )
        for device_id, frame in frames.items()
    }
    boundary.session.library_store = library
    boundary.session.kit_captures.clear()
    ack, _ = _command(
        boundary.session,
        "show_bank_create",
        name="Retained RIO145 sources",
        description="Offline paired originals",
        notes=[],
    )
    assert ack["ok"] is True, ack
    return _OfflineBoundary(boundary, library, records, frames, cast(str, ack["show_bank_id"]))


def _adoption_body(harness: _OfflineBoundary) -> dict[str, object]:
    return {
        "bank_id": harness.bank_id,
        "expected_revision": harness.boundary.workspace.bank(harness.bank_id).revision,
        "rytm_record_id": harness.records[ANALOG_RYTM_DEVICE_ID].record_id,
        "a4_record_id": harness.records[ANALOG_FOUR_DEVICE_ID].record_id,
        "rytm_slot": 20,
        "a4_slot": 21,
    }


def _files(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
            path.stat().st_mode,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def _assert_passive_events(events: list[dict[str, object]]) -> None:
    assert {event["type"] for event in events} >= {
        "session_status",
        "mutation_previewed",
        "send_plan_changed",
        "show_bank_changed",
    }
    assert {"type": "mutation_previewed", "candidate": None} in events
    assert {"type": "send_plan_changed", "send_plan": None} in events
    status = next(event for event in events if event["type"] == "session_status")
    assert status["armed"] is False


@pytest.mark.parametrize("origin", ["file_import", "input_capture"])
def test_public_library_adoption_preserves_exact_sources_and_historical_provenance(
    tmp_path: Path, origin: SourceOrigin
) -> None:
    harness = _offline_boundary(tmp_path, origin=origin)
    boundary = harness.boundary
    library_before = _files(harness.library.library_dir)
    ack, events = _command(
        boundary.session, "show_bank_adopt_library_sources", **_adoption_body(harness)
    )
    assert ack["ok"] is True, ack
    entry_id = cast(str, ack["show_bank_entry_id"])
    bank = boundary.workspace.bank(harness.bank_id)
    entry = bank.entry(entry_id)
    assert is_catalog_only_show_bank(bank)
    assert boundary.workspace.original_source_frames(harness.bank_id, entry_id) == harness.frames
    assert boundary.session.kit_captures == {}
    assert boundary.session.recalled_offline_favorite is True
    assert boundary.session.armed_apply is None and not boundary.session.hardware_intent
    assert boundary.session.current_candidate is None and boundary.session.current_send_plan is None
    for source, device_id, slot in (
        (entry.rytm_source, ANALOG_RYTM_DEVICE_ID, 20),
        (entry.analog_four_source, ANALOG_FOUR_DEVICE_ID, 21),
    ):
        record = harness.records[device_id]
        assert source.capture_id.startswith("file-")
        assert source.hardware_slot == slot
        assert source.captured_at.isoformat() == record.captured_at
        assert source.captured_at < boundary.clock() - timedelta(days=29)
        assert source.sysex.retained is not None
        assert boundary.store.read_retained(source.sysex.retained) == harness.frames[device_id]
        assert source.evidence[0].source == "Library file source (not a fresh physical capture)"
        assert source.evidence[0].observed_at == source.captured_at
        assert harness.library.get(record.record_id).source_origin == origin
    projected = boundary.session.device.capture_snapshot()
    assert projected.snapshot_id == entry.rytm_source.snapshot_id
    assert projected.captured_at == entry.rytm_source.captured_at
    offline_a4 = boundary.session.offline_a4_capture
    assert offline_a4 is not None and offline_a4.frame == harness.frames[ANALOG_FOUR_DEVICE_ID]
    assert _files(harness.library.library_dir) == library_before
    _assert_passive_events(events)
    for command in ("prepare_send_plan", "show_bank_run_preflight", "send"):
        refused, _ = _command(
            boundary.session,
            command,
            bank_id=harness.bank_id,
            entry_id=entry_id,
            expected_revision=bank.revision,
            confirm=True,
        )
        assert refused["ok"] is False, (command, refused)
    assert boundary.session.kit_captures == {}
    assert not boundary.workspace.state_dict()["banks"][0]["readiness"]["show_ready"]


@pytest.mark.parametrize("armed", [False, True])
def test_public_library_adoption_revokes_preexisting_mock_plan_and_output_authority(
    tmp_path: Path, armed: bool
) -> None:
    harness = _offline_boundary(tmp_path)
    session = harness.boundary.session
    provider = _FakeProvider()
    if armed:
        session.arm_secret = "offline-test-arm-secret"
        session.arm_port_provider = provider
        ack, _ = _command(
            session,
            "arm",
            arm_token=session.arm_secret,
            confirm=True,
            port_name=provider.port.name,
        )
        assert ack["ok"] is True, ack
        assert session.armed_apply is not None and session.hardware_intent
    previous_plan = _stage_send(session)
    session.clear_pending_events()
    session.preview_on = True
    ack, events = _command(session, "show_bank_adopt_library_sources", **_adoption_body(harness))
    assert ack["ok"] is True, ack
    assert session.current_candidate is None and session.current_send_plan is None
    assert session.armed_apply is None and not session.hardware_intent
    _assert_passive_events(events)
    refused, _ = _command(session, "send", confirm=True, send_plan_id=previous_plan.plan_id)
    assert refused["ok"] is False
    assert provider.port.sent == [] and provider.port.closed == int(armed)
    assert session.kit_captures == {}


@pytest.mark.parametrize(
    "field, value",
    [
        ("rytm_record_id", True),
        ("a4_record_id", 123),
        ("rytm_record_id", "../source"),
        ("a4_record_id", "a/b"),
        ("rytm_record_id", "a\\b"),
        ("a4_record_id", "a" * 129),
        ("rytm_record_id", ""),
        ("a4_record_id", "missing-record"),
        ("bank_id", "../outside"),
        ("expected_revision", True),
        ("expected_revision", 999),
        ("rytm_slot", True),
        ("a4_slot", False),
        ("rytm_slot", 0),
        ("a4_slot", 129),
        ("rytm_slot", -1),
        ("a4_slot", 20.5),
        ("rytm_slot", "20"),
        ("a4_slot", None),
        ("allow_legacy_reconstruction", "true"),
    ],
)
def test_public_library_adoption_refuses_ambiguous_ids_slots_and_revision_without_publication(
    tmp_path: Path, field: str, value: object
) -> None:
    harness = _offline_boundary(tmp_path)
    body = {**_adoption_body(harness), field: value}
    before = _files(tmp_path)
    bank_before = harness.boundary.workspace.bank(harness.bank_id)
    snapshot_before = harness.boundary.session.device.capture_snapshot()
    ack, events = _command(harness.boundary.session, "show_bank_adopt_library_sources", **body)
    assert ack["ok"] is False, ack
    assert ack["code"] == "validation_error"
    assert events == []
    assert harness.boundary.workspace.bank(harness.bank_id) == bank_before
    assert harness.boundary.session.device.capture_snapshot() == snapshot_before
    assert harness.boundary.session.kit_captures == {}
    assert _files(tmp_path) == before


@pytest.mark.parametrize(
    "fault", ["no-library", "swapped-family", "identity", "schema", "family", "frame"]
)
def test_public_library_adoption_refuses_untrusted_second_source_atomically(
    tmp_path: Path, fault: str
) -> None:
    harness = _offline_boundary(tmp_path)
    session = harness.boundary.session
    body = _adoption_body(harness)
    a4_record = harness.records[ANALOG_FOUR_DEVICE_ID]
    path = harness.library.library_dir / f"{a4_record.record_id}.json"
    if fault == "no-library":
        session.library_store = None
    elif fault == "swapped-family":
        body["a4_record_id"] = harness.records[ANALOG_RYTM_DEVICE_ID].record_id
    elif fault == "frame":
        assert a4_record.source_frame is not None
        (harness.library.library_dir / a4_record.source_frame.artifact_name).write_bytes(
            b"\xf0\x00\xf7"
        )
    else:
        raw = json.loads(path.read_bytes())
        key, value = {
            "identity": ("record_id", "another-record"),
            "schema": ("schema_version", 999),
            "family": ("device_id", ANALOG_RYTM_DEVICE_ID),
        }[fault]
        raw[key] = value
        path.write_text(json.dumps(raw), encoding="utf-8")
    old_plan = _stage_send(session)
    session.clear_pending_events()
    old_candidate = session.current_candidate
    bank_before = harness.boundary.workspace.bank(harness.bank_id)
    before = _files(tmp_path)
    ack, events = _command(session, "show_bank_adopt_library_sources", **body)
    assert ack["ok"] is False, ack
    assert events == []
    assert str(tmp_path) not in json.dumps(ack)
    assert harness.boundary.workspace.bank(harness.bank_id) == bank_before
    assert session.current_candidate is old_candidate and session.current_send_plan is old_plan
    assert session.kit_captures == {}
    assert _files(tmp_path) == before


def _export_favorite(harness: _OfflineBoundary) -> tuple[str, str]:
    boundary = harness.boundary
    session = boundary.session
    ack, _ = _command(session, "show_bank_adopt_library_sources", **_adoption_body(harness))
    assert ack["ok"] is True, ack
    entry_id = cast(str, ack["show_bank_entry_id"])
    for device_id, parameter in (
        (ANALOG_RYTM_DEVICE_ID, "flt"),
        (ANALOG_FOUR_DEVICE_ID, "filter2_resonance"),
    ):
        ack, _ = _command(
            session,
            "set_mutation_parameters",
            device_id=device_id,
            parameter_cells=[{"item_id": 1, "parameter_key": parameter}],
        )
        assert ack["ok"] is True, ack
    ack, _ = _command(
        session,
        "show_bank_generate_candidates",
        bank_id=harness.bank_id,
        entry_id=entry_id,
        expected_revision=boundary.workspace.bank(harness.bank_id).revision,
        profile_id="scene-industrial",
        depth_preset="small",
        depth=0.25,
        seed=99,
        candidate_count=1,
        rytm_targets=[1],
        rytm_locks=[],
        a4_targets=[1],
        a4_locks=[],
    )
    assert ack["ok"] is True, ack
    candidate_id = cast(list[str], ack["candidate_ids"])[0]
    ack, _ = _command(
        session,
        "show_bank_mark_favorite",
        bank_id=harness.bank_id,
        entry_id=entry_id,
        candidate_id=candidate_id,
        expected_revision=boundary.workspace.bank(harness.bank_id).revision,
    )
    assert ack["ok"] is True, ack
    ack, _ = _command(
        session,
        "show_bank_export",
        bank_id=harness.bank_id,
        expected_revision=boundary.workspace.bank(harness.bank_id).revision,
        artifact_name="offline-source-pack",
    )
    assert ack["ok"] is True, ack
    return entry_id, candidate_id


@pytest.mark.parametrize("armed", [False, True])
def test_public_import_copy_preserves_original_namespace_exact_favorite_and_revokes_old_plan(
    tmp_path: Path, armed: bool
) -> None:
    harness = _offline_boundary(tmp_path)
    boundary = harness.boundary
    session = boundary.session
    entry_id, candidate_id = _export_favorite(harness)
    original_bank = boundary.workspace.bank(harness.bank_id)
    original_files = _files(boundary.store.root)
    library_before = _files(harness.library.library_dir)
    favorite_context = boundary.workspace.favorite_context(harness.bank_id, entry_id)
    provider = _FakeProvider()
    if armed:
        session.arm_secret = "offline-test-arm-secret"
        session.arm_port_provider = provider
        ack, _ = _command(
            session,
            "arm",
            arm_token=session.arm_secret,
            confirm=True,
            port_name=provider.port.name,
        )
        assert ack["ok"] is True, ack
    # Seed an unrelated, genuinely prepared mock plan, not a fabricated sentinel.
    mock = _boundary(tmp_path / "mock-state")
    previous_plan = _stage_send(mock.session)
    session.current_candidate = mock.session.current_candidate
    session.current_send_plan = previous_plan
    session.preview_on = True
    ack, events = _command(
        session,
        "show_bank_import",
        pack_name="offline-source-pack",
        destination_bank_id="offline-copy",
    )
    assert ack["ok"] is True, ack
    assert cast(dict[str, object], ack["show_pack_import"])["bank_id"] == "offline-copy"
    assert boundary.workspace.bank(harness.bank_id) == original_bank
    after = _files(boundary.store.root)
    assert all(after[name] == contents for name, contents in original_files.items())
    assert _files(harness.library.library_dir) == library_before
    imported = boundary.workspace.bank("offline-copy")
    assert is_catalog_only_show_bank(imported)
    assert imported.entry(entry_id).favorite_candidate.candidate_id == candidate_id
    assert imported.entry(entry_id).candidates == original_bank.entry(entry_id).candidates
    assert imported.entry(entry_id).rytm_source == original_bank.entry(entry_id).rytm_source
    assert (
        imported.entry(entry_id).analog_four_source
        == original_bank.entry(entry_id).analog_four_source
    )
    restarted = ShowKitForgeWorkspace(boundary.store)
    assert restarted.original_source_frames("offline-copy", entry_id) == harness.frames
    assert restarted.favorite_context("offline-copy", entry_id) == favorite_context
    assert session.current_candidate is None and session.current_send_plan is None
    assert session.armed_apply is None and not session.hardware_intent
    assert session.recalled_offline_favorite
    assert session.kit_captures == {}
    assert provider.port.sent == [] and provider.port.closed == int(armed)
    _assert_passive_events(events)
    refused, _ = _command(session, "send", confirm=True, send_plan_id=previous_plan.plan_id)
    assert refused["ok"] is False
    before_collision = _files(tmp_path)
    collision, collision_events = _command(
        session,
        "show_bank_import",
        pack_name="offline-source-pack",
        destination_bank_id="offline-copy",
    )
    assert collision["ok"] is False and collision_events == []
    assert _files(tmp_path) == before_collision


@pytest.mark.parametrize(
    "destination", [True, 12, "", "../bank", "a/b", "a\\b", "a" * 129, "bank-source"]
)
def test_public_import_refuses_invalid_or_existing_destination_without_partial_publication(
    tmp_path: Path, destination: object
) -> None:
    harness = _offline_boundary(tmp_path)
    _export_favorite(harness)
    before = _files(tmp_path)
    banks_before = harness.boundary.workspace.banks
    ack, events = _command(
        harness.boundary.session,
        "show_bank_import",
        pack_name="offline-source-pack",
        destination_bank_id=destination,
    )
    assert ack["ok"] is False, ack
    assert events == []
    assert harness.boundary.workspace.banks == banks_before
    assert _files(tmp_path) == before


@pytest.mark.parametrize("fault", ["manifest-id", "schema", "family", "bytes", "no-service"])
def test_public_import_refuses_corrupt_pack_without_publishing_or_changing_prior_state(
    tmp_path: Path, fault: str
) -> None:
    harness = _offline_boundary(tmp_path)
    _export_favorite(harness)
    boundary = harness.boundary
    session = boundary.session
    manifest_path = boundary.pack_root / "offline-source-pack.show-pack" / "manifest.json"
    if fault == "no-service":
        session.show_pack_service = None
    elif fault == "bytes":
        source = harness.records[ANALOG_FOUR_DEVICE_ID].source_frame
        assert source is not None
        (manifest_path.parent / source.artifact_name).write_bytes(b"\xf0\x00\xf7")
    else:
        manifest = json.loads(manifest_path.read_bytes())
        if fault == "manifest-id":
            manifest["bank"]["bank_id"] = "../outside"
        elif fault == "schema":
            manifest["bank"]["schema_version"] = "show-bank-v999"
        else:
            manifest["bank"]["entries"][0]["analog_four_source"][
                "device_id"
            ] = ANALOG_RYTM_DEVICE_ID
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    candidate_before = session.current_candidate
    banks_before = boundary.workspace.banks
    history_before = session.history_store.current
    snapshot_before = session.device.capture_snapshot()
    before = _files(tmp_path)
    ack, events = _command(
        session,
        "show_bank_import",
        pack_name="offline-source-pack",
        destination_bank_id="refused-copy",
    )
    assert ack["ok"] is False, ack
    assert events == []
    assert str(tmp_path) not in json.dumps(ack)
    assert boundary.workspace.banks == banks_before
    assert session.current_candidate is candidate_before
    assert session.history_store.current == history_before
    assert session.device.capture_snapshot() == snapshot_before
    assert session.kit_captures == {}
    assert _files(tmp_path) == before
