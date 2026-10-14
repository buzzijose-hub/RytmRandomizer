"""Authenticated, nonwriting migration and schema-1 downgrade refusal."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export import reference_sound_store as store_module
from rytm_randomizer.cockpit.export.reference_sound_errors import reference_sound_failure_reason
from rytm_randomizer.cockpit.export.reference_sound_session import (
    PreparedReferenceSound,
    ReferenceSoundWorkspace,
)
from rytm_randomizer.cockpit.export.reference_sound_store import (
    REFERENCE_SOUND_SCHEMA,
    REFERENCE_SOUND_STORE_ID,
    ReferenceSoundStore,
    reference_sound_digest,
    reference_sound_json,
)
from rytm_randomizer.data.persisted_state import (
    PERSISTED_STATE_STORES,
    PersistedStateDecision,
    PersistedStateMigration,
    classify_payload,
)
from rytm_randomizer.observability.errors import (
    BoundaryError,
    DataError,
    PersistedStateVersionError,
)
from rytm_randomizer.observability.metrics import get_metrics

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def _write_manifest(directory: Path, payload: Mapping[str, object]) -> Path:
    path = directory / f"{payload['session_id']}.sound.json"
    document = {
        **payload,
        "content_sha256": reference_sound_digest(reference_sound_json(payload)),
    }
    path.write_bytes(reference_sound_json(document))
    return path


@pytest.mark.parametrize("explicit_version", [False, True])
def test_registered_migration_changes_only_envelope_when_legacy_evidence_is_absent(
    explicit_version: bool,
) -> None:
    legacy: dict[str, object] = {
        "session_id": "sound-" + "a" * 32,
        "context": {"parameters": ["noise_fade"], "locks": [], "strength": 1},
        "analysis": {"report": {}, "features": {}, "evidence": {}},
        "candidates": [{"candidate_id": "b" * 64}],
        "favorites": ["b" * 64],
        "recordings": [],
        "refinements": [],
    }
    if explicit_version:
        legacy["schema_version"] = 1
    before = copy.deepcopy(legacy)
    declaration = PERSISTED_STATE_STORES[REFERENCE_SOUND_STORE_ID]
    assert declaration.schema_version == REFERENCE_SOUND_SCHEMA == 2
    assert [(step.from_version, step.to_version) for step in declaration.migrations] == [(1, 2)]
    decision = classify_payload(REFERENCE_SOUND_STORE_ID, legacy)
    assert decision.code == "persisted_state.migrated"
    assert (decision.from_version, decision.to_version) == (1, 2)
    assert len(decision.steps) == 1
    assert decision.payload == {**legacy, "schema_version": 2}
    assert legacy == before


@pytest.mark.parametrize("explicit_version", [False, True])
def test_load_migrates_authenticated_original_without_rewriting_it(
    reference_sound_workspace: ReferenceSoundWorkspace, explicit_version: bool
) -> None:
    workspace = reference_sound_workspace
    current = workspace.import_reference(make_reference_pcm(), "Retained")
    legacy = {**current, "schema_version": 1}
    if not explicit_version:
        del legacy["schema_version"]
    path = _write_manifest(workspace.store.directory, legacy)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    counter = get_metrics().persisted_state_migrations
    key = f"{REFERENCE_SOUND_STORE_ID}:1->2"
    count = counter[key]
    assert workspace.store.load(current["session_id"]) == current
    assert counter[key] == count + 1
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert workspace.reopen(current["session_id"]) == current
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize(
    "corruption", ["title", "version", "missing_checksum", "migrated_checksum", "session_id"]
)
def test_original_checksum_and_identity_are_checked_before_any_migration(
    reference_sound_workspace: ReferenceSoundWorkspace,
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    workspace = reference_sound_workspace
    current = workspace.import_reference(make_reference_pcm(), "Original")
    legacy = {**current, "schema_version": 1}
    path = _write_manifest(workspace.store.directory, legacy)
    document = json.loads(path.read_bytes())
    if corruption == "title":
        document["title"] = "Changed without authenticating the original"
    elif corruption == "version":
        document["schema_version"] = 2
    elif corruption == "session_id":
        document["session_id"] = "sound-" + "b" * 32
    elif corruption == "missing_checksum":
        del document["content_sha256"]
    else:
        document["content_sha256"] = reference_sound_digest(reference_sound_json(current))
    path.write_bytes(reference_sound_json(document))
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    metrics = dict(get_metrics().persisted_state_migrations)

    def unexpected_classification(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Unauthenticated original state must not reach migration.")

    monkeypatch.setattr(store_module, "classify_payload", unexpected_classification)
    with pytest.raises(ValueError, match="corrupt"):
        workspace.store.load(current["session_id"])
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert dict(get_metrics().persisted_state_migrations) == metrics


def test_migration_failure_refuses_original_without_partial_payload_or_rewrite(
    reference_sound_workspace: ReferenceSoundWorkspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = reference_sound_workspace
    current = workspace.import_reference(make_reference_pcm(), "Retained")
    path = _write_manifest(workspace.store.directory, {**current, "schema_version": 1})
    before = (path.read_bytes(), path.stat().st_mtime_ns)

    def failed_migration(_payload: Mapping[str, object]) -> Mapping[str, object]:
        raise ValueError("Test-owned unconvertible state")

    declaration = replace(
        PERSISTED_STATE_STORES[REFERENCE_SOUND_STORE_ID],
        migrations=(PersistedStateMigration(1, failed_migration, "Failed test migration."),),
    )
    monkeypatch.setattr(
        store_module,
        "classify_payload",
        lambda store_id, payload, **kwargs: classify_payload(
            store_id, payload, store=declaration, **kwargs
        ),
    )
    counter = get_metrics().persisted_state_refusals_by_code
    key = f"{REFERENCE_SOUND_STORE_ID}:migration_failed"
    count = counter[key]
    with pytest.raises(DataError) as failure:
        workspace.store.load(current["session_id"])
    assert failure.value.context["reason"] == "persisted_state.migration_failed"
    assert counter[key] == count + 1
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize("defect", ["missing", "boolean", "version", "session_id"])
def test_loader_refuses_invalid_accepting_decision_without_recording_success(
    reference_sound_workspace: ReferenceSoundWorkspace,
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    workspace = reference_sound_workspace
    current = workspace.import_reference(make_reference_pcm(), "Retained")
    path = _write_manifest(workspace.store.directory, {**current, "schema_version": 1})
    before = path.read_bytes()
    migrated: dict[str, object] | None = dict(current)
    if defect == "missing":
        migrated = None
    elif defect == "session_id":
        migrated["session_id"] = "sound-" + "b" * 32
    else:
        migrated["schema_version"] = True if defect == "boolean" else 3
    decision = PersistedStateDecision(
        "persisted_state.migrated", REFERENCE_SOUND_STORE_ID, 1, 2, migrated
    )
    monkeypatch.setattr(store_module, "classify_payload", lambda *_args, **_kwargs: decision)
    metrics = dict(get_metrics().persisted_state_migrations)
    with pytest.raises(ValueError, match="corrupt"):
        workspace.store.load(current["session_id"])
    assert path.read_bytes() == before
    assert dict(get_metrics().persisted_state_migrations) == metrics


@pytest.mark.parametrize("stale", [False, True])
def test_publication_uses_migrated_canonical_freshness_without_a_read_side_write(
    reference_sound_workspace: ReferenceSoundWorkspace, stale: bool
) -> None:
    workspace = reference_sound_workspace
    current = workspace.import_reference(make_reference_pcm(), "Legacy title")
    legacy = {**current, "schema_version": 1}
    path = _write_manifest(workspace.store.directory, legacy)
    before = path.read_bytes()
    loaded = workspace.reopen(current["session_id"])
    updated = {**loaded, "title": "Explicit publication"}
    prepared = PreparedReferenceSound(
        updated, {}, reference_sound_digest(reference_sound_json(loaded))
    )
    assert path.read_bytes() == before
    if stale:
        _write_manifest(workspace.store.directory, {**legacy, "title": "Other writer"})
        before = path.read_bytes()
        with pytest.raises(BoundaryError, match="changed while working"):
            workspace.commit(prepared)
        assert path.read_bytes() == before
    else:
        assert workspace.commit(prepared) == updated
        assert workspace.reopen(current["session_id"]) == updated
        document = json.loads(path.read_bytes())
        assert document["schema_version"] == 2
        assert document["content_sha256"] == reference_sound_digest(reference_sound_json(updated))


def test_schema_one_reader_refuses_new_fields_before_strict_record_validation(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    imported = workspace.import_reference(make_reference_pcm(), "New evidence")
    frame, device, target, parameters = reference_sound_source
    if device == "analog_four_mk2":
        parameters += ("noise_fade",)
    generated = workspace.commit(
        workspace.generate(
            imported["session_id"],
            source_frame=frame,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=1.0,
            cancel=Event(),
        )
    )
    candidate = generated["candidates"][0]
    measured = workspace.commit(
        workspace.compare(
            generated["session_id"],
            candidate["candidate_id"],
            candidate_sha256=candidate["frame_sha256"],
            recording=make_reference_pcm(frames=801),
            cancel=Event(),
        )
    )
    assert measured["schema_version"] == 2
    assert "diagnostics" in measured["analysis"]
    assert {"segment", "pitch_comparison"} <= measured["recordings"][0].keys()
    if device == "analog_four_mk2":
        assert measured["context"]["inference_version"] == 2
    before = {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()}
    # Model the installed schema-1 declaration, exercising the real loader's
    # canonical refusal before the old exact-key DTO reader can see new fields.
    older = replace(
        PERSISTED_STATE_STORES[REFERENCE_SOUND_STORE_ID], schema_version=1, migrations=()
    )
    monkeypatch.setattr(store_module, "REFERENCE_SOUND_SCHEMA", 1)
    monkeypatch.setattr(
        store_module,
        "classify_payload",
        lambda store_id, payload, **kwargs: classify_payload(
            store_id, payload, store=older, **kwargs
        ),
    )
    with pytest.raises(PersistedStateVersionError) as failure:
        ReferenceSoundStore(workspace.store.directory).load(measured["session_id"])
    assert failure.value.fingerprint == "persisted_state.schema_newer_than_app"
    assert reference_sound_failure_reason(failure.value) == "schema_newer"
    assert failure.value.context["found_version"] == 2
    assert failure.value.context["app_version"] == 1
    assert {path.name: path.read_bytes() for path in workspace.store.directory.iterdir()} == before
